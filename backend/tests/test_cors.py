"""CORS: only the front end's exact origin may read API responses (never a wildcard)."""
from app.config import FRONTEND_ORIGIN

from conftest import SAMPLES, create, post_log

OTHER = 'http://evil.example'


def preflight(client, origin, method='DELETE'):
    return client.options('/api/analyses/3f6d1f0e-8a52-4c1e-9c57-0b6f7d0a1b2c', headers={
        'Origin': origin, 'Access-Control-Request-Method': method})


def test_default_front_end_origin_is_the_dev_server():
    assert FRONTEND_ORIGIN == 'http://localhost:5173'


def test_preflight_allows_only_the_front_end_origin(client):
    ok = preflight(client, FRONTEND_ORIGIN)
    assert ok.status_code == 200 and ok.headers['access-control-allow-origin'] == FRONTEND_ORIGIN
    assert 'DELETE' in ok.headers['access-control-allow-methods']
    bad = preflight(client, OTHER)
    assert bad.status_code == 400 and 'access-control-allow-origin' not in bad.headers
    assert preflight(client, FRONTEND_ORIGIN, method='PUT').status_code == 400     # methods are limited too


def test_responses_carry_the_allowed_origin_only_for_that_origin(client):
    created = create(client)
    url = f'/api/analyses/{created["analysis_id"]}'
    assert client.get(url, headers={'Origin': FRONTEND_ORIGIN}).headers['access-control-allow-origin'] == FRONTEND_ORIGIN
    assert 'access-control-allow-origin' not in client.get(url, headers={'Origin': OTHER}).headers
    assert client.get(url, headers={'Origin': FRONTEND_ORIGIN}).headers.get('access-control-allow-origin') != '*'


def test_error_responses_are_readable_by_the_front_end(client):
    # The browser only lets the page read an error body when the error response has the CORS header too.
    headers = {'Origin': FRONTEND_ORIGIN}
    not_found = client.get('/api/analyses/3f6d1f0e-8a52-4c1e-9c57-0b6f7d0a1b2c', headers=headers)
    too_big = client.post('/api/analyses', headers=headers, data={'source': 'HDFS'},
                          files={'file': ('a.log', b'x' * (5 * 1024 * 1024 + 1))})
    invalid = post_log(client, 'NOPE', SAMPLES['HDFS'].read_bytes())
    assert not_found.status_code == 404 and too_big.status_code == 413 and invalid.status_code == 422
    for response in (not_found, too_big):
        assert response.headers['access-control-allow-origin'] == FRONTEND_ORIGIN


def test_unexpected_500_is_readable_by_the_front_end_origin_only(client, monkeypatch):
    def broken(path, source):
        raise RuntimeError('boom')
    monkeypatch.setattr(client.app.state.model_service, 'analyse', broken)
    sample = SAMPLES['HDFS'].read_bytes()

    def send(origin):
        return client.post('/api/analyses', headers={'Origin': origin}, data={'source': 'HDFS'},
                           files={'file': ('a.log', sample, 'text/plain')})
    ok, other = send(FRONTEND_ORIGIN), send(OTHER)
    assert ok.status_code == other.status_code == 500
    assert ok.headers['access-control-allow-origin'] == FRONTEND_ORIGIN
    assert 'access-control-allow-origin' not in other.headers
