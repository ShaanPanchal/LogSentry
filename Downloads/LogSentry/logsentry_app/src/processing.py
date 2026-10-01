"""Reconstructed raw HDFS/BGL adapters and fixed 52-feature schema.
This implementation requires its own trained models. The inherited XGBoost
bundle has a different feature schema and is deliberately not loaded here.
"""
import re,zlib,gzip
from pathlib import Path
from datetime import datetime,timezone
from functools import lru_cache
from collections import Counter
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
BLOCK=re.compile(r'blk_-?\d+')
IP=re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b')
PATH=re.compile(r'/(?:[^\s,;:]+/)*[^\s,;:]*')
NUM=re.compile(r'[-+]?\d+(?:\.\d+)?')
HEX=re.compile(r'\b0x[0-9a-fA-F]+\b')
ERR=re.compile(r'error|exception|fail|timed? out|timeout|fatal|panic|corrupt',re.I)
COLS=[f'event_hash_{i:02d}' for i in range(32)]+['n_events','n_event_buckets','duration_s','gap_mean_s','gap_max_s','gap_std_s','events_per_min','n_hosts','n_threads','warning_ratio','error_ratio','keyword_error_ratio','has_allocate','has_delete','replica_deficit','unacked_writes','uncommitted_acks','lifecycle_complete','transition_change_ratio','event_entropy']
def normalise(msg):
    msg=BLOCK.sub('<BLOCK>',msg);msg=IP.sub('<IP>',msg);msg=PATH.sub('<PATH>',msg)
    return NUM.sub('<N>',HEX.sub('<HEX>',msg))
@lru_cache(maxsize=100000)
def bucket(text):return zlib.crc32(text.encode())%32
@lru_cache(maxsize=200000)
def stamp(d,t):return int(datetime.strptime(d+t,'%y%m%d%H%M%S').replace(tzinfo=timezone.utc).timestamp())
def parse(line,source):
    if source=='HDFS':
        p=line.strip().split(None,5)
        if len(p)!=6:raise ValueError('Invalid HDFS fields')
        msg=p[5]
        return list(dict.fromkeys(BLOCK.findall(msg))),stamp(p[0],p[1]),p[2],p[3],msg,[h.split(':')[0] for h in IP.findall(msg)],0
    if source!='BGL':raise ValueError('Unsupported source')
    p=line.strip().split(None,9)
    if len(p)==9:p.append('')
    if len(p)!=10:raise ValueError('Invalid BGL fields')
    t=int(p[1])
    # The leading annotation is removed before computing any feature.
    return [f'window_{t//300}'],t,p[7],p[8],p[9],[p[3]],int(p[0]!='-')
class Session:
    def __init__(self,keep):
        self.c=np.zeros(32,dtype=np.int32);self.n=0;self.first=self.last=0
        self.gsum=self.gsq=self.gmax=0;self.prev=-1;self.change=0
        self.hosts=set();self.threads=set();self.warn=self.error=self.keyword=0
        self.alloc=self.delete=self.recv=self.ack=self.stored=self.label=0
        self.events=[] if keep else None
    def add(self,t,thread,level,msg,hosts,y):
        b=bucket(normalise(msg))
        if self.n:
            gap=t-self.last
            if gap<0:raise ValueError('Log is out of order within a session. Sort it chronologically first.')
            self.gsum+=gap;self.gsq+=gap*gap;self.gmax=max(self.gmax,gap);self.change+=b!=self.prev
        else:self.first=t
        self.last=t;self.prev=b;self.n+=1;self.c[b]+=1
        self.hosts.update(hosts);self.threads.add(thread)
        self.warn+=level.upper() in ('WARN','WARNING');self.error+=level.upper() in ('ERROR','FATAL','SEVERE','FAILURE')
        bad=bool(ERR.search(msg));self.keyword+=bad
        self.alloc+='NameSystem.allocateBlock' in msg;self.delete+='Deleting block' in msg
        self.recv+='Receiving block' in msg;self.ack+='PacketResponder' in msg and 'terminating' in msg and not bad
        self.stored+='addStoredBlock: blockMap updated' in msg;self.label=max(self.label,y)
        if self.events is not None:self.events.append({'time':t,'level':level,'message':msg})
    def row(self,sid,source):
        ng=max(self.n-1,1);dur=self.last-self.first;p=self.c[self.c>0]/self.n;h=source=='HDFS'
        return [sid,source,self.first,self.last,self.label]+self.c.tolist()+[self.n,int((self.c>0).sum()),dur,self.gsum/ng,self.gmax,float(np.sqrt(max(0,self.gsq/ng-(self.gsum/ng)**2))),self.n/(dur/60+1),len(self.hosts),len(self.threads),self.warn/self.n,self.error/self.n,self.keyword/self.n,int(self.alloc>0),int(self.delete>0),3-self.stored if h else 0,self.recv-self.ack if h else 0,self.ack-self.stored if h else 0,int(h and self.alloc>0 and min(self.recv,self.ack,self.stored)>=3),self.change/ng,float(-(p*np.log2(p)).sum())]
def process(path,source,labels=None,keep=False):
    sessions={};audit=Counter();op=gzip.open if str(path).endswith('.gz') else open
    with op(path,'rt',encoding='utf-8',errors='replace') as f:
        for i,line in enumerate(f,1):
            audit['raw_lines']+=1
            try:ids,t,th,lv,msg,hosts,y=parse(line,source)
            except (ValueError,OverflowError):audit['malformed_lines']+=1;continue
            if not ids:audit['no_session_id']+=1;continue
            for sid in ids:
                if sid not in sessions:sessions[sid]=Session(keep)
                sessions[sid].add(t,th,lv,msg,hosts,y);audit['event_assignments']+=1
            if i%1000000==0:print(source,f'{i:,} lines',flush=True)
    if not sessions:raise ValueError('No supported sessions found in this file')
    df=pd.DataFrame([s.row(k,source) for k,s in sessions.items()],columns=['session_id','source','t_start','t_end','label']+COLS)
    if source=='HDFS':
        if labels:
            lab=pd.read_csv(labels,dtype={'BlockId':str})
            if lab.BlockId.duplicated().any():raise ValueError('Duplicate label IDs')
            df.label=df.session_id.map(lab.set_index('BlockId').Label.map({'Normal':0,'Anomaly':1}))
            if df.label.isna().any():raise ValueError('Missing or unrecognised HDFS labels')
            df.label=df.label.astype(int)
        else:df.label=-1
    audit['sessions']=len(df)
    return df,dict(audit),{k:s.events for k,s in sessions.items()} if keep else {}
