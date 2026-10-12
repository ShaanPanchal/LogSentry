import { useRef, useState } from 'react';
import { MAX_UPLOAD_BYTES, SOURCES } from './config.js';
import { formatBytes } from './format.js';
import Progress from './Progress.jsx';

// Checks the chosen file before anything is sent. This is for convenience only: the back end checks everything again.
function validate(file) {
  if (!file) return 'Choose a .log or .txt file.';
  if (!/\.(log|txt)$/i.test(file.name)) return 'Only .log and .txt files are accepted.';
  if (file.size === 0) return 'This file is empty.';
  if (file.size > MAX_UPLOAD_BYTES) return `This file is ${formatBytes(file.size)}. The limit is ${formatBytes(MAX_UPLOAD_BYTES)}.`;
  return null;
}

// `serverError` is the message from a failed request. It is shown in the same place as the form's own messages.
export default function UploadForm({ busy, onSubmit, serverError, onEdit }) {
  const [source, setSource] = useState(SOURCES[0].value);
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);
  const [dragging, setDragging] = useState(false);
  const input = useRef(null);
  const sending = useRef(false);      // blocks a second submit in the same moment, before `busy` has re-rendered

  function choose(chosen) {
    setFile(chosen);
    setError(chosen ? validate(chosen) : null);
    onEdit();
  }

  function clear() {
    input.current.value = '';
    choose(null);
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);
    if (!busy && event.dataTransfer.files.length) choose(event.dataTransfer.files[0]);
  }

  function handleSubmit(event) {
    event.preventDefault();
    if (busy || sending.current) return;
    const problem = validate(file);
    setError(problem);
    if (problem) return;
    sending.current = true;
    Promise.resolve(onSubmit(source, file)).finally(() => {
      sending.current = false;
    });
  }

  return (
    <form onSubmit={handleSubmit} noValidate aria-busy={busy}>
      <label className="field-label" htmlFor="source">Log source</label>
      <div className="source-row">
        <select id="source" name="source" value={source} onChange={(e) => setSource(e.target.value)} disabled={busy}>
          {SOURCES.map((s) => <option key={s.value} value={s.value}>{s.value}</option>)}
        </select>
        <span className="muted">{SOURCES.length} trained sources</span>
      </div>

      <label className={`dropzone${dragging ? ' dragging' : ''}${file ? ' selected' : ''}`} htmlFor="log-file"
             onDragEnter={(e) => { e.preventDefault(); if (!busy) setDragging(true); }}
             onDragOver={(e) => { e.preventDefault(); if (!busy) setDragging(true); }}
             onDragLeave={() => setDragging(false)} onDrop={handleDrop}>
        <span className="upload-symbol" aria-hidden="true">↥</span>
        <strong>{file ? file.name : 'Drop your log file here'}</strong>
        <span>{file ? `${(file.size / 1024 / 1024).toFixed(1)} MB · ${error ? 'cannot be analysed' : 'ready to analyse'}` : 'or click to browse · uncompressed .log / .txt'}</span>
        <input id="log-file" ref={input} type="file" name="log" accept=".log,.txt" disabled={busy}
               onChange={(e) => choose(e.target.files[0] || null)}
               aria-invalid={Boolean(error)} aria-describedby={error || serverError ? 'file-error' : undefined} />
      </label>

      {/* Right under the field it belongs to. */}
      {(error || serverError) && (
        <div id="file-error" className="alert" role="alert"><strong>Error:</strong> {error || serverError}</div>
      )}

      <div className="upload-actions">
        <button className="button secondary" type="button" onClick={clear} disabled={!file || busy}>Clear file</button>
        <button className="button primary" type="submit" disabled={!file || busy}>
          {busy ? 'Analysing…' : <>Analyse log <span aria-hidden="true">↗</span></>}
        </button>
      </div>

      {busy && (
        <Progress title="Analysing sessions" description="Uploading the log and scoring its sessions on the local server. Keep this page open." />
      )}
    </form>
  );
}
