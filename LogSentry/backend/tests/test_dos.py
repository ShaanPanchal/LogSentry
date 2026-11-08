"""Denial-of-service defence: analyses beyond the concurrency cap are refused at once with 503."""
import threading

import app.routes

from conftest import SAMPLES, assert_error, create, post_log


def test_busy_server_refuses_with_503_in_the_shared_format(client, monkeypatch):
    monkeypatch.setattr(app.routes, '_analysis_slots', threading.BoundedSemaphore(1))
    app.routes._analysis_slots.acquire()            # one analysis "already running"
    response = post_log(client, 'HDFS', SAMPLES['HDFS'].read_bytes())
    assert_error(response, 503, 'service_unavailable')
    assert response.headers['retry-after'] == '5'


def test_slot_is_released_after_success_and_after_refusal(client, monkeypatch):
    monkeypatch.setattr(app.routes, '_analysis_slots', threading.BoundedSemaphore(1))
    create(client)
    assert_error(post_log(client, 'HDFS', b'not a log at all\n'), 422, 'invalid_input')
    create(client)                                  # would be 503 if either request had kept its slot


def test_docs_list_503_for_post(client):
    assert '503' in client.get('/openapi.json').json()['paths']['/api/analyses']['post']['responses']
