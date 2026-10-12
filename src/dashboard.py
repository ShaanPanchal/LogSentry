"""Local Flask dashboard: upload a log, score its sessions, filter them and drill down.

An upload goes through the same pipeline as the command line: parse, group into
sessions, extract features (features.py) and score with the saved model (predict.py).
Flagged sessions are also given an anomaly cluster. Saved results in results/ give
the model and cluster information.

Run:  python src/dashboard.py   then open http://127.0.0.1:5050
"""
import atexit
import csv
import io
import json
import math
import shutil
import tempfile
from pathlib import Path

import mkl_setup  # noqa: F401  (Windows MKL fix, must come before numpy)
import joblib
import numpy as np
from flask import Flask, Response, jsonify, render_template, request, url_for

from predict import predict
from processing import ROOT
from sources import get_source
from upload_store import build_index, read_events

SOURCES = ['HDFS', 'BGL']
PAGE_SIZE = 50
MAX_UPLOAD = 4 * 1024 ** 3

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD
# One analysed upload is kept at a time (single-user local tool).
STATE = {'df': None, 'events': {}, 'audit': {}, 'upload_dir': None, 'source': None}


def cleanup():
    if STATE.get('upload_dir'):
        shutil.rmtree(STATE['upload_dir'], ignore_errors=True)


atexit.register(cleanup)


def load_model_info(source):
    """Load the saved model results, cluster descriptions, comparison and folds for a source."""
    info = {'model': None, 'clusters': {}, 'comparison': [], 'comparison_split': None, 'profile_note': '', 'folds': None}
    if not source:
        return info
    evaluation = ROOT / 'results' / f'{source}_evaluation.json'
    if evaluation.exists():
        result = json.loads(evaluation.read_text())
        test = next((t for t in result['temporal_test'] if t['model'] == result['selected_model']), None)
        info['model'] = {'name': result['selected_model'], 'test': test,
                         'n_features': result['final_model']['n_features']}
    comparison = ROOT / 'results' / f'{source}_model_comparison.json'
    if comparison.exists():
        saved = json.loads(comparison.read_text())
        info['comparison'] = comparison_rows(saved)
        info['profile_note'] = saved.get('training_protocol', '')
        info['comparison_split'] = saved['split'] | {'shared': saved['models_share_test_set']}
    folds = ROOT / 'results' / f'{source}_temporal_folds.json'
    if folds.exists():
        info['folds'] = folds_summary(json.loads(folds.read_text()))
    clusters = ROOT / 'models' / f'{source}_clusters.joblib'
    if clusters.exists():
        info['clusters'] = joblib.load(clusters).get('summaries', {})
    return info


def folds_summary(saved):
    """Summarise the rolling temporal folds: mean, min and max F1 for each model."""
    usable = [f for f in saved['folds'] if f['usable']]
    rows = [{'model': name, **{k: v[k] for k in ('mean_f1', 'min_f1', 'max_f1', 'std_f1', 'mean_precision',
                                                 'mean_recall', 'total_fp', 'total_fn')}}
            for name, v in saved['results'].items()]
    return {'n_folds': len(usable), 'rows': rows,
            'rates': ', '.join(f"{f['test_anomaly_rate']:.1%}" for f in usable)}


def dataset_summaries():
    """One row for each dataset that has a trained model, so the sources can be told apart."""
    out = []
    for name in SOURCES:
        spec = get_source(name)
        path = ROOT / 'results' / f'{name}_evaluation.json'
        if not path.exists():
            continue
        ev = json.loads(path.read_text())
        final = next(t for t in ev['temporal_test'] if t['model'] == ev['selected_model'])
        eda = ROOT / 'results' / f'{name}_eda_summary.json'
        total = anomalies = None
        if eda.exists():
            cb = json.loads(eda.read_text())
            total, anomalies = cb['n_sessions'], cb['class_balance']['anomaly']
        out.append({'name': name, 'title': spec.title, 'session': spec.session_definition, 'sessions': total,
                    'anomalies': anomalies, 'test_sessions': final['tn'] + final['fp'] + final['fn'] + final['tp'],
                    'test_anomalies': final['tp'] + final['fn'], 'final': ev['selected_model'],
                    'f1': final['f1'], 'precision': final['precision'], 'recall': final['recall']})
    return out


def dataset_overview(name):
    """Size, anomaly share and feature count of a dataset, from its saved EDA summary and model results."""
    eda = ROOT / 'results' / f'{name}_eda_summary.json'
    if not eda.exists():
        return None
    summary = json.loads(eda.read_text())
    balance = summary['class_balance']
    total = summary['n_sessions']
    # Only show the anomaly numbers if every session has a label (0 or 1), otherwise they would be misleading.
    labelled = balance['normal'] + balance['anomaly'] == total
    features = summary.get('n_features')
    evaluation = ROOT / 'results' / f'{name}_evaluation.json'
    if evaluation.exists():
        features = json.loads(evaluation.read_text()).get('final_model', {}).get('n_features', features)
    return {'sessions': total, 'session_definition': get_source(name).session_definition, 'features': features,
            'anomalies': balance['anomaly'] if labelled else None,
            'anomaly_rate': balance['anomaly'] / total if labelled and total else None}


def comparison_rows(saved):
    """Get the test period rows of the saved model comparison."""
    rows = []
    for r in saved['models']:
        if r['period'] != 'test':
            continue
        rows.append({**r, 'final': r['role'].startswith('final'),
                     'profile': saved.get('profiles', {}).get(r['model'])})
    return rows


def score_histogram(df, bins=10):
    """Count sessions in each score bin. Bar heights use a square root so small bins are still visible."""
    counts, edges = np.histogram(df.score, bins=bins, range=(0, 1))
    # Bar heights use a square root, otherwise the huge normal bin would make the other bars too small to see.
    top = max(math.sqrt(counts.max()), 1)
    return [{'label': f'{edges[i]:.1f}-{edges[i + 1]:.1f}', 'count': int(c),
             'height': round(100 * math.sqrt(c) / top)} for i, c in enumerate(counts)]


def cluster_rows(df, summaries):
    """Group the flagged sessions of this upload by anomaly cluster."""
    flagged = df[df.decision == 'ANOMALY']
    rows = []
    for cluster, n in flagged.cluster.value_counts().sort_index().items():
        if cluster < 0:
            continue
        info = summaries.get(int(cluster), {})
        rows.append({'cluster': int(cluster), 'flagged': int(n),
                     'share': n / max(len(flagged), 1), 'text': info.get('interpretation', '')})
    return rows


def run_upload():
    """Handle an uploaded log. Returns an error message, or None if it worked."""
    source, upload = request.form.get('source'), request.files.get('log')
    if source not in SOURCES or not upload:
        return 'Choose a supported source and a log file.'
    folder = tempfile.mkdtemp(prefix='logsentry-upload-')
    try:
        path = Path(folder) / 'upload.log'
        upload.save(path)
        # predict() is the same function the command line uses, so the dashboard shows real model output.
        df, audit, _ = predict(path, source, keep=False)
        print('Building disk index for session drill-down...', flush=True)
        build_index(path, Path(folder) / 'events.sqlite', source)
        cleanup()  # drop the previous upload
        # Only replace the stored results after scoring and indexing both worked, so a failed upload
        # does not wipe the previous results.
        STATE.update(df=df, audit=audit, events={}, upload_dir=folder, source=source)
    except Exception as e:
        shutil.rmtree(folder, ignore_errors=True)
        if not isinstance(e, (ValueError, FileNotFoundError, KeyError)):
            raise
        return str(e)
    return None


@app.route('/', methods=['GET', 'POST'])
def index():
    # One page handles everything. A POST is an upload (the JavaScript sends it in the background and
    # reloads the page when it finishes). A GET shows the results with the current filters and page.
    error = run_upload() if request.method == 'POST' else None
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=not bool(error), error=error), 400 if error else 200

    df = STATE['df']
    q = request.args.get('q', '')
    only = request.args.get('anomalies') == '1'
    sort = request.args.get('sort', 'score')
    rows, detail, events, truncated = [], None, [], False
    total = flagged = None
    matching, page, pages, prev_url, next_url = 0, 1, 1, None, None
    histogram, clusters = [], []
    spec = get_source(STATE['source']) if STATE['source'] else None
    ready = [s for s in SOURCES if (ROOT / 'models' / f'{s}_final.joblib').exists()]
    datasets = dataset_summaries()
    evaluated = [d['name'] for d in datasets]
    # Which dataset's results are on show: ?results=BGL, else the uploaded source, else the first trained one.
    # Two separate choices: ?results= decides which dataset's model results are shown in the tabs,
    # and the uploaded source (STATE) decides which model scored the table and which clusters are used.
    view_source = request.args.get('results')
    if view_source not in evaluated:
        view_source = STATE['source'] if STATE['source'] in evaluated else (evaluated[0] if evaluated else None)
    info = load_model_info(STATE['source'])          # the uploaded log's source: clusters, drill-down text
    view = load_model_info(view_source)               # the selected dataset: model, comparison, folds
    keep = {'results': request.args.get('results')}

    if df is not None:
        total = len(df)
        flagged = int((df.decision == 'ANOMALY').sum())
        table = df
        if q:
            table = table[table.session_id.str.contains(q, regex=False)]
        if only:
            table = table[table.decision == 'ANOMALY']
        matching = len(table)
        pages = max(1, math.ceil(matching / PAGE_SIZE))
        try:
            page = max(1, min(pages, int(request.args.get('page', 1))))
        except ValueError:
            page = 1
        column = {'score': 'score', 'events': 'n_events', 'id': 'session_id'}.get(sort, 'score')
        start = (page - 1) * PAGE_SIZE
        # Sort, then cut out just the rows for the current page.
        rows = table.sort_values(column, ascending=column == 'session_id').iloc[start:start + PAGE_SIZE].to_dict('records')
        flag = '1' if only else '0'
        if page > 1:
            prev_url = url_for('index', q=q, sort=sort, anomalies=flag, page=page - 1, **keep)
        if page < pages:
            next_url = url_for('index', q=q, sort=sort, anomalies=flag, page=page + 1, **keep)

        # If a session was clicked, find it and read its real log lines back from the uploaded file.
        match = df[df.session_id == request.args.get('session')]
        if len(match):
            detail = match.iloc[0].to_dict()
            detail['cluster_text'] = info['clusters'].get(int(detail['cluster']), {}).get('interpretation', '')
            folder = Path(STATE['upload_dir'])
            events, truncated = read_events(folder / 'upload.log', folder / 'events.sqlite',
                                            STATE['source'], detail['session_id'])
        histogram = score_histogram(df)
        clusters = cluster_rows(df, info['clusters'])

    return render_template('dashboard.html', source=STATE['source'], sort=sort, matching=matching, page=page,
                           pages=pages, prev_url=prev_url, next_url=next_url, ready=ready, error=error,
                           total=total, flagged=flagged, rows=rows, audit=STATE['audit'], q=q, only=only,
                           detail=detail, events=events, truncated=truncated, histogram=histogram,
                           clusters=clusters, comparison=view['comparison'],
                           comparison_split=view['comparison_split'], profile_note=view['profile_note'],
                           folds=view['folds'], spec=spec, datasets=datasets, view_source=view_source,
                           upload_model=info['model'],
                           overview=dataset_overview(view_source) if view_source else None)


@app.errorhandler(413)
def too_large(e):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=False, error='File exceeds the 4 GB upload limit.'), 413
    return 'File exceeds the 4 GB upload limit.', 413


@app.route('/export')
def export():
    """Download the per-session results as a CSV file."""
    df = STATE['df']
    if df is None:
        return 'Upload and analyse a log first.', 400

    def rows():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(df.columns)
        yield buffer.getvalue()
        for row in df.itertuples(index=False, name=None):
            buffer.seek(0)
            buffer.truncate(0)
            writer.writerow(row)
            yield buffer.getvalue()

    return Response(rows(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=logsentry-predictions.csv'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5050, debug=False)
