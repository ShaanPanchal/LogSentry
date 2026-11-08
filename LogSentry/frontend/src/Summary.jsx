import { formatPercent, formatThreshold } from './format.js';

const n = (value) => value.toLocaleString('en-US');

// The four summary boxes. Before an analysis they show dashes, as in A2.
export function Metrics({ summary }) {
  const total = summary?.total_sessions;
  const flagged = summary?.flagged_sessions;
  return (
    <section className="metrics" aria-label="Analysis summary">
      <article>
        <span className="metric-label">SESSIONS ANALYSED</span>
        <strong>{summary ? n(total) : '—'}</strong>
        <span className="metric-foot">{summary ? `${summary.source} · session groups` : 'Awaiting log upload'}</span>
      </article>
      <article>
        <span className="metric-label">FLAGGED SESSIONS</span>
        <strong className="danger">{summary ? n(flagged) : '—'}</strong>
        <span className="metric-foot">{summary ? formatPercent(flagged, total) : '0.0%'} of analysed sessions</span>
      </article>
      <article>
        <span className="metric-label">LOG EVENTS</span>
        <strong>{summary ? n(summary.audit.raw_lines) : '—'}</strong>
        <span className="metric-foot">Raw lines processed</span>
      </article>
      <article>
        <span className="metric-label">PARSING EXCEPTIONS</span>
        <strong>{summary ? n(summary.audit.malformed_lines) : '—'}</strong>
        <span className="metric-foot">Malformed lines skipped</span>
      </article>
    </section>
  );
}

// "Analysis details" panel, with what the score and the decision mean.
export function AnalysisDetails({ summary, dataset }) {
  return (
    <article className="panel mini">
      <span className="eyebrow">ANALYSIS DETAILS · {summary.source}</span>
      <h3>{dataset.title}</h3>
      <div className="kv">
        <span>Model used</span><b>{dataset.finalModel}</b>
        <span>Session definition</span><b>{dataset.session}</b>
        <span>Events assigned to sessions</span><b>{n(summary.audit.event_assignments)}</b>
        <span>Lines without a session</span><b>{n(summary.audit.no_session_id)}</b>
      </div>
      {/* A3: what the score and the decision mean (not in A2). */}
      <p className="note">
        <b>Anomaly score</b>: the model&apos;s 0 to 1 score for a session; higher means more unusual. It is{' '}
        <b>not a probability</b>. Sessions scoring {formatThreshold(summary.threshold)} or more are <b>flagged</b>, which
        means unusual, not proven malicious.
      </p>
    </article>
  );
}
