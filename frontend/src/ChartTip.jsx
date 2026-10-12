import { useRef, useState } from 'react';

// Shared tooltip for the two charts. `show` places a small box above whichever chart element is hovered or focused.
export function useChartTip() {
  const box = useRef(null);
  const [tip, setTip] = useState(null);

  function show(event, text) {
    const target = event.currentTarget.getBoundingClientRect();
    const area = box.current.getBoundingClientRect();
    const half = 120;    // half the tooltip's maximum width: keeps it inside the chart
    const x = Math.min(Math.max(target.left + target.width / 2 - area.left, half), area.width - half);
    setTip({ x, y: target.top - area.top, text });
  }

  return { box, tip, show, hide: () => setTip(null) };
}

export function ChartTip({ tip }) {
  if (!tip) return null;
  return <div className="chart-tip" role="tooltip" style={{ left: tip.x, top: tip.y }}>{tip.text}</div>;
}
