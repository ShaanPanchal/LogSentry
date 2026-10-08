"""One-time pipeline: download -> verify -> sort -> process -> (train).

    python setup_data.py --source HDFS              # everything
    python setup_data.py --source HDFS --process-only   # stop after the processed dataset

Steps
1. Download the Loghub archive from Zenodo into data/raw/ and verify its MD5.
2. Extract the raw log (and, for HDFS, the per-block labels).
3. Sort the log chronologically (external merge sort, constant memory) - the
   session features and the temporal split both require time order.
4. processing.process() builds the session feature table and it is written to
   data/processed/<SOURCE>_sessions.csv.gz  (the dataset the model trains on).
5. train.train() fits the classifiers, clusters the anomalies and writes
   models/ and results/.
If data/processed/<SOURCE>_sessions.csv.gz already exists, steps 1-4 are skipped.
"""
import argparse
import hashlib
import heapq
import json
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))

from processing import ARCHIVES, PROCESSED_DIR, RAW_DIR, bucket_inventory, process, sorted_log_path  # noqa: E402

ZENODO = 'https://zenodo.org/records/8196385/files/{archive}.zip'
# source -> (MD5 of the archive, files to extract)
SOURCES = {
    'HDFS': ('76a24b4d9a6164d543fb275f89773260', ['HDFS.log', 'preprocessed/anomaly_label.csv']),
    'BGL': ('4452953c470f2d95fcb32d5f6e733f7a', ['BGL.log']),
}
CHUNK_LINES = 100000


def sort_key(line, source):
    """Chronological key: HDFS 'yymmdd'+'HHMMSS', BGL unix seconds."""
    parts = line.split(None, 2)
    try:
        return int(parts[0] + parts[1]) if source == 'HDFS' else int(parts[1])
    except (ValueError, IndexError):
        return -1


def sort_file(path, out, source):
    """External merge sort: sort chunks in memory, then k-way merge them."""
    key = lambda line: sort_key(line, source)  # noqa: E731
    with tempfile.TemporaryDirectory(dir=path.parent) as temp:
        chunk_files, chunk = [], []

        def flush():
            chunk_path = Path(temp) / str(len(chunk_files))
            chunk_path.write_text(''.join(sorted(chunk, key=key)))
            chunk_files.append(chunk_path)
            chunk.clear()

        with path.open(encoding='utf-8', errors='replace') as f:
            for line in f:
                chunk.append(line if line.endswith('\n') else line + '\n')
                if len(chunk) >= CHUNK_LINES:
                    flush()
        if chunk:
            flush()
        streams = [p.open() for p in chunk_files]
        try:
            with out.open('w') as f:
                f.writelines(heapq.merge(*streams, key=key))
        finally:
            for s in streams:
                s.close()


def download_and_verify(archive, digest):
    zip_path = RAW_DIR / (archive + '.zip')
    if not zip_path.exists():
        print('Downloading', archive, 'from Zenodo. This may take several minutes.', flush=True)
        urllib.request.urlretrieve(ZENODO.format(archive=archive), zip_path)
    md5 = hashlib.md5()
    with zip_path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            md5.update(block)
    if md5.hexdigest() != digest:
        raise ValueError(f'Archive checksum mismatch. Delete {zip_path} and retry.')
    print('Checksum verified. Extracting required raw files.', flush=True)
    return zip_path


def build_processed_dataset(source):
    archive = ARCHIVES[source]
    digest, files = SOURCES[source]
    dest = RAW_DIR / archive
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = download_and_verify(archive, digest)
    with zipfile.ZipFile(zip_path) as z:
        for name in files:
            z.extract(name, dest)
    print('Sorting records chronologically...', flush=True)
    sort_file(dest / files[0], sorted_log_path(source), source)
    labels = dest / files[1] if source == 'HDFS' else None
    print('Building sessions and features...', flush=True)
    df, audit, _ = process(sorted_log_path(source), source, labels)
    out = PROCESSED_DIR / f'{source}_sessions.csv.gz'
    df.to_csv(out, index=False, float_format='%.8g')
    (ROOT / 'results' / f'{source}_parse_audit.json').write_text(json.dumps(audit, indent=2))
    print(f'Wrote {out} ({len(df):,} sessions)', flush=True)
    write_bucket_inventory(source)


def write_bucket_inventory(source):
    """results/<SOURCE>_event_buckets.json: what each event_hash_NN feature counts."""
    print('Building event-bucket inventory...', flush=True)
    inventory = bucket_inventory(sorted_log_path(source), source)
    (ROOT / 'results' / f'{source}_event_buckets.json').write_text(json.dumps(inventory, indent=2))


def setup(source, process_only=False):
    for folder in (PROCESSED_DIR, RAW_DIR, ROOT / 'models', ROOT / 'results'):
        folder.mkdir(parents=True, exist_ok=True)
    if not (PROCESSED_DIR / f'{source}_sessions.csv.gz').exists():
        build_processed_dataset(source)
    elif not (ROOT / 'results' / f'{source}_event_buckets.json').exists() and sorted_log_path(source).exists():
        write_bucket_inventory(source)
    if process_only:
        return
    from train import train
    train(source)
    print('Ready. Start the dashboard with: python src/dashboard.py', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download, process and train.')
    parser.add_argument('--source', choices=list(SOURCES), default='HDFS')
    parser.add_argument('--process-only', action='store_true', help='stop after writing the processed dataset')
    args = parser.parse_args()
    setup(args.source, args.process_only)
