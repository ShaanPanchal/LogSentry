"""Raw log -> sessions -> feature table (HDFS and BGL adapters).

Pipeline:  parse each line  ->  group lines into sessions  ->  `features.Session`
turns every session into the fixed 52-feature row used by the model.

Raw formats, session definitions and label sources are dataset-specific and live in
sources.py (HDFS: one session per block; BGL: five-minute windows, labels in the log).

Logs must be in chronological order (setup_data.py sorts the raw downloads).
"""
import gzip
from collections import Counter, defaultdict
from pathlib import Path

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
    """Where setup_data.py leaves the chronologically sorted raw log."""
    return RAW_DIR / ARCHIVES[source] / f'{source}.sorted.log'


def parse(line, source):
    """Parse one raw line with the source's adapter (see sources.py).

    Returns (session_ids, unix_time, thread, level, message, host_ips, label).
    Raises ValueError on malformed lines or an unsupported source.
    """
    return get_source(source).parse(line)


def process(path, source, labels=None, keep=False):
    """Stream a log file into a session feature table.

    Returns (DataFrame with META_COLS + COLS, audit counters, events-by-session).
    `labels` is the HDFS anomaly_label.csv path; without it HDFS labels are -1
    (unlabelled, e.g. a user upload).  `keep=True` retains each session's events.
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
    """Map block ids to 0/1 using Loghub's anomaly_label.csv (-1 if not given)."""
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
    """One streaming pass returning the real events of the requested sessions.

    Used to attach concrete examples to cluster and error analyses.
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
    """Which normalised event templates fall into each hash bucket (whole log).

    Hashing is lossy (several templates can share a bucket), so this inventory is
    what lets us say what a feature like event_hash_27 actually counts.
    Returns {feature_name: [{'template', 'count', 'share'}, ...]}.
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
    """Show how the parser reads a log: first parsed lines and parse statistics."""
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
