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
(clustering.py), the five-model comparison record (comparison.py) and error analysis (evaluation.py) and writes everything to
results/.
"""
import argparse
import json
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix,
                             f1_score, precision_score, recall_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

import comparison
from processing import COLS, PROCESSED_DIR, ROOT

SEED = 7
# The final (deployed) model is chosen among these original three only. The
# extra models below are evaluated on the identical split and saved, but do not
# take part in final-model selection.
FINAL_CANDIDATES = ('Logistic regression', 'Random forest', 'Histogram gradient boosting')
EXTRA_MODELS = ('XGBoost', 'Extra trees')
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
        # Extra trees: like the random forest but with random split thresholds;
        # same depth/leaf limits so the comparison with it is like-for-like.
        'Extra trees': ExtraTreesClassifier(
            n_estimators=100, max_depth=18, min_samples_leaf=2, class_weight='balanced',
            n_jobs=2, random_state=seed),
        # XGBoost: regularised gradient boosting (a different implementation from
        # the histogram GB above); no resampling needed, the threshold is tuned.
        'XGBoost': XGBClassifier(
            n_estimators=100, max_depth=6, learning_rate=.1, tree_method='hist',
            n_jobs=2, random_state=seed, eval_metric='logloss'),
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
        started = time.perf_counter()
        model.fit(X[tr], y[tr])
        fit_seconds = time.perf_counter() - started
        p = model.predict_proba(X[va])[:, 1]
        validation.append({'model': name, **metrics(y[va], p, best_threshold(y[va], p)),
                           'fit_seconds': round(fit_seconds, 2)})
    best = max((v for v in validation if v['model'] in FINAL_CANDIDATES),
               key=lambda r: (r['f1'], r['average_precision']))

    tests, final = [], None
    for name, model in models.items():
        started = time.perf_counter()
        model.fit(X[dev], y[dev])
        fit_seconds = time.perf_counter() - started
        started = time.perf_counter()
        p = model.predict_proba(X[te])[:, 1]
        predict_seconds = time.perf_counter() - started
        threshold = next(v['threshold'] for v in validation if v['model'] == name)
        tests.append({'model': name, **metrics(y[te], p, threshold),
                      'fit_seconds': round(fit_seconds, 2), 'predict_seconds': round(predict_seconds, 3),
                      'scaling': comparison.scaling_note(name, model),
                      'params': comparison.key_params(name, model)})
        slug = None
        if name == best['model']:
            slug = 'final'
            out = df.loc[te, ['session_id', 'label']].copy()
            out['probability'] = p
            out['prediction'] = (p >= threshold).astype(int)
            out.to_csv(ROOT / 'results' / f'{source}_test_predictions.csv.gz', index=False)
            final = {'name': name, 'class': type(model).__name__, 'n_features': len(COLS),
                     'features': COLS, 'threshold': float(threshold),
                     'trained_on': 'train + validation (earliest 80% of sessions by time)',
                     'saved_to': f'models/{source}_final.joblib'}
        elif name in EXTRA_MODELS:
            slug = name.lower().replace(' ', '_')
        if slug:  # same bundle format for the final model and the extra models
            joblib.dump({'model': model, 'model_name': name, 'columns': COLS,
                         'threshold': threshold, 'source': source},
                        ROOT / 'models' / f'{source}_{slug}.joblib', compress=3)
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
              'extra_models': {n: f"models/{source}_{n.lower().replace(' ', '_')}.joblib" for n in EXTRA_MODELS},
              'validation': validation, 'temporal_test': tests,
              'split_counts': df.split.value_counts().to_dict()}
    (ROOT / 'results' / f'{source}_evaluation.json').write_text(json.dumps(result, indent=2))

    comparison.write(source, comparison.build(df, tr, va, te, validation, tests, final['name']))
    clustering.run(source, df=df, dev=tr | va, te=te)
    evaluation.run(source, df=df, tr=tr, va=va, te=te)
    print('Saved model and evaluation:', source, final['name'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train classifiers, cluster anomalies, analyse errors.')
    parser.add_argument('--source', choices=['HDFS', 'BGL'], default='HDFS')
    train(parser.parse_args().source)
