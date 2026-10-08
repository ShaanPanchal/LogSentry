"""Error analysis, a hard test subset, seed-stability and rolling-origin temporal folds.

`run()` is called by train.py after the final model is fitted and writes
results/<SOURCE>_error_analysis.json.  `stability()` (python src/evaluation.py
--stability) refits the models under several random seeds on the same temporal
split to show how much of the reported score is luck.
"""
import argparse
import json

import numpy as np
import pandas as pd

from clustering import describe_feature, load_bucket_templates
from processing import COLS, ROOT, collect_session_events, sorted_log_path

N_EXAMPLES = 5
KEY_FEATURES = ['n_events', 'duration_s', 'gap_max_s', 'n_hosts', 'keyword_error_ratio',
                'lifecycle_complete', 'replica_deficit', 'unacked_writes']


def differences(group, reference, scale, buckets, top=5):
    """Features whose mean differs most between two groups (in units of `scale`)."""
    if len(group) == 0 or len(reference) == 0:
        return []
    diff = (group.mean(0) - reference.mean(0)) / scale
    out = []
    for j in np.argsort(np.abs(diff))[::-1][:top]:
        meaning = describe_feature(COLS[j], buckets)
        out.append({'feature': COLS[j], 'group_mean': float(group[:, j].mean()),
                    'reference_mean': float(reference[:, j].mean()), 'z': float(diff[j]),
                    'measures': meaning[0]})
    return out


def describe_group(name, diffs, reference_name, n):
    if not diffs:
        return f'No {name} in the test period.'
    parts = []
    for d in diffs[:3]:
        direction = 'higher' if d['z'] > 0 else 'lower'
        what = f" [{d['measures'][:110]}]" if d['feature'].startswith('event_hash') else ''
        parts.append(f"{d['feature']}{what} {direction} ({d['group_mean']:.3g} vs {d['reference_mean']:.3g})")
    return f'{name} (n={n}) differ from {reference_name} mainly in: ' + '; '.join(parts) + '.'


def examples(rows, df, X, events):
    out = []
    for _, r in rows.iterrows():
        i = df.index[df.session_id == r.session_id][0]
        out.append({'session_id': r.session_id, 'probability': float(r.probability),
                    'features': {k: float(X[i, COLS.index(k)]) for k in KEY_FEATURES},
                    'events': [{**e, 'message': e['message'][:200]} for e in events.get(r.session_id, [])[:15]]})
    return out


def run(source, df, tr, va, te):
    """Analyse test-period mistakes of the saved final model."""
    pred = pd.read_csv(ROOT / 'results' / f'{source}_test_predictions.csv.gz', dtype={'session_id': str})
    pos = df.reset_index().set_index('session_id')['index']
    X = df[COLS].to_numpy(dtype=np.float32)
    idx = pos.loc[pred.session_id].to_numpy()
    Xt = X[idx]
    scale = np.where(Xt.std(0) > 0, Xt.std(0), 1)
    y, yhat = pred.label.to_numpy(), pred.prediction.to_numpy()

    tp, tn = (y == 1) & (yhat == 1), (y == 0) & (yhat == 0)
    fp, fn = (y == 0) & (yhat == 1), (y == 1) & (yhat == 0)

    fp_rows = pred[fp].sort_values('probability', ascending=False).head(N_EXAMPLES)
    fn_rows = pred[fn].sort_values('probability').head(N_EXAMPLES)
    events, log = {}, sorted_log_path(source)
    if log.exists() and len(fp_rows) + len(fn_rows):
        events = collect_session_events(log, source, list(fp_rows.session_id) + list(fn_rows.session_id))

    buckets = load_bucket_templates(source)
    fp_diff = differences(Xt[fp], Xt[tn], scale, buckets)
    fn_diff = differences(Xt[fn], Xt[tp], scale, buckets)
    fn_vs_normal = differences(Xt[fn], Xt[tn], scale, buckets)

    # Deliberately difficult subset: anomalies with no failure keywords at all.
    kw = Xt[:, COLS.index('keyword_error_ratio')]
    quiet = (y == 1) & (kw == 0)
    loud = (y == 1) & (kw > 0)
    hard = {'definition': 'test anomalies whose messages contain no error/exception/timeout words',
            'n': int(quiet.sum()),
            'recall': float(yhat[quiet].mean()) if quiet.any() else None,
            'recall_on_keyword_anomalies': float(yhat[loud].mean()) if loud.any() else None}

    result = {
        'source': source, 'test_sessions': int(len(pred)),
        'confusion': {'tn': int(tn.sum()), 'fp': int(fp.sum()), 'fn': int(fn.sum()), 'tp': int(tp.sum())},
        'hard_subset': hard,
        'false_positives': {
            'count': int(fp.sum()),
            'vs_true_negatives': fp_diff,
            'what_they_share': describe_group('False positives', fp_diff, 'correctly-cleared normal sessions', int(fp.sum())),
            'examples': examples(fp_rows, df, X, events)},
        'false_negatives': {
            'count': int(fn.sum()),
            'vs_true_positives': fn_diff,
            'vs_normal_sessions': fn_vs_normal,
            'what_they_share': describe_group('Missed anomalies', fn_diff, 'detected anomalies', int(fn.sum()))
                               + ' ' + describe_group('Missed anomalies', fn_vs_normal, 'normal sessions', int(fn.sum())).replace('Missed anomalies (n=%d) differ' % int(fn.sum()), 'They also differ'),
            'examples': examples(fn_rows, df, X, events)},
    }
    (ROOT / 'results' / f'{source}_error_analysis.json').write_text(json.dumps(result, indent=2))
    pred[fp | fn].sort_values('probability', ascending=False) \
        .to_csv(ROOT / 'results' / f'{source}_error_cases.csv', index=False)
    print(f"Error analysis: {int(fp.sum())} false positives, {int(fn.sum())} false negatives", flush=True)
    return result


def stability(source, seeds=(0, 1, 7, 13, 42)):
    """Refit each model under several seeds (same split, same thresholds)."""
    from sklearn.metrics import average_precision_score, f1_score
    from train import candidates, load_dataset, split
    df, tr, va, te = split(load_dataset(source))
    X = df[COLS].to_numpy(dtype=np.float32)
    y = df.label.to_numpy()
    dev = tr | va
    saved = json.loads((ROOT / 'results' / f'{source}_evaluation.json').read_text())
    thresholds = {v['model']: v['threshold'] for v in saved['validation']}
    runs = {}
    for seed in seeds:
        for name, model in candidates(seed).items():
            model.fit(X[dev], y[dev])
            p = model.predict_proba(X[te])[:, 1]
            runs.setdefault(name, []).append({
                'seed': seed, 'f1': float(f1_score(y[te], p >= thresholds[name], zero_division=0)),
                'average_precision': float(average_precision_score(y[te], p))})
            print('stability', source, name, seed, round(runs[name][-1]['f1'], 4), flush=True)
    summary = {name: {'runs': r, 'mean_f1': float(np.mean([x['f1'] for x in r])),
                      'std_f1': float(np.std([x['f1'] for x in r])),
                      'min_f1': float(min(x['f1'] for x in r)), 'max_f1': float(max(x['f1'] for x in r))}
               for name, r in runs.items()}
    (ROOT / 'results' / f'{source}_stability.json').write_text(json.dumps({'seeds': list(seeds), 'results': summary}, indent=2))
    return summary


def rolling_origin(source, n_chunks=5):
    """Rolling-origin (expanding window) temporal evaluation.

    The sessions, ordered by start time, are cut into `n_chunks` equal time chunks. Fold k trains on chunks
    0..k-1 and tests on chunk k, so every model is always scored on data *later* than everything it was
    trained on, and on several different periods rather than a single one. This matters when the anomaly
    rate drifts over time (e.g. BGL): one 20% test period can flatter or punish a model by chance.
    The decision threshold is tuned on the last 25% (by time) of each training window, then the model is
    refit on the whole window. Sessions that straddle the train/test boundary are purged from training.
    """
    from train import candidates, best_threshold, load_dataset, metrics
    df = load_dataset(source).sort_values(['t_start', 'session_id']).reset_index(drop=True)
    X = df[COLS].to_numpy(dtype=np.float32)
    y = df.label.to_numpy()
    bounds = [int(len(df) * k / n_chunks) for k in range(n_chunks + 1)]
    idx = np.arange(len(df))
    folds, per_model = [], {}
    for k in range(1, n_chunks):
        test = (idx >= bounds[k]) & (idx < bounds[k + 1])
        t0 = df.t_start.iloc[bounds[k]]
        train = (idx < bounds[k]) & (df.t_end.to_numpy() < t0)
        inner = int(train.sum() * .75)
        fit_part = train & (np.cumsum(train) <= inner)
        tune_part = train & ~fit_part
        usable = len(set(y[train])) == 2 and len(set(y[test])) == 2 and len(set(y[tune_part])) == 2
        fold = {'fold': k, 'train_sessions': int(train.sum()), 'test_sessions': int(test.sum()),
                'test_anomalies': int(y[test].sum()), 'test_anomaly_rate': float(y[test].mean()),
                'test_start': int(df.t_start[test].min()), 'test_end': int(df.t_end[test].max()), 'usable': bool(usable)}
        folds.append(fold)
        if not usable:
            print(f'fold {k}: skipped (a partition lacks one of the classes)', flush=True)
            continue
        for name, model in candidates().items():
            model.fit(X[fit_part], y[fit_part])
            threshold = best_threshold(y[tune_part], model.predict_proba(X[tune_part])[:, 1])
            model.fit(X[train], y[train])
            m = metrics(y[test], model.predict_proba(X[test])[:, 1], threshold)
            per_model.setdefault(name, []).append({'fold': k, **m})
            print(f'fold {k} {name:28s} F1={m["f1"]:.3f} P={m["precision"]:.3f} R={m["recall"]:.3f}', flush=True)
    summary = {}
    for name, runs in per_model.items():
        f1s = [r['f1'] for r in runs]
        summary[name] = {'folds': runs, 'mean_f1': float(np.mean(f1s)), 'std_f1': float(np.std(f1s)),
                         'min_f1': float(min(f1s)), 'max_f1': float(max(f1s)),
                         'mean_precision': float(np.mean([r['precision'] for r in runs])),
                         'mean_recall': float(np.mean([r['recall'] for r in runs])),
                         'mean_pr_auc': float(np.mean([r['average_precision'] for r in runs])),
                         'total_fp': int(sum(r['fp'] for r in runs)), 'total_fn': int(sum(r['fn'] for r in runs))}
    result = {'source': source, 'method': 'rolling-origin expanding window, temporal, purged', 'n_chunks': n_chunks,
              'folds': folds, 'results': summary}
    (ROOT / 'results' / f'{source}_temporal_folds.json').write_text(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Error analysis (re-run) or seed stability.')
    parser.add_argument('--source', choices=['HDFS', 'BGL'], default='HDFS')
    parser.add_argument('--stability', action='store_true', help='refit models under several seeds')
    parser.add_argument('--folds', action='store_true', help='rolling-origin temporal evaluation (several test periods)')
    args = parser.parse_args()
    if args.stability:
        stability(args.source)
    elif args.folds:
        rolling_origin(args.source)
    else:
        from train import load_dataset, split
        d, tr_, va_, te_ = split(load_dataset(args.source))
        run(args.source, d, tr_, va_, te_)
