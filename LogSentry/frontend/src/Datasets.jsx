import { DATASETS } from './datasets.js';
import { MODEL_RESULTS } from './modelResults.js';

const n = (value) => value.toLocaleString('en-US');

// "Choose a dataset to inspect": the A2 results table, with tabs that pick which dataset the overview boxes describe.
export default function Datasets({ view, onView }) {
  const d = DATASETS.find((x) => x.name === view);
  return (
    <section className="panel datasets" id="results" aria-label="Datasets">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">LOG SOURCES · MODEL RESULTS</span>
          <h2>Choose a dataset to inspect</h2>
        </div>
        <div className="tabs" role="group" aria-label="Dataset">
          {DATASETS.map((x) => (
            <button key={x.name} type="button" className={`tab${x.name === view ? ' active' : ''}`}
                    aria-pressed={x.name === view} onClick={() => onView(x.name)}>
              {x.name}
            </button>
          ))}
        </div>
      </div>

      <div className="table-wrap" role="region" aria-label="Dataset results" tabIndex={0}>
        <table>
          <thead>
            <tr>
              <th>Dataset</th><th>Session definition</th><th>Sessions</th><th>Anomalous</th>
              <th>Test sessions (anomalous)</th><th>Final model</th><th>Test precision</th><th>Test recall</th><th>Test F1</th>
            </tr>
          </thead>
          <tbody>
            {DATASETS.map((x) => (
              <tr key={x.name} className={x.name === view ? 'sel' : undefined}>
                <td><b>{x.name}</b><br /><span className="muted">{x.title}</span></td>
                <td className="muted">{x.session}</td>
                <td>{n(x.sessions)}</td>
                <td>{n(x.anomalies)}</td>
                <td>{n(x.testSessions)} ({n(x.testAnomalies)})</td>
                <td>{x.finalModel}</td>
                <td>{x.precision.toFixed(3)}</td>
                <td>{x.recall.toFixed(3)}</td>
                <td>{x.f1.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="overview" aria-label="Dataset overview">
        <div>
          <span className="metric-label">DATASET SIZE</span>
          <strong>{n(d.sessions)}</strong>
          <span className="metric-foot">{d.session}</span>
        </div>
        <div>
          <span className="metric-label">ANOMALOUS SESSIONS</span>
          <strong>{n(d.anomalies)}</strong>
          <span className="metric-foot">{(d.anomalyRate * 100).toFixed(2)}% of the dataset</span>
        </div>
        <div>
          <span className="metric-label">MODEL FEATURES</span>
          <strong>{d.features}</strong>
          <span className="metric-foot">inputs to the classifier</span>
        </div>
      </div>
      <p className="muted">
        The datasets are trained and evaluated separately and are never mixed. These are the model&apos;s test results
        for <b>{view}</b>, not results for an uploaded log.
      </p>
      <ModelComparison view={view} />
    </section>
  );
}

const f3 = (v) => v.toFixed(3);
const f4 = (v) => v.toFixed(4);

// The A2 "Model comparison" section for the selected dataset: classifier profiles, the five-classifier table and,
// where A2 had one (BGL), the temporal-robustness table, all inside one collapsible section. As in A2 (where switching
// dataset reloaded the page), it starts closed and closes again when the dataset tab changes.
function ModelComparison({ view }) {
  const r = MODEL_RESULTS[view];
  return (
    <details className="collapse" key={view}>
      <summary>
        <span className="eyebrow">MODEL COMPARISON · {view} · FIVE CLASSIFIERS · SAME TEMPORAL TEST SET</span>
      </summary>
      <div className="cmp-details">
        {r.models.filter((m) => m.profile).map((m) => (
          <details key={m.model}>
            <summary>{m.model} <span className="muted">· {m.profile.type}</span></summary>
            <dl>
              <dt>Learning approach</dt><dd>{m.profile.learningApproach}</dd>
              <dt>Feature scaling</dt><dd>{m.profile.scaling}</dd>
              <dt>Key configuration</dt><dd className="mono">{m.profile.keyConfig}</dd>
              <dt>Suitability for the {m.profile.nFeatures} session features</dt><dd>{m.profile.suitability}</dd>
            </dl>
          </details>
        ))}
      </div>
      <p className="muted">{r.profileNote}</p>
      <p className="muted">
        All models were trained on the earliest part of the log and scored on the same{' '}
        {n(r.split.testSessions)} later sessions ({n(r.split.testAnomalies)} anomalous); test-set identity{' '}
        {r.split.shared ? 'verified' : 'NOT verified'} (id hash {r.split.testSetSha1.slice(0, 10)}). Only the final model
        scores uploads.
      </p>
      <div className="table-wrap" role="region" aria-label={`Model comparison, ${view}`} tabIndex={0}>
        <table>
          <thead>
            <tr>
              <th>Model</th><th>Role</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>PR-AUC</th>
              <th>False pos.</th><th>False neg.</th><th>Fit (s)</th><th>Predict (s)</th>
            </tr>
          </thead>
          <tbody>
            {r.models.map((m) => (
              <tr key={m.model}>
                <td>{m.model}{m.final && <>{' '}<span className="badge normal">final</span></>}</td>
                <td className="muted">{m.role}</td>
                <td>{f4(m.accuracy)}</td><td>{f4(m.precision)}</td><td>{f4(m.recall)}</td><td>{f4(m.f1)}</td><td>{f4(m.prAuc)}</td>
                <td>{m.fp}</td><td>{m.fn}</td>
                <td>{m.fitSeconds.toFixed(1)}</td><td>{m.predictSeconds.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {r.folds && (
        <div className="table-wrap folds" role="region" aria-label={`Temporal robustness, ${view}`} tabIndex={0}>
          <span className="eyebrow">
            TEMPORAL ROBUSTNESS · {view} · {r.folds.n_folds} ROLLING-ORIGIN FOLDS (test anomaly rate per fold: {r.folds.rates})
          </span>
          <table>
            <thead>
              <tr>
                <th>Model</th><th>Mean F1</th><th>Min F1</th><th>Max F1</th><th>Mean precision</th><th>Mean recall</th>
                <th>Total FP</th><th>Total FN</th>
              </tr>
            </thead>
            <tbody>
              {r.folds.rows.map((row) => (
                <tr key={row.model}>
                  <td>{row.model}</td><td>{f3(row.mean_f1)}</td><td>{f3(row.min_f1)}</td><td>{f3(row.max_f1)}</td>
                  <td>{f3(row.mean_precision)}</td><td>{f3(row.mean_recall)}</td><td>{row.total_fp}</td><td>{row.total_fn}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </details>
  );
}
