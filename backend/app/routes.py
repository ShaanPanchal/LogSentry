"""POST /api/analyses: upload a log, score its sessions with the A2 model."""
import os
import shutil
import tempfile
import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from .config import ALLOWED_EXTENSIONS
from .schemas import AnalysisResponse, ParseAudit, SessionResult, Source, Summary

router = APIRouter(prefix='/api')


@router.post('/analyses', response_model=AnalysisResponse, status_code=201, summary='Analyse a log file')
def create_analysis(request: Request,
                    source: Annotated[Source, Form(description='Which log format and model to use.')],
                    file: Annotated[UploadFile, File(description='A .log or .txt file in time order.')]):
    # A plain `def` endpoint: FastAPI runs it in a worker thread, so scoring does not block the event loop.
    name = (file.filename or '').lower()
    if not name.endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(415, 'Upload a .log or .txt file.')

    # The submitted filename is only checked above. The file is stored under a name the server generates.
    fd, path = tempfile.mkstemp(prefix='logsentry-', suffix='.log')
    try:
        with os.fdopen(fd, 'wb') as out:
            shutil.copyfileobj(file.file, out)
        analysis = request.app.state.model_service.analyse(path, source)
    except ValueError as e:      # logs the A2 pipeline rejects: no sessions found, not in time order
        raise HTTPException(422, str(e)) from e
    finally:
        os.remove(path)

    df = analysis.sessions
    sessions = [SessionResult(session_id=r['session_id'], score=float(r['score']), flagged=bool(r['flagged']),
                              cluster=int(r['cluster']) if r['cluster'] >= 0 else None,
                              n_events=int(r['n_events']), t_start=int(r['t_start']), t_end=int(r['t_end']))
                for r in df.to_dict('records')]
    audit = ParseAudit(**{k: v for k, v in analysis.audit.items() if k in ParseAudit.model_fields})
    summary = Summary(source=source, total_sessions=len(sessions), flagged_sessions=int(df['flagged'].sum()),
                      threshold=analysis.threshold, audit=audit)
    return AnalysisResponse(analysis_id=str(uuid.uuid4()), summary=summary, sessions=sessions)
