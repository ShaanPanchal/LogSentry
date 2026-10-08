"""Classification: temporal split, model comparison, final model selection.

Evaluation design
-----------------
Sessions are ordered by start time and split 60 / 20 / 20 into train /
validation / test.  Sessions that straddle a boundary are *purged* so no
session's events leak across partitions.  Models and decision thresholds are
chosen on validation only; the selected models are then refit on train+validation
and scored once on the later test period.  A random split would let a model see
the future; this one cannot.

Running this module trains the classifiers, then runs the clustering analysis
(clustering.py) and error analysis (evaluation.py) and writes everything to
results/.
"""
import argparse
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix,
                             f1_score, precision_score, recall_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from processing import COLS, PROCESSED_DIR, ROOT

SEED = 7
THRESHOLD_GRID = np.arange(.05, 1, .05)


def metrics(y, p, threshold):
    """Standard binary metrics at a probability threshold (+ PR-AUC and confusion counts)."""
    pred = p >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        'accuracy': float(accuracy_score(y, pred)),
        'precision': float(precision_score(y, pred, zero_division=0)),
        'recall': float(recall_score(y, pred, zero_division=0)),
        'f1': float(f1_score(y, pred, zero_division=0)),
        'average_precision': float(average_precision_score(y, p)),
        'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp),
        'threshold': float(threshold),
    }


def load_dataset(source):
    """Read the processed session table (the exact table the model trains on)."""
    path = PROCESSED_DIR / f'{source}_sessions.csv.gz'
    if not path.exists():
        raise FileNotFoundError(f'{path} not found. Run: python setup_data.py --source {source}')
    return pd.read_csv(path, dtype={'session_id': str})


def split(df):
    """Purged chronological 60/20/20 split. Returns (df, train_mask, val_mask, test_mask)."""
    df = df.sort_values(['t_start', 'session_id']).reset_index(drop=True)
    a = df.t_start.iloc[int(len(df) * .6)]
    b = df.t_start.iloc[int(len(df) * .8)]
    train = (df.t_start < a) & (df.t_end < a)
    val = (df.t_start >= a) & (df.t_start < b) & (df.t_end < b)
    test = df.t_start >= b
    df['split'] = np.select([train, val, test], ['train', 'validation', 'test'], default='purged')
    for name, mask in [('train', train), ('validation', val), ('test', test)]:
        if df.loc[mask, 'label'].nunique() != 2:
            raise ValueError(f'{name} must contain both classes. Use the full labelled dataset.')
    return df, train.to_numpy(), val.to_numpy(), test.to_numpy()


def candidates(seed=SEED):
    """The compared classifiers. Class imbalance (~3% anomalies) is handled by
    class weighting where the estimator supports it."""
    return {
        'Logistic regression': make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=500, class_weight='balanced', random_state=seed)),
        'Random forest': RandomForestClassifier(
            n_estimators=80, max_depth=18, min_samples_leaf=2, class_weight='balanced',
            n_jobs=2, random_state=seed),
        'Histogram gradient boosting': HistGradientBoostingClassifier(
            max_iter=100, max_leaf_nodes=31, random_state=seed),
    }


def best_threshold(y, p):
    """Probability cut-off maximising F1 on validation data."""
    return max(THRESHOLD_GRID, key=lambda t: f1_score(y, p >= t, zero_division=0))


def train_classifiers(df, tr, va, te, source):
    """Select on validation, refit on train+val, score on the test period.

    Returns (validation rows, test rows, final-model summary).
    """
    X = df[COLS].to_numpy(dtype=np.float32)
    y = df.label.to_numpy()
    dev = tr | va
    if not np.isfinite(X).all():
        raise ValueError('Nonfinite features')

    models, validation = candidates(), []
    for name, model in models.items():
        print('Fitting', source, name, flush=True)
        model.fit(X[tr], y[tr])
        p = model.predict_proba(X[va])[:, 1]
        validation.append({'model': name, **metrics(y[va], p, best_threshold(y[va], p))})
    best = max(validation, key=lambda r: (r['f1'], r['average_precision']))

    tests, final = [], None
    for name, model in models.items():
        model.fit(X[dev], y[dev])
        p = model.predict_proba(X[te])[:, 1]
        threshold = next(v['threshold'] for v in validation if v['model'] == name)
        tests.append({'model': name, **metrics(y[te], p, threshold)})
        if name == best['model']:
            joblib.dump({'model': model, 'model_name': name, 'columns': COLS,
                         'threshold': threshold, 'source': source},
                        ROOT / 'models' / f'{source}_final.joblib', compress=3)
            out = df.loc[te, ['session_id', 'label']].copy()
            out['probability'] = p
            out['prediction'] = (p >= threshold).astype(int)
            out.to_csv(ROOT / 'results' / f'{source}_test_predictions.csv.gz', index=False)
            final = {'name': name, 'class': type(model).__name__, 'n_features': len(COLS),
                     'features': COLS, 'threshold': float(threshold),
                     'trained_on': 'train + validation (earliest 80% of sessions by time)',
                     'saved_to': f'models/{source}_final.joblib'}
    return validation, tests, final


def train(source):
    # Imported here to avoid a circular import (both modules reuse split()).
    import clustering
    import evaluation

    for d in ('models', 'results'):
        (ROOT / d).mkdir(exist_ok=True)
    df, tr, va, te = split(load_dataset(source))
    validation, tests, final = train_classifiers(df, tr, va, te, source)
    df[['session_id', 'split']].to_csv(ROOT / 'results' / f'{source}_splits.csv.gz', index=False)
    result = {'source': source, 'selected_model': final['name'], 'final_model': final,
              'validation': validation, 'temporal_test': tests,
              'split_counts': df.split.value_counts().to_dict()}
    (ROOT / 'results' / f'{source}_evaluation.json').write_text(json.dumps(result, indent=2))

    clustering.run(source, df=df, dev=tr | va, te=te)
    evaluation.run(source, df=df, tr=tr, va=va, te=te)
    print('Saved model and evaluation:', source, final['name'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train classifiers, cluster anomalies, analyse errors.')
    parser.add_argument('--source', choices=['HDFS', 'BGL'], default='HDFS')
    train(parser.parse_args().source)
