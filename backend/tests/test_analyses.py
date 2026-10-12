"""POST /api/analyses against the existing A2 pipeline (src/predict.py) on the supplied sample logs."""
import os

import app.a2  # noqa: F401  (first: puts src/ on sys.path and applies the MKL setting before numpy loads)
import joblib
import numpy as np
import pytest

from app.config import MODELS_DIR
from predict import predict as a2_predict  # the A2 reference: loads the models on every call

from conftest import SAMPLES, post_log


@pytest.mark.parametrize('source', ['HDFS', 'BGL'])
def test_scores_and_decisions_match_a2_pipeline(client, source):
    reference, ref_audit, _ = a2_predict(SAMPLES[source], source)
    response = post_log(client, source, SAMPLES[source].read_bytes())
    assert response.status_code == 201
    body = response.json()
    got = body['sessions']

    assert [s['session_id'] for s in got] == reference.session_id.tolist()
    np.testing.assert_allclose([s['score'] for s in got], reference.score.to_numpy(), rtol=0, atol=1e-12)
    assert [s['flagged'] for s in got] == (reference.decision == 'ANOMALY').tolist()
    assert [-1 if s['cluster'] is None else s['cluster'] for s in got] == reference.cluster.tolist()
    assert [s['n_events'] for s in got] == reference.n_events.tolist()
    assert [(s['t_start'], s['t_end']) for s in got] == list(zip(reference.t_start, reference.t_end))

    # The summary uses the threshold saved in the trained model file, read here independently.
    saved_threshold = joblib.load(MODELS_DIR / f'{source}_final.joblib')['threshold']
    assert body['summary']['threshold'] == pytest.approx(saved_threshold)
    assert body['summary']['source'] == source
    assert body['summary']['total_sessions'] == len(reference)
    assert body['summary']['flagged_sessions'] == int((reference.decision == 'ANOMALY').sum())
    assert body['summary']['audit']['raw_lines'] == ref_audit['raw_lines']
    assert body['analysis_id']

    # Guard against a vacuous comparison: the samples contain both normal and flagged sessions.
    assert 0 < body['summary']['flagged_sessions'] < body['summary']['total_sessions']
    assert all(0 <= s['score'] <= 1 for s in got)
    assert all((s['cluster'] is not None) == s['flagged'] for s in got)


def test_models_are_loaded_at_startup_not_per_request(client, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('joblib.load was called while serving a request')
    monkeypatch.setattr(joblib, 'load', forbidden)
    for source in ('HDFS', 'BGL', 'HDFS'):
        assert post_log(client, source, SAMPLES[source].read_bytes()).status_code == 201


def test_submitted_filename_is_never_used_as_a_storage_path(client, monkeypatch):
    seen = []
    real = client.app.state.model_service.analyse

    def spy(path, source):
        seen.append((str(path), os.path.exists(path)))
        return real(path, source)
    monkeypatch.setattr(client.app.state.model_service, 'analyse', spy)

    response = post_log(client, 'HDFS', SAMPLES['HDFS'].read_bytes(), filename='../../evil.log')
    assert response.status_code == 201
    path, existed = seen[0]
    assert existed and 'evil' not in path and os.path.basename(path).startswith('logsentry-')
    assert not os.path.exists(path)         # temporary file is removed afterwards


def test_oversized_upload_is_refused(client):
    too_big = b'x' * (5 * 1024 * 1024 + 1)
    assert post_log(client, 'HDFS', too_big).status_code == 413

    def chunks():                            # no Content-Length: the size is counted as the body streams in
        yield (b'--B\r\nContent-Disposition: form-data; name="source"\r\n\r\nHDFS\r\n'
               b'--B\r\nContent-Disposition: form-data; name="file"; filename="a.log"\r\n\r\n')
        for _ in range(6):
            yield b'x' * (1024 * 1024)
        yield b'\r\n--B--\r\n'
    response = client.post('/api/analyses', content=chunks(), headers={'Content-Type': 'multipart/form-data; boundary=B'})
    assert response.status_code == 413


def test_rejects_bad_source_extension_and_unsorted_log(client):
    sample = SAMPLES['HDFS'].read_bytes()
    assert post_log(client, 'WINDOWS', sample).status_code == 422
    assert post_log(client, 'HDFS', sample, filename='sample.exe').status_code == 415
    reversed_log = b''.join(reversed(sample.splitlines(keepends=True)))
    response = post_log(client, 'HDFS', reversed_log)
    assert response.status_code == 422 and 'order' in response.json()['detail']
