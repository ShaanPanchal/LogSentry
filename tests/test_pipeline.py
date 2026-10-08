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
    BGL_LINES = (
        '- 1117838570 2005.06.03 R02-M1-N0-C:J12-U11 2005-06-03-15.42.50.675872 R02-M1-N0-C:J12-U11 RAS KERNEL INFO instruction cache parity error corrected\n'
        '- 1117838573 2005.06.03 R02-M1-N0-C:J12-U11 2005-06-03-15.42.53.276129 R02-M1-N0-C:J12-U11 RAS KERNEL INFO instruction cache parity error corrected\n'
        'KERNDTLB 1117838880 2005.06.03 R04-M0-N1-C:J02-U01 2005-06-03-15.48.00.000001 R04-M0-N1-C:J02-U01 RAS KERNEL FATAL data TLB error interrupt\n'
        '- 1117839200 2005.06.03 R04-M0-N1-C:J02-U01 2005-06-03-15.53.20.000001 R04-M0-N1-C:J02-U01 RAS APP INFO ciod: generated 128 core files\n')

    def test_bgl_parser_fields_windows_and_labels(self):
        import sources
        lines = self.BGL_LINES.splitlines()
        ids, t, comp, level, msg, hosts, label = sources.parse_bgl(lines[0])
        self.assertEqual((t, comp, level, hosts, label), (1117838570, 'KERNEL', 'INFO', ['R02-M1-N0-C:J12-U11'], 0))
        self.assertEqual(msg, 'instruction cache parity error corrected')
        self.assertEqual(ids, ['window_' + str(1117838570 // 300)])
        self.assertEqual(sources.parse_bgl(lines[2])[6], 1)                              # alert tag -> label 1
        self.assertEqual(sources.parse_bgl('KERNDTLB 1 2 3 4 5 RAS KERNEL FATAL')[4], '')  # empty message ok
        with self.assertRaises(ValueError):sources.parse_bgl('too short')
        for line in lines:   # fast session lookup used by the drill-down index agrees with the parser
            self.assertEqual(sources.bgl_session_ids(line), sources.parse_bgl(line)[0])
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'bgl.log';p.write_text(self.BGL_LINES + 'garbage line\n')
            df, audit, _ = processing.process(p, 'BGL', keep=True)
        self.assertEqual(audit['malformed_lines'], 1);self.assertEqual(audit['event_assignments'], 4)
        by = df.set_index('session_id')
        w1, w2 = f'window_{1117838570 // 300}', f'window_{1117838880 // 300}'
        self.assertEqual(int(by.loc[w1, 'n_events']), 2)                                 # two lines, one window
        self.assertEqual((by.loc[w1, 'label'], by.loc[w2, 'label']), (0, 1))             # window label = any alert
        self.assertEqual(by.loc[w1, 'error_ratio'], 0);self.assertEqual(by.loc[w2, 'error_ratio'], 1)  # FATAL level
        # HDFS-only lifecycle features are "not applicable" (0), never fabricated
        for c in ('replica_deficit', 'unacked_writes', 'uncommitted_acks', 'lifecycle_complete'):
            self.assertTrue((df[c] == 0).all(), c)

    def test_feature_schema_is_single_source(self):
        # Training table, live features and the model all use features.COLS.
        import features
        self.assertIs(processing.COLS, features.COLS)
        self.assertEqual(len(features.COLS), 52)
        self.assertEqual(len(set(features.COLS)), 52)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'log';p.write_text(RAW)
            df, _, _ = processing.process(p, 'HDFS')
            self.assertEqual(list(df.columns), processing.META_COLS + features.COLS)

    def _synthetic_sessions(self, n=3000, seed=0):
        rng = np.random.default_rng(seed)
        df = pd.DataFrame(rng.random((n, 52)) * 3, columns=processing.COLS)
        df['label'] = (rng.random(n) < .12).astype(int)
        # anomalies come in two kinds so clustering has structure to find
        kind = rng.random(n) < .5
        df.loc[(df.label == 1) & kind, 'duration_s'] += 40
        df.loc[(df.label == 1) & ~kind, 'keyword_error_ratio'] += 6
        df['session_id'] = [f's{i}' for i in range(n)];df['source'] = 'HDFS'
        df['t_start'] = np.arange(n) * 10;df['t_end'] = df.t_start + 5
        return df

    def test_clustering_within_anomalies_and_described(self):
        import clustering
        df, tr, va, te = split(self._synthetic_sessions())
        with tempfile.TemporaryDirectory() as d:
            old = clustering.ROOT;clustering.ROOT = Path(d)
            try:
                res = clustering.run('HDFS', df=df, dev=tr | va, te=te, log_path=Path(d) / 'missing.log')
            finally:clustering.ROOT = old
        n_dev_anomalies = int(((tr | va) & (df.label == 1)).sum())
        self.assertEqual(res['n_clustered'], n_dev_anomalies)
        self.assertEqual(sum(c['sessions'] for c in res['clusters']), n_dev_anomalies)
        for c in res['clusters']:
            self.assertEqual(c['composition']['normal'], 0)       # single class only
            self.assertTrue(c['interpretation'])                   # every cluster is described
            self.assertEqual(len(c['top_features']), clustering.N_TOP_FEATURES)
            self.assertNotIn('label', [f['feature'] for f in c['top_features']])
        # the two synthetic anomaly kinds are found via their distinguishing features
        top = {f['feature'] for c in res['clusters'] for f in c['top_features'][:2]}
        self.assertTrue({'duration_s', 'keyword_error_ratio'} & top)

    def test_error_analysis(self):
        import evaluation
        df, tr, va, te = split(self._synthetic_sessions())
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'results').mkdir()
            test_rows = df.loc[te, ['session_id', 'label']].copy()
            test_rows['probability'] = np.where(test_rows.label == 1, .9, .1)
            test_rows.iloc[0, 2] = .9 - .8 * test_rows.iloc[0, 1] + .0  # one deliberate error
            test_rows['prediction'] = (test_rows.probability >= .5).astype(int)
            test_rows.to_csv(Path(d) / 'results/HDFS_test_predictions.csv.gz', index=False)
            old = evaluation.ROOT;evaluation.ROOT = Path(d)
            try:
                res = evaluation.run('HDFS', df, tr, va, te)
            finally:evaluation.ROOT = old
        c = res['confusion']
        self.assertEqual(c['fp'] + c['fn'], int((test_rows.label != test_rows.prediction).sum()))
        self.assertEqual(c['tp'] + c['tn'] + c['fp'] + c['fn'], int(te.sum()))

    def test_extra_models_same_split_and_final_unchanged(self):
        import joblib, train
        df, tr, va, te = split(self._synthetic_sessions())
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'models').mkdir();(Path(d) / 'results').mkdir()
            old = train.ROOT;train.ROOT = Path(d)
            try:
                val, tests, final = train.train_classifiers(df, tr, va, te, 'HDFS')
            finally:train.ROOT = old
            names = [t['model'] for t in tests]
            self.assertEqual(sorted(names), sorted(list(train.FINAL_CANDIDATES) + list(train.EXTRA_MODELS)))
            self.assertIn(final['name'], train.FINAL_CANDIDATES)       # extra models never become final
            # every model was scored on the identical test sessions
            self.assertEqual({t['tn'] + t['fp'] + t['fn'] + t['tp'] for t in tests}, {int(te.sum())})
            for slug in ('final', 'xgboost', 'extra_trees'):
                b = joblib.load(Path(d) / 'models' / f'HDFS_{slug}.joblib')
                self.assertEqual(b['columns'], processing.COLS)
                p = b['model'].predict_proba(df[b['columns']].to_numpy(dtype='float32')[:5])
                self.assertEqual(p.shape, (5, 2))

    def test_comparison_record_shares_test_set(self):
        import comparison, train
        df, tr, va, te = split(self._synthetic_sessions())
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'models').mkdir();(Path(d) / 'results').mkdir()
            old = train.ROOT;train.ROOT = Path(d)
            try:val, tests, final = train.train_classifiers(df, tr, va, te, 'HDFS')
            finally:train.ROOT = old
        rec = comparison.build(df, tr, va, te, val, tests, final['name'])
        self.assertTrue(rec['models_share_test_set'])
        self.assertEqual(len([m for m in rec['models'] if m['period'] == 'test']), 5)
        self.assertEqual(len([m for m in rec['models'] if m['period'] == 'validation']), 5)
        self.assertEqual(rec['split']['test_sessions'], int(te.sum()))
        self.assertEqual(rec['split']['test_set_sha1'], comparison.test_set_hash(df, te))
        roles = {m['model']: m['role'] for m in rec['models'] if m['period'] == 'test'}
        self.assertEqual(roles['Logistic regression'], 'baseline')
        self.assertEqual(roles['XGBoost'], 'additional');self.assertEqual(roles['Extra trees'], 'additional')
        self.assertEqual(sum(r.startswith('final') for r in roles.values()), 1)
        # every model has a profile, real hyperparameters read from the fitted estimator, and timings
        self.assertEqual(set(rec['profiles']), set(roles))
        for name, prof in rec['profiles'].items():
            for field in ('type', 'learning_approach', 'scaling', 'suitability', 'key_params'):
                self.assertTrue(prof[field], (name, field))
        self.assertIn('StandardScaler', rec['profiles']['Logistic regression']['scaling'])
        self.assertEqual(rec['profiles']['Random forest']['scaling'], 'not required')
        self.assertEqual(rec['profiles']['XGBoost']['key_params']['max_depth'], 6)
        self.assertEqual(rec['profiles']['Extra trees']['key_params']['bootstrap'], False)
        self.assertTrue(all(m['fit_seconds'] is not None and m['predict_seconds'] is not None
                            for m in rec['models'] if m['period'] == 'test'))

    def test_missing_model_message(self):
        with tempfile.TemporaryDirectory() as d:
            old=predict.ROOT;predict.ROOT=Path(d)
            try:
                with self.assertRaisesRegex(ValueError,'setup_data.py'):predict.predict(Path(d)/'log','HDFS')
            finally:predict.ROOT=old
if __name__=='__main__':unittest.main()
