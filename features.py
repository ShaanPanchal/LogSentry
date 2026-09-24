"""
features.py
-----------
Stage 2 of the pipeline: turn the structured event table into one row per
session, which is the unit the models actually classify.

Everything here is written as reusable functions over a generic event table
(block_id / event_id / ts / thread / level / ip1 / ip2 / n_ips).  Nothing in
this module knows it is looking at HDFS, so the same code runs over the other
log sources handled in `extra_sources.py` once they have been mapped onto the
same columns.

Feature groups and why each one is here
---------------------------------------
G1  Event count vector.  The standard session representation in the log
    anomaly literature: one column per mined template, holding how many times
    that event fired in the session (Xu et al., 2009; He et al., 2016).

G2  Volume and variety.  Total events, distinct event types.  A block whose
    write is retried leaves more events than one that succeeds first time.

G3  Timing.  Duration and the distribution of gaps between consecutive events.
    A healthy HDFS write is a tight burst; a session that stalls mid-way
    leaves a long gap even when its event counts look ordinary.

G4  Topology.  How many distinct hosts and threads the session touched.
    HDFS replicates each block to three datanodes, so host count is close to a
    direct read-out of whether replication completed.

G5  Lifecycle completeness ("absence") features.  A healthy block follows
    allocate -> receive x3 -> acknowledge x3 -> store x3 -> delete.  These
    columns measure what is *missing* from that chain rather than what is
    present, because in HDFS the common failure is a step that never happens:
    a datanode dies mid-write and the acknowledgement simply never arrives.
    A plain count vector can represent this only indirectly, as a zero among
    non-zeros; stating the shortfall explicitly gives the model a feature that
    means the same thing in every session regardless of its length.

G6  Severity and error mix.  Share of events that are exception or error
    templates, and counts by log level.

G7  Sequence regularity.  Two order-sensitive columns -- the first and last
    event of the session -- plus a transition-model score added later in
    `sequence_model.py`.  Event counts throw ordering away entirely, and
    ordering is the signal DeepLog (Du et al., 2017) is built on.
"""

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------
# Template semantics
# --------------------------------------------------------------------------
# The lifecycle features need to know which mined template means "receiving a
# block", which means "acknowledged", and so on.  Matching on the template
# *text* rather than hard-coding the integer ids matters: Drain assigns ids in
# the order it first sees each message, so the ids change if the input file
# changes.  Matching on text keeps the feature definitions stable.
ROLE_PATTERNS = {
    "allocate":     ["NameSystem.allocateBlock"],
    "receiving":    ["Receiving block"],
    "acknowledged": ["PacketResponder"],
    "stored":       ["addStoredBlock: blockMap updated"],
    "received_ok":  ["Received block"],
    "served":       ["Served block"],
    "invalidated":  ["NameSystem.delete"],
    "deleted":      ["Deleting block"],
    "verified":     ["Verification succeeded"],
    "replicate":    ["ask", "to replicate"],
    "transferred":  ["Transmitted block", "Starting thread to transfer"],
}

# Any template naming a failure. Counted together as an error-pressure signal
# and kept individually in the count vector.
ERROR_MARKERS = ["Exception", "exception", "Failed", "error", "Unexpected",
                 "timed out", "does not belong", "Redundant",
                 "already existing", "Could not"]

# HDFS writes each block to three datanodes by default, so a completed write
# should produce three acknowledgements and three stored confirmations.
EXPECTED_REPLICAS = 3


def classify_templates(templates):
    """Map each mined template id to a semantic role and an error flag.

    Parameters
    ----------
    templates : DataFrame with columns event_id, template

    Returns
    -------
    roles  : dict role -> list of event ids
    is_err : boolean array indexed by event id
    """
    n = int(templates["event_id"].max()) + 1
    text = [""] * n
    for eid, tmpl in zip(templates["event_id"], templates["template"]):
        text[int(eid)] = str(tmpl)

    roles = {}
    for role, needles in ROLE_PATTERNS.items():
        roles[role] = [
            i for i, t in enumerate(text)
            if all(nd in t for nd in needles)
            and not any(m in t for m in ERROR_MARKERS)
        ]
    is_err = np.array(
        [any(m in t for m in ERROR_MARKERS) for t in text], dtype=bool
    )
    return roles, is_err


# --------------------------------------------------------------------------
# Session feature construction
# --------------------------------------------------------------------------

def build_session_features(events, templates, id_col="block_id"):
    """Aggregate an event table into one feature row per session.

    The event table must already be sorted by (session, timestamp); sorting
    11 million rows once here is cheaper than sorting inside every groupby.
    """
    n_events_total = len(events)
    n_templates = int(templates["event_id"].max()) + 1
    roles, is_err = classify_templates(templates)

    events = events.sort_values([id_col, "ts", "line_no"], kind="stable")
    sid_codes, sid_values = pd.factorize(events[id_col].to_numpy(), sort=False)
    n_sessions = len(sid_values)

    eid = events["event_id"].to_numpy().astype(np.int64)
    ts = events["ts"].to_numpy().astype(np.int64)

    out = pd.DataFrame({id_col: sid_values})

    # -- G1  event count vector -------------------------------------------
    # One pass of bincount over the flattened (session, event) index is far
    # faster than a pivot_table on 11 M rows and uses a fraction of the memory.
    flat = sid_codes.astype(np.int64) * n_templates + eid
    counts = np.bincount(flat, minlength=n_sessions * n_templates)
    counts = counts.reshape(n_sessions, n_templates)
    # Built as one block and concatenated: inserting 44 (or, on other log
    # sources, several hundred) columns one at a time fragments the frame and
    # is measurably slower.
    out = pd.concat(
        [out, pd.DataFrame(counts,
                           columns=[f"evt_{e}" for e in range(n_templates)])],
        axis=1)

    # -- G2  volume and variety -------------------------------------------
    out["n_events"] = counts.sum(axis=1)
    out["n_distinct_events"] = (counts > 0).sum(axis=1)

    # -- G3  timing --------------------------------------------------------
    # Group boundaries: because the frame is sorted, each session occupies one
    # contiguous slice, so first/last timestamps come straight from the index.
    starts = np.searchsorted(sid_codes, np.arange(n_sessions), side="left")
    ends = np.searchsorted(sid_codes, np.arange(n_sessions), side="right") - 1
    out["t_start"] = ts[starts]
    out["duration_s"] = ts[ends] - ts[starts]

    gap = np.diff(ts)
    same = sid_codes[1:] == sid_codes[:-1]
    gaps = pd.DataFrame({"sid": sid_codes[1:][same], "gap": gap[same]})
    gstat = gaps.groupby("sid")["gap"].agg(["mean", "max", "std"])
    gstat = gstat.reindex(range(n_sessions))
    out["gap_mean_s"] = gstat["mean"].to_numpy()
    out["gap_max_s"] = gstat["max"].to_numpy()
    out["gap_std_s"] = gstat["std"].to_numpy()
    # A single-event session has no gaps at all; 0 is the honest value here
    # (no waiting happened), not a missing measurement.
    out[["gap_mean_s", "gap_max_s", "gap_std_s"]] = \
        out[["gap_mean_s", "gap_max_s", "gap_std_s"]].fillna(0.0)
    out["events_per_min"] = out["n_events"] / (out["duration_s"] / 60.0 + 1.0)

    # -- G4  topology ------------------------------------------------------
    hosts = pd.concat([
        pd.DataFrame({"sid": sid_codes, "h": events["ip1"].to_numpy()}),
        pd.DataFrame({"sid": sid_codes, "h": events["ip2"].to_numpy()}),
    ])
    hosts = hosts[hosts["h"] != 0].drop_duplicates()
    out["n_hosts"] = (hosts.groupby("sid").size()
                      .reindex(range(n_sessions), fill_value=0).to_numpy())
    threads = pd.DataFrame({"sid": sid_codes,
                            "t": events["thread"].to_numpy()}).drop_duplicates()
    out["n_threads"] = (threads.groupby("sid").size()
                        .reindex(range(n_sessions), fill_value=0).to_numpy())

    # -- G5  lifecycle completeness (absence) ------------------------------
    def role_count(role):
        ids = roles.get(role, [])
        if not ids:
            return np.zeros(n_sessions, dtype=np.int64)
        return counts[:, ids].sum(axis=1)

    n_recv = role_count("receiving")
    n_ack = role_count("acknowledged")
    n_stored = role_count("stored")
    n_alloc = role_count("allocate")
    n_del = role_count("deleted")

    out["has_allocate"] = (n_alloc > 0).astype(np.int8)
    out["has_delete"] = (n_del > 0).astype(np.int8)
    # Shortfall against the expected replication factor: positive means
    # replicas that were promised but never confirmed.
    out["replica_deficit"] = EXPECTED_REPLICAS - n_stored
    # Writes that started but were never acknowledged, and acknowledgements
    # that were never committed to the namespace.  Both are "the next step
    # never happened" signals.
    out["unacked_writes"] = n_recv - n_ack
    out["uncommitted_acks"] = n_ack - n_stored
    out["lifecycle_complete"] = (
        (n_alloc > 0) & (n_recv >= EXPECTED_REPLICAS)
        & (n_ack >= EXPECTED_REPLICAS) & (n_stored >= EXPECTED_REPLICAS)
    ).astype(np.int8)

    # -- G6  severity and error mix ---------------------------------------
    err_ids = np.nonzero(is_err)[0]
    n_err = counts[:, err_ids].sum(axis=1) if len(err_ids) else np.zeros(n_sessions)
    out["n_error_events"] = n_err
    out["error_ratio"] = n_err / np.maximum(out["n_events"], 1)
    lv = pd.DataFrame({"sid": sid_codes, "lv": events["level"].to_numpy()})
    for code, name in [(1, "warn"), (2, "error")]:
        s = lv[lv["lv"] == code].groupby("sid").size()
        out[f"n_level_{name}"] = s.reindex(range(n_sessions),
                                           fill_value=0).to_numpy()

    # -- G7  sequence endpoints -------------------------------------------
    out["first_event"] = eid[starts]
    out["last_event"] = eid[ends]

    assert out["n_events"].sum() == n_events_total, \
        "event rows lost during aggregation"
    return out


def feature_columns(df, id_col="block_id"):
    """The model input columns: everything except identifiers, the label and
    the session start time.  `t_start` is deliberately excluded -- it is used
    to build the temporal split, and leaving it in would let a model learn
    'anomalies happened on the second day' instead of learning the log."""
    drop = {id_col, "label", "t_start", "source"}
    return [c for c in df.columns if c not in drop]
