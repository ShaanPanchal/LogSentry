"""Classifiers, purged chronological evaluation and within-class clustering."""
import argparse,json
import joblib,numpy as np,pandas as pd
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,average_precision_score,confusion_matrix,silhouette_score
from processing import ROOT,COLS
def metrics(y,p,t):
    pred=p>=t;tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    return {'accuracy':float(accuracy_score(y,pred)),'precision':float(precision_score(y,pred,zero_division=0)),'recall':float(recall_score(y,pred,zero_division=0)),'f1':float(f1_score(y,pred,zero_division=0)),'average_precision':float(average_precision_score(y,p)),'tn':int(tn),'fp':int(fp),'fn':int(fn),'tp':int(tp),'threshold':float(t)}
def split(df):
    df=df.sort_values(['t_start','session_id']).reset_index(drop=True)
    a=df.t_start.iloc[int(len(df)*.6)];b=df.t_start.iloc[int(len(df)*.8)]
    tr=(df.t_start<a)&(df.t_end<a);va=(df.t_start>=a)&(df.t_start<b)&(df.t_end<b);te=df.t_start>=b
    df['split']=np.select([tr,va,te],['train','validation','test'],default='purged')
    for name,m in [('train',tr),('validation',va),('test',te)]:
        if df.loc[m,'label'].nunique()!=2:raise ValueError(f'{name} must contain both classes. Use the full labelled dataset.')
    return df,tr.to_numpy(),va.to_numpy(),te.to_numpy()
def candidates():return {'Logistic regression':make_pipeline(StandardScaler(),LogisticRegression(max_iter=500,class_weight='balanced',random_state=7)),'Random forest':RandomForestClassifier(n_estimators=80,max_depth=18,min_samples_leaf=2,class_weight='balanced',n_jobs=2,random_state=7),'Histogram gradient boosting':HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=31,random_state=7)}
def train(source):
    for d in ['models','results']:(ROOT/d).mkdir(exist_ok=True)
    df=pd.read_csv(ROOT/'data'/f'{source}_sessions.csv.gz',dtype={'session_id':str});df,tr,va,te=split(df)
    X=df[COLS].to_numpy(dtype=np.float32);y=df.label.to_numpy();dev=tr|va
    if not np.isfinite(X).all():raise ValueError('Nonfinite features')
    validation=[];models=candidates()
    for name,m in models.items():
        print('Fitting',source,name,flush=True);m.fit(X[tr],y[tr]);p=m.predict_proba(X[va])[:,1]
        t=max(np.arange(.05,1,.05),key=lambda t:f1_score(y[va],p>=t,zero_division=0))
        validation.append({'model':name,**metrics(y[va],p,t)})
    best=max(validation,key=lambda r:(r['f1'],r['average_precision']));tests=[]
    for name,m in models.items():
        m.fit(X[dev],y[dev]);p=m.predict_proba(X[te])[:,1];t=next(v['threshold'] for v in validation if v['model']==name)
        tests.append({'model':name,**metrics(y[te],p,t)})
        if name==best['model']:
            joblib.dump({'model':m,'columns':COLS,'threshold':t,'source':source},ROOT/'models'/f'{source}_final.joblib',compress=3)
            out=df.loc[te,['session_id','label']].copy();out['probability']=p;out['prediction']=(p>=t).astype(int)
            out.to_csv(ROOT/'results'/f'{source}_test_predictions.csv.gz',index=False)
            err=out[out.label!=out.prediction];err.head(20).to_csv(ROOT/'results'/f'{source}_error_cases.csv',index=False)
    ids=np.flatnonzero(dev&(y==1));L=np.sign(X)*np.log1p(np.abs(X));scaler=StandardScaler().fit(L[ids]);Z=scaler.transform(L[ids]);sweep=[];kms=[]
    for k in range(2,min(6,len(ids)-1)+1):
        km=KMeans(n_clusters=k,n_init=10,random_state=7).fit(Z)
        score=float(silhouette_score(Z,km.labels_,sample_size=min(3000,len(ids)),random_state=7));sweep.append({'k':k,'silhouette':score});kms.append(km)
    if not kms:raise ValueError('Not enough development anomalies for clustering')
    km=kms[max(range(len(sweep)),key=lambda i:sweep[i]['silhouette'])];profiles=[];mean=X[ids].mean(0);std=X[ids].std(0)
    for c in range(km.n_clusters):
        ci=ids[km.labels_==c];avg=X[ci].mean(0);z=(avg-mean)/np.where(std>0,std,1);top=np.argsort(np.abs(z))[-3:][::-1]
        profiles.append({'cluster':c,'sessions':len(ci),'normal':0,'anomaly':len(ci),'top_features':[{'feature':COLS[j],'cluster_mean':float(avg[j]),'overall_anomaly_mean':float(mean[j]),'z':float(z[j])} for j in top],'example_session_ids':df.iloc[ci[:3]].session_id.tolist()})
    joblib.dump({'scaler':scaler,'kmeans':km,'columns':COLS,'transform':'signed log1p'},ROOT/'models'/f'{source}_clusters.joblib')
    pd.DataFrame({'session_id':df.iloc[ids].session_id.to_numpy(),'cluster':km.labels_}).to_csv(ROOT/'results'/f'{source}_anomaly_clusters.csv',index=False)
    result={'source':source,'selected_model':best['model'],'validation':validation,'temporal_test':tests,'split_counts':df.split.value_counts().to_dict(),'clustering':{'sweep':sweep,'selected_k':km.n_clusters,'profiles':profiles}}
    (ROOT/'results'/f'{source}_evaluation.json').write_text(json.dumps(result,indent=2));df[['session_id','split']].to_csv(ROOT/'results'/f'{source}_splits.csv.gz',index=False)
    print('Saved model and evaluation:',source,best['model'],flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',choices=['HDFS','BGL'],default='HDFS');a=p.parse_args();train(a.source)
