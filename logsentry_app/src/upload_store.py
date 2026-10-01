"""Disk-backed raw log index for large dashboard uploads."""
import sqlite3
from processing import BLOCK,parse

def build_index(log_path,index_path,source):
    with sqlite3.connect(index_path) as db:
        db.execute('CREATE TABLE events (session TEXT, offset INTEGER)')
        batch=[]
        with log_path.open('rb') as f:
            while True:
                offset=f.tell();line=f.readline()
                if not line:break
                text=line.decode('utf-8',errors='replace')
                if source=='HDFS':ids=set(BLOCK.findall(text))
                else:
                    try:ids=[f'window_{int(text.split(None,2)[1])//300}']
                    except (ValueError,IndexError):continue
                batch.extend((sid,offset) for sid in ids)
                if len(batch)>=10000:
                    db.executemany('INSERT INTO events VALUES (?,?)',batch);batch.clear()
        if batch:db.executemany('INSERT INTO events VALUES (?,?)',batch)
        db.execute('CREATE INDEX session_events ON events(session)')

def read_events(log_path,index_path,source,sid,limit=500):
    events=[]
    with sqlite3.connect(index_path) as db,log_path.open('rb') as f:
        offsets=db.execute('SELECT offset FROM events WHERE session=? ORDER BY offset LIMIT ?', (sid,limit+1)).fetchall()
        for (offset,) in offsets[:limit]:
            f.seek(offset)
            try:ids,t,th,level,msg,hosts,y=parse(f.readline().decode('utf-8',errors='replace'),source)
            except (ValueError,OverflowError):continue
            if sid in ids:events.append({'time':t,'level':level,'message':msg})
    return events,len(offsets)>limit
