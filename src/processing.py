"""Turns a raw log into sessions and then into a feature table (HDFS and BGL).

Each line is parsed, lines are grouped into sessions, and `features.Session` turns every
session into one row of 52 features. The parts that differ between datasets (line format,
session definition, labels) are in sources.py.

The log must be in time order (setup_data.py sorts the raw downloads).
"""
import gzip
from collections import Counter, defaultdict
from pathlib import Path

import mkl_setup  # noqa: F401  (Windows MKL fix, must come before numpy)
import pandas as pd

from features import BLOCK, COLS, IP, Session, bucket, normalise  # noqa: F401 (re-exported)
from sources import BGL_WINDOW_SECONDS, SOURCES, get_source  # noqa: F401

# Repository root: src/ lives directly under it.
ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / 'data' / 'processed'
RAW_DIR = ROOT / 'data' / 'raw'

META_COLS = ['session_id', 'source', 't_start', 't_end', 'label']
ARCHIVES = {name: s.archive for name, s in SOURCES.items()}  # folder names under data/raw/


def sorted_log_path(source):
    """Path of the time-sorted raw log made by setup_data.py."""
    return RAW_DIR / ARCHIVES[source] / f'{source}.sorted.log'


def parse(line, source):
    """Parse one raw line using the adapter for the source (see sources.py).

    Returns (session_ids, unix_time, thread, level, message, host_ips, label).
    Raises ValueError for a bad line or an unsupported source.
    """
    return get_source(source).parse(line)


def process(path, source, labels=None, keep=False):
    """Read a log file and build the session feature table.

    Returns (feature table, audit counters, events by session).
    `labels` is the HDFS anomaly_label.csv path. Without it HDFS labels are -1 (unknown).
    `keep=True` also keeps the events of each session.
    """
    # The log is read line by line, so a huge file never has to fit in memory.
    # Each session id gets one Session object that collects its events.
    # The audit counters (raw lines, bad lines, ...) are shown in the dashboard's parsing statistics.
    sessions, audit = {}, Counter()
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f, 1):
            audit['raw_lines'] += 1
            try:
                ids, t, thread, level, msg, hosts, label = parse(line, source)
            except (ValueError, OverflowError):
                audit['malformed_lines'] += 1
                continue
            # Some lines do not belong to any session (e.g. HDFS lines without a block id). They are counted but skipped.
            if not ids:
                audit['no_session_id'] += 1
                continue
            for sid in ids:
                if sid not in sessions:
                    sessions[sid] = Session(keep)
                sessions[sid].add(t, thread, level, msg, hosts, label)
                audit['event_assignments'] += 1
            if i % 1000000 == 0:
                print(source, f'{i:,} lines', flush=True)
    if not sessions:
        raise ValueError('No supported sessions found in this file')

    spec = get_source(source)
    # Once every line is read, turn each session into one row of features.
    # has_lifecycle is False for BGL, which turns off the HDFS-only write chain features.
    df = pd.DataFrame([s.row(k, source, spec.has_lifecycle) for k, s in sessions.items()],
                      columns=META_COLS + COLS)
    if not spec.labels_in_log:  # e.g. HDFS: labels live in a separate per-session file
        df['label'] = attach_hdfs_labels(df, labels)
    audit['sessions'] = len(df)
    events = {k: s.events for k, s in sessions.items()} if keep else {}
    return df, dict(audit), events


def attach_hdfs_labels(df, labels_path):
    """Turn the block labels in anomaly_label.csv into 0 or 1 (-1 if no file is given)."""
    if not labels_path:
        return -1
    lab = pd.read_csv(labels_path, dtype={'BlockId': str})
    if lab.BlockId.duplicated().any():
        raise ValueError('Duplicate label IDs')
    # Stop with an error if any block has no label, otherwise it would be silently given a wrong class.
    mapped = df.session_id.map(lab.set_index('BlockId').Label.map({'Normal': 0, 'Anomaly': 1}))
    if mapped.isna().any():
        raise ValueError('Missing or unrecognised HDFS labels')
    return mapped.astype(int)


def collect_session_events(path, source, session_ids, limit=200):
    """Read the log once and return the real events of the requested sessions.

    Used to show example events in the cluster and error analyses.
    """
    # One pass over the log that only keeps lines of the sessions we ask for (at most `limit` each).
    wanted, found = set(session_ids), {s: [] for s in session_ids}
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8', errors='replace') as f:
        for line in f:
            try:
                ids, t, _, level, msg, _, _ = parse(line, source)
            except (ValueError, OverflowError):
                continue
            for sid in ids:
                if sid in wanted and len(found[sid]) < limit:
                    found[sid].append({'time': t, 'level': level, 'message': msg})
    return found


def bucket_inventory(path, source, top=5):
    """List which message templates fall into each hash bucket.

    Several templates can share a bucket, so this shows what a feature like
    event_hash_27 really counts. Returns {feature_name: [{template, count, share}, ...]}.
    """
    counts = defaultdict(Counter)
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8', errors='replace') as f:
        for line in f:
            try:
                msg = parse(line, source)[4]
            except (ValueError, OverflowError):
                continue
            # Count each template per bucket, so we can see what kinds of event share the same feature column.
            template = normalise(msg)
            counts[bucket(template)][template] += 1
    out = {}
    for b, c in sorted(counts.items()):
        total = sum(c.values())
        out[f'event_hash_{b:02d}'] = [{'template': t, 'count': n, 'share': n / total} for t, n in c.most_common(top)]
    return out


def verify_parser(path, source, head=5, sample=200000):
    """Print the first parsed lines and some parsing statistics for a log."""
    import itertools
    opener = gzip.open if str(path).endswith('.gz') else open
    ok = bad = 0
    levels, labels, sessions = Counter(), Counter(), set()
    with opener(path, 'rt', encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(itertools.islice(f, sample)):
            try:
                ids, t, thread, level, msg, hosts, label = parse(line, source)
            except (ValueError, OverflowError):
                bad += 1
                continue
            ok += 1
            levels[level] += 1
            labels[label] += 1
            sessions.update(ids)
            if ok <= head:
                print(f'line {i + 1}: sessions={ids} time={t} component/thread={thread!r} level={level} '
                      f'hosts={hosts} line_label={label}\n         message={msg[:90]!r}')
    spec = get_source(source)
    print(f'\n{source} ({spec.title}): {ok:,} of {ok + bad:,} lines parsed ({bad:,} malformed)')
    print(f'sessions seen in this sample: {len(sessions):,}  ({spec.session_definition})')
    print(f'levels: {dict(levels.most_common())}')
    print(f'line labels: {dict(labels)}  ({spec.label_policy})')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Verify the parser on a raw log: shows parsed fields and statistics.')
    parser.add_argument('--source', choices=list(SOURCES), default='HDFS')
    parser.add_argument('--log', required=True)
    parser.add_argument('--head', type=int, default=5, help='how many parsed lines to print')
    args = parser.parse_args()
    verify_parser(args.log, args.source, args.head)
