"""Local Flask dashboard: upload a log, score sessions, filter, drill down.

The page is backed by the real pipeline: an upload is parsed and grouped into
sessions, features are extracted by features.py, the saved final classifier
scores each session (predict.py) and flagged sessions are assigned to an anomaly
cluster.  Training results (results/*.json) supply the model/cluster context.

Run:  python src/dashboard.py   ->  http://127.0.0.1:5000
"""
import atexit
import csv
import io
import json
import math
import shutil
import tempfile
from pathlib import Path

import joblib
import numpy as np
from flask import Flask, Response, jsonify, render_template, request, url_for

from predict import predict
from processing import ROOT
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
    """Final-model test metrics and cluster blurbs saved by training (None if untrained)."""
    info = {'model': None, 'clusters': {}, 'comparison': [], 'comparison_split': None}
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
        info['comparison_split'] = saved['split'] | {'shared': saved['models_share_test_set']}
    clusters = ROOT / 'models' / f'{source}_clusters.joblib'
    if clusters.exists():
        info['clusters'] = joblib.load(clusters).get('summaries', {})
    return info


BAR_FLOOR = .8  # comparison bars start at 0.80 so differences among strong models stay visible


def comparison_rows(saved):
    """Test-period rows of the saved model comparison, with bar widths for the chart."""
    rows = []
    for r in saved['models']:
        if r['period'] != 'test':
            continue
        bars = {k: max(0, round(100 * (r[k] - BAR_FLOOR) / (1 - BAR_FLOOR))) for k in ('precision', 'recall', 'f1')}
        rows.append({**r, 'bars': bars, 'final': r['role'].startswith('final')})
    return rows


def score_histogram(df, bins=10):
    """Counts of sessions per anomaly-score bin, with bar heights on a sqrt scale
    so the rare high-score bins stay visible next to the huge normal bin."""
    counts, edges = np.histogram(df.score, bins=bins, range=(0, 1))
    top = max(math.sqrt(counts.max()), 1)
    return [{'label': f'{edges[i]:.1f}-{edges[i + 1]:.1f}', 'count': int(c),
             'height': round(100 * math.sqrt(c) / top)} for i, c in enumerate(counts)]


def cluster_rows(df, summaries):
    """Flagged sessions of this upload grouped by anomaly cluster."""
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
    """Handle the POSTed upload. Returns an error message or None."""
    source, upload = request.form.get('source'), request.files.get('log')
    if source not in SOURCES or not upload:
        return 'Choose a supported source and a log file.'
    folder = tempfile.mkdtemp(prefix='logsentry-upload-')
    try:
        path = Path(folder) / 'upload.log'
        upload.save(path)
        df, audit, _ = predict(path, source, keep=False)
        print('Building disk index for session drill-down...', flush=True)
        build_index(path, Path(folder) / 'events.sqlite', source)
        cleanup()  # drop the previous upload
        STATE.update(df=df, audit=audit, events={}, upload_dir=folder, source=source)
    except Exception as e:
        shutil.rmtree(folder, ignore_errors=True)
        if not isinstance(e, (ValueError, FileNotFoundError, KeyError)):
            raise
        return str(e)
    return None


@app.route('/', methods=['GET', 'POST'])
def index():
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
    ready = [s for s in SOURCES if (ROOT / 'models' / f'{s}_final.joblib').exists()]
    info = load_model_info(STATE['source'] or (ready[0] if ready else None))

    if df is not None:
        total = len(df)
        flagged = int((df.decision == 'ANOMALY').sum())
        view = df
        if q:
            view = view[view.session_id.str.contains(q, regex=False)]
        if only:
            view = view[view.decision == 'ANOMALY']
        matching = len(view)
        pages = max(1, math.ceil(matching / PAGE_SIZE))
        try:
            page = max(1, min(pages, int(request.args.get('page', 1))))
        except ValueError:
            page = 1
        column = {'score': 'score', 'events': 'n_events', 'id': 'session_id'}.get(sort, 'score')
        start = (page - 1) * PAGE_SIZE
        rows = view.sort_values(column, ascending=column == 'session_id').iloc[start:start + PAGE_SIZE].to_dict('records')
        flag = '1' if only else '0'
        if page > 1:
            prev_url = url_for('index', q=q, sort=sort, anomalies=flag, page=page - 1)
        if page < pages:
            next_url = url_for('index', q=q, sort=sort, anomalies=flag, page=page + 1)

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
                           clusters=clusters, model=info['model'], comparison=info['comparison'], comparison_split=info['comparison_split'])


@app.errorhandler(413)
def too_large(e):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=False, error='File exceeds the 4 GB upload limit.'), 413
    return 'File exceeds the 4 GB upload limit.', 413


@app.route('/export')
def export():
    """Stream the per-session results as CSV."""
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
    app.run(host='127.0.0.1', port=5000, debug=False)
