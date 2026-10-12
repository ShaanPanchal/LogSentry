# LogSentry - Log Anomaly Detection

COS30049 Assignment 2 - Session 12, Group 3 - Shaan Panchal, Neeven Emmanuel, Dominique Tait

LogSentry turns raw HDFS and BGL logs into sessions, classifies each session as normal or anomalous, clusters the anomalies, and shows the results in a Flask dashboard. Run every command from the repository root.

## 0. Open the repository root.
Open a terminal in the extracted LogSentry folder before running the commands below.

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

### OPTIONAL: raw logs for example events

Raw logs are not required for normal training or prediction when the prepared datasets are included. They are used to rebuild missing processed datasets and to add real example events to cluster descriptions and error analysis. To fetch and sort them (even though the processed datasets already exist), run:

```bash
python setup_data.py --source HDFS --raw-only
python setup_data.py --source BGL --raw-only
```

The HDFS download is large (the sorted log is about 1.5 GB) and can take about 10 minutes (most of it the 186 MB download); BGL is much smaller. If the sorted log already exists the command does nothing. Training still works without raw logs. If complete cluster and error-analysis files already exist (as they do in the submission), training without raw logs keeps them and does not overwrite them. If complete cluster and error-analysis files are not already available, training without raw logs may produce cluster descriptions and error-analysis results without example events. A warning is printed.

## 3. Train the models

```bash
python src/train.py --source HDFS
python src/train.py --source BGL
```

## 4. Predict

```bash
python src/predict.py --source HDFS --log data/supporting/sample_HDFS.log --out predictions.csv
python src/predict.py --source BGL --log data/supporting/sample_BGL.log --out predictions_bgl.csv
```

## Dashboard

```bash
python src/dashboard.py
```
Open http://127.0.0.1:5050 in your browser and upload a sample .log file from data/supporting/. Keep the terminal open while using the dashboard.




On macOS you can use `./Start-LogSentry.command` instead (it creates a `.venv` and installs `requirements.txt`).

## Where things are

* Prepared datasets: `data/processed/HDFS_sessions.csv.gz`, `data/processed/BGL_sessions.csv.gz`
* Final models: `models/HDFS_final.joblib`, `models/BGL_final.joblib` (plus `*_clusters`, `*_xgboost`, `*_extra_trees`)
* Results: `results/`, sample logs: `data/supporting/`
* Figures are not included. `python src/eda.py` and `python src/charts.py` create them in `figures/`.

## Notes

* Data Credits: Curated by LOGPAI. (2023). Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.8196385 
* Raw data is not included in the submission ZIP. `setup_data.py` downloads it into `data/raw/` only when a processed table is rebuilt or `--raw-only` is run.
* `scikit-learn` is pinned to 1.9.1 to maintain compatibility with the saved models.
* On Windows, `src/mkl_setup.py` automatically applies a workaround for an MKL threading issue.