"""Small synthetic fixtures verify mechanics, not model accuracy."""
import io,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import joblib,numpy as np,pandas as pd
from sklearn.dummy import DummyClassifier
import processing,predict,dashboard
from train import split

RAW='081109 203518 1 INFO dfs.DataNode: Receiving block blk_1 from 10.0.0.1\n081109 203519 2 ERROR dfs.DataNode: Error block blk_1\n081109 203520 3 INFO dfs.DataNode: Receiving block blk_2\n'
class PipelineTests(unittest.TestCase):
    def test_normalisation(self):
        self.assertEqual(processing.normalise('block blk_10 on 10.0.0.1 value 32'),processing.normalise('block blk_-20 on 192.168.1.2 value 99'))
    def test_hdfs_sessions(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'log';p.write_text(RAW+'bad line\n')
            df,a,e=processing.process(p,'HDFS',keep=True)
            self.assertEqual(len(df),2);self.assertEqual(a['malformed_lines'],1)
            self.assertEqual(len(processing.COLS),52);self.assertEqual(len(e['blk_1']),2)
            self.assertEqual(df.iloc[0].error_ratio,.5)
    def test_bgl_annotation_exclusion(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'log';base=' 1117838570 2005.06.03 node 2005-06-03-15.42.50 node RAS KERNEL INFO message\n'
            p.write_text('-'+base);a,_,_=processing.process(p,'BGL')
            p.write_text('KERNERR'+base);b,_,_=processing.process(p,'BGL')
            np.testing.assert_equal(a[processing.COLS].to_numpy(),b[processing.COLS].to_numpy())
            self.assertEqual(a.label.iloc[0],0);self.assertEqual(b.label.iloc[0],1)
    def test_split_purges_boundary_sessions(self):
        df=pd.DataFrame({'session_id':[str(i) for i in range(20)],'t_start':range(20),'t_end':range(20),'label':[i%2 for i in range(20)]})
        df.loc[10,'t_end']=13
        df,tr,va,te=split(df)
        self.assertEqual(df.loc[df.session_id=='10','split'].iloc[0],'purged')
        self.assertFalse((tr&va|tr&te|va&te).any())
    def test_dashboard_upload_and_drilldown(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'models').mkdir()
            m=DummyClassifier(strategy='prior').fit(np.zeros((2,52)),[0,1])
            joblib.dump({'model':m,'columns':processing.COLS,'threshold':.4},root/'models/HDFS_final.joblib')
            oldp,oldd=predict.ROOT,dashboard.ROOT
            predict.ROOT=dashboard.ROOT=root
            try:
                c=dashboard.app.test_client()
                r=c.post('/',data={'source':'HDFS','log':(io.BytesIO(RAW.encode()),'test.log')})
                self.assertEqual(r.status_code,200);self.assertIn(b'SESSIONS ANALYSED',r.data)
                r=c.get('/?session=blk_1');self.assertIn(b'Error block blk_1',r.data)
                r=c.get('/?q=blk_2');self.assertIn(b'blk_2',r.data);self.assertNotIn(b'href="/?session=blk_1"',r.data)
                # A real multipart request above the previous 64 MiB limit.
                large=root/'large.log'
                with large.open('wb') as f:
                    f.write(RAW.encode())
                    for _ in range(65):f.write(b' '*(1024*1024-1)+b'\n')
                with large.open('rb') as f:
                    r=c.post('/',data={'source':'HDFS','log':(f,'large.log')})
                self.assertEqual(r.status_code,200);self.assertIn(b'SESSIONS ANALYSED',r.data)
                self.assertEqual(dashboard.STATE['events'],{})
                r=c.get('/?session=blk_1');self.assertIn(b'Error block blk_1',r.data)
                r=c.get('/export');self.assertEqual(r.status_code,200);self.assertIn(b'session_id',r.data);self.assertIn(b'blk_1',r.data)
                r=c.post('/',headers={'X-Requested-With':'XMLHttpRequest'},data={'source':'HDFS','log':(io.BytesIO(RAW.encode()),'test.log')})
                self.assertTrue(r.json['success'])
                r=c.post('/',headers={'X-Requested-With':'XMLHttpRequest'},data={'source':'UNKNOWN','log':(io.BytesIO(RAW.encode()),'test.log')})
                self.assertEqual(r.status_code,400);self.assertFalse(r.json['success'])
            finally:
                dashboard.cleanup()
                predict.ROOT, dashboard.ROOT=oldp,oldd
                dashboard.STATE.update(df=None,events={},audit={})
    def test_missing_model_message(self):
        with tempfile.TemporaryDirectory() as d:
            old=predict.ROOT;predict.ROOT=Path(d)
            try:
                with self.assertRaisesRegex(ValueError,'setup_data.py'):predict.predict(Path(d)/'log','HDFS')
            finally:predict.ROOT=old
if __name__=='__main__':unittest.main()
