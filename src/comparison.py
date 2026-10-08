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
           'pr_auc', 'fp', 'fn', 'tp', 'tn', 'threshold']


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
            'tp': entry['tp'], 'tn': entry['tn'], 'threshold': entry['threshold']}


def test_set_hash(df, te):
    ids = sorted(df.loc[te, 'session_id'])
    return hashlib.sha1('\n'.join(ids).encode()).hexdigest()


def build(df, tr, va, te, validation, tests, final_name):
    """Assemble the comparison record from the models' validation/test metrics."""
    n_test = int(te.sum())
    # Same test set for every model: each confusion matrix covers all n_test sessions.
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
        'models_share_test_set': bool(same_size), 'models': rows}


def write(source, result):
    out = ROOT / 'results'
    out.mkdir(exist_ok=True)
    (out / f'{source}_model_comparison.json').write_text(json.dumps(result, indent=2))
    pd.DataFrame(result['models'])[COLUMNS + ['f1_gain_vs_baseline']].to_csv(
        out / f'{source}_model_comparison.csv', index=False, float_format='%.6g')


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
