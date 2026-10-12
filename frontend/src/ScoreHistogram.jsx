import { useMemo } from 'react';
import { ChartTip, useChartTip } from './ChartTip.jsx';
import { formatThreshold } from './format.js';

const BINS = 10;
const GAP = 6;       // px between bars: the same value as `.hist { gap }` in styles.css

// The A2 score-distribution chart: ten bars, heights on a square-root scale. Added in A3: tooltips, keyboard focus and
// a dashed line for the decision threshold.
// Question answered: how are the anomaly scores spread, and where does the decision threshold fall?
export default function ScoreHistogram({ sessions, threshold }) {
  const { box, tip, show, hide } = useChartTip();

  const counts = useMemo(() => {
    const c = new Array(BINS).fill(0);
    for (const s of sessions) c[Math.min(BINS - 1, Math.floor(s.score * BINS))] += 1;
    return c;
  }, [sessions]);

  const max = Math.max(...counts, 1);
  const label = (i) => `Scores ${(i / BINS).toFixed(1)} to ${((i + 1) / BINS).toFixed(1)}: ${counts[i]} ${counts[i] === 1 ? 'session' : 'sessions'}`;

  // Where the threshold sits: inside bin k of ten equal bars with fixed gaps between them.
  const k = Math.min(BINS - 1, Math.floor(threshold * BINS));
  const thresholdLeft = `calc(${(threshold * 100).toFixed(2)}% + ${(GAP * k - GAP * (BINS - 1) * threshold).toFixed(2)}px)`;

  return (
    <article className="panel mini" aria-label="Anomaly score distribution">
      <span className="eyebrow">ANOMALY SCORE DISTRIBUTION</span>
      <div className="chart" ref={box}>
        <div className="hist" role="group" aria-label="Bar chart: number of sessions in each anomaly score range">
          {counts.map((n, i) => (
            <div key={i} className="bar" tabIndex={0} role="img" aria-label={label(i)}
                 onMouseEnter={(e) => show(e, label(i))} onMouseLeave={hide} onFocus={(e) => show(e, label(i))} onBlur={hide}>
              <i style={{ height: `${((100 * Math.sqrt(n)) / Math.sqrt(max)).toFixed(1)}%` }} />
              <span>{(i / BINS).toFixed(1)}</span>
            </div>
          ))}
          <div className="threshold-line" style={{ left: thresholdLeft }} aria-hidden="true" />
        </div>
        <ChartTip tip={tip} />
      </div>
      <p className="muted">
        Number of sessions in each anomaly score bin, from 0.0 to 1.0 (each bin is labelled by its lower edge). Bar
        height is square-root scaled.<br />
        <span className="swatch" aria-hidden="true" />Dashed line: decision threshold {formatThreshold(threshold)}.
      </p>
    </article>
  );
}
