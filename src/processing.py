"""Raw log -> sessions -> feature table (HDFS and BGL adapters).

Pipeline:  parse each line  ->  group lines into sessions  ->  `features.Session`
turns every session into the fixed 52-feature row used by the model.

* HDFS sessions are blocks: every `blk_<id>` mentioned in a line is a session.
* BGL has no session id, so lines are grouped into five-minute windows.

Logs must be in chronological order (setup_data.py sorts the raw downloads).
"""
import gzip
from collections import Counter, defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import pandas as pd

from features import BLOCK, COLS, IP, Session, bucket, normalise  # noqa: F401 (re-exported)

# Repository root: src/ lives directly under it.
ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / 'data' / 'processed'
RAW_DIR = ROOT / 'data' / 'raw'
BGL_WINDOW_SECONDS = 300

META_COLS = ['session_id', 'source', 't_start', 't_end', 'label']
ARCHIVES = {'HDFS': 'HDFS_v1', 'BGL': 'BGL'}  # folder names under data/raw/


def sorted_log_path(source):
    """Where setup_data.py leaves the chronologically sorted raw log."""
    return RAW_DIR / ARCHIVES[source] / f'{source}.sorted.log'


@lru_cache(maxsize=200000)
def stamp(date, time):
    """HDFS 'yymmdd' + 'HHMMSS' -> unix seconds (UTC)."""
    return int(datetime.strptime(date + time, '%y%m%d%H%M%S').replace(tzinfo=timezone.utc).timestamp())


def parse(line, source):
    """Parse one raw line.

    Returns (session_ids, unix_time, thread, level, message, host_ips, label).
    `label` is a per-line annotation: always 0 for HDFS (labels come from a
    separate per-block file) and, for BGL, 1 when the leading alert tag is not '-'.
    Raises ValueError on malformed lines.
    """
    if source == 'HDFS':
        parts = line.strip().split(None, 5)
        if len(parts) != 6:
            raise ValueError('Invalid HDFS fields')
        msg = parts[5]
        session_ids = list(dict.fromkeys(BLOCK.findall(msg)))
        hosts = [h.split(':')[0] for h in IP.findall(msg)]
        return session_ids, stamp(parts[0], parts[1]), parts[2], parts[3], msg, hosts, 0
    if source != 'BGL':
        raise ValueError('Unsupported source')
    parts = line.strip().split(None, 9)
    if len(parts) == 9:  # empty message
        parts.append('')
    if len(parts) != 10:
        raise ValueError('Invalid BGL fields')
    t = int(parts[1])
    # parts[0] is the alert annotation. It becomes the label only and is never
    # passed to the feature code, so it cannot leak into the model.
    return [f'window_{t // BGL_WINDOW_SECONDS}'], t, parts[7], parts[8], parts[9], [parts[3]], int(parts[0] != '-')


def process(path, source, labels=None, keep=False):
    """Stream a log file into a session feature table.

    Returns (DataFrame with META_COLS + COLS, audit counters, events-by-session).
    `labels` is the HDFS anomaly_label.csv path; without it HDFS labels are -1
    (unlabelled, e.g. a user upload).  `keep=True` retains each session's events.
    """
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

    df = pd.DataFrame([s.row(k, source) for k, s in sessions.items()], columns=META_COLS + COLS)
    if source == 'HDFS':
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
    mapped = df.session_id.map(lab.set_index('BlockId').Label.map({'Normal': 0, 'Anomaly': 1}))
    if mapped.isna().any():
        raise ValueError('Missing or unrecognised HDFS labels')
    return mapped.astype(int)


def collect_session_events(path, source, session_ids, limit=200):
    """One streaming pass returning the real events of the requested sessions.

    Used to attach concrete examples to cluster and error analyses.
    """
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
            template = normalise(msg)
            counts[bucket(template)][template] += 1
    out = {}
    for b, c in sorted(counts.items()):
        total = sum(c.values())
        out[f'event_hash_{b:02d}'] = [{'template': t, 'count': n, 'share': n / total} for t, n in c.most_common(top)]
    return out
