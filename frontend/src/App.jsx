import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, createAnalysis, deleteAnalysis, getAnalysis, onConnectionChange } from './api.js';
import { MAX_UPLOAD_BYTES } from './config.js';
import Datasets from './Datasets.jsx';
import NotFound from './NotFound.jsx';
import Notice from './Notice.jsx';
import Progress from './Progress.jsx';
import Results from './Results.jsx';
import SessionDetail from './SessionDetail.jsx';
import SessionTable from './SessionTable.jsx';
import Shell from './Shell.jsx';
import { Metrics } from './Summary.jsx';
import UploadForm from './UploadForm.jsx';

const SAVED_ID = 'logsentry.analysisId';

// sessionStorage can be blocked by the browser, so every use is wrapped. The app works without it.
const saveId = (id) => { try { sessionStorage.setItem(SAVED_ID, id); } catch { /* ignore */ } };
const loadId = () => { try { return sessionStorage.getItem(SAVED_ID); } catch { return null; } };
const clearId = () => { try { sessionStorage.removeItem(SAVED_ID); } catch { /* ignore */ } };

const STEPS = [
  ['01', 'Parse & normalise', 'Structure events and standardise variable values.'],
  ['02', 'Group sessions', 'HDFS block IDs or BGL time windows.'],
  ['03', 'Score anomalies', 'Apply your trained classifier to session features.'],
  ['04', 'Inspect events', 'Open flagged sessions and read their original log lines.'],
];

// There is only one page (the home page). Any other address gets the not-found page.
export default function App() {
  const known = ['/', '/index.html'].includes(window.location.pathname);
  return known ? <Home /> : <NotFound />;
}

function Home() {
  const [analysis, setAnalysis] = useState(null);     // the AnalysisResponse from the API
  const [selected, setSelected] = useState(null);     // session id whose detail panel is open
  const [notice, setNotice] = useState(null);         // { kind: 'error' | 'info', text }, shown above the summary boxes
  const [uploadError, setUploadError] = useState(null);   // a failed upload, shown under the file field
  const [busy, setBusy] = useState(false);            // an upload is being analysed
  const [deleting, setDeleting] = useState(false);
  const [restoring, setRestoring] = useState(() => Boolean(loadId()));
  const [connection, setConnection] = useState('unknown');
  const [active, setActive] = useState('overview');
  const [view, setView] = useState('HDFS');           // which dataset the "Choose a dataset" panel describes
  const current = useRef(null);
  const summaryHeading = useRef(null);
  const showSummary = useRef(false);
  current.current = analysis;

  useEffect(() => onConnectionChange((reachable) => setConnection(reachable ? 'up' : 'down')), []);

  // After a page reload, ask the server for the analysis we had open (GET /api/analyses/{id}).
  useEffect(() => {
    const id = loadId();
    if (!id) return;
    getAnalysis(id)
      .then((result) => { setAnalysis(result); setView(result.summary.source); })
      .catch((error) => {
        clearId();
        setNotice(error instanceof ApiError && error.status === 404
          ? { kind: 'info', text: 'Your previous analysis is no longer on the server. It was deleted, or the server restarted. Upload the log again.' }
          : { kind: 'error', text: error.message });
      })
      .finally(() => setRestoring(false));
  }, []);

  // When the result changes (new analysis, or deleted), bring the summary into view, as A2 did after an upload.
  useEffect(() => {
    if (!showSummary.current) return;
    showSummary.current = false;
    document.getElementById('summary')?.scrollIntoView();
    summaryHeading.current?.focus({ preventScroll: true });
  }, [analysis]);

  async function handleSubmit(source, file) {
    setBusy(true);
    setNotice(null);
    setUploadError(null);
    try {
      const result = await createAnalysis(source, file);
      const previous = current.current;
      showSummary.current = true;
      setAnalysis(result);
      setView(result.summary.source);
      setSelected(null);
      saveId(result.analysis_id);
      // Replacing a result: free the old one on the server (best effort, the user is not told if it fails).
      if (previous) deleteAnalysis(previous.analysis_id).catch(() => {});
    } catch (error) {
      setUploadError(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    setNotice(null);
    try {
      await deleteAnalysis(analysis.analysis_id);
      setNotice({ kind: 'info', text: 'The analysis was deleted from the server.' });
    } catch (error) {
      if (!(error instanceof ApiError && error.status === 404)) {      // 404: it is already gone, which is what was wanted
        setNotice({ kind: 'error', text: error.message });
        setDeleting(false);
        return;
      }
      setNotice({ kind: 'info', text: 'The analysis was already gone from the server.' });
    }
    clearId();
    showSummary.current = true;
    setAnalysis(null);
    setSelected(null);
    setDeleting(false);
  }

  const select = useCallback((sessionId) => setSelected(sessionId), []);

  // "Close" in the detail panel: back to the session list, as in A2.
  function closeDetail() {
    setSelected(null);
    requestAnimationFrame(() => {
      const heading = document.getElementById('sessions-title');
      heading?.scrollIntoView();
      heading?.focus({ preventScroll: true });
    });
  }

  return (
    <Shell connection={connection} active={active} onNav={setActive}>
      <section id="overview" className="intro">
        <h1>LogSentry</h1>
      </section>

      <Datasets view={view} onView={setView} />

      <div className="main-grid">
        <section className="panel" id="upload" aria-labelledby="upload-title">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">LOG UPLOAD</span>
              <h2 id="upload-title">Upload a log</h2>
            </div>
            <span className="tag">UP TO {MAX_UPLOAD_BYTES / 1024 / 1024} MiB</span>
          </div>
          <UploadForm busy={busy} onSubmit={handleSubmit} serverError={uploadError} onEdit={() => setUploadError(null)} />
          <p className="note">
            Use chronologically ordered logs and complete sessions. Files up to 5 MiB take a few seconds to analyse. Keep
            this page open until the analysis finishes.
          </p>
        </section>

        <section className="panel steps-panel" aria-labelledby="steps-title">
          <span className="eyebrow">ANALYSIS PIPELINE</span>
          <h2 id="steps-title">Processing steps</h2>
          <ol className="pipeline">
            {STEPS.map(([number, title, text]) => (
              <li key={number}>
                <span aria-hidden="true">{number}</span>
                <div><strong>{title}</strong><p>{text}</p></div>
              </li>
            ))}
          </ol>
        </section>
      </div>

      <section id="summary">
        <h2 className="sr-only" tabIndex={-1} ref={summaryHeading}>Analysis summary</h2>
        {notice && <Notice kind={notice.kind}>{notice.text}</Notice>}
        {restoring && <Progress title="Loading previous analysis" description="Fetching your last analysis from the server." />}
        <Metrics summary={analysis?.summary} />
      </section>

      {analysis && <Results analysis={analysis} onSelect={select} />}

      <SessionTable key={analysis?.analysis_id} sessions={analysis?.sessions ?? null} onSelect={select}
                    onDelete={handleDelete} deleting={deleting} />

      {analysis && selected && (
        <SessionDetail analysisId={analysis.analysis_id} sessionId={selected} onClose={closeDetail} />
      )}
    </Shell>
  );
}
