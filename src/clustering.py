"""Clusters the anomalous sessions and explains each cluster.

The classifier says whether a session is anomalous. Clustering the anomalies shows
what kinds of failure there are.

How it works:
* Labels are only used to pick which sessions to cluster. They are not a clustering input.
* Features get a signed log transform (counts and durations have a few huge values) and
  are standardised. K-means is used, and k is chosen with the silhouette score.
* Each cluster is described by its most distinctive features, the real events of the
  sessions nearest its centre, and a short plain English summary.
* All clustered sessions are anomalies, so we also assign the later test period to the
  nearest cluster to see which clusters look like normal behaviour.
"""
import argparse
import json
from collections import Counter

import mkl_setup  # noqa: F401  (Windows MKL fix, must come before numpy)
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from processing import COLS, ROOT, collect_session_events, normalise, sorted_log_path
from features import bucket
from sources import get_source

K_RANGE = range(2, 9)   # all reported in the sweep
MIN_K = 3               # k=2 only splits the class on one dominant feature; require >=3 groups
N_NEAREST = 10      # sessions per cluster whose events are summarised
N_EXAMPLES = 3      # sessions per cluster shown in full
N_TOP_FEATURES = 5
SEED = 7

# feature -> (what it measures, meaning when high, meaning when low).
# Wording is tied to how each feature is computed in features.py; it states
# what the feature measures and does not claim a root cause.
FEATURE_INFO = {
    'n_events': ('number of log events', 'more events than a typical anomaly (repeated or retried operations)', 'very few events (the session stops early)'),
    'n_event_buckets': ('number of distinct event kinds', 'a wider variety of event kinds', 'only a few kinds of event'),
    'duration_s': ('seconds from first to last event', 'long-running sessions', 'sessions that finish almost instantly'),
    'gap_mean_s': ('mean seconds between consecutive events', 'long pauses between events (slow progress)', 'events arriving back-to-back'),
    'gap_max_s': ('longest pause between events', 'at least one long stall mid-session', 'no long stalls'),
    'gap_std_s': ('variability of the gaps between events', 'irregular timing (bursts and stalls)', 'very regular timing'),
    'events_per_min': ('event rate', 'dense bursts of events', 'sparse events spread over time'),
    'n_hosts': ('distinct hosts/nodes involved', 'more hosts than usual', 'fewer hosts than usual'),
    'n_threads': ('distinct threads (HDFS) or components (BGL) involved', 'more threads/components involved', 'few threads/components involved'),
    'warning_ratio': ('share of WARN-level events', 'a high share of warnings', 'few warnings'),
    'error_ratio': ('share of ERROR-level events', 'a high share of ERROR-level events', 'no ERROR-level events'),
    'keyword_error_ratio': ('share of messages containing error/exception/timeout/fail words', 'many failure messages', 'few failure messages'),
    'has_allocate': ('block allocation seen', 'the allocation event is present', 'the allocation event is missing'),
    'has_delete': ('block deletion seen', 'the block was deleted (lifecycle ran to the end)', 'no deletion event (lifecycle did not reach the end)'),
    'replica_deficit': ('3 minus number of "stored" confirmations', 'fewer replica confirmations than the 3 expected', 'more confirmations than expected (duplicate or re-replicated copies)'),
    'unacked_writes': ('"receiving" events minus acknowledgements', 'writes started but never acknowledged', 'few or no unacknowledged writes (acknowledgements keep up with writes)'),
    'uncommitted_acks': ('acknowledgements minus "stored" confirmations', 'acknowledged writes never committed to the namespace', 'more stored confirmations than acknowledgements'),
    'lifecycle_complete': ('full allocate/receive/ack/store chain present', 'the full write chain completed', 'the write chain did not complete'),
    'transition_change_ratio': ('share of consecutive events that change kind', 'frequent switching between event kinds', 'the same event kind repeated'),
    'event_entropy': ('diversity of the event-kind distribution', 'a more varied mix of events', 'dominated by one event kind'),
}


# Counts and durations have a few huge values. log1p shrinks them, and np.sign keeps negative values
# (replica_deficit can be negative). predict.py imports this so it uses the same transform.
def signed_log(X):
    """log1p that keeps the sign, so very large values are shrunk."""
    return np.sign(X) * np.log1p(np.abs(X))


def load_bucket_templates(source):
    """Load the list of events in each hash bucket (empty if the file is missing)."""
    path = ROOT / 'results' / f'{source}_event_buckets.json'
    return json.loads(path.read_text()) if path.exists() else {}


def describe_feature(name, bucket_templates):
    """Return (what the feature measures, meaning when high, meaning when low)."""
    if name in FEATURE_INFO:
        return FEATURE_INFO[name]
    seen = bucket_templates.get(name, [])[:2]
    if seen:
        kind = ' / '.join(f'"{e["template"]}"' for e in seen)
        shared = '' if seen[0].get('share', 1) >= .9 else ' (bucket shared by several event kinds)'
        return (f'count of events in hash bucket {name[-2:]}: {kind}{shared}',
                f'more events like {kind}{shared}', f'fewer events like {kind}{shared}')
    return (f'count of events in hash bucket {name[-2:]} (no example available)',
            f'more events in bucket {name[-2:]}', f'fewer events in bucket {name[-2:]}')


def profile_sentence(cluster_mean, anomaly_mean, write_chain=True):
    """One sentence with key numbers: cluster average compared with the anomaly average.

    The write-chain statistic only applies to HDFS, so it is left out when write_chain is False (BGL).
    """
    def pair(feature, fmt):
        j = COLS.index(feature)
        return f'{fmt.format(cluster_mean[j])} (anomaly avg {fmt.format(anomaly_mean[j])})'
    parts = [f"write chain complete in {pair('lifecycle_complete', '{:.0%}')} of sessions"] if write_chain else []
    parts += [f"mean events {pair('n_events', '{:.1f}')}", f"mean duration {pair('duration_s', '{:,.0f}')} s",
              f"share of failure-keyword messages {pair('keyword_error_ratio', '{:.1%}')}",
              f"mean hosts {pair('n_hosts', '{:.1f}')}"]
    return 'Profile: ' + '; '.join(parts) + '.'


# Builds the plain English description of a cluster from its top features and example events.
# It only reports what the numbers show (higher or lower than the anomaly average), not a root cause.
def feature_clause(f):
    """One clause about one feature: is the cluster above or below the anomaly average, and what that means.

    The direction comes from z, the cluster centre on the signed-log scale that K-means works on. The numbers
    shown are raw means. For a very skewed feature a few huge values can pull the raw average the other way,
    so when the two disagree the clause shows the log-scale typical values that match z and says why.
    """
    _, high, low = f['_meaning']
    up = f['z'] > 0
    direction = 'above' if up else 'below'
    meaning = high if up else low
    cm, om = f['cluster_mean'], f['overall_anomaly_mean']
    if f.get('_typical') is not None and cm != om and (cm > om) != up:
        ct, ot = f['_typical']
        return (f"{f['feature']} is {direction} the anomaly average on the log scale used for clustering "
                f"(typical value {ct:.3g} vs {ot:.3g}; the raw means, {cm:.3g} vs {om:.3g}, point the other way "
                f"because a few very large values skew the raw average): {meaning}")
    return f"{f['feature']} is {direction} the anomaly average ({cm:.3g} vs {om:.3g}): {meaning}"


def interpret(cluster, feats, share, examples, profile=''):
    """Write a plain English description of a cluster from its statistics."""
    clauses = [feature_clause(f) for f in feats]
    text = (f"Cluster {cluster} holds {share:.1%} of the clustered anomalies. Compared with the "
            f"overall anomaly population, its members show: " + '; '.join(clauses) + '.')
    if examples and examples[0].get('typical_events'):
        top = ', '.join(f"\"{e['template']}\" ({e['per_session']:.1f}/session)"
                        for e in examples[0]['typical_events'][:3])
        text += f" The sessions nearest its centre are dominated by: {top}."
    return text + ' ' + profile


def event_templates_for(events_by_session):
    """Count how often each message template appears in the given events."""
    stats = {}
    for events in events_by_session.values():
        for ev in events:
            t = normalise(ev['message'])
            s = stats.setdefault(t, {'template': t, 'bucket': bucket(t), 'count': 0})
            s['count'] += 1
    return stats


def run(source, df=None, dev=None, te=None, log_path=None):
    """Cluster the anomalies from train + validation and save the analysis."""
    from train import load_dataset, split  # local import: train imports this module
    if df is None:
        df, tr, va, te = split(load_dataset(source))
        dev = tr | va
    for d in ('models', 'results'):
        (ROOT / d).mkdir(exist_ok=True)

    X = df[COLS].to_numpy(dtype=np.float32)
    y = df.label.to_numpy()
    # Only anomalies from train + validation are clustered, so the test period is not used to build clusters.
    # The label is only used to choose these rows. It is not given to K-means.
    ids = np.flatnonzero(dev & (y == 1))           # labels only SELECT the class
    if len(ids) < 4:
        raise ValueError('Not enough development anomalies for clustering')
    L = signed_log(X)
    # Standardise so each feature has mean 0 and spread 1. Otherwise big-valued features would dominate K-means.
    scaler = StandardScaler().fit(L[ids])
    Z = scaler.transform(L[ids])                   # clustering input: features only

    # Try several values of k. Keep every fitted model so we can pick the best k afterwards.
    sweep, models = [], []
    for k in K_RANGE:
        if k > len(ids) - 1:
            break
        km = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(Z)
        # Silhouette score is slow on many points, so it is measured on a sample of up to 3000.
        sil = silhouette_score(Z, km.labels_, sample_size=min(3000, len(ids)), random_state=SEED)
        sweep.append({'k': k, 'silhouette': float(sil), 'inertia': float(km.inertia_)})
        models.append(km)
    # Pick the k with the best silhouette score, but only from k >= 3 (see MIN_K).
    # If there are too few anomalies for that, all values of k are allowed.
    eligible = [i for i, s_ in enumerate(sweep) if s_['k'] >= MIN_K] or range(len(sweep))
    km = models[max(eligible, key=lambda i: sweep[i]['silhouette'])]

    # Composition check on the later test period: nearest-cluster assignment.
    test_idx = np.flatnonzero(te)
    # Assign the test sessions (normal and anomalous) to the nearest cluster. This shows which clusters
    # look like normal behaviour, since the clusters were only built from anomalies.
    test_cluster = km.predict(scaler.transform(L[test_idx]))
    test_comp = pd.crosstab(test_cluster, y[test_idx]).reindex(range(km.n_clusters), fill_value=0)

    # Real events of the sessions nearest each centroid.
    log_path = log_path or sorted_log_path(source)
    nearest = {}
    for c in range(km.n_clusters):
        members = np.flatnonzero(km.labels_ == c)
        # Sort the members by distance to the cluster centre. The closest ones are the most typical,
        # so their real log events are used as examples of the cluster.
        order = members[np.argsort(((Z[members] - km.cluster_centers_[c]) ** 2).sum(1))]
        nearest[c] = ids[order[:N_NEAREST]]
    events = {}
    if log_path.exists():
        wanted = [df.session_id.iloc[i] for c in nearest for i in nearest[c]]
        events = collect_session_events(log_path, source, wanted)
    else:
        print(f'Note: {log_path} not found - cluster descriptions will not include example events.')

    bucket_templates = load_bucket_templates(source)
    if not bucket_templates:  # no inventory: fall back to the sampled sessions' events
        for ev_list in events.values():
            for ev in ev_list:
                t = normalise(ev['message'])
                entries = bucket_templates.setdefault(f'event_hash_{bucket(t):02d}', [])
                if all(e['template'] != t for e in entries) and len(entries) < 2:
                    entries.append({'template': t, 'share': None})

    # For each cluster, compare its average feature values with the average of all anomalies.
    anomaly_mean = X[ids].mean(0)
    all_mean = X[dev].mean(0)
    # The same averages on the signed-log scale, converted back to counts. Their direction always agrees
    # with the cluster centre z, so they can be shown next to the raw means when the two disagree.
    L_anomaly = L[ids].mean(0)

    def typical(m):
        return np.sign(m) * np.expm1(np.abs(m))
    clusters = []
    for c in range(km.n_clusters):
        members = ids[km.labels_ == c]
        mean = X[members].mean(0)
        L_mean = L[members].mean(0)
        # The data was standardised, so each centre value says how far this cluster is from the average anomaly
        # for that feature. The features with the biggest values are what make the cluster different.
        z = km.cluster_centers_[c]                 # standardised log-scale offset vs anomaly mean
        top = np.argsort(np.abs(z))[::-1][:N_TOP_FEATURES]
        feats = [{'feature': COLS[j], 'cluster_mean': float(mean[j]),
                  'overall_anomaly_mean': float(anomaly_mean[j]),
                  'all_sessions_mean': float(all_mean[j]), 'z': float(z[j]),
                  '_meaning': describe_feature(COLS[j], bucket_templates),
                  '_typical': (float(typical(L_mean[j])), float(typical(L_anomaly[j])))} for j in top]

        examples = []
        for i in nearest[c][:N_EXAMPLES]:
            sid = df.session_id.iloc[i]
            ev = events.get(sid, [])
            summary = Counter(normalise(e['message']) for e in ev)
            examples.append({'session_id': sid, 'n_events': int(X[i][COLS.index('n_events')]),
                             'events': [{**e, 'message': e['message'][:200]} for e in ev[:25]],
                             'typical_events': [{'template': t, 'per_session': n / 1.0}
                                                for t, n in summary.most_common(4)]})
        # Typical events across all N_NEAREST sessions (per-session average)
        agg = Counter()
        n_have = 0
        for i in nearest[c]:
            ev = events.get(df.session_id.iloc[i])
            if ev:
                n_have += 1
                agg.update(normalise(e['message']) for e in ev)
        typical = [{'template': t, 'per_session': n / max(n_have, 1)} for t, n in agg.most_common(5)]
        if examples:
            examples[0]['typical_events'] = typical

        clusters.append({
            'cluster': c, 'sessions': int(len(members)), 'share': float(len(members) / len(ids)),
            'composition': {'normal': int((y[members] == 0).sum()), 'anomaly': int((y[members] == 1).sum()),
                            'note': 'Only anomalies were clustered, so this is 100% anomalous by construction.'},
            'test_period_assignment': {'normal': int(test_comp.loc[c].get(0, 0)),
                                       'anomaly': int(test_comp.loc[c].get(1, 0))},
            'top_features': [{k: v for k, v in f.items() if not k.startswith('_')} | {'measures': f['_meaning'][0]}
                             for f in feats],
            'interpretation': interpret(c, feats, len(members) / len(ids), examples,
                                      profile_sentence(mean, anomaly_mean, get_source(source).has_lifecycle)),
            'typical_events': typical,
            'example_sessions': examples,
        })

    result = {'source': source, 'algorithm': 'KMeans (signed-log + standardised features, labels excluded)',
              'clustered': 'development-period anomalies only', 'n_clustered': int(len(ids)),
              'selected_k': int(km.n_clusters), 'sweep': sweep, 'clusters': clusters,
              'example_events_available': bool(events)}
    (ROOT / 'results' / f'{source}_cluster_analysis.json').write_text(json.dumps(result, indent=2))
    pd.DataFrame({'session_id': df.session_id.iloc[ids].to_numpy(), 'cluster': km.labels_}) \
        .to_csv(ROOT / 'results' / f'{source}_anomaly_clusters.csv', index=False)
    # Save the scaler, K-means model and column list. predict.py uses them to give new flagged sessions a cluster.
    # Small per-cluster blurbs for the dashboard.
    joblib.dump({'scaler': scaler, 'kmeans': km, 'columns': COLS, 'transform': 'signed log1p',
                 'summaries': {c['cluster']: {'sessions': c['sessions'], 'share': c['share'],
                                              'interpretation': c['interpretation']} for c in clusters}},
                ROOT / 'models' / f'{source}_clusters.joblib', compress=3)
    write_markdown_report(source, result)
    print(f'Clustered {len(ids):,} anomalies into k={km.n_clusters} (silhouette '
          f'{next(s_["silhouette"] for s_ in sweep if s_["k"] == km.n_clusters):.3f})', flush=True)
    return result


def write_markdown_report(source, result):
    lines = [f'# {source} anomaly clusters', '',
             f"{result['algorithm']}. Clustered: {result['clustered']} (n={result['n_clustered']:,}); "
             f"k={result['selected_k']} chosen by silhouette among k>={MIN_K}.", '']
    for c in result['clusters']:
        lines += [f"## Cluster {c['cluster']} - {c['sessions']:,} sessions ({c['share']:.1%})", '',
                  c['interpretation'], '',
                  '| feature | cluster mean | anomaly mean | all-sessions mean | z |', '|---|---|---|---|---|']
        lines += [f"| {f['feature']} | {f['cluster_mean']:.4g} | {f['overall_anomaly_mean']:.4g} | "
                  f"{f['all_sessions_mean']:.4g} | {f['z']:+.2f} |" for f in c['top_features']]
        t = c['test_period_assignment']
        lines += ['', f"Test-period sessions nearest this cluster: {t['anomaly']:,} anomalous, {t['normal']:,} normal.", '']
        for ex in c['example_sessions'][:2]:
            lines += [f"Example session `{ex['session_id']}` ({ex['n_events']} events):", '']
            lines += [f"    {e['level']:5} {e['message'][:120]}" for e in ex['events'][:8]] + ['']
    (ROOT / 'results' / f'{source}_cluster_report.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cluster the anomaly class and describe each cluster.')
    parser.add_argument('--source', choices=['HDFS', 'BGL'], default='HDFS')
    run(parser.parse_args().source)
