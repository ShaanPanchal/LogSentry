# LogSentry - Log Anomaly Detection

COS30049 Assignment 2 · Session 12, Group 3 · Shaan Panchal, Neeven Emmanuel, Dominique

LogSentry takes a log file from a distributed system, groups the entries into
**sessions**, decides which sessions look abnormal, and presents the findings on
a monitoring dashboard with drill-down into individual sessions.

```
raw log -> parse/clean -> sessions -> 52 features -> classifier -> anomaly score
                                                          |-> clustering of anomalies -> dashboard + drill-down
```

* **Data**: Loghub HDFS (11,175,629 log lines -> 575,061 block sessions, 16,838 anomalous). BGL is also supported by the code.
* **Classification** (core task): normal vs anomalous session. Final model: **HistGradientBoostingClassifier**.
* **Clustering**: K-means on the anomaly class only, labels excluded, every cluster described from its features and real events.
* **Evaluation**: purged chronological train/validation/test split, precision/recall/F1/PR-AUC/confusion matrix, error analysis, seed stability.
* **Website**: Flask dashboard that runs the same pipeline on an uploaded log.

There is **one** pipeline (this repository). Material from an earlier experiment
whose code no longer exists is kept for reference only in `archive/` and is not
used by anything (see "Project structure").

---

## 1. Environment setup (conda)

```bash
conda env create -f environment.yml
conda activate logsentry
```

Equivalent manual commands:

```bash
conda create -n logsentry python=3.12 -y
conda activate logsentry
conda install -c conda-forge numpy pandas scikit-learn=1.9.1 joblib flask matplotlib -y
```

`pip install -r requirements.txt` also works inside any Python >= 3.11 environment.
`scikit-learn` is pinned to 1.9.1 because the shipped models in `models/` are
pickles and must be loaded by the version that trained them.

Dependencies: numpy, pandas, scikit-learn, joblib, Flask, matplotlib.
Verify: `python -m unittest discover -s tests -v`

All commands below are run from the repository root. Paths are relative; nothing
is machine-specific.

## 2. Dataset

| Item | Location |
|---|---|
| **Processed dataset used by the final model** | `data/processed/HDFS_sessions.csv.gz` (575,061 rows: `session_id, source, t_start, t_end, label` + the 52 features) |
| Small real sample log (200 complete sessions, 2,819 lines, for trying prediction / the dashboard) | `data/supporting/sample_HDFS.log` (+ `sample_HDFS_labels.csv`) |
| What each `event_hash_NN` feature counts | `results/HDFS_event_buckets.json` |
| Raw Loghub data (186 MB download, not committed) | fetched by `setup_data.py` into `data/raw/` |

Source: Loghub (Zhu et al., ISSRE 2023), Zenodo record 8196385, `HDFS_v1.zip` (MD5 verified by the script).
Loghub datasets are free for research/academic use; cite Zhu, J., He, S., He, P., Liu, J. and Lyu, M.R. (2023)
'Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics', ISSRE, doi:10.1109/ISSRE59848.2023.00071.

## 3. Data processing and feature extraction

Reproduce the processed dataset **from the raw data** (downloads 186 MB, needs ~5 GB disk and a few GB RAM; roughly 10-15 min):

```bash
python setup_data.py --source HDFS --process-only
```

This downloads and verifies the archive, sorts the log chronologically, calls
`processing.process()` (parse -> normalise -> group into sessions -> features) and writes
`data/processed/HDFS_sessions.csv.gz` and `results/HDFS_event_buckets.json`.

If you only have the prepared dataset (as in the submission ZIP) you can skip this
and continue from section 4 - training reads `data/processed/HDFS_sessions.csv.gz` directly.

Feature extraction is reusable code in `src/features.py` (class `Session`), shared by
training, the CLI and the dashboard. Seven feature groups (justification in the module docstring):
event-type counts (32 hashed buckets), volume/variety, timing, topology, HDFS lifecycle
completeness ("absence" features), severity, and sequence regularity.

Exploratory analysis of the processed data (class balance, distributions, correlations, figures):

```bash
python src/eda.py --source HDFS      # -> results/HDFS_eda_summary.json, figures/HDFS_eda*.png
```

## 4. Training (classification, clustering, error analysis)

```bash
python src/train.py --source HDFS    # ~1-2 min
```

This one command:
1. makes the purged chronological 60/20/20 split (sessions straddling a boundary are dropped),
2. fits three classifiers (logistic regression, random forest, histogram gradient boosting) and picks each decision threshold on validation only,
3. refits on train+validation, scores the later **test period** once, and saves the best model to `models/HDFS_final.joblib`,
4. clusters the anomalies (`src/clustering.py`) -> `results/HDFS_cluster_analysis.json`, `HDFS_cluster_report.md`, `models/HDFS_clusters.joblib`,
5. analyses false positives/negatives (`src/evaluation.py`) -> `results/HDFS_error_analysis.json`.

Individual steps can be re-run: `python src/clustering.py`, `python src/evaluation.py`,
`python src/evaluation.py --stability` (refits every model under 5 seeds, ~10 min), `python src/charts.py` (figures).

`python setup_data.py --source HDFS` does everything end to end (download -> process -> train).

Note: the real example events inside the cluster/error analyses are read from the raw log
(`data/raw/HDFS_v1/HDFS.sorted.log`, created by `setup_data.py`). The committed `results/` were generated with it
present. If you retrain from the prepared dataset alone, all metrics are identical (verified) but the cluster
descriptions are generated from the features and `HDFS_event_buckets.json` only, without example events.

## 5. Prediction

```bash
python src/predict.py --source HDFS --log data/supporting/sample_HDFS.log --out predictions.csv
```

Writes one row per session with the 52 features, `score` (anomaly probability), `decision`
(`ANOMALY` if `score` >= the saved threshold) and `cluster` (nearest anomaly cluster for flagged sessions, else -1).
Logs must be in chronological order (the raw Loghub file is; `setup_data.py` sorts it).

From Python:

```python
import sys; sys.path.insert(0, "src")
from predict import predict
df, audit, _ = predict("data/supporting/sample_HDFS.log", "HDFS")
print(df[["session_id", "score", "decision", "cluster"]].sort_values("score", ascending=False).head())
```

## 6. Dashboard

```bash
python src/dashboard.py              # http://127.0.0.1:5000
```

Upload a log (try `data/supporting/sample_HDFS.log`, source HDFS). The page shows the final model and its
test metrics, sessions analysed / flagged, the anomaly-score distribution, the anomaly clusters present in the
upload with their descriptions, and a searchable/sortable session table. **Inspect** opens a session: its score,
decision, cluster and the real raw events read back from the uploaded file. Results can be exported as CSV.
The dashboard calls `predict.predict()` - the same code path as the CLI - so there is no demo data.

## 7. Results (HDFS, temporal test period: the latest 20% of the log, 115,018 sessions)

| Model | Accuracy | Precision | Recall | F1 | PR-AUC |
|---|---|---|---|---|---|
| Logistic regression | 0.9980 | 0.9578 | 0.9042 | 0.9302 | 0.9328 |
| Random forest | 0.9987 | 1.0000 | 0.9113 | 0.9536 | 0.9999 |
| **Histogram gradient boosting (final)** | **0.9998** | **0.9994** | **0.9869** | **0.9931** | **0.9996** |

Final model confusion matrix: TN 113,337 · FP 1 · FN 22 · TP 1,658.
Seed stability (5 seeds, F1): histogram GB 0.9932 ± 0.0004; random forest 0.9437 ± 0.0149 (range 0.918-0.957).
Hard subset - anomalies whose messages contain no error words (n=858): recall 0.977.
All numbers are generated by the code and stored in `results/`; the 22 missed anomalies and
the single false positive are analysed in `results/HDFS_error_analysis.json`.

Clustering (11,494 development-period anomalies, k=6 by silhouette among k>=3; k=2..8 sweep reported): the
clusters are truncated 2-event sessions, long/stalled sessions that still complete, failed writes
("Could not read from stream"), over-replicated sessions with many hosts, and two tiny clusters of rare exception
types. Each cluster's mean features vs the anomaly and overall averages, label composition, test-period
assignment, interpretation and real example sessions are in `results/HDFS_cluster_report.md`.

## 8. Project structure

```
README.md  environment.yml  requirements.txt  setup_data.py
src/
  features.py     feature schema + Session accumulator (single source of truth)
  processing.py   raw log parsing, session grouping, process() -> feature table
  train.py        split, classifier comparison, final model; orchestrates the steps below
  clustering.py   K-means within the anomaly class + automatic cluster interpretation
  evaluation.py   error analysis, hard subset, seed stability
  eda.py          exploratory analysis       charts.py   result figures
  predict.py      scoring entry point (CLI + dashboard)
  dashboard.py, upload_store.py, templates/, static/    Flask application
tests/            unit + integration tests (python -m unittest discover -s tests -v)
data/processed/   the final processed dataset      data/supporting/  sample log + labels
models/           HDFS_final.joblib (classifier), HDFS_clusters.joblib (scaler + K-means)
results/          all metrics, cluster/error analyses, predictions     figures/  plots
archive/          earlier experiment's outputs (see below); not used by the code
```

`archive/original_experiment/` holds outputs (results, figures, a feature module) of an earlier prototype that used a
different, 66-feature schema and a separate template miner. Its source and model are not part of this project, so it is
kept only as historical reference and nothing here depends on it.

## 9. Limitations

* BGL: the adapter, feature code and unit test exist (`python setup_data.py --source BGL`), but only HDFS has been run end to end for the submitted models/results.
* HDFS lifecycle features are HDFS-specific (zero for BGL).
* Hash-bucket event features can merge several event kinds into one bucket (see `results/HDFS_event_buckets.json`).
* The dashboard keeps one analysed upload at a time and is meant for local use.
