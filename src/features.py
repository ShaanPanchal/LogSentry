"""Session feature extraction (the single authoritative feature schema).

One `Session` accumulates the events of one session (an HDFS block, or a BGL
five-minute window) and `Session.row()` turns it into one fixed-length feature
vector.  The same code produces the training table, the dashboard's live
features and the command-line predictions, so the model can never see a
different schema at prediction time than it was trained on.

Feature groups and why each is here
-----------------------------------
G1  Event-type counts (32 hashed buckets).  The standard session representation
    in the log-anomaly literature (Xu et al. 2009; He et al. 2016): how many
    times each kind of event fired.  Each message is first normalised so that
    variable parts (block ids, IPs, paths, numbers) disappear, then hashed into
    one of 32 buckets.  Hashing keeps the schema fixed for logs whose template
    set is unknown in advance (e.g. a user upload) - no template miner or
    vocabulary has to be shipped with the model.
G2  Volume and variety: total events, number of distinct buckets used.
G3  Timing: duration and the distribution of gaps between consecutive events.
    A healthy HDFS write is a tight burst; a stalled one leaves a long gap.
G4  Topology: distinct hosts and threads touched.  HDFS replicates each block
    to three datanodes, so host count tracks whether replication completed.
G5  Lifecycle completeness ("absence") features.  A healthy HDFS block follows
    allocate -> receive x3 -> acknowledge x3 -> store x3 -> delete.  These
    columns measure what is *missing* from that chain, because the common HDFS
    failure is a step that never happens.  They are HDFS-specific: for
    sources without that write chain (BGL) replica_deficit, unacked_writes,
    uncommitted_acks and lifecycle_complete are fixed at 0 (not applicable) and
    has_allocate / has_delete are 0 because those messages never occur.
G6  Severity: share of WARN and ERROR-level events, and of messages that
    contain failure keywords (error, exception, timeout, ...).
G7  Sequence regularity: share of consecutive event pairs that change bucket,
    and the Shannon entropy of the bucket distribution.  Counts discard order;
    these two recover a little of it (cf. DeepLog, Du et al. 2017).
"""
import re
import zlib
from functools import lru_cache

import numpy as np

# --------------------------------------------------------------------------
# Message normalisation and hashing
# --------------------------------------------------------------------------
BLOCK = re.compile(r'blk_-?\d+')
IP = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b')
PATH = re.compile(r'/(?:[^\s,;:]+/)*[^\s,;:]*')
NUM = re.compile(r'[-+]?\d+(?:\.\d+)?')
HEX = re.compile(r'\b0x[0-9a-fA-F]+\b')
ERROR_WORDS = re.compile(r'error|exception|fail|timed? out|timeout|fatal|panic|corrupt', re.I)

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
COLS = BUCKET_COLS + STRUCTURAL_COLS  # the 52 model input columns


def normalise(msg):
    """Replace variable tokens so messages of one kind look identical."""
    msg = BLOCK.sub('<BLOCK>', msg)
    msg = IP.sub('<IP>', msg)
    msg = PATH.sub('<PATH>', msg)
    return NUM.sub('<N>', HEX.sub('<HEX>', msg))


@lru_cache(maxsize=100000)
def bucket(text):
    """Stable hash bucket of a normalised message (crc32, not Python's hash())."""
    return zlib.crc32(text.encode()) % N_BUCKETS


class Session:
    """Streaming accumulator: feed events in time order, then call `row()`."""

    def __init__(self, keep=False):
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
        failed = bool(ERROR_WORDS.search(msg))
        self.keyword += failed

        # Lifecycle milestones (matched on message text, G5)
        self.alloc += 'NameSystem.allocateBlock' in msg
        self.delete += 'Deleting block' in msg
        self.recv += 'Receiving block' in msg
        self.ack += 'PacketResponder' in msg and 'terminating' in msg and not failed
        self.stored += 'addStoredBlock: blockMap updated' in msg
        self.label = max(self.label, label)
        if self.events is not None:
            self.events.append({'time': t, 'level': level, 'message': msg})

    def row(self, sid, source, lifecycle=True):
        """[session_id, source, t_start, t_end, label] + the 52 COLS values.

        `lifecycle=False` (sources without an HDFS-style write chain, e.g. BGL) sets the
        four chain-completeness features to 0: the events they count do not exist there,
        so 0 means 'not applicable' rather than a measurement.
        """
        hdfs = lifecycle
        n_gaps = max(self.n - 1, 1)
        duration = self.last - self.first
        gap_mean = self.gap_sum / n_gaps
        gap_std = float(np.sqrt(max(0, self.gap_sq / n_gaps - gap_mean ** 2)))
        share = self.counts[self.counts > 0] / self.n
        complete = hdfs and self.alloc > 0 and min(self.recv, self.ack, self.stored) >= EXPECTED_REPLICAS
        features = (
            self.counts.tolist()
            + [self.n, int((self.counts > 0).sum()),
               duration, gap_mean, self.gap_max, gap_std, self.n / (duration / 60 + 1),
               len(self.hosts), len(self.threads),
               self.warn / self.n, self.error / self.n, self.keyword / self.n,
               int(self.alloc > 0), int(self.delete > 0),
               # shortfall vs. expected replicas: "the next step never happened"
               EXPECTED_REPLICAS - self.stored if hdfs else 0,
               self.recv - self.ack if hdfs else 0,
               self.ack - self.stored if hdfs else 0,
               int(complete),
               self.changes / n_gaps, float(-(share * np.log2(share)).sum())]
        )
        return [sid, source, self.first, self.last, self.label] + features
