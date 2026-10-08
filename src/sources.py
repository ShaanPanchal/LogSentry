"""Dataset adapters: everything specific to one log format lives here.

The shared pipeline (processing.py -> features.py -> models) never looks at raw
line formats.  An adapter turns one raw line into the common event tuple

    (session_ids, unix_time, thread, level, message, host_ips, line_label)

and states how that dataset defines a session and where its labels come from.
Adding a log source means adding one `Source` here and nothing else.

HDFS  - a session is a block (`blk_<id>`): every line mentioning a block belongs
        to that block's session.  Labels come from a separate per-block file.
BGL   - Blue Gene/L has no session identifier, so a session is a fixed
        five-minute time window (a standard choice for BGL).  Labels are in the
        log itself: the first field of each line is '-' for normal lines and an
        alert category otherwise.  A window is anomalous if any line in it is an
        alert.  That tag is returned only as the line label; it is never passed
        to the feature code.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from typing import Callable

from features import BLOCK, IP

BGL_WINDOW_SECONDS = 300


@lru_cache(maxsize=200000)
def stamp(date, time):
    """HDFS 'yymmdd' + 'HHMMSS' -> unix seconds (UTC)."""
    return int(datetime.strptime(date + time, '%y%m%d%H%M%S').replace(tzinfo=timezone.utc).timestamp())


# --------------------------------------------------------------------------- HDFS
def parse_hdfs(line):
    """`081109 203518 143 INFO dfs.DataNode$PacketResponder: <message>`"""
    parts = line.strip().split(None, 5)
    if len(parts) != 6:
        raise ValueError('Invalid HDFS fields')
    msg = parts[5]
    session_ids = list(dict.fromkeys(BLOCK.findall(msg)))
    hosts = [h.split(':')[0] for h in IP.findall(msg)]
    return session_ids, stamp(parts[0], parts[1]), parts[2], parts[3], msg, hosts, 0


def hdfs_session_ids(line):
    return set(BLOCK.findall(line))


def hdfs_sort_key(line):
    parts = line.split(None, 2)
    try:
        return int(parts[0] + parts[1])
    except (ValueError, IndexError):
        return -1


# --------------------------------------------------------------------------- BGL
def bgl_window(t):
    return f'window_{t // BGL_WINDOW_SECONDS}'


def parse_bgl(line):
    """`<tag> <unix_ts> <date> <node> <time> <node> RAS <component> <level> <message>`

    Fields used: node (host), component (stands in for HDFS's thread), level and
    message.  The alert tag is the line's label only.
    """
    parts = line.strip().split(None, 9)
    if len(parts) == 9:  # empty message
        parts.append('')
    if len(parts) != 10:
        raise ValueError('Invalid BGL fields')
    t = int(parts[1])
    return [bgl_window(t)], t, parts[7], parts[8], parts[9], [parts[3]], int(parts[0] != '-')


def bgl_session_ids(line):
    try:
        return [bgl_window(int(line.split(None, 2)[1]))]
    except (ValueError, IndexError):
        return []


def bgl_sort_key(line):
    parts = line.split(None, 2)
    try:
        return int(parts[1])
    except (ValueError, IndexError):
        return -1


# ------------------------------------------------------------------------ registry
@dataclass(frozen=True)
class Source:
    name: str
    title: str
    archive: str                  # folder / zip name under data/raw/ (Loghub, Zenodo record 8196385)
    md5: str                      # MD5 of the zip as published on Zenodo
    files: tuple                  # members to extract; files[0] is the raw log
    session_definition: str
    label_policy: str
    labels_in_log: bool           # True: labels come from the log lines; False: separate label file
    has_lifecycle: bool           # True: HDFS write-lifecycle features (G5) are meaningful for this source
    parse: Callable
    session_ids: Callable         # fast, parse-free session lookup (used for the drill-down index)
    sort_key: Callable


SOURCES = {
    'HDFS': Source(
        name='HDFS', title='Hadoop Distributed File System (HDFS)', archive='HDFS_v1',
        md5='76a24b4d9a6164d543fb275f89773260', files=('HDFS.log', 'preprocessed/anomaly_label.csv'),
        session_definition='one session per block id (blk_...)',
        label_policy='per-block labels from anomaly_label.csv', labels_in_log=False, has_lifecycle=True,
        parse=parse_hdfs, session_ids=hdfs_session_ids, sort_key=hdfs_sort_key),
    'BGL': Source(
        name='BGL', title='Blue Gene/L supercomputer (BGL)', archive='BGL',
        md5='4452953c470f2d95fcb32d5f6e733f7a', files=('BGL.log',),
        session_definition=f'fixed {BGL_WINDOW_SECONDS // 60}-minute time windows (no session id exists in BGL)',
        label_policy="window is anomalous if any line has an alert tag (first field != '-')", labels_in_log=True,
        has_lifecycle=False, parse=parse_bgl, session_ids=bgl_session_ids, sort_key=bgl_sort_key),
}


def get_source(name):
    try:
        return SOURCES[name]
    except KeyError:
        raise ValueError('Unsupported source') from None
