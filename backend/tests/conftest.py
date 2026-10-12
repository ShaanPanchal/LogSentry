import pytest
from fastapi.testclient import TestClient

from app.config import REPO_ROOT
from app.main import app

SAMPLES = {s: REPO_ROOT / 'data' / 'supporting' / f'sample_{s}.log' for s in ('HDFS', 'BGL')}


@pytest.fixture(scope='module')
def client():
    # The `with` block runs the lifespan, so the models are loaded here, once, like at server start.
    with TestClient(app) as c:
        yield c


def post_log(client, source, content, filename='sample.log'):
    return client.post('/api/analyses', data={'source': source}, files={'file': (filename, content, 'text/plain')})
