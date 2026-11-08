// The A2 progress panel. fetch cannot report upload progress, so the bar is a moving "working" bar, not a percentage.
export default function Progress({ title, description }) {
  return (
    <div className="progress-panel" role="status">
      <div className="progress-heading">
        <strong>{title}</strong><span>Processing</span>
      </div>
      <div className="progress-track" role="progressbar" aria-label={title}><div className="progress-bar processing" /></div>
      <p className="muted">{description}</p>
    </div>
  );
}
