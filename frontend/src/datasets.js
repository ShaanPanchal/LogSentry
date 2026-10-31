// Model results shown in the "Choose a dataset to inspect" panel.
// These are the Assignment 2 training and evaluation results (the evaluation and EDA summary files on the a2-backup
// branch). The A3 API does not serve them, so they are copied here. The test numbers come from
// the temporal test split of each dataset, not from an uploaded log.
export const DATASETS = [
  {
    name: 'HDFS',
    title: 'Hadoop Distributed File System (HDFS)',
    session: 'one session per block id (blk_...)',
    sessions: 575061,
    anomalies: 16838,
    anomalyRate: 0.029280371995318757,
    testSessions: 115018,
    testAnomalies: 1680,
    finalModel: 'Histogram gradient boosting',
    features: 52,
    precision: 0.9993972272453285,
    recall: 0.986904761904762,
    f1: 0.9931117100928422,
  },
  {
    name: 'BGL',
    title: 'Blue Gene/L supercomputer (BGL)',
    session: 'fixed 5-minute time windows (no session id exists in BGL)',
    sessions: 14494,
    anomalies: 1054,
    anomalyRate: 0.07271974610183524,
    testSessions: 2899,
    testAnomalies: 225,
    finalModel: 'Histogram gradient boosting',
    features: 52,
    precision: 0.8571428571428571,
    recall: 0.56,
    f1: 0.6774193548387096,
  },
];
