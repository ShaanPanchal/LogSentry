"""Prediction: raw log -> session features -> anomaly score, decision and cluster.

Uses exactly the same `processing.process()` / `features.Session` code that built
the training table, then applies the saved final classifier.  Sessions flagged
as anomalous are also assigned to the nearest anomaly cluster (clustering.py).

    python src/predict.py --source HDFS --log data/raw/HDFS_v1/HDFS.sorted.log --out predictions.csv
"""
import argparse

import joblib
import numpy as np

from clustering import signed_log
from processing import ROOT, process


def assign_clusters(df, flagged, source):
    """Nearest anomaly cluster for flagged sessions; -1 for the rest / if no cluster model."""
    clusters = np.full(len(df), -1, dtype=int)
    path = ROOT / 'models' / f'{source}_clusters.joblib'
    if flagged.any() and path.exists():
        c = joblib.load(path)
        Z = c['scaler'].transform(signed_log(df.loc[flagged, c['columns']].to_numpy(dtype='float32')))
        clusters[flagged] = c['kmeans'].predict(Z)
    return clusters


def predict(path, source, keep=False):
    """Score a log file. Returns (per-session DataFrame, parse audit, events-by-session)."""
    model_path = ROOT / 'models' / f'{source}_final.joblib'
    if not model_path.exists():
        raise ValueError(f'{source} model has not been trained. Run python setup_data.py --source {source} first.')
    bundle = joblib.load(model_path)
    df, audit, events = process(path, source, keep=keep)

    # bundle['columns'] is the exact feature order the model was trained on.
    scores = bundle['model'].predict_proba(df[bundle['columns']].to_numpy(dtype='float32'))[:, 1]
    flagged = scores >= bundle['threshold']
    # Sessions whose label is known from the log itself (BGL alert tags); -1 means unlabelled (HDFS uploads).
    audit = {**audit, 'labelled_sessions': int((df.label >= 0).sum()), 'labelled_anomalous': int((df.label == 1).sum())}
    df = df.drop(columns='label')
    df['score'] = scores
    df['decision'] = np.where(flagged, 'ANOMALY', 'NORMAL')
    df['cluster'] = assign_clusters(df, flagged, source)
    return df, audit, events


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Score a log file with the trained final model.')
    parser.add_argument('--log', required=True, help='chronologically sorted raw log')
    parser.add_argument('--source', choices=['HDFS', 'BGL'], default='HDFS')
    parser.add_argument('--out', default='predictions.csv')
    args = parser.parse_args()
    result, audit, _ = predict(args.log, args.source)
    result.to_csv(args.out, index=False)
    print(audit)
    print(f"{(result.decision == 'ANOMALY').sum():,} of {len(result):,} sessions flagged -> {args.out}")
