# LogSentry - Log Anomaly Detection

COS30049 Assignment 2 · Session 12, Group 3 · Shaan Panchal, Neeven Emmanuel, Dominique

LogSentry turns raw HDFS and BGL logs into sessions, classifies each session as normal or anomalous, clusters the anomalies,
and shows the results in a Flask dashboard. Run every command from the repository root.

> *Explain how to configure your project environment using conda commands, how to perform further data processing based on your
> prepared training dataset, how to train your model, and how to use your model for prediction.*

## 1. Configure the environment (conda)

```bash
conda env create -f environment.yml
conda activate logsentry
python -m unittest discover -s tests -v    # optional check
```

## 2. Process the data

The prepared datasets are included, so you can skip to step 3. To rebuild them, this downloads the raw Loghub data from Zenodo, verifies its checksum and builds the feature tables. `eda.py` then analyses a prepared dataset.

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
```

On macOS you can use `./Start-LogSentry.command` instead (it creates a `.venv` and installs `requirements.txt`).

## Where things are

* Prepared datasets: `data/processed/HDFS_sessions.csv.gz`, `data/processed/BGL_sessions.csv.gz`
* Final models: `models/HDFS_final.joblib`, `models/BGL_final.joblib` (plus `*_clusters`, `*_xgboost`, `*_extra_trees`)
* Results: `results/`, figures: `figures/`, sample logs: `data/supporting/`

## Notes

* Data: Curated by LOGPAI. (2023). Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.8196385 
  
  The raw data is not in the zip; `setup_data.py` downloads it into `data/raw/`.
* `scikit-learn` is pinned to 1.9.1 to maintain compatibility with the saved models.
* On Windows, `src/mkl_setup.py` automatically applies a workaround for an MKL threading issue.
* Retraining reproduces the final model results; the logistic regression baseline may differ slightly due to numerical-library differences.