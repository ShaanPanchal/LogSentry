"""Pydantic models: the shape of every request and response the API accepts or returns."""
from typing import Literal, Optional

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, Field

Source = Literal['HDFS', 'BGL']

_SESSION_EXAMPLE = {'session_id': 'blk_-6161574319804418055', 'score': 0.0021, 'flagged': False, 'cluster': None,
                    'n_events': 14, 't_start': 1226389363, 't_end': 1226389371}
_FLAGGED_EXAMPLE = {'session_id': 'blk_3587508140051953248', 'score': 0.9987, 'flagged': True, 'cluster': 2,
                    'n_events': 9, 't_start': 1226389401, 't_end': 1226389460}


# ----------------------------------------------------------------------------- requests
class AnalysisForm(BaseModel):
    """The multipart form sent to POST /api/analyses."""
    model_config = ConfigDict(extra='forbid')     # unknown form fields are rejected, not ignored

    source: Source = Field(description='Which log format (and which trained model) to use.', examples=['HDFS'])
    file: UploadFile = Field(description='The log file. Must end in .log or .txt and be in time order.')


# ----------------------------------------------------------------------------- responses
class SessionResult(BaseModel):
    session_id: str = Field(description='HDFS block id (blk_...) or BGL five-minute window (window_...).')
    score: float = Field(ge=0, le=1, description=(
        "The model's anomaly score on its 0-1 scale. Higher means more anomalous. It is a model score, "
        'not a probability.'))
    flagged: bool = Field(description="True when score >= the model's saved decision threshold.")
    cluster: Optional[int] = Field(description='Nearest A2 anomaly cluster. Only flagged sessions get one.')
    n_events: int = Field(description='Number of log lines in the session.')
    t_start: int = Field(description='Unix time of the first event.')
    t_end: int = Field(description='Unix time of the last event.')


class ParseAudit(BaseModel):
    raw_lines: int = Field(0, description='Lines read from the file.')
    malformed_lines: int = Field(0, description='Lines that could not be parsed and were skipped.')
    no_session_id: int = Field(0, description='Lines that belong to no session and were skipped.')
    event_assignments: int = Field(0, description='Lines assigned to a session.')


class Summary(BaseModel):
    source: Source
    total_sessions: int
    flagged_sessions: int
    threshold: float = Field(description='Decision threshold saved with the trained model for this source.')
    audit: ParseAudit


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={'examples': [{
        'analysis_id': '3f6d1f0e-8a52-4c1e-9c57-0b6f7d0a1b2c',
        'summary': {'source': 'HDFS', 'total_sessions': 200, 'flagged_sessions': 40, 'threshold': 0.95,
                    'audit': {'raw_lines': 2819, 'malformed_lines': 0, 'no_session_id': 0, 'event_assignments': 2819}},
        'sessions': [_FLAGGED_EXAMPLE, _SESSION_EXAMPLE]}]})

    analysis_id: str = Field(description='Generated server-side identifier (UUID4). Use it to fetch or delete this analysis.')
    summary: Summary
    sessions: list[SessionResult]


class EventLine(BaseModel):
    time: int = Field(description='Unix time of the log line.')
    level: str = Field(description='Log level from the line, e.g. INFO.')
    message: str = Field(description='The log message. Untrusted text from the uploaded file: show it as plain text.')


class SessionDetail(BaseModel):
    model_config = ConfigDict(json_schema_extra={'examples': [{
        **_FLAGGED_EXAMPLE, 'source': 'HDFS', 'threshold': 0.95,
        'cluster_description': 'Cluster 2 holds 8.1% of the clustered anomalies. ...',
        'features': {'n_events': 9.0, 'duration_s': 59.0, 'error_ratio': 0.0, 'replica_deficit': 1.0},
        'events': [{'time': 1226389401, 'level': 'INFO',
                    'message': 'Receiving block blk_3587508140051953248 src: /10.250.14.224:42420 dest: /10.250.14.224:50010'}],
        'events_truncated': False}]})

    session_id: str
    source: Source
    score: float = Field(ge=0, le=1, description='Model anomaly score (0-1). Not a probability.')
    flagged: bool
    threshold: float = Field(description='The decision threshold the score was compared with.')
    cluster: Optional[int] = Field(description='Nearest A2 anomaly cluster (flagged sessions only).')
    cluster_description: Optional[str] = Field(description='A2 description of that cluster, if the session has one.')
    n_events: int
    t_start: int
    t_end: int
    features: dict[str, float] = Field(description=(
        'The structural feature values the model received (counts, timings, ratios). Context only: '
        'this is not an explanation of why the score is what it is.'))
    events: list[EventLine] = Field(description='The first log lines of the session, in time order.')
    events_truncated: bool = Field(description='True when the session has more lines than are returned here.')


class ErrorResponse(BaseModel):
    """Every error, from any endpoint, has exactly this shape."""
    error: str = Field(description='Short machine-readable error code.', examples=['not_found'])
    detail: str = Field(description='Human-readable explanation. Never contains stack traces or server paths.')
