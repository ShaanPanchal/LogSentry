import { useEffect, useMemo, useState } from 'react';
import { getSession } from './api.js';
import { DATASETS } from './datasets.js';
import ScoreHistogram from './ScoreHistogram.jsx';
import SessionTimeline from './SessionTimeline.jsx';
import { AnalysisDetails } from './Summary.jsx';

// "Anomaly clusters in this log" (A2): how the flagged sessions spread over the A2 anomaly clusters, with each cluster's
// description. The analysis response has no descriptions, so one flagged session per cluster is read from the
// session-detail endpoint, which returns its cluster's description.
function Clusters({ analysisId, sessions }) {
  const clusters = useMemo(() => {
    const flagged = sessions.filter((s) => s.flagged).sort((a, b) => b.score - a.score);
    const byCluster = new Map();
    for (const s of flagged) {
      const c = byCluster.get(s.cluster) || { count: 0, example: s.session_id };
      c.count += 1;
      byCluster.set(s.cluster, c);
    }
    return { total: flagged.length, list: [...byCluster].sort((a, b) => a[0] - b[0]) };
  }, [sessions]);

  const [texts, setTexts] = useState({});
  useEffect(() => {
    let current = true;
    setTexts({});
    for (const [cluster, { example }] of clusters.list) {
      getSession(analysisId, example)
        .then((d) => current && d.cluster_description && setTexts((t) => ({ ...t, [cluster]: d.cluster_description })))
        .catch(() => {});      // without a description the panel still shows the counts
    }
    return () => { current = false; };
  }, [analysisId, clusters]);

  if (!clusters.list.length) return null;     // as in A2, the panel only appears when sessions were flagged
  return (
    <section className="panel-row">
      <article className="panel mini wide">
        <span className="eyebrow">ANOMALY CLUSTERS IN THIS LOG</span>
        {clusters.list.map(([cluster, { count }]) => (
          <div className="cluster" key={cluster}>
            <b>Cluster {cluster}</b>{' '}
            <span className="muted">
              {count.toLocaleString('en-US')} flagged sessions · {Math.round((100 * count) / clusters.total)}% of flagged sessions
            </span>
            {texts[cluster] && <p className="muted">{texts[cluster]}</p>}
          </div>
        ))}
      </article>
    </section>
  );
}

// The panels that describe one analysis, in the A2 order, with the A3 timeline after the score distribution.
export default function Results({ analysis, onSelect }) {
  const { summary, sessions } = analysis;
  const dataset = DATASETS.find((d) => d.name === summary.source);
  return (
    <>
      <section className="panel-row">
        <AnalysisDetails summary={summary} dataset={dataset} />
        <ScoreHistogram sessions={sessions} threshold={summary.threshold} />
      </section>
      <section className="panel-row">
        <SessionTimeline sessions={sessions} threshold={summary.threshold} onSelect={onSelect} />
      </section>
      <Clusters analysisId={analysis.analysis_id} sessions={sessions} />
    </>
  );
}
