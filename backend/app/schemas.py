"""Response models for POST /api/analyses."""
from typing import Literal, Optional

from pydantic import BaseModel, Field

Source = Literal['HDFS', 'BGL']


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
    raw_lines: int = 0
    malformed_lines: int = 0
    no_session_id: int = 0
    event_assignments: int = 0


class Summary(BaseModel):
    source: Source
    total_sessions: int
    flagged_sessions: int
    threshold: float = Field(description='Decision threshold saved with the trained model for this source.')
    audit: ParseAudit


class AnalysisResponse(BaseModel):
    analysis_id: str = Field(description='Generated server-side identifier (UUID4).')
    summary: Summary
    sessions: list[SessionResult]
