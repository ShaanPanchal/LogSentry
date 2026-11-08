"""Temporary in-memory storage for finished analyses.

Everything here lives in the server process only. It is lost when the server restarts, and nothing is
written to disk (the uploaded file itself is deleted as soon as it has been scored). There is no limit
on how many analyses are kept yet: that belongs to the later denial-of-service work.
"""
import threading
from dataclasses import dataclass
from typing import Optional

from .schemas import AnalysisResponse, SessionDetail


@dataclass
class StoredAnalysis:
    response: AnalysisResponse                 # what POST and GET /api/analyses/{id} return
    details: dict[str, SessionDetail]          # per-session detail views, by session id


class AnalysisStore:
    def __init__(self):
        self._items: dict[str, StoredAnalysis] = {}
        self._lock = threading.Lock()          # endpoints run in worker threads

    def put(self, analysis_id: str, item: StoredAnalysis) -> None:
        with self._lock:
            self._items[analysis_id] = item

    def get(self, analysis_id: str) -> Optional[StoredAnalysis]:
        with self._lock:
            return self._items.get(analysis_id)

    def delete(self, analysis_id: str) -> bool:
        """Remove an analysis. Returns False if it did not exist."""
        with self._lock:
            return self._items.pop(analysis_id, None) is not None
