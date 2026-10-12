"""The API endpoints: submit a log, read an analysis, read one session, delete an analysis.

Finished analyses are kept in memory only (see store.py): they are temporary and are lost when the
server restarts.
"""
import os
import shutil
import tempfile
import uuid
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, Path, Request, Response

from . import config
from .a2 import STRUCTURAL_COLS
from .errors import error_docs
from .model_service import Analysis, LogRejected, ModelService
from .schemas import (AnalysisForm, AnalysisResponse, EventLine, ParseAudit, SessionDetail, SessionResult,
                      Summary)
from .store import StoredAnalysis

router = APIRouter(prefix='/api', tags=['analyses'])

AnalysisId = Annotated[UUID, Path(description='The analysis_id returned when the log was submitted.',
                                  examples=['3f6d1f0e-8a52-4c1e-9c57-0b6f7d0a1b2c'])]
SessionId = Annotated[str, Path(pattern=r'^(blk_-?\d+|window_\d+)$', max_length=64,
                                description='An HDFS block id (blk_...) or a BGL window id (window_...).',
                                examples=['blk_3587508140051953248'])]

NOT_FOUND = 'Analysis not found. It may have been deleted, or the server may have restarted.'


def _stored(request: Request, analysis_id: UUID) -> StoredAnalysis:
    item = request.app.state.store.get(str(analysis_id))
    if item is None:
        raise HTTPException(404, NOT_FOUND)
    return item


def _build(analysis: Analysis, source: str, analysis_id: str, service: ModelService) -> StoredAnalysis:
    """Turn the scored log into the response models, plus a detail view for every session."""
    sessions, details = [], {}
    for r in analysis.sessions.to_dict('records'):
        sid = r['session_id']
        cluster = int(r['cluster']) if r['cluster'] >= 0 else None
        common = dict(score=float(r['score']), flagged=bool(r['flagged']), cluster=cluster,
                      n_events=int(r['n_events']), t_start=int(r['t_start']), t_end=int(r['t_end']))
        sessions.append(SessionResult(session_id=sid, **common))
        lines = analysis.events.get(sid, [])
        details[sid] = SessionDetail(
            session_id=sid, source=source, threshold=analysis.threshold, **common,
            cluster_description=service.cluster_description(source, cluster) if cluster is not None else None,
            features={c: float(r[c]) for c in STRUCTURAL_COLS},
            events=[EventLine(**e) for e in lines[:config.MAX_EVENTS_PER_SESSION]],
            events_truncated=len(lines) > config.MAX_EVENTS_PER_SESSION)

    audit = ParseAudit(**{k: v for k, v in analysis.audit.items() if k in ParseAudit.model_fields})
    summary = Summary(source=source, total_sessions=len(sessions),
                      flagged_sessions=sum(s.flagged for s in sessions), threshold=analysis.threshold, audit=audit)
    return StoredAnalysis(AnalysisResponse(analysis_id=analysis_id, summary=summary, sessions=sessions), details)


@router.post('/analyses', response_model=AnalysisResponse, status_code=201, summary='Submit a log for analysis',
             description=(
                 'Upload a **.log** or **.txt** file in time order, with `source` set to `HDFS` or `BGL`. '
                 'The log is split into sessions and each session is scored by the trained model.\n\n'
                 'Example: `curl -F source=HDFS -F file=@sample_HDFS.log http://127.0.0.1:8000/api/analyses`\n\n'
                 'The result is stored **in memory only**, under the returned `analysis_id`. It is temporary and '
                 'is lost when the server restarts.'),
             responses=error_docs(413, 415, 422, 500))
def create_analysis(request: Request, form: Annotated[AnalysisForm, Form()]):
    # A plain `def` endpoint: FastAPI runs it in a worker thread, so scoring does not block other requests.
    upload, source = form.file, form.source
    if not (upload.filename or '').lower().endswith(config.ALLOWED_EXTENSIONS):
        raise HTTPException(415, 'Upload a .log or .txt file.')

    # The submitted filename is only checked above. The file is stored under a name the server generates.
    fd, path = tempfile.mkstemp(prefix='logsentry-', suffix='.log')
    try:
        with os.fdopen(fd, 'wb') as out:
            shutil.copyfileobj(upload.file, out)
        service = request.app.state.model_service
        analysis = service.analyse(path, source)
    except LogRejected as e:
        raise HTTPException(422, str(e)) from e
    finally:
        os.remove(path)

    analysis_id = str(uuid.uuid4())
    item = _build(analysis, source, analysis_id, service)
    request.app.state.store.put(analysis_id, item)
    return item.response


@router.get('/analyses/{analysis_id}', response_model=AnalysisResponse, summary='Get an analysis',
            description=('Return the summary and every session of a stored analysis. Analyses are kept in memory '
                         'only and disappear when the server restarts or when they are deleted.'),
            responses=error_docs(404, 422))
def get_analysis(request: Request, analysis_id: AnalysisId):
    return _stored(request, analysis_id).response


@router.get('/analyses/{analysis_id}/sessions/{session_id}', response_model=SessionDetail,
            summary='Get one session in detail',
            description=('Return the score, decision, cluster, feature values and the first log lines '
                         f'(at most {config.MAX_EVENTS_PER_SESSION}) of one session of a stored analysis.'),
            responses=error_docs(404, 422))
def get_session(request: Request, analysis_id: AnalysisId, session_id: SessionId):
    item = _stored(request, analysis_id)
    detail = item.details.get(session_id)
    if detail is None:
        raise HTTPException(404, 'Session not found in this analysis.')
    return detail


@router.delete('/analyses/{analysis_id}', status_code=204, summary='Delete an analysis',
               description='Remove a stored analysis and all of its session data from memory. Returns no body.',
               responses=error_docs(404, 422))
def delete_analysis(request: Request, analysis_id: AnalysisId):
    if not request.app.state.store.delete(str(analysis_id)):
        raise HTTPException(404, NOT_FOUND)
    return Response(status_code=204)
