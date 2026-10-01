"""Local browser interface: upload, score, filter and drill down."""
import tempfile,shutil,atexit,math,csv,io
from pathlib import Path
from flask import Flask,request,render_template,jsonify,Response,url_for
from predict import predict
from processing import ROOT
from upload_store import build_index,read_events
app=Flask(__name__);app.config['MAX_CONTENT_LENGTH']=4*1024*1024*1024
STATE={'df':None,'events':{},'audit':{},'upload_dir':None,'source':None}
def cleanup():
    if STATE.get('upload_dir'):shutil.rmtree(STATE['upload_dir'],ignore_errors=True)
atexit.register(cleanup)
@app.route('/',methods=['GET','POST'])
def index():
    error=None
    if request.method=='POST':
        source=request.form.get('source');upload=request.files.get('log')
        if source not in ('HDFS','BGL') or not upload:error='Choose a supported source and a log file.'
        else:
            d=tempfile.mkdtemp(prefix='logsentry-upload-')
            try:
                path=Path(d)/'upload.log';upload.save(path)
                df,audit,_=predict(path,source,keep=False)
                print('Building disk index for session drill-down...',flush=True)
                build_index(path,Path(d)/'events.sqlite',source)
                cleanup()
                STATE.update(df=df,audit=audit,events={},upload_dir=d,source=source)
            except Exception as e:
                shutil.rmtree(d,ignore_errors=True)
                if not isinstance(e,(ValueError,FileNotFoundError,KeyError)):raise
                error=str(e)
    if request.method=='POST' and request.headers.get('X-Requested-With')=='XMLHttpRequest':
        return jsonify(success=not bool(error),error=error),400 if error else 200
    truncated=False
    df=STATE['df'];rows=[];total=flagged=None;detail=None;events=[];q=request.args.get('q','');only=request.args.get('anomalies')=='1'
    sort=request.args.get('sort','score');matching=0;page=1;pages=1;prev_url=next_url=None
    if df is not None:
        total=len(df);flagged=int((df.decision=='ANOMALY').sum());view=df
        if q:view=view[view.session_id.str.contains(q,regex=False)]
        if only:view=view[view.decision=='ANOMALY']
        matching=len(view);pages=max(1,math.ceil(matching/50))
        try:page=max(1,min(pages,int(request.args.get('page',1))))
        except ValueError:page=1
        column={'score':'score','events':'n_events','id':'session_id'}.get(sort,'score')
        rows=view.sort_values(column,ascending=column=='session_id').iloc[(page-1)*50:page*50].to_dict('records')
        if page>1:prev_url=url_for('index',q=q,sort=sort,anomalies='1' if only else '0',page=page-1)
        if page<pages:next_url=url_for('index',q=q,sort=sort,anomalies='1' if only else '0',page=page+1)
        sid=request.args.get('session');match=df[df.session_id==sid]
        if len(match):
            detail=match.iloc[0].to_dict();d=Path(STATE['upload_dir'])
            events,truncated=read_events(d/'upload.log',d/'events.sqlite',STATE['source'],sid)
    ready=[s for s in ['HDFS','BGL'] if (ROOT/'models'/f'{s}_final.joblib').exists()]
    return render_template('dashboard.html',source=STATE['source'],sort=sort,matching=matching,page=page,pages=pages,prev_url=prev_url,next_url=next_url,ready=ready,error=error,total=total,flagged=flagged,rows=rows,audit=STATE['audit'],q=q,only=only,detail=detail,events=events,truncated=truncated)
@app.errorhandler(413)
def large(e):
    if request.headers.get('X-Requested-With')=='XMLHttpRequest':return jsonify(success=False,error='File exceeds the 4 GB upload limit.'),413
    return 'File exceeds the 4 GB upload limit.',413
@app.route('/export')
def export():
    df=STATE['df']
    if df is None:return 'Upload and analyse a log first.',400
    def rows():
        buffer=io.StringIO();writer=csv.writer(buffer)
        writer.writerow(df.columns);yield buffer.getvalue();buffer.seek(0);buffer.truncate(0)
        for row in df.itertuples(index=False,name=None):
            writer.writerow(row);yield buffer.getvalue();buffer.seek(0);buffer.truncate(0)
    return Response(rows(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=logsentry-predictions.csv'})
if __name__=='__main__':app.run(host='127.0.0.1',port=5000,debug=False)
