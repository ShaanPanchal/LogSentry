"""Response-size side-channel defence: a response's size never depends on the decision."""
import pytest

import app.config
from app.routes import _analysis_response, _detail_response
from app.main import app as fastapi_app

from conftest import create


@pytest.mark.parametrize('source', ['HDFS', 'BGL'])
def test_analysis_size_depends_only_on_the_session_count(client, source):
    created = create(client, source)
    response = client.get(f'/api/analyses/{created["analysis_id"]}')
    n = len(created['sessions'])
    assert len(response.content) == app.config.SIZE_PAD_BASE_BYTES + app.config.SIZE_PAD_PER_SESSION_BYTES * n
    assert response.json() == created               # padding is whitespace only


@pytest.mark.parametrize('source', ['HDFS', 'BGL'])
def test_flipping_the_decision_does_not_change_any_size(client, source):
    created = create(client, source)
    stored = fastapi_app.state.store.get(created['analysis_id'])
    service = fastapi_app.state.model_service
    flipped = stored.response.model_copy(update=dict(sessions=[
        s.model_copy(update=dict(flagged=not s.flagged, cluster=None if s.flagged else 5, score=1 - s.score))
        for s in stored.response.sessions]))
    assert len(_analysis_response(flipped).body) == len(_analysis_response(stored.response).body)

    for d in stored.details.values():
        other = d.model_copy(update=dict(flagged=not d.flagged, cluster=None if d.flagged else 5, score=1 - d.score,
                                         cluster_description=None if d.flagged else 'x'))
        assert len(_detail_response(other, service).body) == len(_detail_response(d, service).body)


def test_without_the_defence_sizes_differ(client, monkeypatch):
    stored = fastapi_app.state.store.get(create(client)['analysis_id'])
    monkeypatch.setattr(app.config, 'UNIFORM_SIZE', False)
    flipped = stored.response.model_copy(update=dict(sessions=[
        s.model_copy(update=dict(flagged=not s.flagged)) for s in stored.response.sessions]))
    assert len(_analysis_response(flipped).body) != len(_analysis_response(stored.response).body)
