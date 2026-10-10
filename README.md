# LogSentry - Log Anomaly Detection

COS30049 Assignment 2 - Session 12, Group 3 - Shaan Panchal, Neeven Emmanuel, Dominique Tait

LogSentry turns raw HDFS and BGL logs into sessions, classifies each session as normal or anomalous, clusters the anomalies, and shows the results in a Flask dashboard. Run every command from the repository root.

## 1. Configure the environment (conda)

```bash
conda env create -f environment.yml
conda activate logsentry
```

## 2. Process the data

The prepared datasets are included, so you can skip to step 3. `setup_data.py` only builds a table that is missing: if `data/processed/<SOURCE>_sessions.csv.gz` already exists, `--process-only` does nothing and downloads nothing. To rebuild a table, first delete (or move) its `.csv.gz` file, then run the command below, which downloads the raw Loghub data from Zenodo, verifies its checksum, sorts the log by time and builds the feature table. `eda.py` then analyses a prepared dataset.

```bash
python setup_data.py --source HDFS --process-only
python setup_data.py --source BGL --process-only
python src/eda.py --source HDFS
python src/eda.py --source BGL
```

## 3. Train the models

```bash
python src/train.py --source HDFS
python src/train.py --source BGL
```

## 4. Predict

```bash
python src/predict.py --source HDFS --log data/supporting/sample_HDFS.log --out predictions.csv
python src/predict.py --source BGL  --log data/supporting/sample_BGL.log  --out predictions_bgl.csv
```

## Dashboard

```bash
python src/dashboard.py     # open http://127.0.0.1:5050 and upload a sample log
                            # Note: First-time startup may take a few minutes.
```

On macOS you can use `./Start-LogSentry.command` instead (it creates a `.venv` and installs `requirements.txt`).

## Where things are

* Prepared datasets: `data/processed/HDFS_sessions.csv.gz`, `data/processed/BGL_sessions.csv.gz`
* Final models: `models/HDFS_final.joblib`, `models/BGL_final.joblib` (plus `*_clusters`, `*_xgboost`, `*_extra_trees`)
* Results: `results/`, sample logs: `data/supporting/`
* Figures are not included. `python src/eda.py` and `python src/charts.py` create them in `figures/`.

## Notes

* Data Credits: Curated by LOGPAI. (2023). Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.8196385 
* Raw data is not included in the submission ZIP; `setup_data.py` downloads it into `data/raw/`. 
* `scikit-learn` is pinned to 1.9.1 to maintain compatibility with the saved models.
* On Windows, `src/mkl_setup.py` automatically applies a workaround for an MKL threading issue.