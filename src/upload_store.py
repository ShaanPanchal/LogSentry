"""Keeps an index of an uploaded log on disk, so big files can be used without loading them.

`build_index` saves the byte position of every line of each session. `read_events` jumps
straight to those positions for the drill-down view. The source adapter (sources.py)
decides which session a line belongs to.
"""
import sqlite3

from processing import parse
from sources import get_source

BATCH = 10000


def build_index(log_path, index_path, source):
    session_ids = get_source(source).session_ids
    with sqlite3.connect(index_path) as db:
        db.execute('CREATE TABLE events (session TEXT, offset INTEGER)')
        batch = []
        with log_path.open('rb') as f:
            while True:
                # Remember where each line starts in the file (its byte offset) and which session it belongs to.
                # Binary mode is used so the offsets are exact.
                offset = f.tell()
                line = f.readline()
                if not line:
                    break
                ids = session_ids(line.decode('utf-8', errors='replace'))
                batch.extend((sid, offset) for sid in ids)
                if len(batch) >= BATCH:
                    db.executemany('INSERT INTO events VALUES (?,?)', batch)
                    batch.clear()
        if batch:
            db.executemany('INSERT INTO events VALUES (?,?)', batch)
        db.execute('CREATE INDEX session_events ON events(session)')


def read_events(log_path, index_path, source, sid, limit=500):
    """Get the first `limit` events of a session. Returns (events, truncated)."""
    events = []
    with sqlite3.connect(index_path) as db, log_path.open('rb') as f:
        # Look up the saved offsets for this session, then jump straight to those lines in the file.
        # The query asks for limit + 1 rows so we can tell if there were more events than we show.
        offsets = db.execute('SELECT offset FROM events WHERE session=? ORDER BY offset LIMIT ?',
                             (sid, limit + 1)).fetchall()
        for (offset,) in offsets[:limit]:
            f.seek(offset)
            try:
                ids, t, _, level, msg, _, _ = parse(f.readline().decode('utf-8', errors='replace'), source)
            except (ValueError, OverflowError):
                continue
            if sid in ids:
                events.append({'time': t, 'level': level, 'message': msg})
    return events, len(offsets) > limit
