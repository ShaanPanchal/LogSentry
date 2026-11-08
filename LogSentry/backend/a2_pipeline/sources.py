"""Dataset adapters. Everything that is specific to one log format is in this file.

The rest of the pipeline never reads raw lines. An adapter turns a line into this tuple:

    (session_ids, unix_time, thread, level, message, host_ips, line_label)

It also says how the dataset defines a session and where its labels come from.

HDFS: a session is a block (blk_<id>). Any line that mentions a block belongs to it.
      Labels come from a separate file.
BGL:  there is no session id, so a session is a fixed five minute time window. The label
      is in the log: the first field is '-' for normal lines and an alert name otherwise.
      A window is anomalous if any of its lines is an alert. The alert name is only used
      as the label and is never given to the features.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from typing import Callable

from features import BLOCK, IP

BGL_WINDOW_SECONDS = 300


@lru_cache(maxsize=200000)
def stamp(date, time):
    """Convert an HDFS date and time ('yymmdd', 'HHMMSS') to unix seconds (UTC)."""
    return int(datetime.strptime(date + time, '%y%m%d%H%M%S').replace(tzinfo=timezone.utc).timestamp())


# --------------------------------------------------------------------------- HDFS
def parse_hdfs(line):
    """Line format: `081109 203518 143 INFO dfs.DataNode$PacketResponder: <message>`"""
    parts = line.strip().split(None, 5)
    if len(parts) != 6:
        raise ValueError('Invalid HDFS fields')
    msg = parts[5]
    # One line can mention several blocks. dict.fromkeys removes repeats but keeps the order.
    session_ids = list(dict.fromkeys(BLOCK.findall(msg)))
    # Hosts are the IP addresses in the message. The port is removed so one machine counts once.
    hosts = [h.split(':')[0] for h in IP.findall(msg)]
    return session_ids, stamp(parts[0], parts[1]), parts[2], parts[3], msg, hosts, 0


# --------------------------------------------------------------------------- BGL
# BGL has no session id, so the session is the 5 minute window the timestamp falls in.
def bgl_window(t):
    return f'window_{t // BGL_WINDOW_SECONDS}'


def parse_bgl(line):
    """Line format: `<tag> <unix_ts> <date> <node> <time> <node> RAS <component> <level> <message>`

    Used fields: node (host), component (in place of the HDFS thread), level and message.
    The tag is only the label.
    """
    parts = line.strip().split(None, 9)
    # A BGL line with an empty message gives one field fewer, so add an empty message back.
    if len(parts) == 9:  # empty message
        parts.append('')
    if len(parts) != 10:
        raise ValueError('Invalid BGL fields')
    t = int(parts[1])
    # The first field is "-" for normal lines. It becomes the label (0 or 1) and is never used as a feature.
    # The BGL component (e.g. KERNEL) is used where HDFS has a thread id.
    return [bgl_window(t)], t, parts[7], parts[8], parts[9], [parts[3]], int(parts[0] != '-')


# ------------------------------------------------------------------------ registry
@dataclass(frozen=True)
class Source:
    name: str
    labels_in_log: bool           # True: labels come from the log lines; False: separate label file
    has_lifecycle: bool           # True: HDFS write-lifecycle features (G5) are meaningful for this source
    parse: Callable


SOURCES = {
    'HDFS': Source(name='HDFS', labels_in_log=False, has_lifecycle=True, parse=parse_hdfs),
    'BGL': Source(name='BGL', labels_in_log=True, has_lifecycle=False, parse=parse_bgl),
}


def get_source(name):
    try:
        return SOURCES[name]
    except KeyError:
        raise ValueError('Unsupported source') from None
