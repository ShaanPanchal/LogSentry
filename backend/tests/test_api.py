"""The four endpoints, their status codes, the shared error format and the /docs content."""
import logging
import uuid

import pytest
from fastapi.testclient import TestClient

import app.config
from app.main import app as fastapi_app

from conftest import SAMPLES, assert_error, create, post_log

UNKNOWN_ID = '3f6d1f0e-8a52-4c1e-9c57-0b6f7d0a1b2c'


# ----------------------------------------------------------------------------- success
@pytest.mark.parametrize('source', ['HDFS', 'BGL'])
def test_create_then_get_returns_the_same_analysis(client, source):
    created = create(client, source)
    uuid.UUID(created['analysis_id'])                      # a generated UUID
    got = client.get(f'/api/analyses/{created["analysis_id"]}')
    assert got.status_code == 200
    assert got.json() == created
    assert created['summary']['total_sessions'] == len(created['sessions'])


@pytest.mark.parametrize('source', ['HDFS', 'BGL'])
def test_session_detail_has_real_log_lines_and_matches_the_list(client, source):
    created = create(client, source)
    raw = SAMPLES[source].read_text(encoding='utf-8', errors='replace')
    flagged = next(s for s in created['sessions'] if s['flagged'])
    normal = next(s for s in created['sessions'] if not s['flagged'])

    for listed in (flagged, normal):
        response = client.get(f'/api/analyses/{created["analysis_id"]}/sessions/{listed["session_id"]}')
        assert response.status_code == 200
        d = response.json()
        for key in ('session_id', 'score', 'flagged', 'cluster', 'n_events', 't_start', 't_end'):
            assert d[key] == listed[key]
        assert d['source'] == source and d['threshold'] == created['summary']['threshold']
        assert d['events_truncated'] is False and len(d['events']) == d['n_events'] > 0
        assert all(e['message'] in raw for e in d['events'])      # the lines come from the uploaded file
        times = [e['time'] for e in d['events']]
        assert times == sorted(times)
        assert 'n_events' in d['features'] and 'event_entropy' in d['features']
        assert (d['cluster'] is not None) == listed['flagged']
        assert bool(d['cluster_description']) == (d['cluster'] is not None)


def test_session_detail_limits_the_number_of_lines(client, monkeypatch):
    monkeypatch.setattr(app.config, 'MAX_EVENTS_PER_SESSION', 3)
    created = create(client, 'HDFS')
    sid = created['sessions'][0]['session_id']
    d = client.get(f'/api/analyses/{created["analysis_id"]}/sessions/{sid}').json()
    assert len(d['events']) == 3 and d['events_truncated'] is True and d['n_events'] > 3


def test_each_analysis_has_its_own_id_and_data(client):
    a, b = create(client, 'HDFS'), create(client, 'BGL')
    assert a['analysis_id'] != b['analysis_id']
    assert client.get(f'/api/analyses/{a["analysis_id"]}').json()['summary']['source'] == 'HDFS'
    assert client.get(f'/api/analyses/{b["analysis_id"]}').json()['summary']['source'] == 'BGL'


# ----------------------------------------------------------------------------- deletion
def test_delete_removes_the_analysis_and_its_sessions(client):
    keep, gone = create(client), create(client)
    sid = gone['sessions'][0]['session_id']

    response = client.delete(f'/api/analyses/{gone["analysis_id"]}')
    assert response.status_code == 204 and response.content == b''

    assert_error(client.get(f'/api/analyses/{gone["analysis_id"]}'), 404, 'not_found')
    assert_error(client.get(f'/api/analyses/{gone["analysis_id"]}/sessions/{sid}'), 404, 'not_found')
    assert_error(client.delete(f'/api/analyses/{gone["analysis_id"]}'), 404, 'not_found')
    assert client.get(f'/api/analyses/{keep["analysis_id"]}').status_code == 200      # the other one is untouched


def test_stored_analyses_do_not_survive_a_restart(client):
    created = create(client)
    with TestClient(fastapi_app, raise_server_exceptions=False) as restarted:      # a new lifespan = a new store
        assert_error(restarted.get(f'/api/analyses/{created["analysis_id"]}'), 404, 'not_found')


# ----------------------------------------------------------------------------- missing things (404)
def test_unknown_analysis_and_session_are_404(client):
    created = create(client)
    assert_error(client.get(f'/api/analyses/{UNKNOWN_ID}'), 404, 'not_found')
    assert_error(client.get(f'/api/analyses/{UNKNOWN_ID}/sessions/blk_1'), 404, 'not_found')
    assert_error(client.delete(f'/api/analyses/{UNKNOWN_ID}'), 404, 'not_found')
    body = assert_error(client.get(f'/api/analyses/{created["analysis_id"]}/sessions/blk_123'), 404, 'not_found')
    assert 'Session' in body['detail']
    assert_error(client.get('/api/nothing-here'), 404, 'not_found')               # unknown address


# ----------------------------------------------------------------------------- invalid input (422)
def test_invalid_form_input_is_422(client):
    sample = SAMPLES['HDFS'].read_bytes()
    body = assert_error(post_log(client, 'WINDOWS', sample), 422, 'invalid_input')
    assert 'WINDOWS' not in body['detail'] and 'source' in body['detail']          # the bad value is not echoed back
    assert_error(client.post('/api/analyses', files={'file': ('a.log', sample)}), 422, 'invalid_input')       # no source
    assert_error(client.post('/api/analyses', data={'source': 'HDFS'}), 422, 'invalid_input')                 # no file
    extra = client.post('/api/analyses', data={'source': 'HDFS', 'colour': 'red'}, files={'file': ('a.log', sample)})
    assert_error(extra, 422, 'invalid_input')                                                                 # unknown field


def test_invalid_ids_in_the_url_are_422(client):
    created = create(client)
    assert_error(client.get('/api/analyses/not-a-uuid'), 422, 'invalid_input')
    assert_error(client.delete('/api/analyses/12345'), 422, 'invalid_input')
    for bad in ('blk_abc', 'window_x', 'DROP TABLE', 'a' * 200):
        assert_error(client.get(f'/api/analyses/{created["analysis_id"]}/sessions/{bad}'), 422, 'invalid_input')


@pytest.mark.parametrize('content, source, expected', [
    (b'', 'HDFS', 'empty'),                                                       # empty file
    (b'just some text\nthat is not a log\n', 'HDFS', 'does not look like a HDFS log'),
    (SAMPLES['BGL'].read_bytes(), 'HDFS', 'does not look like a HDFS log'),       # a BGL log sent as HDFS
    (b''.join(reversed(SAMPLES['HDFS'].read_bytes().splitlines(keepends=True))), 'HDFS', 'time order'),
], ids=['empty-file', 'not-a-log', 'bgl-as-hdfs', 'out-of-order'])
def test_logs_that_cannot_be_analysed_are_422(client, content, source, expected):
    assert expected in assert_error(post_log(client, source, content), 422, 'invalid_input')['detail']


# ----------------------------------------------------------------------------- file type and size
def test_unsupported_file_type_is_415(client):
    sample = SAMPLES['HDFS'].read_bytes()
    for name in ('sample.exe', 'sample.csv', 'sample', 'sample.log.png'):
        assert_error(post_log(client, 'HDFS', sample, filename=name), 415, 'unsupported_media_type')
    assert post_log(client, 'HDFS', sample, filename='SAMPLE.TXT').status_code == 201


def test_oversized_upload_is_413_in_the_shared_format(client):
    assert_error(post_log(client, 'HDFS', b'x' * (5 * 1024 * 1024 + 1)), 413, 'payload_too_large')

    def chunks():                                                                  # no Content-Length header
        yield (b'--B\r\nContent-Disposition: form-data; name="source"\r\n\r\nHDFS\r\n'
               b'--B\r\nContent-Disposition: form-data; name="file"; filename="a.log"\r\n\r\n')
        for _ in range(6):
            yield b'x' * (1024 * 1024)
        yield b'\r\n--B--\r\n'
    response = client.post('/api/analyses', content=chunks(), headers={'Content-Type': 'multipart/form-data; boundary=B'})
    assert_error(response, 413, 'payload_too_large')


# ----------------------------------------------------------------------------- wrong method
def test_wrong_method_is_405_in_the_shared_format(client):
    assert_error(client.put('/api/analyses'), 405, 'method_not_allowed')
    assert_error(client.get('/api/analyses'), 405, 'method_not_allowed')
    assert_error(client.post(f'/api/analyses/{UNKNOWN_ID}'), 405, 'method_not_allowed')


# ----------------------------------------------------------------------------- unexpected errors (500)
@pytest.mark.parametrize('failure', [RuntimeError('boom at C:\\Users\\x\\secret.pem'), ValueError('internal detail')])
def test_unexpected_errors_are_a_generic_500_and_logged_on_the_server(client, monkeypatch, caplog, failure):
    seen = []

    def broken(path, source):
        seen.append(path)
        raise failure
    monkeypatch.setattr(client.app.state.model_service, 'analyse', broken)

    with caplog.at_level(logging.ERROR, logger='logsentry'):
        response = post_log(client, 'HDFS', SAMPLES['HDFS'].read_bytes())
    body = assert_error(response, 500, 'internal_error')
    assert 'boom' not in response.text and 'internal detail' not in response.text and 'secret' not in response.text
    assert 'try again' in body['detail']
    assert str(failure) in caplog.text                       # the real cause is in the server log only
    import os
    assert not os.path.exists(seen[0])                       # the temporary upload was still deleted


# ----------------------------------------------------------------------------- /docs
def test_docs_describe_every_endpoint_with_examples(client):
    assert client.get('/docs').status_code == 200
    spec = client.get('/openapi.json').json()
    operations = {(method.upper(), path) for path, item in spec['paths'].items() for method in item}
    assert operations == {('POST', '/api/analyses'), ('GET', '/api/analyses/{analysis_id}'),
                          ('GET', '/api/analyses/{analysis_id}/sessions/{session_id}'),
                          ('DELETE', '/api/analyses/{analysis_id}')}
    for path, item in spec['paths'].items():
        for method, op in item.items():
            assert op['summary'] and len(op['description']) > 30, (method, path)
            for status, response in op['responses'].items():
                if status.startswith('4') and status != '422' or status == '404':
                    assert response['content']['application/json']['example']['error'], (method, path, status)
    schemas = spec['components']['schemas']
    for name in ('AnalysisResponse', 'SessionDetail'):
        assert schemas[name]['examples'], name
    assert schemas['AnalysisForm']['properties']['source']['examples'] == ['HDFS']
    assert 'memory' in spec['info']['description'] and 'memory' in spec['paths']['/api/analyses']['post']['description']
