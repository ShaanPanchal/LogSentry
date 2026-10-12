"""Turns the events of a session into one row of 52 features (the feature schema).

A `Session` collects the events of one session (an HDFS block, or a BGL five minute window).
`Session.row()` then gives the feature values. Training, the dashboard and the command line
all use this code, so the model always sees the same features it was trained on.

Feature groups:
G1  Event counts (32 hash buckets). Counting event types is a standard approach in log
    anomaly research (Xu et al. 2009; He et al. 2016). Messages are first cleaned so that
    ids, IPs, paths and numbers disappear, then hashed into 32 buckets. This works even
    when we do not know the event types in advance (e.g. an uploaded log).
G2  Volume: total events and number of different buckets used.
G3  Timing: duration and the gaps between events. A healthy HDFS write is quick, a stalled
    one has a long gap.
G4  Topology: number of hosts and threads. HDFS keeps 3 copies of each block, so the host
    count shows whether replication finished.
G5  Write chain (HDFS only): a healthy block is allocated, received x3, acknowledged x3,
    stored x3 and later deleted. These features measure which step is missing. For BGL the
    chain features are fixed at 0, meaning "not applicable".
G6  Severity: share of WARN and ERROR events, and of messages with failure words.
G7  Order: how often consecutive events change type, and the entropy of the event types.
    Counts lose the order of events, and these two bring a little of it back (cf. DeepLog,
    Du et al. 2017).
"""
import re
import zlib
from functools import lru_cache

import numpy as np

# --------------------------------------------------------------------------
# Message normalisation and hashing
# --------------------------------------------------------------------------
# These patterns find the parts of a message that change every time (ids, IPs, paths, numbers).
# normalise() replaces them so two messages of the same kind end up as the same text.
# The specific patterns run first. If plain numbers ran first they would break up the ids and IPs.
BLOCK = re.compile(r'blk_-?\d+')
IP = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b')
PATH = re.compile(r'/(?:[^\s,;:]+/)*[^\s,;:]*')
NUM = re.compile(r'[-+]?\d+(?:\.\d+)?')
HEX = re.compile(r'\b0x[0-9a-fA-F]+\b')
ERROR_WORDS = re.compile(r'error|exception|fail|timed? out|timeout|fatal|panic|corrupt', re.I)

# Every message kind is hashed into one of 32 buckets, so the number of columns is always the same.
# Two different kinds can land in the same bucket. results/*_event_buckets.json shows what is in each one.
N_BUCKETS = 32
WARN_LEVELS = ('WARN', 'WARNING')
ERROR_LEVELS = ('ERROR', 'FATAL', 'SEVERE', 'FAILURE')
EXPECTED_REPLICAS = 3  # HDFS default replication factor

BUCKET_COLS = [f'event_hash_{i:02d}' for i in range(N_BUCKETS)]
STRUCTURAL_COLS = [
    'n_events', 'n_event_buckets',                                    # G2
    'duration_s', 'gap_mean_s', 'gap_max_s', 'gap_std_s',             # G3
    'events_per_min',
    'n_hosts', 'n_threads',                                           # G4
    'warning_ratio', 'error_ratio', 'keyword_error_ratio',            # G6
    'has_allocate', 'has_delete', 'replica_deficit',                  # G5
    'unacked_writes', 'uncommitted_acks', 'lifecycle_complete',
    'transition_change_ratio', 'event_entropy',                       # G7
]
# The order of these columns matters. The saved model stores it and predict.py uses the same order.
COLS = BUCKET_COLS + STRUCTURAL_COLS  # the 52 model input columns


# Turns a raw message into a "template", e.g. "Receiving block blk_1 src: /10.0.0.1" becomes
# "Receiving block <BLOCK> src: <PATH>". This lets us count how often each kind of event happens.
def normalise(msg):
    """Replace ids, IPs, paths and numbers so messages of the same kind look identical."""
    msg = BLOCK.sub('<BLOCK>', msg)
    msg = IP.sub('<IP>', msg)
    msg = PATH.sub('<PATH>', msg)
    return NUM.sub('<N>', HEX.sub('<HEX>', msg))


@lru_cache(maxsize=100000)
def bucket(text):
    """Hash a cleaned message into a bucket number (crc32, which gives the same result every run)."""
    return zlib.crc32(text.encode()) % N_BUCKETS


class Session:
    """Collects the events of one session. Add events in time order, then call row()."""

    def __init__(self, keep=False):
        # We only keep running totals (event count, sum of gaps, sum of squared gaps) instead of every event.
        # This keeps memory small and is enough to work out the mean and standard deviation of the gaps later.
        self.counts = np.zeros(N_BUCKETS, dtype=np.int32)
        self.n = 0
        self.first = self.last = 0
        self.gap_sum = self.gap_sq = self.gap_max = 0
        self.prev_bucket = -1
        self.changes = 0
        self.hosts, self.threads = set(), set()
        self.warn = self.error = self.keyword = 0
        # HDFS lifecycle milestones
        self.alloc = self.delete = self.recv = self.ack = self.stored = 0
        self.label = 0
        self.events = [] if keep else None

    def add(self, t, thread, level, msg, hosts, label):
        b = bucket(normalise(msg))
        if self.n:
            # The gap is the time since the previous event in this session. A negative gap means the log is not sorted.
            gap = t - self.last
            if gap < 0:
                raise ValueError('Log is out of order within a session. Sort it chronologically first.')
            self.gap_sum += gap
            self.gap_sq += gap * gap
            self.gap_max = max(self.gap_max, gap)
            self.changes += b != self.prev_bucket
        else:
            self.first = t
        self.last, self.prev_bucket = t, b
        self.n += 1
        self.counts[b] += 1
        self.hosts.update(hosts)
        self.threads.add(thread)

        level = level.upper()
        self.warn += level in WARN_LEVELS
        self.error += level in ERROR_LEVELS
        # This looks for words like "error" or "timeout" in the message itself, separate from the log level.
        failed = bool(ERROR_WORDS.search(msg))
        self.keyword += failed

        # Lifecycle milestones (matched on message text, G5)
        self.alloc += 'NameSystem.allocateBlock' in msg
        self.delete += 'Deleting block' in msg
        self.recv += 'Receiving block' in msg
        # An acknowledgement is only counted if the message has no failure word in it.
        self.ack += 'PacketResponder' in msg and 'terminating' in msg and not failed
        self.stored += 'addStoredBlock: blockMap updated' in msg
        self.label = max(self.label, label)
        if self.events is not None:
            self.events.append({'time': t, 'level': level, 'message': msg})

    def row(self, sid, source, lifecycle=True):
        """Return [session_id, source, t_start, t_end, label] followed by the 52 feature values.

        lifecycle=False is for sources without an HDFS write chain (BGL). The four chain
        features are set to 0, which means "not applicable" and not a real measurement.
        """
        hdfs = lifecycle
        # Number of gaps between events = events - 1. max(..., 1) avoids dividing by zero for a 1 event session.
        n_gaps = max(self.n - 1, 1)
        duration = self.last - self.first
        gap_mean = self.gap_sum / n_gaps
        # Standard deviation from the running totals (mean of squares minus square of the mean).
        # max(0, ...) stops a tiny negative number from rounding breaking the square root.
        gap_std = float(np.sqrt(max(0, self.gap_sq / n_gaps - gap_mean ** 2)))
        # share = what fraction of this session's events fall in each bucket. It is used for the entropy feature.
        share = self.counts[self.counts > 0] / self.n
        # A write is "complete" if the block was allocated and all 3 copies were received, acknowledged and stored.
        complete = hdfs and self.alloc > 0 and min(self.recv, self.ack, self.stored) >= EXPECTED_REPLICAS
        # The values below must be in the same order as COLS: the 32 bucket counts first, then the structural features.
        features = (
            self.counts.tolist()
            + [self.n, int((self.counts > 0).sum()),
               # events per minute: the +1 stops a huge value when a session lasts only a few seconds
               duration, gap_mean, self.gap_max, gap_std, self.n / (duration / 60 + 1),
               len(self.hosts), len(self.threads),
               self.warn / self.n, self.error / self.n, self.keyword / self.n,
               int(self.alloc > 0), int(self.delete > 0),
               # These three show where the write chain stopped: copies missing, writes never acknowledged,
               # and acknowledgements never stored. They are 0 for BGL because it has no write chain.
               # shortfall vs. expected replicas: "the next step never happened"
               EXPECTED_REPLICAS - self.stored if hdfs else 0,
               self.recv - self.ack if hdfs else 0,
               self.ack - self.stored if hdfs else 0,
               int(complete),
               self.changes / n_gaps, float(-(share * np.log2(share)).sum())]
        )
        return [sid, source, self.first, self.last, self.label] + features
