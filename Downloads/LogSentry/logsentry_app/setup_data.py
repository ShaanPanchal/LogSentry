"""One-time download, chronological sorting, feature building and training."""
import argparse,hashlib,heapq,json,sys,tempfile,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from processing import process
from train import train
SOURCES={'HDFS':('HDFS_v1','76a24b4d9a6164d543fb275f89773260',['HDFS.log','preprocessed/anomaly_label.csv']),'BGL':('BGL','4452953c470f2d95fcb32d5f6e733f7a',['BGL.log'])}
def sort_file(path,out,source):
    def key(line):
        p=line.split(None,2)
        try:return int(p[0]+p[1]) if source=='HDFS' else int(p[1])
        except (ValueError,IndexError):return -1
    with tempfile.TemporaryDirectory(dir=path.parent) as temp:
        files=[];chunk=[]
        def flush():
            p=Path(temp)/str(len(files));p.write_text(''.join(sorted(chunk,key=key)));files.append(p);chunk.clear()
        with path.open(encoding='utf-8',errors='replace') as f:
            for line in f:
                chunk.append(line if line.endswith('\n') else line+'\n')
                if len(chunk)>=100000:flush()
        if chunk:flush()
        streams=[p.open() for p in files]
        try:
            with out.open('w') as f:f.writelines(heapq.merge(*streams,key=key))
        finally:
            for f in streams:f.close()
def setup(source):
    for folder in ('data','models','results'):(ROOT/folder).mkdir(exist_ok=True)
    archive,digest,files=SOURCES[source];raw=ROOT/'raw';raw.mkdir(exist_ok=True);dest=raw/archive;dest.mkdir(exist_ok=True)
    processed=ROOT/'data'/f'{source}_sessions.csv.gz'
    if not processed.exists():
        zip_path=raw/(archive+'.zip')
        if not zip_path.exists():
            print('Downloading',archive,'from Zenodo. This may take several minutes.',flush=True)
            urllib.request.urlretrieve(f'https://zenodo.org/records/8196385/files/{archive}.zip',zip_path)
        h=hashlib.md5()
        with zip_path.open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
        if h.hexdigest()!=digest:raise ValueError(f'Archive checksum mismatch. Delete {zip_path} and retry.')
        print('Checksum verified. Extracting required raw files.',flush=True)
        with zipfile.ZipFile(zip_path) as z:
            for name in files:z.extract(name,dest)
        log=dest/files[0];sorted_log=dest/(source+'.sorted.log')
        print('Sorting records chronologically...',flush=True);sort_file(log,sorted_log,source)
        labels=dest/files[1] if source=='HDFS' else None
        print('Building sessions and features...',flush=True);df,audit,_=process(sorted_log,source,labels)
        df.to_csv(processed,index=False,float_format='%.8g');(ROOT/'results'/f'{source}_parse_audit.json').write_text(json.dumps(audit,indent=2))
    train(source)
    print('Ready. Start the dashboard with: python src/dashboard.py',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',choices=['HDFS','BGL'],default='HDFS');a=p.parse_args();setup(a.source)
