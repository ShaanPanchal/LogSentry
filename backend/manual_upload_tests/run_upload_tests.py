r"""Manual upload-security checks for a running LogSentry backend.

Sends harmless test uploads to POST /api/analyses on a server you have already started, and prints the expected and
actual HTTP status of each one. It checks the unsafe-file-upload defence (backend/app/upload_safety.py, and the request
size limit in backend/app/main.py) from the outside, over a real socket, as any client would see it.

This is a local test utility, not application code. It never starts, stops or changes the server's code or files, and
it only writes inside its own temporary folder, which is deleted at the end. See README.md in this folder.

Run from the repository root, with the backend already running:

    backend\.venv\Scripts\python backend\manual_upload_tests\run_upload_tests.py [--base-url URL] [--source HDFS|BGL]

Exit code: 0 every case passed; 1 at least one case FAILED (the server answered, but not as expected); 2 the server
could not be reached, or at least one case ended in a network ERROR, so the defence was not fully verified.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import select
import socket
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

KIT = Path(__file__).resolve().parent
FIXTURES = KIT / 'fixtures'
REPO_ROOT = KIT.parents[1]
CONFIG_FILE = REPO_ROOT / 'backend' / 'app' / 'config.py'
ENDPOINT = '/api/analyses'
DEFAULT_BASE_URL = 'http://127.0.0.1:8000'          # where the front end expects the API (frontend/src/config.js)
VALID = {'HDFS': FIXTURES / 'valid_hdfs.log', 'BGL': FIXTURES / 'valid_bgl.log'}
# The "error" code the API sends with each status (backend/app/errors.py, CODES).
ERROR_CODES = {400: 'bad_request', 413: 'payload_too_large', 415: 'unsupported_media_type', 422: 'invalid_input'}
BS = '\\'
CHUNK = 64 * 1024


# ============================================================================ limits
def load_config():
    """backend/app/config.py on its own (it imports nothing else from the app), so the limits are the server's own.

    It reads LOGSENTRY_MAX_UPLOAD_BYTES from this process's environment: if the server was started with a different
    value, set the same one here or pass --max-upload-bytes.
    """
    spec = importlib.util.spec_from_file_location('logsentry_config', CONFIG_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ============================================================================ test cases
@dataclass
class Case:
    label: str
    source: str
    content: Path               # the file whose bytes are uploaded
    filename: str               # the name as it should arrive, before it is written into the multipart header
    expected: int
    reason: str = ''            # text the refusal's "detail" must contain (so it is refused for the right reason)
    style: str = 'escaped'      # how backslashes in the filename are written in the header (see filename_param)
    known_limitation: bool = False


def filename_param(name: str, style: str) -> bytes:
    """The filename as written between the quotes of filename="..." in the file part's Content-Disposition header.

    escaped: each backslash is written as two backslashes, as httpx and urllib3 (requests) do.
    raw:     backslashes are written unchanged, as browsers do (WHATWG multipart/form-data encoding).
    Both write a double quote as %22. Everything else, control characters included, is sent unchanged as UTF-8.
    The two styles only differ for names that contain a backslash.
    """
    if style == 'escaped':
        name = name.replace(BS, BS * 2)
    return name.replace('"', '%22').encode('utf-8')


def make_file(folder: Path, name: str, size: int, seed: bytes) -> Path:
    """A file of exactly `size` bytes of harmless log text, in the runner's own temporary folder."""
    path = folder / name
    with open(path, 'wb') as f:
        written = 0
        while written < size:
            piece = seed[:size - written]
            f.write(piece)
            written += len(piece)
    return path


# Filename cases. Each one uploads the valid fixture for the selected source, so the name is the only thing wrong.
# (name, {style: expected status}, reason the refusal must give)
NOT_A_PATH, BAD_CHARS, CONTROL = 'not a path', 'Use only letters', 'control characters'
FILENAME_CASES = [
    ('../evil.log', {'escaped': 400}, NOT_A_PATH),
    ('..' + BS + 'evil.log', {'escaped': 400, 'raw': 400}, NOT_A_PATH),
    ('../../outside.log', {'escaped': 400}, NOT_A_PATH),
    ('subfolder/evil.log', {'escaped': 400}, NOT_A_PATH),
    ('subfolder' + BS + 'evil.log', {'escaped': 400, 'raw': 400}, NOT_A_PATH),
    ('C:evil.log', {'escaped': 400}, NOT_A_PATH),
    ('C:/Windows/evil.log', {'escaped': 400}, NOT_A_PATH),
    ('//server/share/evil.log', {'escaped': 400}, NOT_A_PATH),
    # python-multipart cuts a name that starts with "X:\" or "\\" to its last backslash-separated part before the app
    # sees it (an old Internet Explorer workaround), so these arrive as the harmless name "evil.log" and are accepted.
    # Its check runs after it has turned "\\" into "\", so the raw UNC form arrives as "\server\share\evil.log" and is
    # refused instead. See the README, "Known limitation".
    ('C:' + BS + 'Windows' + BS + 'evil.log', {'escaped': 201, 'raw': 201}, ''),
    (BS * 2 + 'server' + BS + 'share' + BS + 'evil.log', {'escaped': 201, 'raw': 400}, NOT_A_PATH),
    ('sample;whoami|more&$(id).log', {'escaped': 400}, BAD_CHARS),
    ('sample\x1b[31m.log', {'escaped': 400}, CONTROL),        # ESC (terminal colour code)
    ('sample\x00.log', {'escaped': 400}, CONTROL),            # NUL
]
BACKSLASH_PATHS = ('C:' + BS + 'Windows' + BS + 'evil.log', BS * 2 + 'server' + BS + 'share' + BS + 'evil.log')


def build_cases(source: str, max_upload: int, max_request: int, tmp: Path) -> list[tuple[str, list[Case]]]:
    other = 'BGL' if source == 'HDFS' else 'HDFS'
    valid = VALID[source]
    seed = valid.read_bytes()

    content = [
        Case('valid HDFS log, source HDFS', 'HDFS', VALID['HDFS'], 'valid_hdfs.log', 201),
        Case('valid BGL log, source BGL', 'BGL', VALID['BGL'], 'valid_bgl.log', 201),
        Case('empty file', source, FIXTURES / 'empty.log', 'empty.log', 422, 'empty'),
        Case('text file named .exe', source, FIXTURES / 'wrong_extension.exe', 'wrong_extension.exe', 415,
             'Upload a .log or .txt file'),
        Case('PNG bytes renamed .log', source, FIXTURES / 'png_renamed.log', 'png_renamed.log', 415, 'PNG'),
        Case('HDFS log sent with source BGL', 'BGL', FIXTURES / 'hdfs_content_for_bgl_source.log',
             'hdfs_content_for_bgl_source.log', 422, 'does not look like a BGL log'),
        Case('BGL log sent with source HDFS', 'HDFS', FIXTURES / 'bgl_content_for_hdfs_source.log',
             'bgl_content_for_hdfs_source.log', 422, 'does not look like a HDFS log'),
        Case(f'mostly malformed lines, source {source}', source, FIXTURES / 'malformed_lines.log',
             'malformed_lines.log', 422, f'does not look like a {source} log'),
    ]

    over_file = make_file(tmp, 'oversized_file.log', max_upload + 1, seed)
    over_request = make_file(tmp, 'oversized_request.log', max_request + 1024 * 1024, seed)
    size = [
        Case(f'file {max_upload + 1:,} bytes (limit + 1)', source, over_file, 'oversized_file.log', 413,
             'larger than'),
        Case(f'request over {max_request:,} bytes (refused on Content-Length)', source, over_request,
             'oversized_request.log', 413, 'Request body is too large'),
    ]

    names = []
    for name, outcomes, reason in FILENAME_CASES:
        for style, expected in outcomes.items():
            label = f'name "{shown(name)}"' + (f' [{style}]' if BS in name else '')
            names.append(Case(label, source, valid, name, expected, reason if expected != 201 else '', style,
                              known_limitation=name in BACKSLASH_PATHS and expected == 201))
    ordinary = f'sample_{source} (1).log'
    names.append(Case(f'name "{ordinary}"', source, valid, ordinary, 201))

    recovery = [Case(f'valid {source} upload after the rejections', source, valid, f'sample_{source}.log', 201)]
    return [('Content and type', content), ('Size', size), ('Filenames', names), ('Still usable afterwards', recovery)]


def shown(name: str) -> str:
    """A filename made safe to print: control and non-ASCII characters as \\xNN, backslashes left single."""
    return ''.join(c if ' ' <= c < '\x7f' else f'\\x{ord(c):02x}' for c in name)


# ============================================================================ HTTP over a plain socket
class NetworkError(Exception):
    """The request could not be completed, so nothing can be said about the defence."""


@dataclass
class Target:
    host: str
    port: int
    netloc: str
    prefix: str
    url: str


@dataclass
class Reply:
    status: int
    headers: dict
    body: bytes

    def json(self):
        try:
            return json.loads(self.body)
        except ValueError:
            return None


def parse_base_url(url: str) -> Target:
    parts = urlsplit(url)
    if parts.scheme != 'http' or not parts.hostname:
        raise ValueError(f'--base-url must be an http:// URL with a host, e.g. {DEFAULT_BASE_URL}')
    return Target(parts.hostname, parts.port or 80, parts.netloc, parts.path.rstrip('/'), url.rstrip('/'))


def http(target: Target, method: str, path: str, headers=(), body=(), body_size=None, timeout=60.0) -> Reply:
    """One HTTP/1.1 request on a new connection. A plain socket is used (no third-party client) so the multipart
    filename bytes are sent exactly as written, and a reply that arrives before the body is fully sent is still read."""
    try:
        sock = socket.create_connection((target.host, target.port), timeout=timeout)
    except OSError as e:
        raise NetworkError(f'cannot connect to {target.host}:{target.port} ({e.__class__.__name__}: {e})') from None
    try:
        with sock:
            lines = [f'{method} {target.prefix}{path} HTTP/1.1', f'Host: {target.netloc}', 'Connection: close', *headers]
            if body_size is not None:
                lines.append(f'Content-Length: {body_size}')
            sock.sendall(('\r\n'.join(lines) + '\r\n\r\n').encode('ascii'))
            _send_body(sock, body, body_size or 0)
            return _parse(_receive(sock))
    except socket.timeout:
        raise NetworkError(f'no complete reply within {timeout:g} s') from None
    except NetworkError:
        raise
    except OSError as e:
        raise NetworkError(f'{e.__class__.__name__}: {e}') from None
    finally:
        getattr(body, 'close', lambda: None)()        # closes the fixture file if sending stopped early


def _send_body(sock, body, size: int) -> None:
    """Send the body, but stop once the server has answered or closed: it may refuse before reading it all."""
    wait = 0.5 if size > 1024 * 1024 else 0       # time for a server that refuses on Content-Length alone to say so
    for chunk in body:
        if select.select([sock], [], [], wait)[0]:
            return
        wait = 0
        try:
            sock.sendall(chunk)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            return                                # the server stopped reading; its reply, if any, is read next


def _receive(sock) -> bytes:
    data = b''
    while not _complete(data):
        try:
            part = sock.recv(65536)
        except (ConnectionResetError, ConnectionAbortedError):
            break                                 # closed hard after replying: keep what arrived
        if not part:
            break
        data += part
    if not data:
        raise NetworkError('the server closed the connection without replying')
    return data


def _complete(data: bytes) -> bool:
    head, sep, body = data.partition(b'\r\n\r\n')
    if not sep:
        return False
    for line in head.split(b'\r\n')[1:]:
        key, _, value = line.partition(b':')
        if key.strip().lower() == b'content-length' and value.strip().isdigit():
            return len(body) >= int(value)
    return False                                  # no length given: read until the server closes


def _parse(raw: bytes) -> Reply:
    head, sep, body = raw.partition(b'\r\n\r\n')
    lines = head.decode('latin-1').split('\r\n')
    status_parts = lines[0].split(' ')
    if not sep or not lines[0].startswith('HTTP/') or len(status_parts) < 2 or not status_parts[1].isdigit():
        raise NetworkError(f'incomplete or non-HTTP reply: {lines[0][:60]!r}')
    headers = {k.strip().lower(): v.strip() for k, _, v in (line.partition(':') for line in lines[1:])}
    if 'chunked' in headers.get('transfer-encoding', '').lower():
        body = _dechunk(body)
    elif headers.get('content-length', '').isdigit():
        body = body[:int(headers['content-length'])]
    return Reply(int(status_parts[1]), headers, body)


def _dechunk(data: bytes) -> bytes:
    out = b''
    while data:
        size_line, _, data = data.partition(b'\r\n')
        size = int(size_line.split(b';')[0] or b'0', 16)
        if size == 0:
            break
        out, data = out + data[:size], data[size + 2:]
    return out


# ============================================================================ running the cases
@dataclass
class Result:
    label: str
    expected: str
    actual: str
    verdict: str                # PASS, FAIL or ERROR
    message: str
    case: Case | None = None


def upload(target: Target, case: Case, timeout: float) -> Reply:
    boundary = f'logsentry-manual-{uuid.uuid4().hex}'
    head = (f'--{boundary}\r\nContent-Disposition: form-data; name="source"\r\n\r\n{case.source}\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="').encode() \
        + filename_param(case.filename, case.style) + b'"\r\nContent-Type: text/plain\r\n\r\n'
    tail = f'\r\n--{boundary}--\r\n'.encode()

    def parts():
        yield head
        with open(case.content, 'rb') as f:
            while chunk := f.read(CHUNK):
                yield chunk
        yield tail

    size = len(head) + case.content.stat().st_size + len(tail)
    return http(target, 'POST', ENDPOINT, [f'Content-Type: multipart/form-data; boundary={boundary}'],
                parts(), size, timeout)


def error_shape_problem(reply: Reply, body) -> str:
    """'' if the refusal follows the API's {"error": "...", "detail": "..."} convention, else what is wrong."""
    if not reply.headers.get('content-type', '').startswith('application/json'):
        return f'refusal is not JSON (Content-Type {reply.headers.get("content-type")!r})'
    if not isinstance(body, dict) or set(body) != {'error', 'detail'}:
        return f'refusal body is not exactly {{"error", "detail"}}: {reply.body[:120]!r}'
    if body['error'] != ERROR_CODES.get(reply.status):
        return f'"error" is {body["error"]!r}, expected {ERROR_CODES.get(reply.status)!r}'
    if not isinstance(body['detail'], str) or not body['detail']:
        return '"detail" is missing or empty'
    return ''


def run_case(target: Target, case: Case, timeout: float, created: list[str]) -> Result:
    try:
        reply = upload(target, case, timeout)
    except NetworkError as e:
        return Result(case.label, str(case.expected), '-', 'ERROR', f'network error, no verdict: {e}', case)
    body = reply.json()
    if isinstance(body, dict) and reply.status == 201 and body.get('analysis_id'):
        created.append(body['analysis_id'])
    detail = body.get('detail') if isinstance(body, dict) and isinstance(body.get('detail'), str) else ''

    def result(verdict, message):
        return Result(case.label, str(case.expected), str(reply.status), verdict, message, case)

    if reply.status != case.expected:
        return result('FAIL', f'expected {case.expected}, got {reply.status}' + (f': {detail}' if detail else ''))
    if case.expected == 201:
        if not created or not isinstance(body, dict) or body.get('analysis_id') != created[-1]:
            return result('FAIL', '201 without an analysis_id')
        return result('PASS', f'accepted, analysis_id {created[-1]}')
    problem = error_shape_problem(reply, body)
    if problem:
        return result('FAIL', problem)
    if case.reason and case.reason not in detail:
        return result('FAIL', f'right status, but refused for another reason: {detail}')
    return result('PASS', f'{body["error"]}: {detail}')


def read_back(target: Target, analysis_id: str, timeout: float) -> Result:
    label = 'stored analysis can be read back (GET)'
    try:
        reply = http(target, 'GET', f'{ENDPOINT}/{analysis_id}', timeout=timeout)
    except NetworkError as e:
        return Result(label, '200', '-', 'ERROR', f'network error, no verdict: {e}')
    body = reply.json()
    if reply.status == 200 and isinstance(body, dict) and body.get('analysis_id') == analysis_id:
        return Result(label, '200', '200', 'PASS', f'{body["summary"]["total_sessions"]} sessions returned')
    return Result(label, '200', str(reply.status), 'FAIL', f'unexpected reply: {reply.body[:120]!r}')


# ============================================================================ output
ROW = '{:>3}  {:<62} {:>8} {:>6}  {}'


def print_row(number: int, r: Result, verbose: bool) -> None:
    flag = '  (known limitation)' if r.case and r.case.known_limitation else ''
    print(ROW.format(number, r.label, r.expected, r.actual, r.verdict + flag))
    if r.verdict != 'PASS' or verbose:
        print(f'{"":5}-> {r.message}')


def parser_view() -> dict[tuple[str, str], str] | None:
    """What python-multipart (the parser FastAPI uses) hands the app for each filename case, computed locally."""
    try:
        from python_multipart.multipart import parse_options_header
    except ImportError:
        return None
    view = {}
    for name, outcomes, _ in FILENAME_CASES:
        for style in outcomes:
            header = b'form-data; name="file"; filename="' + filename_param(name, style) + b'"'
            _, options = parse_options_header(header)
            view[(name, style)] = options.get(b'filename', b'').decode('utf-8', 'replace')
    return view


def print_parser_section(results: list[Result]) -> None:
    import importlib.metadata
    view = parser_view()
    print('\nWindows drive and UNC names with backslashes (exact multipart filename strings):')
    if view is None:
        print('  python-multipart is not installed in this interpreter, so the name the app receives cannot be shown.')
        print(r'  Run the kit with backend\.venv\Scripts\python to see it.')
    else:
        version = importlib.metadata.version('python-multipart')
        print(f'  "Arrives as" is computed locally with python-multipart {version} (backend/requirements.txt pins the'
              f' version the server uses).')
    for r in results:
        if r.case and r.case.filename in BACKSLASH_PATHS:
            arrives = f'arrives as "{shown(view[(r.case.filename, r.case.style)])}"' if view else ''
            meaning = {'201': 'ACCEPTED (stored under a generated name)', '400': 'REFUSED'}.get(r.actual, r.actual)
            print(f'  {shown(r.case.filename):<26} {r.case.style:<8} {arrives:<38} HTTP {r.actual:<4} {meaning}')
    if view:
        rewritten = [(n, s, got) for (n, s), got in view.items() if got != n]
        print(f'\n  Filename cases the parser changes before the app checks them: {len(rewritten)} of {len(view)}')
        for name, style, got in rewritten:
            print(f'    {shown(name):<26} [{style}] -> "{shown(got)}"')


def check_upload_folders(target: Target) -> None:
    """Read-only: the server's private upload folders should be empty once its requests have finished."""
    print('\nTemporary upload files (read-only check):')
    if target.host not in ('127.0.0.1', 'localhost', '::1'):
        print('  skipped: the server is not on this machine.')
        return
    folders = sorted(Path(tempfile.gettempdir()).glob('logsentry-uploads-*'))
    leftovers = []
    for folder in folders:
        try:
            leftovers += list(folder.iterdir())
        except OSError:
            pass
    print(f'  {len(folders)} logsentry-uploads-* folder(s) in {tempfile.gettempdir()}, {len(leftovers)} file(s) inside.')
    if leftovers:
        print('  WARNING: files were left behind (they may also be from an earlier server process that was killed).'
              ' Nothing was deleted:')
        for path in leftovers[:10]:
            print(f'    {path}')
    elif not folders:
        print('  No upload folder found: the server may use a different temp folder (e.g. another user account).')


def delete_created(target: Target, created: list[str], timeout: float) -> None:
    deleted = 0
    for analysis_id in created:
        try:
            deleted += http(target, 'DELETE', f'{ENDPOINT}/{analysis_id}', timeout=timeout).status == 204
        except NetworkError:
            pass
    print(f'\nRemoved {deleted} of {len(created)} analyses this run created (DELETE {ENDPOINT}/{{id}}).')


# ============================================================================ main
def parse_args(argv):
    parser = argparse.ArgumentParser(description='Manual upload-security checks for a running LogSentry backend.')
    parser.add_argument('--base-url', default=DEFAULT_BASE_URL, help=f'API base URL (default {DEFAULT_BASE_URL})')
    parser.add_argument('--source', choices=('HDFS', 'BGL'), default='HDFS',
                        help='source used for the filename, size, malformed and recovery cases (default HDFS)')
    parser.add_argument('--max-upload-bytes', type=int,
                        help='the server\'s file size limit, if it was started with a non-default '
                             'LOGSENTRY_MAX_UPLOAD_BYTES (default: read from backend/app/config.py)')
    parser.add_argument('--timeout', type=float, default=60.0, help='seconds to wait for each reply (default 60)')
    parser.add_argument('--verbose', action='store_true', help="show the server's reply for every case")
    parser.add_argument('--keep-analyses', action='store_true',
                        help='do not delete the analyses this run created (they are deleted by default)')
    parser.add_argument('--dry-run', action='store_true', help='list the cases and the parser view; send nothing')
    return parser.parse_args(argv)


def main(argv=None) -> int:
    sys.stdout.reconfigure(errors='backslashreplace')
    args = parse_args(argv)
    try:
        target = parse_base_url(args.base_url)
    except ValueError as e:
        print(f'error: {e}', file=sys.stderr)
        return 2
    config = load_config()
    max_upload = args.max_upload_bytes or config.MAX_UPLOAD_BYTES
    max_request = max_upload + config.MULTIPART_OVERHEAD_BYTES

    print(f'LogSentry manual upload-security checks -> {target.url}{ENDPOINT}')
    print(f'Source for name/size/recovery cases: {args.source}.  File limit {max_upload:,} bytes, '
          f'request limit {max_request:,} bytes.')

    with tempfile.TemporaryDirectory(prefix='logsentry-manual-upload-') as tmp:
        groups = build_cases(args.source, max_upload, max_request, Path(tmp))
        if args.dry_run:
            number = 0
            for group, cases in groups:
                print(f'\n{group}')
                for case in cases:
                    number += 1
                    print(ROW.format(number, case.label, case.expected, '', ''))
            print_parser_section([])
            return 0

        try:
            spec =http(target, 'GET', '/openapi.json', timeout=args.timeout).json() or {}
            if ENDPOINT not in spec.get('paths', {}):
                raise NetworkError(f'{target.url} answered, but GET /openapi.json does not list {ENDPOINT}: '
                                   'it is not the LogSentry API')
        except NetworkError as e:
            print(f'\nSERVER UNAVAILABLE: {e}')
            print('No cases were run, so nothing was verified. Start the backend first (see README.md):')
            print(r'  cd backend; .venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000')
            return 2
        print(f'Server reachable: {spec.get("info", {}).get("title", "?")} {spec.get("info", {}).get("version", "")}')

        results, created, number = [], [], 0
        print('\n' + ROW.format('#', 'Test', 'Expected', 'Actual', 'Result'))
        for group, cases in groups:
            print(f'\n{group}')
            for case in cases:
                number += 1
                results.append(run_case(target, case, args.timeout, created))
                print_row(number, results[-1], args.verbose)
        last = results[-1]
        if last.verdict == 'PASS':
            number += 1
            results.append(read_back(target, created[-1], args.timeout))
            print_row(number, results[-1], args.verbose)

    print_parser_section(results)
    check_upload_folders(target)
    if not args.keep_analyses:
        delete_created(target, created, args.timeout)

    counts = {v: sum(r.verdict == v for r in results) for v in ('PASS', 'FAIL', 'ERROR')}
    print(f'\nSummary: {counts["PASS"]} passed, {counts["FAIL"]} failed, {counts["ERROR"]} could not be run '
          f'(network error), of {len(results)}.')
    if counts['FAIL']:
        print('RESULT: FAIL - the server answered at least one case differently from the expected behaviour.')
        return 1
    if counts['ERROR']:
        print('RESULT: INCOMPLETE - at least one case hit a network error, so the defence was not fully verified.')
        return 2
    print('RESULT: PASS - every case matched the expected behaviour.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
