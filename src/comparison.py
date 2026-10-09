"""Five-model comparison on one shared temporal split.

Every model is trained on the same training period (and refit on train+validation),
uses the same 52 features, and is scored on the same, never-shuffled test period.
This module records that comparison and *proves* the test set is shared:

* `test_set_sha1` - hash of the test session ids; recomputed from the dataset by
  `python src/comparison.py` and compared with the stored value
* every model's confusion counts must add up to the test-set size

Outputs (results/):  <SOURCE>_model_comparison.csv   one row per model and period
                     <SOURCE>_model_comparison.json  the same plus split metadata
Reproduce with `python src/train.py` (re-fits everything) or re-verify/regenerate
the tables from saved results with `python src/comparison.py`.
"""
import argparse
import hashlib
import json

import pandas as pd

from processing import COLS, ROOT

BASELINE = 'Logistic regression'
EXTRA = ('XGBoost', 'Extra trees')  # models beyond the standard set
COLUMNS = ['model', 'role', 'period', 'accuracy', 'precision', 'recall', 'f1',
           'pr_auc', 'fp', 'fn', 'tp', 'tn', 'threshold', 'fit_seconds', 'predict_seconds']

TRAINING_PROTOCOL = (
    'Identical for all models: fit on the training period; choose the decision threshold that maximises F1 on the '
    'validation period; refit on train+validation; score once on the later test period. No shuffling, same 52 features.')

# Hyperparameters worth reporting, read from each fitted estimator (never hard-coded).
KEY_PARAMS = {
    'Logistic regression': ['C', 'max_iter', 'class_weight'],
    'Random forest': ['n_estimators', 'max_depth', 'min_samples_leaf', 'max_features', 'class_weight'],
    'Histogram gradient boosting': ['max_iter', 'max_leaf_nodes', 'learning_rate', 'early_stopping'],
    'Extra trees': ['n_estimators', 'max_depth', 'min_samples_leaf', 'bootstrap', 'class_weight'],
    'XGBoost': ['n_estimators', 'max_depth', 'learning_rate', 'tree_method'],
}

# Written profiles, source-neutral on purpose (they are reused for HDFS and BGL): they rely only on properties both
# session tables share - an imbalanced anomaly class, binary flags next to counts and durations on very different
# scales, and correlated timing features (see results/<SOURCE>_eda_summary.json). Observed performance is in the
# results tables, not asserted here.
PROFILES = {
    'Logistic regression': {
        'type': 'Linear model (L2-regularised logistic regression)',
        'learning_approach': 'Learns one weight per feature; the anomaly probability is a sigmoid of a weighted sum, '
                             'fitted by convex optimisation. It is the only model that is linear in its inputs.',
        'scaling': 'required',
        'suitability': 'Fast, interpretable baseline; class weighting offsets the anomaly class imbalance. It cannot express '
                       'feature interactions or thresholds (e.g. "no completion event AND a long gap") unless they are '
                       'hand-crafted, and durations/counts are used on their raw, heavily skewed scale.'},
    'Random forest': {
        'type': 'Bagged ensemble of deep decision trees',
        'learning_approach': 'Many trees are grown independently on bootstrap samples with random feature subsets and '
                             'their votes are averaged: variance is reduced by averaging, not by correcting errors.',
        'scaling': 'not required',
        'suitability': 'Splits are threshold tests, so mixed binary/count/duration features, skew and correlated timing '
                       'features need no transformation, and interactions between lifecycle and timing features are learned.'},
    'Histogram gradient boosting': {
        'type': 'Gradient-boosted decision trees (scikit-learn, histogram-based)',
        'learning_approach': 'Shallow trees are added one after another, each fitted to the errors of the ensemble so '
                             'far; features are pre-binned into histograms so training is fast on 575k sessions.',
        'scaling': 'not required',
        'suitability': 'Boosting concentrates on hard, borderline sessions, which matters when the anomaly class is the minority; '
                       'binning copes with the skewed feature scales. Not class-weighted: the threshold is tuned instead.'},
    'XGBoost': {
        'type': 'Gradient-boosted decision trees (XGBoost library)',
        'learning_approach': 'Boosting like the model above, but each tree is fitted using second-order (curvature) '
                             'gradient information and an explicitly regularised objective that penalises complex trees.',
        'scaling': 'not required',
        'suitability': 'Same suitability as other tree boosters for mixed, skewed tabular features; the added '
                       'regularisation limits over-fitting to rare failure patterns. Not class-weighted.'},
    'Extra trees': {
        'type': 'Extremely randomised trees ensemble',
        'learning_approach': 'Like the random forest, but split thresholds are drawn at random rather than optimised and '
                             'each tree uses the whole training set: extra randomisation lowers variance and trains faster.',
        'scaling': 'not required',
        'suitability': 'Random thresholds give smoother decision boundaries on the correlated timing features and '
                       'cheap training; class weighting offsets the rare anomaly class.'},
}


def key_params(name, model):
    """Selected hyperparameters (and iterations actually fitted) of a fitted estimator."""
    est = model.steps[-1][1] if hasattr(model, 'steps') else model
    params = est.get_params()
    out = {k: params[k] for k in KEY_PARAMS.get(name, []) if k in params}
    if hasattr(est, 'n_iter_'):  # iterations actually used (boosting rounds / solver steps), may be < max_iter
        out['n_iter_fitted'] = int(max(est.n_iter_)) if hasattr(est.n_iter_, '__len__') else int(est.n_iter_)
    return {k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v)) for k, v in out.items()}


def scaling_note(name, model):
    """Whether this run applied feature scaling."""
    needs = PROFILES[name]['scaling']
    if hasattr(model, 'steps') and any(type(s).__name__ == 'StandardScaler' for _, s in model.steps):
        return f'{needs} - StandardScaler applied inside the model pipeline'
    return needs


def role(name, final_name):
    if name == final_name:
        return 'final (deployed)'
    if name == BASELINE:
        return 'baseline'
    return 'additional' if name in EXTRA else 'compared'


def row(entry, period, final_name):
    return {'model': entry['model'], 'role': role(entry['model'], final_name), 'period': period,
            'accuracy': entry['accuracy'], 'precision': entry['precision'], 'recall': entry['recall'],
            'f1': entry['f1'], 'pr_auc': entry['average_precision'], 'fp': entry['fp'], 'fn': entry['fn'],
            'tp': entry['tp'], 'tn': entry['tn'], 'threshold': entry['threshold'],
            'fit_seconds': entry.get('fit_seconds'), 'predict_seconds': entry.get('predict_seconds')}


def test_set_hash(df, te):
    # Hash of the sorted test session ids. If two runs give the same hash they used the same test sessions.
    ids = sorted(df.loc[te, 'session_id'])
    return hashlib.sha1('\n'.join(ids).encode()).hexdigest()


def build(df, tr, va, te, validation, tests, final_name):
    """Assemble the comparison record from the models' validation/test metrics."""
    n_test = int(te.sum())
    # Same test set for every model: each confusion matrix covers all n_test sessions.
    # If every model's confusion matrix adds up to the test size, they were all scored on the same sessions.
    same_size = all(t['tn'] + t['fp'] + t['fn'] + t['tp'] == n_test for t in tests)
    base_f1 = next(t['f1'] for t in tests if t['model'] == BASELINE)
    rows = ([row(v, 'validation', final_name) for v in validation]
            + [row(t, 'test', final_name) for t in tests])
    for r in rows:
        r['f1_gain_vs_baseline'] = r['f1'] - base_f1 if r['period'] == 'test' else None
    return {
        'baseline': BASELINE, 'final_model': final_name, 'n_features': len(COLS),
        'split': {'method': 'purged chronological 60/20/20 by session start time (no shuffling)',
                  'train_sessions': int(tr.sum()), 'validation_sessions': int(va.sum()),
                  'test_sessions': n_test,
                  'test_start_time': int(df.loc[te, 't_start'].min()), 'test_end_time': int(df.loc[te, 't_end'].max()),
                  'test_anomalies': int((df.loc[te, 'label'] == 1).sum()),
                  'test_set_sha1': test_set_hash(df, te)},
        'models_share_test_set': bool(same_size), 'models': rows,
        'training_protocol': TRAINING_PROTOCOL,
        'profiles': {t['model']: {**PROFILES[t['model']], 'scaling': t['scaling'], 'key_params': t['params'],
                                   'n_features': len(COLS)} for t in tests}}


def write(source, result):
    out = ROOT / 'results'
    out.mkdir(exist_ok=True)
    (out / f'{source}_model_comparison.json').write_text(json.dumps(result, indent=2))
    pd.DataFrame(result['models'])[COLUMNS + ['f1_gain_vs_baseline']].to_csv(
        out / f'{source}_model_comparison.csv', index=False, float_format='%.6g')
    write_markdown(source, result)


def write_markdown(source, result):
    """Report-ready summary: results table, cost, and per-model profile."""
    test = [r for r in result['models'] if r['period'] == 'test']
    sp = result['split']
    lines = [f'# {source}: five-model comparison', '',
             f"Same temporal test set for every model: {sp['test_sessions']:,} sessions ({sp['test_anomalies']:,} anomalous), "
             f"{result['n_features']} features, test-id hash `{sp['test_set_sha1'][:12]}`.", '',
             result['training_protocol'], '',
             '| Model | Role | Accuracy | Precision | Recall | F1 | PR-AUC | FP | FN | Fit (s) | Predict (s) |',
             '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in test:
        lines.append(f"| {r['model']} | {r['role']} | {r['accuracy']:.4f} | {r['precision']:.4f} | {r['recall']:.4f} | "
                     f"{r['f1']:.4f} | {r['pr_auc']:.4f} | {r['fp']} | {r['fn']} | {r['fit_seconds']:.1f} | {r['predict_seconds']:.2f} |")
    lines += ['', 'Fit time is the refit on train+validation; predict time is scoring the whole test set. '
              'Timings depend on the machine (models used at most 2 CPU threads).', '']
    for name, p in result['profiles'].items():
        params = ', '.join(f'{k}={v}' for k, v in p['key_params'].items())
        lines += [f'## {name}', '', f"* **Type:** {p['type']}", f"* **Learning approach:** {p['learning_approach']}",
                  f"* **Feature scaling:** {p['scaling']}", f"* **Key configuration:** {params}",
                  f"* **Suitability for the {p['n_features']} {source} session features:** {p['suitability']}", '']
    (ROOT / 'results' / f'{source}_model_comparison.md').write_text('\n'.join(lines))


def run(source):
    """Re-verify a saved comparison against the dataset and regenerate its tables."""
    from train import load_dataset, split
    path = ROOT / 'results' / f'{source}_model_comparison.json'
    saved = json.loads(path.read_text())
    df, tr, va, te = split(load_dataset(source))
    current = test_set_hash(df, te)
    ok = current == saved['split']['test_set_sha1'] and saved['models_share_test_set']
    print(f"Test set hash {'matches' if current == saved['split']['test_set_sha1'] else 'DIFFERS FROM'} the saved comparison; "
          f"all models cover the same {saved['split']['test_sessions']:,} test sessions: {saved['models_share_test_set']}")
    write(source, saved)
    test = [r for r in saved['models'] if r['period'] == 'test']
    print(pd.DataFrame(test)[['model', 'role', 'accuracy', 'precision', 'recall', 'f1', 'pr_auc', 'fp', 'fn']]
          .to_string(index=False, float_format=lambda v: f'{v:.4f}'))
    if not ok:
        raise SystemExit('Comparison is not on a verified shared test set. Re-run python src/train.py.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verify and print the five-model comparison.')
    parser.add_argument('--source', choices=['HDFS', 'BGL'], default='HDFS')
    run(parser.parse_args().source)
