"""Loads the trained A2 models once and scores logs with them.

`analyse` follows src/predict.py step for step (same feature order, same saved threshold, same
cluster assignment); the only difference is that the joblib files are read once at startup instead
of on every call. No scoring logic is new.
"""
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .a2 import process, signed_log
from .config import MODELS_DIR, SOURCES


@dataclass
class Analysis:
    """Result of scoring one log. `sessions` has the A2 columns plus score, flagged and cluster."""
    sessions: pd.DataFrame
    audit: dict
    threshold: float
    events: dict          # session id -> [{'time', 'level', 'message'}, ...], from A2's process(keep=True)


class LogRejected(Exception):
    """The uploaded log cannot be analysed. The message is written for the user and is safe to send."""


# A2 raises plain ValueErrors. Only these known ones are the user's problem; their text is replaced with
# our own wording. Any other ValueError is a bug and is left to surface as a 500.
_REJECTIONS = (
    ('No supported sessions found',
     'No sessions were found in this file. Check that the log matches the selected source.'),
    ('out of order', 'The log is not in time order. Sort it chronologically and try again.'),
)


class ModelService:
    def __init__(self, models_dir: Path = MODELS_DIR):
        # Fails at startup (not on the first request) if a file is missing.
        self.bundles = {s: joblib.load(models_dir / f'{s}_final.joblib') for s in SOURCES}
        self.clusters = {s: joblib.load(models_dir / f'{s}_clusters.joblib') for s in SOURCES}

    def analyse(self, path: Path, source: str) -> Analysis:
        """Parse the log at `path`, build session features, then score every session.

        Raises LogRejected for logs the A2 pipeline rejects (no sessions, out of time order).
        """
        bundle = self.bundles[source]
        try:
            df, audit, events = process(path, source, keep=True)   # keep=True also returns each session's lines
        except ValueError as e:
            for marker, message in _REJECTIONS:
                if marker in str(e):
                    raise LogRejected(message) from e
            raise

        # bundle['columns'] is the exact feature order the model was trained on.
        scores = bundle['model'].predict_proba(df[bundle['columns']].to_numpy(dtype='float32'))[:, 1]
        flagged = scores >= bundle['threshold']   # threshold saved with the model, not 0.5
        df = df.drop(columns='label')
        df['score'] = scores
        df['flagged'] = flagged
        df['cluster'] = self._assign_clusters(df, flagged, source)
        return Analysis(df, audit, float(bundle['threshold']), events)

    def cluster_description(self, source: str, cluster: int):
        """The A2 text describing an anomaly cluster, or None if there is none."""
        return self.clusters[source].get('summaries', {}).get(int(cluster), {}).get('interpretation')

    def _assign_clusters(self, df: pd.DataFrame, flagged: np.ndarray, source: str) -> np.ndarray:
        """Nearest anomaly cluster for flagged sessions; -1 (no cluster) for the rest."""
        clusters = np.full(len(df), -1, dtype=int)
        if flagged.any():
            c = self.clusters[source]
            Z = c['scaler'].transform(signed_log(df.loc[flagged, c['columns']].to_numpy(dtype='float32')))
            clusters[flagged] = c['kmeans'].predict(Z)
        return clusters
