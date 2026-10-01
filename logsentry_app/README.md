# LogSentry reconstructed source files

Extract this ZIP into `~/Downloads/LogSentry`. It creates a separate
`logsentry_app` folder. It does not replace the original files.

These are newly reconstructed runnable source files. They are not the lost
submission package, and they do not reproduce the previous experiment's scores.
The original saved XGBoost model expects a different feature schema and is not
compatible with this pipeline. Train the new model once before scoring logs.
The ZIP does not include trained models or processed training datasets.

## macOS installation

In Terminal:

```bash
cd ~/Downloads/LogSentry/logsentry_app
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Use Python 3.11 or 3.12. To open the interface immediately:

```bash
python src/dashboard.py
```

Open http://127.0.0.1:5000. It displays setup instructions until you train a model.
Stop the server with Control+C before starting training in the same Terminal.

## One-time model setup

```bash
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
python setup_data.py --source HDFS
python src/dashboard.py
```

Setup downloads the 186.6 MB HDFS archive, checks its publisher MD5, extracts
the raw log and block labels, sorts chronologically, builds session features,
compares three classifiers and saves the selected model. Allow several minutes,
about 6 GB available RAM and about 5 GB free disk space. Progress is printed.
Download source: https://zenodo.org/records/8196385/files/HDFS_v1.zip

For an additional heterogeneous dataset:

```bash
python setup_data.py --source BGL
```

BGL is downloaded separately, transformed to five-minute windows and fitted
separately. The same 52-feature schema is used, with HDFS-only lifecycle fields
zero for BGL. The leading BGL annotation never enters features. Numbers embedded
in machine names and hexadecimal addresses are masked before fixed hashing.

## Command-line prediction

```bash
python src/predict.py --source HDFS --log raw/HDFS_v1/HDFS.sorted.log --out predictions.csv
```

Full raw logs exceed the dashboard's 64 MB limit; the command line supports them.
For browser uploads use chronological logs containing complete block sessions.

## Training and results

```bash
python src/train.py --source HDFS
python -m unittest discover -s tests -v
```

Prepared CSVs are in `data/`; newly trained models are in `models/`. Validation
and temporal test metrics, false predictions, split membership and clustering
profiles are in `results/`. Models and thresholds are selected on validation F1.
The later test period is excluded from training. Sessions crossing the next
period boundary are purged from development partitions.

K-means is applied within development anomalies only. Labels select that class
but are excluded from clustering inputs. Signed-log features are standardized,
k=2..6 is compared by sampled silhouette, and the three strongest feature-mean
differences and real session IDs are recorded for each group. Label composition
is an integrity check, not independent evidence of cluster quality.

These files supply the executable workflow. They do not complete the report,
real weekly minutes, signed contribution form or full assessment evaluation.
The included `original_features.py` preserves the original repository module
for reference; the reconstructed application uses `src/processing.py` instead.

## Dataset notice

Loghub datasets are freely available for research or academic work. For any
usage or distribution, refer to https://github.com/logpai/loghub and cite:
Zhu, J., He, S., He, P., Liu, J. and Lyu, M.R. (2023), 'Loghub: A Large Collection
of System Log Datasets for AI-driven Log Analytics', ISSRE.
DOI: 10.1109/ISSRE59848.2023.00071.
Preserve this notice with derived datasets.
