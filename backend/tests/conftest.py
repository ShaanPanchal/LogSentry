import re

import pytest
from fastapi.testclient import TestClient

from app.config import REPO_ROOT
from app.main import app

SAMPLES = {s: REPO_ROOT / 'data' / 'supporting' / f'sample_{s}.log' for s in ('HDFS', 'BGL')}


@pytest.fixture(scope='module')
def client():
    # The `with` block runs the lifespan, so the models are loaded here, once, like at server start.
    # raise_server_exceptions=False: an unexpected crash must come back as the real 500 response.
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def post_log(client, source, content, filename='sample.log'):
    return client.post('/api/analyses', data={'source': source}, files={'file': (filename, content, 'text/plain')})


def create(client, source='HDFS'):
    response = post_log(client, source, SAMPLES[source].read_bytes())
    assert response.status_code == 201, response.text
    return response.json()


def assert_error(response, status, code):
    """Every error has exactly {"error", "detail"} and leaks nothing about the server."""
    assert response.status_code == status, response.text
    assert response.headers['content-type'].startswith('application/json')
    body = response.json()
    assert set(body) == {'error', 'detail'}
    assert body['error'] == code and isinstance(body['detail'], str) and body['detail']
    assert 'Traceback' not in response.text and 'File "' not in response.text
    assert not re.search(r'[A-Za-z]:\\|/Users/|/home/|site-packages|\.py\b', response.text)
    return body
