"""Unsafe-file-upload defence (Assignment 3, Section 2.7): the three required attacks and their variations.

1. Oversized upload    2. Crafted filename    3. File contents that do not match the expected type
Every refused upload must leave nothing behind in the private upload folder and never reach the model.
"""
import asyncio
import gzip
import io
import json
import os
import zipfile

import pytest

import app.routes
from app import config
from app.main import BodyLimitMiddleware

from conftest import SAMPLES, assert_error, post_log

HDFS, BGL = SAMPLES['HDFS'].read_bytes(), SAMPLES['BGL'].read_bytes()


@pytest.fixture(autouse=True)
def nothing_left_behind(client):
    """After every test the private upload folder is empty: refused or failed uploads are always cleaned up."""
    yield
    folder = client.app.state.upload_dir
    assert not os.path.exists(folder) or os.listdir(folder) == [], os.listdir(folder)


@pytest.fixture
def pipeline_calls(client, monkeypatch):
    """Records every file that reaches the model, to prove refused uploads never do."""
    calls, real = [], client.app.state.model_service.analyse
    monkeypatch.setattr(client.app.state.model_service, 'analyse', lambda path, source: calls.append(path) or real(path, source))
    return calls


@pytest.fixture
def received_names(monkeypatch):
    """Records the filename exactly as the server received it, to prove each crafted name really arrived."""
    names, real = [], app.routes.check_filename
    monkeypatch.setattr(app.routes, 'check_filename', lambda name: names.append(name) or real(name))
    return names


# =========================================================================== 1. oversized upload
def test_file_at_the_limit_is_not_refused_for_size(client):
    # Multipart overhead is allowed for: a file of exactly MAX_UPLOAD_BYTES gets past the size checks
    # (this one is then refused for its content, which is not a log).
    response = post_log(client, 'HDFS', b'a' * config.MAX_UPLOAD_BYTES)
    assert response.status_code != 413
    assert_error(response, 422, 'invalid_input')


def test_file_one_byte_over_the_limit_is_413(client, pipeline_calls):
    # The whole request is still under MAX_REQUEST_BYTES; the file itself is caught while it is copied.
    body = assert_error(post_log(client, 'HDFS', b'a' * (config.MAX_UPLOAD_BYTES + 1)), 413, 'payload_too_large')
    assert '5 MiB' in body['detail'] and pipeline_calls == []


def test_request_over_the_limit_with_honest_content_length_is_413_before_the_endpoint_runs(client, received_names):
    response = post_log(client, 'HDFS', b'a' * (config.MAX_REQUEST_BYTES + 1))
    assert_error(response, 413, 'payload_too_large')
    assert received_names == []                     # refused by the middleware, the endpoint never ran


def test_streamed_body_without_content_length_is_413(client, received_names):
    def chunks():                                   # chunked transfer: no Content-Length at all
        yield (b'--B\r\nContent-Disposition: form-data; name="source"\r\n\r\nHDFS\r\n'
               b'--B\r\nContent-Disposition: form-data; name="file"; filename="a.log"\r\n\r\n')
        for _ in range(8):
            yield b'x' * (1024 * 1024)
        yield b'\r\n--B--\r\n'
    response = client.post('/api/analyses', content=chunks(), headers={'Content-Type': 'multipart/form-data; boundary=B'})
    assert_error(response, 413, 'payload_too_large')
    assert received_names == []


# The middleware on its own, with exact control over the headers and how much body arrives.
def _run_middleware(headers, body_chunks):
    sent, pulled = [], {'bytes': 0, 'calls': 0}
    chunks = list(body_chunks)

    async def receive():
        pulled['calls'] += 1
        chunk = chunks.pop(0) if chunks else b''
        pulled['bytes'] += len(chunk)
        return {'type': 'http.request', 'body': chunk, 'more_body': bool(chunks)}

    async def send(message):
        sent.append(message)

    async def endpoint(scope, receive, send):     # reads the whole body, like a form parser would
        while (await receive()).get('more_body'):
            pass
        await send({'type': 'http.response.start', 'status': 200, 'headers': []})
        await send({'type': 'http.response.body', 'body': b'ok'})

    scope = {'type': 'http', 'method': 'POST', 'path': '/api/analyses', 'headers': headers}
    asyncio.run(BodyLimitMiddleware(endpoint, config.MAX_REQUEST_BYTES)(scope, receive, send))
    status = sent[0]['status']
    body = json.loads(sent[1]['body']) if status != 200 else None
    return status, body, pulled


MIB = b'x' * (1024 * 1024)


def test_misleading_content_length_too_small_is_counted_and_stopped():
    # Says 10 bytes, sends 20 MiB: the bytes actually received are counted, and reading stops at the limit.
    status, body, pulled = _run_middleware([(b'content-length', b'10')], [MIB] * 20)
    assert status == 413 and body['error'] == 'payload_too_large'
    assert pulled['bytes'] <= config.MAX_REQUEST_BYTES + len(MIB)   # never more than one chunk past the limit


def test_declared_oversized_content_length_is_refused_without_reading_the_body():
    status, _, pulled = _run_middleware([(b'content-length', str(config.MAX_REQUEST_BYTES + 1).encode())], [MIB] * 20)
    assert status == 413 and pulled['calls'] == 0


@pytest.mark.parametrize('value', [b'abc', b'-5', b'1e9', b'10, 10', b''])
def test_invalid_content_length_is_400(value):
    status, body, pulled = _run_middleware([(b'content-length', value)], [b'data'])
    assert status == 400 and body == {'error': 'bad_request', 'detail': 'The Content-Length header is not a valid number.'}
    assert pulled['calls'] == 0


def test_missing_content_length_small_body_is_allowed_through():
    status, _, _ = _run_middleware([], [b'small'])
    assert status == 200


# =========================================================================== 2. crafted filename
@pytest.mark.parametrize('name', [
    '../../evil.log',                 # traversal, forward slashes
    '..\\..\\evil.log',               # traversal, backslashes
    '../../../app/main.log',
    'logs/../../evil.log',
    'sub/dir.log',                    # any path separator
    'sub\\dir.log',
    '/etc/passwd.log',                # absolute paths
    '\\Windows\\evil.log',
    'C:evil.log',                     # drive letters (the backslash forms are covered separately below)
    'C:/evil.log',
    '//server/share/evil.log',        # UNC path with forward slashes
    '..log', 'a..log',                # ".." anywhere
    '.hidden.log', '-rf.log', ' lead.log',   # must start with a letter, digit, _ ( or [
    'naïve.log', 'файл.log',          # outside the permitted character set
    'evil|cmd.log', "a'b.log", 'a<b>.log', 'a;b.log', 'a$b.log', 'a*b.log', 'a?b.log',
    'x' * 97 + '.log',                # 101 characters: too long
])
def test_crafted_filenames_are_refused_with_400(client, name, pipeline_calls, received_names):
    body = assert_error(post_log(client, 'HDFS', HDFS, filename=name), 400, 'bad_request')
    assert received_names == [name], f'the crafted name did not reach the server unchanged: {received_names!r}'
    assert pipeline_calls == []
    assert name not in body['detail']                 # the message does not repeat the attacker's text


@pytest.mark.parametrize('name', ['C:\\Windows\\evil.log', '\\\\server\\share\\evil.log'], ids=['drive-backslash', 'unc-backslash'])
def test_backslash_drive_and_unc_paths_are_cut_to_a_plain_name_by_the_multipart_parser(client, name, received_names, pipeline_calls):
    # python-multipart (python_multipart/multipart.py, an old Internet Explorer 6 workaround) rewrites a filename
    # that starts with "X:\" or "\\" to its last backslash-separated part BEFORE FastAPI or our code see it. These
    # two attacks therefore arrive as the harmless name "evil.log": no path survives, and the file is stored under a
    # generated name anyway. They are not refused with 400, because the original text is no longer available.
    # check_filename itself refuses both forms (see test_filename_check_unit_cases).
    response = post_log(client, 'HDFS', HDFS, filename=name)
    assert received_names == ['evil.log']
    assert response.status_code == 201
    assert 'evil' not in os.path.basename(pipeline_calls[0])


@pytest.mark.parametrize('name, expected', [('a\x00.log', 'control'), ('a\x1b[31m.log', 'control'), ('a\x7f.log', 'control'),
                                            ('a\x85.log', 'control'), ('a\tb.log', 'control')])
def test_filenames_with_nul_or_control_characters_are_refused(client, name, expected, received_names):
    # The multipart layer may alter some of these on the way in; whatever arrives, it must not be accepted.
    response = post_log(client, 'HDFS', HDFS, filename=name)
    assert response.status_code == 400, (received_names, response.text)
    if received_names == [name]:                      # it arrived intact, so the control-character rule fired
        assert expected in response.json()['detail']


def test_filename_check_unit_cases():
    # The same rules without HTTP in between (covers names an HTTP client cannot send unchanged).
    from app.upload_safety import UploadRejected, check_filename
    for name in ['', 'a\x00.log', 'a\r\n.log', 'a\x1b.log', '../x.log', 'C:x.log', 'x' * 101 + '.log',
                 'C:\\Windows\\evil.log', '\\\\server\\share\\evil.log', 'a"b.log']:
        with pytest.raises(UploadRejected) as e:
            check_filename(name)
        assert e.value.status == 400, name
    for name in ['a.exe', 'a.log.exe', 'a.log.png', 'a.csv', 'a']:
        with pytest.raises(UploadRejected) as e:
            check_filename(name)
        assert e.value.status == 415, name
    for name in ['a.log', 'SAMPLE.TXT', 'sample_HDFS (1).log', '[2024] run-1+x,y@z=1.txt', '_x.log', 'x' * 96 + '.log']:
        check_filename(name)                          # does not raise


@pytest.mark.parametrize('name', ['sample_HDFS (1).log', 'SAMPLE.TXT', 'x' * 96 + '.log'])
def test_ordinary_filenames_are_accepted(client, name):
    assert post_log(client, 'HDFS', HDFS, filename=name).status_code == 201


@pytest.mark.parametrize('name', ['sample.exe', 'sample.log.exe', 'sample.log.png', 'sample.csv', 'sample'])
def test_wrong_extension_is_415(client, name, pipeline_calls):
    assert_error(post_log(client, 'HDFS', HDFS, filename=name), 415, 'unsupported_media_type')
    assert pipeline_calls == []


# =========================================================================== 3. content does not match the type
def _zip_bytes():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        z.writestr('sample_HDFS.log', HDFS)
    return buffer.getvalue()


@pytest.mark.parametrize('content, kind', [
    (b'\x89PNG\r\n\x1a\n' + b'\x00' * 200, 'PNG'),
    (gzip.compress(HDFS), 'gzip'),                    # the real sample, compressed, renamed .log
    (_zip_bytes(), 'zip'),
    (b'%PDF-1.7\n' + b'x' * 100, 'PDF'),
    (b'\x7fELF\x02\x01\x01' + b'\x00' * 100, 'ELF executable'),
    (b'MZ\x90\x00' + b'\x00' * 100, 'Windows executable'),
    (b'\xff\xd8\xff\xe0' + b'\x00' * 100, 'JPEG'),
    (HDFS.decode().encode('utf-16'), 'UTF-16 text'),  # the real sample in another encoding
], ids=['png', 'gzip', 'zip', 'pdf', 'elf', 'exe', 'jpeg', 'utf16'])
def test_binary_files_renamed_log_are_415(client, content, kind, pipeline_calls):
    # Content-Type says text/plain and the name says .log; neither is trusted.
    body = assert_error(post_log(client, 'HDFS', content, filename='sample.log'), 415, 'unsupported_media_type')
    assert kind in body['detail'] and pipeline_calls == []


@pytest.mark.parametrize('content, words', [
    (HDFS[:5000] + b'\x00' + HDFS[5000:], 'NUL'),     # one NUL byte inside an otherwise valid log
    (HDFS.replace(b'Receiving', b'R\xe9ceiving', 1), 'UTF-8'),   # Latin-1 byte: invalid UTF-8
    (HDFS.replace(b'Receiving', b'Rec\x1beiving', 1), 'control characters'),
    (b'\x07' * 100, 'control characters'),
], ids=['nul-inside-log', 'latin1-byte', 'escape-char', 'bell-chars'])
def test_text_with_binary_bytes_or_bad_encoding_is_415(client, content, words, pipeline_calls):
    body = assert_error(post_log(client, 'HDFS', content), 415, 'unsupported_media_type')
    assert words in body['detail'] and pipeline_calls == []


@pytest.mark.parametrize('content', [b'', b'\n\n  \r\n\t\n'], ids=['zero-bytes', 'blank-lines'])
def test_zero_byte_or_blank_files_are_422(client, content, pipeline_calls):
    assert 'empty' in assert_error(post_log(client, 'HDFS', content), 422, 'invalid_input')['detail']
    assert pipeline_calls == []


@pytest.mark.parametrize('content, source', [(BGL, 'HDFS'), (HDFS, 'BGL')], ids=['bgl-as-hdfs', 'hdfs-as-bgl'])
def test_file_under_the_wrong_source_selector_is_422(client, content, source, pipeline_calls):
    # HDFS-as-BGL matters: the A2 parser alone accepts it and invents 71 sessions from the HDFS sample.
    body = assert_error(post_log(client, source, content), 422, 'invalid_input')
    assert f'does not look like a {source} log' in body['detail'] and pipeline_calls == []


def test_mostly_junk_text_is_422_but_a_few_bad_lines_are_tolerated(client):
    lines = HDFS.splitlines(keepends=True)
    junk = [b'this is not a log line\n'] * 30
    assert_error(post_log(client, 'HDFS', b''.join(lines[:30] + junk)), 422, 'invalid_input')   # half junk
    assert post_log(client, 'HDFS', b''.join(lines[:-2] + [b'garbage line\n'])).status_code == 201  # 1 bad line in 2,818


def test_content_type_header_is_ignored_both_ways(client):
    # A genuine log sent with a misleading header is still accepted (the header is not trusted);
    # the binary cases above show a reassuring header does not get a binary file in.
    response = client.post('/api/analyses', data={'source': 'HDFS'}, files={'file': ('sample.log', HDFS, 'image/png')})
    assert response.status_code == 201


@pytest.mark.parametrize('variant', ['bom', 'crlf'])
def test_harmless_text_variants_of_a_real_log_are_accepted(client, variant):
    content = b'\xef\xbb\xbf' + HDFS if variant == 'bom' else HDFS.replace(b'\n', b'\r\n')
    assert post_log(client, 'HDFS', content).status_code == 201


@pytest.mark.parametrize('source', ['HDFS', 'BGL'])
def test_supplied_samples_still_pass_every_check(client, source):
    assert post_log(client, source, SAMPLES[source].read_bytes()).status_code == 201


# =========================================================================== storage and clean-up
def test_upload_is_stored_under_a_generated_name_in_the_private_folder(client, pipeline_calls):
    assert post_log(client, 'HDFS', HDFS, filename='sample_HDFS (1).log').status_code == 201
    path = pipeline_calls[0]
    assert os.path.dirname(path) == client.app.state.upload_dir
    assert os.path.basename(path).startswith('upload-') and 'sample' not in os.path.basename(path)


def test_temporary_file_is_removed_when_the_model_fails(client, monkeypatch):
    def broken(path, source):
        raise RuntimeError('model crashed')
    monkeypatch.setattr(client.app.state.model_service, 'analyse', broken)
    assert_error(post_log(client, 'HDFS', HDFS), 500, 'internal_error')
    # nothing_left_behind (autouse) checks the folder afterwards


def test_upload_folder_is_recreated_if_a_temp_cleaner_deleted_it(client):
    folder = client.app.state.upload_dir
    os.rmdir(folder)
    assert post_log(client, 'HDFS', HDFS).status_code == 201
    assert os.path.isdir(folder)
