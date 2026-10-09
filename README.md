# LogSentry - Log Anomaly Detection

COS30049 Assignment 2 · Session 12, Group 3 · Shaan Panchal, Neeven Emmanuel, Dominique

LogSentry takes a log file from a distributed system, groups the entries into
**sessions**, decides which sessions look abnormal, and presents the findings on
a monitoring dashboard with drill-down into individual sessions.

```
raw log -> parse/clean -> sessions -> 52 features -> classifier -> anomaly score
                                                          |-> clustering of anomalies -> dashboard + drill-down
```

* **Data**: two Loghub sources, processed and modelled **separately** (never mixed): HDFS (11,175,629 log lines -> 575,061 block sessions, 16,838 anomalous) and Blue Gene/L, BGL (4,747,963 lines -> 14,494 five-minute windows, 1,054 anomalous).
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
conda install -c conda-forge numpy pandas scikit-learn=1.9.1 joblib flask matplotlib xgboost -y
```

`pip install -r requirements.txt` also works inside any Python >= 3.11 environment.
`scikit-learn` is pinned to 1.9.1 because the shipped models in `models/` are
pickles and must be loaded by the version that trained them.

Dependencies: numpy, pandas, scikit-learn, joblib, Flask, matplotlib, xgboost
(already have the environment? add XGBoost with `conda install -c conda-forge xgboost`, or `pip install "xgboost>=2.0,<4"`).
Verify: `python -m unittest discover -s tests -v`

All commands below are run from the repository root. Paths are relative; nothing
is machine-specific.

## 2. Dataset

| Item | Location |
|---|---|
| **Processed dataset used by the final model** | `data/processed/HDFS_sessions.csv.gz` (575,061 rows: `session_id, source, t_start, t_end, label` + the 52 features) |
| Small real sample log (200 complete sessions, 2,819 lines, for trying prediction / the dashboard) | `data/supporting/sample_HDFS.log` (+ `sample_HDFS_labels.csv`) |
| **Processed BGL dataset** (14,494 five-minute windows, same 52 features) | `data/processed/BGL_sessions.csv.gz` |
| Small real BGL sample (100 complete windows, 2,595 lines, 25 anomalous) | `data/supporting/sample_BGL.log` (+ `sample_BGL_labels.csv`) |
| What each `event_hash_NN` feature counts | `results/HDFS_event_buckets.json`, `results/BGL_event_buckets.json` |
| Raw Loghub data (HDFS_v1.zip 186 MB, BGL.zip 57 MB; not committed) | fetched by `setup_data.py` into `data/raw/` (`BGL.log` ends up at `data/raw/BGL/BGL.log`) |

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

### BGL (second source)

```bash
python setup_data.py --source BGL --process-only    # download BGL.zip (57 MB), verify MD5, sort, parse, process (~3 min)
python setup_data.py --source BGL                   # ... and train/cluster/evaluate (results/BGL_*, models/BGL_*)
```

BGL goes through the **same** `processing.process()` -> `features.Session` -> 52-feature table as HDFS; only the raw-line
parser, session definition and label source differ, and those live in `src/sources.py` (one adapter per dataset):

| | HDFS | BGL |
|---|---|---|
| Raw line | `081109 203518 143 INFO dfs.DataNode: ...` | `- 1117838570 2005.06.03 R02-M1-N0-C:J12-U11 2005-06-03-15.42.50.675872 R02-M1-N0-C:J12-U11 RAS KERNEL INFO ...` |
| Session | one per block id (`blk_...`) | fixed 5-minute time window (BGL has no session id) |
| Label | per-block file `anomaly_label.csv` | in the log: first field `-` = normal, anything else = alert; a window is anomalous if any line is an alert |
| Host / thread | IPs in the message / thread id | node name / component (KERNEL, APP, ...) |

The alert tag is used **only** as the label and never reaches the feature code (unit-tested).
Six features are HDFS-specific (`has_allocate`, `has_delete`, `replica_deficit`, `unacked_writes`, `uncommitted_acks`,
`lifecycle_complete`): BGL has no block write chain, so they are fixed at 0 meaning "not applicable" (not fabricated), leaving
46 active features for BGL (confirmed in `results/BGL_eda_summary.json`, `constant_columns`).

Check the parser on any raw log (prints parsed fields, level/label counts, parse rate):

```bash
python src/processing.py --source BGL --log data/supporting/sample_BGL.log --head 3
```

Exploratory analysis of the processed data (class balance, distributions, correlations, figures):

```bash
python src/eda.py --source HDFS      # -> results/HDFS_eda_summary.json, figures/HDFS_eda*.png  (use --source BGL for BGL)
```

## 4. Training (classification, clustering, error analysis)

```bash
python src/train.py --source HDFS    # ~1 min   (python src/train.py --source BGL for BGL, ~10 s)
```

This one command:
1. makes the purged chronological 60/20/20 split (sessions straddling a boundary are dropped),
2. fits five classifiers - logistic regression, random forest, histogram gradient boosting, **XGBoost** and **Extra trees** - on the same 52 features and picks each decision threshold on validation only,
3. refits on train+validation, scores every model on the same later **test period** once, and saves the final model to `models/HDFS_final.joblib` (plus `HDFS_xgboost.joblib` and `HDFS_extra_trees.joblib`). The final model is selected on validation F1 among the original three only (`train.FINAL_CANDIDATES`); XGBoost and Extra trees are compared but do not change the deployed model,
4. clusters the anomalies (`src/clustering.py`) -> `results/HDFS_cluster_analysis.json`, `HDFS_cluster_report.md`, `models/HDFS_clusters.joblib`,
5. analyses false positives/negatives (`src/evaluation.py`) -> `results/HDFS_error_analysis.json`.

The five-model comparison is written to `results/HDFS_model_comparison.csv` / `.json` (validation and test rows, role of
each model, fit/predict time, and a hash of the test session ids). Each model's type, hyperparameters (read from the fitted
estimator), scaling requirement, learning approach and suitability for the 52 features are in `HDFS_model_comparison.json` and a
report-ready `results/HDFS_model_comparison.md`. `python src/comparison.py` re-verifies that every model was scored on
the same test set and prints the table; the dashboard shows it as a table plus a precision/recall/F1 bar chart.

Individual steps can be re-run: `python src/clustering.py`, `python src/evaluation.py`,
`python src/evaluation.py --stability` (refits every model under 5 seeds), `python src/evaluation.py --folds` (rolling-origin temporal evaluation over several test periods, see BGL below), `python src/charts.py` (figures).

`python setup_data.py --source HDFS` does everything end to end (download -> process -> train).
`python setup_data.py --source HDFS --raw-only` only re-fetches and sorts the raw log (needed for the example events below).

Note: the real example events inside the cluster/error analyses are read from the raw log
(`data/raw/HDFS_v1/HDFS.sorted.log`, created by `setup_data.py`). The committed `results/` were generated with it
present. If you retrain from the prepared dataset alone, all metrics are identical (verified) but the cluster
descriptions are generated from the features and `HDFS_event_buckets.json` only, without example events.

## 5. Prediction

```bash
python src/predict.py --source HDFS --log data/supporting/sample_HDFS.log --out predictions.csv
python src/predict.py --source BGL  --log data/supporting/sample_BGL.log  --out predictions_bgl.csv
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

The **Log sources** table at the top lists each trained dataset (session definition, sizes, final model, test precision/recall/F1); click the **HDFS** / **BGL** tab to switch the model panel, five-model comparison (and, for BGL, the temporal-robustness table) between the two datasets without uploading anything. The datasets are never mixed. Pick the log source (HDFS or BGL) and upload a log (try `data/supporting/sample_HDFS.log` or `sample_BGL.log`). An "Analysis details" panel shows the source, model used, session definition, sessions analysed, sessions the model flagged, sessions labelled anomalous in the log itself (BGL only), events assigned and the parsing statistics (raw lines, malformed lines, lines without a session). The page shows the final model and its
test metrics, sessions analysed / flagged, the anomaly-score distribution, the anomaly clusters present in the
upload with their descriptions, and a searchable/sortable session table. **Inspect** opens a session: its score,
decision, cluster and the real raw events read back from the uploaded file. Results can be exported as CSV.
The dashboard calls `predict.predict()` - the same code path as the CLI - so there is no demo data.

## 7. Results (HDFS, temporal test period: the latest 20% of the log, 115,018 sessions)

| Model | Accuracy | Precision | Recall | F1 | PR-AUC | FP | FN |
|---|---|---|---|---|---|---|---|
| Logistic regression | 0.9980 | 0.9578 | 0.9042 | 0.9302 | 0.9328 | 67 | 161 |
| Random forest | 0.9987 | 1.0000 | 0.9113 | 0.9536 | 0.9999 | 0 | 149 |
| **Histogram gradient boosting (final)** | **0.9998** | **0.9994** | **0.9869** | **0.9931** | **0.9996** | 1 | 22 |
| Extra trees | 0.9998 | 1.0000 | 0.9845 | 0.9922 | 0.9998 | 0 | 26 |
| XGBoost | 0.9999 | 0.9988 | 0.9923 | 0.9955 | 0.9996 | 2 | 13 |

XGBoost and Extra trees were added after the original comparison; they use the identical split and test sessions.
XGBoost scores slightly higher than the final model on the test period but did worse on validation (F1 0.907 vs 0.994,
threshold chosen on validation), so it was not promoted; Extra trees had the best validation F1 (0.9975) but a lower test F1.
Changing the final model is a deliberate decision, not something the code does automatically.

Final model confusion matrix: TN 113,337 · FP 1 · FN 22 · TP 1,658.
Seed stability (5 seeds, test F1): histogram GB 0.9932 ± 0.0004; XGBoost 0.9955 (identical across seeds); Extra trees 0.9834 ± 0.0084 (0.971-0.992); random forest 0.9437 ± 0.0149 (0.918-0.957); logistic regression 0.9302 (deterministic).
Hard subset - anomalies whose messages contain no error words (n=858): recall 0.977.
All numbers are generated by the code and stored in `results/`; the 22 missed anomalies and
the single false positive of the final model are analysed in `results/HDFS_error_analysis.json`.

### BGL (temporal test period: the latest 20% of windows, 2,899 windows of which 225 anomalous)

| Model | Accuracy | Precision | Recall | F1 | PR-AUC | FP | FN |
|---|---|---|---|---|---|---|---|
| Logistic regression | 0.9383 | 0.5865 | 0.6933 | 0.6354 | 0.6024 | 110 | 69 |
| Random forest | 0.9614 | 0.8343 | 0.6267 | 0.7157 | 0.8760 | 28 | 84 |
| **Histogram gradient boosting (final)** | **0.9586** | **0.8571** | **0.5600** | **0.6774** | **0.8804** | 21 | 99 |
| Extra trees | 0.9486 | 0.8276 | 0.4267 | 0.5630 | 0.7950 | 20 | 129 |
| XGBoost | 0.9683 | 0.8482 | 0.7200 | 0.7788 | 0.8965 | 29 | 63 |

**How BGL is split and why.** BGL sessions carry timestamps, so the same purged chronological 60/20/20 split as HDFS is used
(train 8,696 / validation 2,899 / test 2,899 windows, June-October 2005 / October-November / November 2005-January 2006); a random
split would leak the future. BGL windows do not overlap, so nothing is purged. Because the anomaly rate drifts over time
(8.5% train, 3.0% validation, 7.8% test) and the test period holds only 225 anomalies, one test period is a noisy basis for ranking
models, so two further checks are stored:

* **Rolling-origin temporal folds** (`results/BGL_temporal_folds.json`): the windows are cut into 5 time chunks; fold k trains on chunks
  before k and tests on chunk k (4 folds, test anomaly rates 8.0%, 10.3%, 3.0%, 7.8%), thresholds tuned on the last 25% of each
  training window. Fold 4 is the same period as the table above.

| Model (BGL, 4 folds) | Mean F1 | Min | Max | Mean precision | Mean recall | Total FP | Total FN |
|---|---|---|---|---|---|---|---|
| Logistic regression | 0.598 | 0.529 | 0.661 | 0.557 | 0.712 | 495 | 246 |
| Random forest | 0.777 | 0.716 | 0.839 | 0.795 | 0.784 | 191 | 176 |
| Histogram gradient boosting | 0.776 | 0.677 | 0.863 | 0.786 | 0.787 | 189 | 192 |
| Extra trees | 0.720 | 0.563 | 0.838 | 0.725 | 0.774 | 231 | 190 |
| XGBoost | 0.784 | 0.636 | 0.871 | 0.760 | 0.819 | 242 | 152 |

* **Seed stability** (`results/BGL_stability.json`, standard split, 5 seeds, F1): XGBoost 0.779 (identical across seeds), random forest
  0.716 +/- 0.021, HGB 0.683 +/- 0.022, Extra trees 0.572 +/- 0.011, logistic regression 0.635 (deterministic).

Reading: on BGL, XGBoost, random forest and HGB are statistically indistinguishable (mean F1 about 0.78, fold-to-fold spread about 0.09);
Extra trees is the least stable; logistic regression is clearly worst. The single-split ranking should not be over-interpreted.

BGL is a much harder problem than HDFS under the same temporal protocol (F1 0.56-0.78 vs about 0.99). The final model is chosen by the
same validation rule as for HDFS (HGB), and XGBoost is best on the test period here. Note the anomaly share differs sharply between
the validation (3.0%) and test (7.8%) periods, so thresholds tuned on validation transfer imperfectly. BGL clusters
(829 anomalies, k=7) are weak (silhouette 0.21); see `results/BGL_cluster_report.md`. Results for the two sources are never mixed:
every file is prefixed `HDFS_` or `BGL_`.

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
  sources.py      per-dataset adapters (HDFS, BGL): line parser, session definition, label source, download metadata
  processing.py   source-independent session grouping, process() -> feature table, parser verification
  train.py        split, classifier comparison, final model; orchestrates the steps below
  clustering.py   K-means within the anomaly class + automatic cluster interpretation
  comparison.py   five-model comparison record + shared-test-set verification
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

`figures/` holds 14 PNGs (7 per source: `<SOURCE>_eda1_overview`, `_eda2_by_class`, `_eda3_correlation`, `_model_comparison`,
`_confusion_matrix`, `_cluster_silhouette`, `_cluster_signatures`). All are generated by this pipeline: the `eda*` plots by
`src/eda.py` and the other four by `src/charts.py` (both write to `figures/`). They are report evidence and are not used by the dashboard.

`archive/original_experiment/` holds the **results of an earlier prototype**, not of this pipeline. That prototype used a
different feature schema (its own README says 66 or 70 features) and a separate template miner, and evaluated models with different
splits. Its source and model are not part of this project, and its README (`README_original.md`), figures (`fig*.png`) and metrics
(`model_results.csv`, `*.json`) describe that prototype only: its setup instructions, paths and numbers do not apply here and must
not be compared with or mixed into the HDFS/BGL results in `results/` and `figures/`. It is kept only as historical reference and
nothing here depends on it.

## 9. Limitations

* BGL sessions are fixed five-minute windows (a common but arbitrary choice); a different window size changes the dataset (`sources.BGL_WINDOW_SECONDS`, then rebuild).
* HDFS lifecycle features are not applicable to BGL (fixed 0), so BGL models use 46 informative features.
* The processed CSVs store features to 8 significant digits, so a live re-computation can differ from a stored score by a tiny amount for borderline sessions (checked: identical once the same rounding is applied).
* Hash-bucket event features can merge several event kinds into one bucket (see `results/HDFS_event_buckets.json`).
* The dashboard keeps one analysed upload at a time and is meant for local use.
