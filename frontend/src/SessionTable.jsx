import { useMemo, useState } from 'react';
import { formatScore } from './format.js';

const PAGE_SIZE = 50;    // as in A2

const SORTS = {
  score: (a, b) => b.score - a.score,
  events: (a, b) => b.n_events - a.n_events,
  id: (a, b) => (a.session_id < b.session_id ? -1 : a.session_id > b.session_id ? 1 : 0),
};
const NO_FILTERS = { query: '', sort: 'score', flaggedOnly: false };

// After a page change or new filters, go back to the top of the explorer (A2 reloaded the page at #sessions).
function backToTop() {
  requestAnimationFrame(() => {
    const heading = document.getElementById('sessions-title');
    heading?.scrollIntoView();
    heading?.focus({ preventScroll: true });
  });
}

// The A2 "Session Explorer" panel. `sessions` is null before any log has been analysed.
// As in A2, the filter fields take effect when "Apply" is pressed, and the table is shown 50 rows per page.
export default function SessionTable({ sessions, onSelect, onDelete, deleting }) {
  const [draft, setDraft] = useState(NO_FILTERS);       // what is typed or chosen in the filter fields
  const [filters, setFilters] = useState(NO_FILTERS);   // what the table currently shows
  const [page, setPage] = useState(1);

  const rows = useMemo(() => {
    if (!sessions) return [];
    const q = filters.query.trim().toLowerCase();
    return sessions
      .filter((s) => (!filters.flaggedOnly || s.flagged) && (!q || s.session_id.toLowerCase().includes(q)))
      .sort(SORTS[filters.sort]);
  }, [sessions, filters]);

  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const shown = rows.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  function apply(event) {
    event.preventDefault();
    setFilters(draft);
    setPage(1);
  }
  function reset() {
    setDraft(NO_FILTERS);
    setFilters(NO_FILTERS);
    setPage(1);
  }
  function goTo(n) {
    setPage(n);
    backToTop();
  }

  return (
    <section className="panel explorer" id="sessions" aria-labelledby="sessions-title">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">INVESTIGATE</span>
          <h2 id="sessions-title" tabIndex={-1}>Session Explorer</h2>
        </div>
        {sessions && (
          <button type="button" className="button secondary" onClick={onDelete} disabled={deleting}
                  title="Remove this analysis and its session details from the server">
            {deleting ? 'Deleting…' : 'Delete analysis'}
          </button>
        )}
      </div>

      {sessions ? (
        <>
          <form className="filters" role="search" onSubmit={apply}>
            <label className="search">
              <span aria-hidden="true">⌕</span>
              <input value={draft.query} onChange={(e) => setDraft({ ...draft, query: e.target.value })}
                     placeholder="Search session ID" aria-label="Search session ID" />
            </label>
            <select value={draft.sort} onChange={(e) => setDraft({ ...draft, sort: e.target.value })} aria-label="Sort sessions">
              <option value="score">Highest score</option>
              <option value="events">Most events</option>
              <option value="id">Session ID</option>
            </select>
            <label className="flag-toggle">
              <input type="checkbox" checked={draft.flaggedOnly}
                     onChange={(e) => setDraft({ ...draft, flaggedOnly: e.target.checked })} />
              Flagged only
            </label>
            <button className="button secondary" type="submit">Apply</button>
            <button type="button" className="reset" onClick={reset}>Reset</button>
          </form>

          <div className="table-wrap" role="region" aria-label="Session results" tabIndex={0}>
            <table>
              <caption className="sr-only">Sessions with their anomaly score, status, number of events and anomaly cluster</caption>
              <thead>
                <tr>
                  <th scope="col">Session ID</th>
                  <th scope="col">Anomaly score</th>
                  <th scope="col">Status</th>
                  <th scope="col">Events</th>
                  <th scope="col">Cluster</th>
                  <th scope="col"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {shown.map((r) => (
                  <tr key={r.session_id}>
                    <td className="mono">
                      <button type="button" className="id-button" onClick={() => onSelect(r.session_id)}>{r.session_id}</button>
                    </td>
                    <td>
                      <div className="score-cell">
                        <div className="score-track"><i style={{ width: `${Math.min(100, Math.max(0, r.score * 100)).toFixed(1)}%` }} /></div>
                        <span className="mono">{formatScore(r.score)}</span>
                      </div>
                    </td>
                    <td><span className={`badge ${r.flagged ? 'flagged' : 'normal'}`}>{r.flagged ? 'Flagged' : 'Normal'}</span></td>
                    <td>{r.n_events}</td>
                    <td>{r.cluster === null ? '—' : r.cluster}</td>
                    <td>
                      <button type="button" className="inspect" onClick={() => onSelect(r.session_id)}
                              aria-label={`Inspect ${r.session_id}`}>Inspect ↗</button>
                    </td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr><td colSpan={6} className="empty">No sessions match these filters.</td></tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="table-footer">
            <span aria-live="polite">{rows.length.toLocaleString('en-US')} matching sessions · page {page} of {pages}</span>
            <div>
              {page > 1 && <button type="button" className="button secondary" onClick={() => goTo(page - 1)}>← Previous</button>}
              {page < pages && <button type="button" className="button secondary" onClick={() => goTo(page + 1)}>Next →</button>}
            </div>
          </div>
        </>
      ) : (
        <div className="empty-state">
          <span aria-hidden="true">⌕</span>
          <h3>No log analysed yet</h3>
          <p>Upload a log to see its sessions, anomaly scores and original events.</p>
          <a href="#upload" className="button secondary">Upload a log ↥</a>
        </div>
      )}
    </section>
  );
}
