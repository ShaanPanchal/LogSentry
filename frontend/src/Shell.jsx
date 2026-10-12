// The A2 page frame: fixed sidebar (brand, section links, local-environment note) and the top bar.
const NAV = [
  { id: 'overview', icon: '▦', label: 'Overview' },
  { id: 'upload', icon: '↥', label: 'Log Upload' },
  { id: 'sessions', icon: '≡', label: 'Session Explorer' },
];

const CONNECTION = {
  unknown: { text: 'Local server', dot: 'unknown' },
  up: { text: 'Server running', dot: '' },
  down: { text: 'Server not reachable', dot: 'down' },
};

export default function Shell({ children, connection = 'unknown', active = 'overview', onNav, home = true }) {
  const status = CONNECTION[connection];
  const prefix = home ? '' : '/';      // on other addresses the links must go back to the home page
  return (
    <>
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="LogSentry home">
          <span className="logo" aria-hidden="true">◈</span>LogSentry<span className="edition">ML</span>
        </a>
        <nav aria-label="Dashboard sections">
          <div className="nav-label">MONITORING DASHBOARD</div>
          {NAV.map((n) => (
            <a key={n.id} className={`nav${home && active === n.id ? ' active' : ''}`} href={`${prefix}#${n.id}`}
               aria-current={home && active === n.id ? 'true' : undefined} onClick={() => onNav?.(n.id)}>
              <span aria-hidden="true">{n.icon}</span> {n.label}
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <span className="status-dot" aria-hidden="true" /> Local environment
          <p>Offline inference<br />Data stays on this computer.</p>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <span>MONITORING DASHBOARD <b aria-hidden="true">/</b> LOG ANOMALY DETECTION</span>
          <div className="top-actions">
            <span className="connection" role="status">
              <i className={`status-dot ${status.dot}`} aria-hidden="true" /> {status.text}
            </span>
          </div>
        </header>
        {children}
      </main>
    </>
  );
}
