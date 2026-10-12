import { useEffect, useRef, useState } from 'react';
import { getSession } from './api.js';
import { formatFeature, formatScore } from './format.js';
import Notice from './Notice.jsx';
import Progress from './Progress.jsx';

// The A2 "Drill down" panel: score, decision, event count, cluster and the original log lines.
// A3 adds the session's feature values at the end.
export default function SessionDetail({ analysisId, sessionId, onClose }) {
  const [state, setState] = useState({ status: 'loading' });     // loading | error | ready
  const [copy, setCopy] = useState('Copy events');
  const panel = useRef(null);
  const heading = useRef(null);

  useEffect(() => {
    let current = true;                                          // ignore the answer if the user has already moved on
    setState({ status: 'loading' });
    getSession(analysisId, sessionId)
      .then((detail) => current && setState({ status: 'ready', detail }))
      .catch((error) => current && setState({ status: 'error', message: error.message }));
    return () => { current = false; };
  }, [analysisId, sessionId]);

  // Move keyboard focus to the heading as soon as a session is opened.
  useEffect(() => heading.current?.focus({ preventScroll: true }), [sessionId]);

  // Bring the panel into view once its content has arrived: while it only shows "loading" the page is still short,
  // so scrolling earlier would stop too far down.
  useEffect(() => {
    if (state.status !== 'loading') panel.current?.scrollIntoView();
  }, [sessionId, state.status]);

  async function copyEvents() {
    const text = state.detail.events.map((e) => `${e.time}\t${e.level}\t${e.message}`).join('\n');
    try {
      await navigator.clipboard.writeText(text);
      setCopy('Copied ✓');
      setTimeout(() => setCopy('Copy events'), 1800);
    } catch {
      setCopy('Copy unavailable');
    }
  }

  const d = state.detail;
  return (
    <section id="detail" className="panel detail" ref={panel} aria-labelledby="detail-title">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">DRILL DOWN</span>
          <h2 className="mono" id="detail-title" tabIndex={-1} ref={heading}>{sessionId}</h2>
        </div>
        <button type="button" className="button secondary" onClick={onClose} aria-label="Close session details">Close ×</button>
      </div>

      {state.status === 'loading' && <Progress title="Loading session details" description="Fetching this session from the server." />}
      {state.status === 'error' && <Notice kind="error">{state.message}</Notice>}

      {d && (
        <>
          <div className="detail-stats">
            <div><span className="metric-label">ANOMALY SCORE</span><strong>{formatScore(d.score)}</strong></div>
            <div><span className="metric-label">DECISION</span><strong>{d.flagged ? 'ANOMALY' : 'NORMAL'}</strong></div>
            <div><span className="metric-label">EVENT COUNT</span><strong>{d.n_events}</strong></div>
            {d.cluster !== null && <div><span className="metric-label">ANOMALY CLUSTER</span><strong>{d.cluster}</strong></div>}
          </div>
          {d.cluster_description && <p className="note">{d.cluster_description}</p>}

          <div className="events-heading">
            <h3>Original log events</h3>
            <button className="button secondary" type="button" onClick={copyEvents}>{copy}</button>
          </div>
          <p className="note">
            {d.events_truncated && <>Showing the first {d.events.length} of {d.n_events} events. </>}
            Observed events provide context, not causal explanations of the model&apos;s decision. The anomaly score is
            a model score compared with the threshold {d.threshold.toFixed(2)}, not a probability.
          </p>
          <div className="event-list" role="region" aria-label="Original log events" tabIndex={0}>
            {d.events.map((e, i) => (
              <div className="event" key={i}>
                <span className="event-time mono">{e.time}</span>
                <span className={`event-level${['ERROR', 'FATAL', 'SEVERE'].includes(e.level) ? ' danger' : ''}`}>{e.level}</span>
                {/* The message comes from the uploaded file. React shows it as plain text, never as HTML. */}
                <pre>{e.message}</pre>
              </div>
            ))}
          </div>

          {/* A3 addition (not in A2): collapsed by default, in the A2 collapsible style, so the panel above matches A2. */}
          <details className="collapse">
            <summary><span className="eyebrow">SESSION FEATURES · {Object.keys(d.features).length} VALUES THE MODEL RECEIVED</span></summary>
            <p className="note">
              The summary numbers the model received for this session. They give context only and are not an explanation of the score.
            </p>
            <div className="table-wrap" role="region" aria-label="Session features" tabIndex={0}>
              <table>
                <thead><tr><th scope="col">Feature</th><th scope="col">Value</th></tr></thead>
                <tbody>
                  {Object.entries(d.features).map(([name, value]) => (
                    <tr key={name}><td className="mono">{name}</td><td>{formatFeature(value)}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </>
      )}
    </section>
  );
}
