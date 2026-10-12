import { useEffect, useMemo, useRef, useState } from 'react';
import { ChartTip, useChartTip } from './ChartTip.jsx';
import { formatScore, formatShortTime, formatThreshold, formatTime } from './format.js';

const H = 240, M = { l: 44, r: 12, t: 12, b: 42 };
const PAD = 8;       // keeps points with score 0 or 1, or at the first or last time, off the axis lines and the plot edge

// Question answered: when did the sessions start, and which ones scored high? Click a point to open that session.
// A3 chart (A2 had none), drawn in the A2 panel style. The drawing is as wide as its panel in pixels, so text keeps
// the same size on a phone and on a desktop.
export default function SessionTimeline({ sessions, threshold, onSelect }) {
  const { box, tip, show, hide } = useChartTip();
  const showRef = useRef(show);      // the points are rebuilt only when the data or width change; they call the latest `show`
  showRef.current = show;
  const [width, setWidth] = useState(800);

  useEffect(() => {
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(260, Math.round(entry.contentRect.width))));
    observer.observe(box.current);
    return () => observer.disconnect();
  }, [box]);

  const plotW = width - M.l - M.r, plotH = H - M.t - M.b;
  let tMin = Math.min(...sessions.map((s) => s.t_start));
  let tMax = Math.max(...sessions.map((s) => s.t_start));
  if (tMin === tMax) { tMin -= 1800; tMax += 1800; }                   // all sessions at one moment: give the axis some width
  const xOf = (t) => M.l + PAD + ((t - tMin) / (tMax - tMin)) * (plotW - 2 * PAD);
  const yOf = (score) => M.t + PAD + (plotH - 2 * PAD) * (1 - score);

  const points = useMemo(() => {
    // Flagged sessions are drawn last so they stay visible on top. Flagged = diamond, normal = circle.
    const ordered = [...sessions].sort((a, b) => Number(a.flagged) - Number(b.flagged));
    return ordered.map((s) => {
      const cx = xOf(s.t_start), cy = yOf(s.score);
      const text = `${s.session_id}\nScore ${formatScore(s.score)}, ${s.flagged ? 'flagged' : 'normal'}\nStarts ${formatTime(s.t_start)}`;
      return (
        <g key={s.session_id} className="point" onClick={() => onSelect(s.session_id)}
           onMouseEnter={(e) => showRef.current(e, text)} onMouseLeave={hide}>
          {s.flagged
            ? <path className="mark-flagged" d={`M${cx} ${cy - 5}L${cx + 5} ${cy}L${cx} ${cy + 5}L${cx - 5} ${cy}Z`} />
            : <circle className="mark-ok" cx={cx} cy={cy} r={3} />}
          <circle className="hit-point" cx={cx} cy={cy} r={8} />
        </g>
      );
    });
  }, [sessions, onSelect, width]);   // tMin, tMax, xOf and yOf only change when `sessions` or `width` do

  const ticks = width < 520 ? [tMin, tMax] : [tMin, (tMin + tMax) / 2, tMax];

  return (
    <article className="panel mini wide">
      <span className="eyebrow">SESSIONS OVER TIME</span>
      <div className="chart timeline" ref={box}>
        <svg width={width} height={H} viewBox={`0 0 ${width} ${H}`} role="group"
             aria-label="Scatter chart of each session's anomaly score against its start time">
          {/* Axes, grid and threshold come first so the points are drawn (and hovered) on top of them. */}
          {[0, 0.25, 0.5, 0.75, 1].map((v) => (
            <g key={v}>
              <line className="grid" x1={M.l} x2={width - M.r} y1={yOf(v)} y2={yOf(v)} />
              <text className="tick" x={M.l - 8} y={yOf(v) + 3} textAnchor="end">{v}</text>
            </g>
          ))}
          <text className="tick" transform={`translate(10 ${M.t + plotH / 2}) rotate(-90)`} textAnchor="middle">Anomaly score</text>
          <line className="axis" x1={M.l} x2={width - M.r} y1={M.t + plotH} y2={M.t + plotH} />
          {ticks.map((t, i) => (
            <text key={i} className="tick" x={xOf(t)} y={M.t + plotH + 16}
                  textAnchor={i === 0 ? 'start' : i === ticks.length - 1 ? 'end' : 'middle'}>{formatShortTime(t)}</text>
          ))}
          <text className="tick" x={M.l + plotW / 2} y={H - 6} textAnchor="middle">Session start time (UTC)</text>
          <line className="threshold" x1={M.l} x2={width - M.r} y1={yOf(threshold)} y2={yOf(threshold)} />
          {/* Below the line, on the left: flagged points sit above the line and would hide the label. */}
          <text className="threshold-label" x={M.l + PAD + 4} y={yOf(threshold) + 14}>Threshold {formatThreshold(threshold)}</text>

          {points}
        </svg>
        <ChartTip tip={tip} />
      </div>
      <p className="muted legend-list">
        <span><svg width="12" height="12" viewBox="-6 -6 12 12" aria-hidden="true"><path className="mark-flagged" d="M0 -5L5 0L0 5L-5 0Z" /></svg> Flagged</span>
        <span><svg width="12" height="12" viewBox="-6 -6 12 12" aria-hidden="true"><circle className="mark-ok" r="3" /></svg> Normal</span>
        <span>Hover a point for details and click it to open the session. With a keyboard, open sessions from the Session Explorer.</span>
      </p>
    </article>
  );
}
