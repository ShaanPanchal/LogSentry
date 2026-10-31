"""Turns a raw log into sessions and then into a feature table (HDFS and BGL).

Each line is parsed, lines are grouped into sessions, and `features.Session` turns every
session into one row of 52 features. The parts that differ between datasets (line format,
session definition, labels) are in sources.py.

The log must be in time order.
"""
import gzip
from collections import Counter
from pathlib import Path

import mkl_setup  # noqa: F401  (Windows MKL fix, must come before numpy)
import pandas as pd

from features import COLS, Session
from sources import get_source

# Repository root: src/ lives directly under it.
ROOT = Path(__file__).resolve().parents[1]

META_COLS = ['session_id', 'source', 't_start', 't_end', 'label']


def parse(line, source):
    """Parse one raw line using the adapter for the source (see sources.py).

    Returns (session_ids, unix_time, thread, level, message, host_ips, label).
    Raises ValueError for a bad line or an unsupported source.
    """
    return get_source(source).parse(line)


def process(path, source, keep=False):
    """Read a log file and build the session feature table.

    Returns (feature table, audit counters, events by session).
    `keep=True` also keeps the events of each session.
    """
    # The log is read line by line, so a huge file never has to fit in memory.
    # Each session id gets one Session object that collects its events.
    # The audit counters (raw lines, bad lines, ...) are returned with every analysis.
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
    if not spec.labels_in_log:  # e.g. HDFS: labels live in a separate file, so an uploaded log has none
        df['label'] = -1
    audit['sessions'] = len(df)
    events = {k: s.events for k, s in sessions.items()} if keep else {}
    return df, dict(audit), events
