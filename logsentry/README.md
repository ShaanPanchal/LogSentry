# LogSentry — Log Anomaly Detection

COS30049 Assignment 2 · Session 12, Group 3 · Shaan Panchal, Neeven Emmanuel, Dominique

This package turns a raw distributed-system log into session-level anomaly
predictions. It contains the full pipeline: log parsing and template mining,
session construction, feature extraction, exploratory analysis,
hyperparameter tuning, model training, clustering, evaluation, and a
prediction entry point.

---

## 1. Contents

```
README.md                         this file
data/
  sessions_features.csv           575,061 sessions x 70 features + label
                                  (the exact table the final model is trained on)
  event_templates.csv             the 44 event templates mined from HDFS.log
  anomaly_failure_families.csv    cluster assignment for each anomalous session
models/
  final_model_xgboost.joblib      trained model + the column order it expects
src/                              all source code (see section 6)
figures/                          every figure in the report
model_results.csv                 all models, both splits
tuning.json                       every hyperparameter sweep
clustering.json                   k sweep, cluster signatures, DBSCAN sweep
evaluation.json                   held-out families, hard subset, error analysis
stability.json                    seed-sensitivity runs
eda_summary.json                  exploratory analysis output
```

The raw `HDFS.log` (1.5 GB) and `anomaly_label.csv` are **not** included —
they are the dataset supplied with the assignment. Download them from
<https://doi.org/10.5281/zenodo.8196385> and place them in `data/` if you want
to re-run the pipeline from the raw log. Everything from stage 2 onwards runs
from `data/sessions_features.csv` alone.

---

## 2. Environment setup (conda)

```bash
# create and activate the environment
conda create -n logsentry python=3.11 -y
conda activate logsentry

# core scientific stack
conda install -c conda-forge pandas=3.0 numpy=2.4 scikit-learn=1.8 \
    pyarrow=25.0 matplotlib=3.9 -y

# gradient boosting libraries
conda install -c conda-forge xgboost=3.2 lightgbm=4.7 joblib -y
```

Equivalent with pip, if you prefer:

```bash
conda create -n logsentry python=3.11 -y && conda activate logsentry
pip install pandas numpy scikit-learn pyarrow matplotlib xgboost lightgbm joblib
```

Verify:

```bash
python -c "import pandas, numpy, sklearn, pyarrow, xgboost, lightgbm, joblib; print('ok')"
```

**Paths.** The scripts use absolute paths under `/home/claude/a2`. If you run
them elsewhere, edit the `PROC`, `OUT` and `RAW_LOG` constants at the top of
`src/modelling.py`, `src/build_events.py` and `src/build_sessions.py`, or set
the project root with:

```bash
export LOGSENTRY_ROOT=$(pwd)
```

**Hardware.** The full pipeline was developed on 2 CPU cores and 7 GB RAM.
Stage 1 takes about 200 s, everything after that is under a minute per stage
except the tuning sweeps (about 9 minutes).

---

## 3. Re-running the data processing

Stage 1 and 2 rebuild the processed dataset from the raw log. Skip them if you
just want to train from the supplied `sessions_features.csv`.

```bash
# Stage 1 — parse 11.2 M raw lines, mine event templates  (~200 s)
python src/build_events.py
#   -> processed/events.parquet, processed/templates.csv

# Stage 2 — group events into block sessions and build features  (~15 s)
python src/build_sessions.py
#   -> processed/sessions.parquet   (575,061 sessions x 66 features + label)

# Stage 2b — store each session's ordered event sequence  (~20 s)
python src/build_sequences.py
#   -> processed/sequences.npz
```

Expected stage-1 output:

```
raw lines read      : 11,175,629
malformed / skipped : 0
no block id         : 0
event rows written  : 11,175,629
templates mined     : 44
```

### Processing a different log format

`src/extra_sources.py` maps BGL, Thunderbird and OpenStack onto the same event
schema, so the same feature code works on all of them:

```python
import sys; sys.path.insert(0, "src")
import extra_sources as X
from features import build_session_features

events, sessions, templates = X.load_windowed_source("BGL.log", "BGL",
                                                     window_seconds=300)
features = build_session_features(events, templates).merge(sessions,
                                                           on="block_id")
```

---

## 4. Exploratory analysis and hyperparameter tuning

```bash
# EDA — quality checks, class balance, distributions, correlation  (~20 s)
python src/eda.py
#   -> eda_summary.json, figures/fig_eda1..3

# Hyperparameter tuning on the VALIDATION split only  (~9 min)
python src/tune.py
#   -> tuning.json
```

`tune.py` splits the data three ways by time — train / validation / test —
and never touches the test set. Each algorithm's most influential parameter is
swept and selected on validation PR-AUC. Parameters chosen:

| Algorithm | Parameter | Swept | Chosen |
|---|---|---|---|
| Logistic Regression | `C` | 0.01 – 100 | 0.1 |
| Decision Tree | `max_depth` | 2 – 20, none | 12 |
| Random Forest | `n_estimators` | 25 – 400 | 25 |
| KNN | `n_neighbors` | 1 – 25 | 25 |
| XGBoost | `max_depth` | 2 – 10 | 6 |
| XGBoost | `learning_rate` | 0.01 – 0.3 | 0.05 |
| LightGBM | `num_leaves` | 15 – 127 | 63 |
| Isolation Forest | `contamination` | 0.01 – 0.10 | 0.01 |

`src/modelling.py` reads these values back out of `tuning.json`, so training
always uses the tuned settings. If `tuning.json` is absent it falls back to
documented defaults.

---

## 5. Training the models

```bash
# Train all 8 models under both splits, save the final model  (~2 min)
python src/train.py
#   -> model_results.csv
#   -> outputs/final_model_xgboost.joblib
#   -> processed/sessions_with_seq.parquet

# Clustering: K-means within the anomaly class + DBSCAN comparison  (~3 min)
python src/cluster.py
#   -> clustering.json, processed/anomaly_clusters.parquet

# Seed sensitivity: decision tree vs random forest over 10 seeds  (~1 min)
python src/stability.py
#   -> stability.json

# Stress evaluation: held-out failure families + error analysis  (~6 min)
python src/evaluate.py
#   -> evaluation.json

# Regenerate every figure from the saved results  (~1 min)
python src/charts.py
#   -> figures/
```

Expected result on the temporal split (the honest one — the model is trained
on the first 70% of the log by time and tested on the last 30%):

| Model | Precision | Recall | F1 | PR-AUC |
|---|---|---|---|---|
| Logistic Regression | 0.997 | 0.997 | 0.997 | 0.999 |
| Decision Tree | 0.615 | 0.976 | 0.755 | 0.508 |
| Random Forest | 0.999 | 0.997 | 0.998 | 1.000 |
| KNN | 0.984 | 0.998 | 0.991 | 0.998 |
| **XGBoost (final model)** | **0.998** | **0.999** | **0.998** | **1.000** |
| LightGBM | 0.983 | 0.999 | 0.991 | 1.000 |
| Isolation Forest | 0.160 | 0.019 | 0.034 | 0.348 |
| Markov sequence (rule) | 0.997 | 0.316 | 0.480 | 0.330 |

The decision tree's low score is real, not a misconfiguration: refitting it
with a different random seed gives F1 anywhere between 0.699 and 0.987. Run
`src/stability.py` to reproduce that.

---

## 6. Using the model for prediction

`src/predict.py` runs the whole pipeline on a log file it has never seen and
writes one row per session.

```bash
# Score an HDFS log
python src/predict.py --log data/HDFS.log --out predictions.csv

# Score a different format
python src/predict.py --log BGL.log --source BGL --out bgl_predictions.csv

# Raise the bar for flagging a session
python src/predict.py --log data/HDFS.log --threshold 0.8 --out strict.csv
```

Options:

| Flag | Default | Meaning |
|---|---|---|
| `--log` | *required* | raw log file to score |
| `--source` | `HDFS` | `HDFS`, `BGL`, `Thunderbird` or `OpenStack` |
| `--model` | `outputs/final_model_xgboost.joblib` | trained model to load |
| `--out` | `predictions.csv` | where to write the results |
| `--threshold` | `0.5` | probability above which a session is flagged |

Output columns:

```
session_id, anomaly_probability, decision, n_events, duration_s,
lifecycle_complete, unacked_writes, unseen_transitions
```

Example:

```
session_id             anomaly_probability  decision  n_events  lifecycle_complete
-1608999687919862906                0.9987   ANOMALY        12                   0
 7503483334202473044                0.0013    NORMAL        19                   1
```

The trailing columns are there so the dashboard can explain a decision rather
than only report it: `lifecycle_complete = 0` means the block never finished
its write chain, `unacked_writes > 0` means a write was started and never
acknowledged, and `unseen_transitions > 0` means the session contained an
event ordering never observed in normal data.

### Loading the model directly

```python
import joblib, pandas as pd
bundle = joblib.load("models/final_model_xgboost.joblib")
model, columns = bundle["model"], bundle["columns"]

df = pd.read_csv("data/sessions_features.csv")
probabilities = model.predict_proba(df[columns])[:, 1]
```

`columns` is the exact feature order the model expects. Always index with it
rather than relying on the CSV's column order.

---

## 7. Source files

| File | What it does |
|---|---|
| `log_parser.py` | HDFS line parsing and our Drain template-miner implementation |
| `build_events.py` | Stage 1: stream the raw log into a structured event table |
| `features.py` | Session feature construction (all seven feature groups) |
| `build_sessions.py` | Stage 2: events → labelled session table |
| `build_sequences.py` | Stage 2b: store each session's ordered event sequence |
| `sequence_model.py` | First-order Markov transition model over event types |
| `extra_sources.py` | Adapters for BGL, Thunderbird and OpenStack |
| `eda.py` | Exploratory analysis and its figures |
| `modelling.py` | Splits, the model zoo, tuned-parameter lookup, scoring |
| `tune.py` | Hyperparameter sweeps on the validation split |
| `train.py` | Train and compare all models, save the final one |
| `cluster.py` | K-means within the anomaly class, DBSCAN comparison |
| `stability.py` | Seed sensitivity of the tree vs the forest |
| `evaluate.py` | Held-out failure families, hard subset, error analysis |
| `charts.py` | Every figure in the report |
| `predict.py` | Prediction entry point |

---

## 8. Dataset citation

Zhu, J., He, S., He, P., Liu, J. and Lyu, M.R. (2023) 'Loghub: a large
collection of system log datasets for AI-driven log analytics', *Proceedings
of the 34th IEEE International Symposium on Software Reliability Engineering
(ISSRE)*. Florence, 9–12 October. IEEE, pp. 355–366. Available at:
<https://doi.org/10.5281/zenodo.8196385>

Original HDFS data: Xu, W., Huang, L., Fox, A., Patterson, D. and Jordan, M.I.
(2009) 'Detecting large-scale system problems by mining console logs',
*Proceedings of the ACM SIGOPS 22nd Symposium on Operating Systems Principles
(SOSP)*. New York: ACM, pp. 117–132.
