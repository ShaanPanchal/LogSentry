"""One-time setup: download, check, sort, process and (optionally) train.

    python setup_data.py --source HDFS                 # everything
    python setup_data.py --source HDFS --process-only   # stop after the processed dataset
    python setup_data.py --source HDFS --raw-only       # only make the sorted raw log

Steps:
1. Download the Loghub zip from Zenodo into data/raw/ and check its MD5.
2. Extract the raw log (and the labels file for HDFS).
3. Sort the log by time. The sessions and the temporal split both need time order.
4. Build the session feature table and save it to data/processed/<SOURCE>_sessions.csv.gz.
5. Train the models, cluster the anomalies and write models/ and results/.
If the processed file already exists, steps 1 to 4 are skipped.
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

from processing import PROCESSED_DIR, RAW_DIR, bucket_inventory, process, sorted_log_path  # noqa: E402
from sources import SOURCES, get_source  # noqa: E402

ZENODO = 'https://zenodo.org/records/8196385/files/{archive}.zip'
CHUNK_LINES = 100000
DOWNLOAD_ATTEMPTS = 4


def sort_file(path, out, source):
    """Sort a big file in chunks, then merge the sorted chunks (external merge sort)."""
    # The raw log is too big to sort in memory. So sort it in chunks, save each chunk,
    # then merge the sorted chunks into one file.
    key = get_source(source).sort_key  # chronological key for this source's line format
    with tempfile.TemporaryDirectory(dir=path.parent) as temp:
        chunk_files, chunk = [], []

        def flush():
            chunk_path = Path(temp) / str(len(chunk_files))
            chunk_path.write_text(''.join(sorted(chunk, key=key)), encoding='utf-8')
            chunk_files.append(chunk_path)
            chunk.clear()

        with path.open(encoding='utf-8', errors='replace') as f:
            for line in f:
                chunk.append(line if line.endswith('\n') else line + '\n')
                if len(chunk) >= CHUNK_LINES:
                    flush()
        if chunk:
            flush()
        streams = [p.open(encoding='utf-8') for p in chunk_files]
        try:
            with out.open('w', encoding='utf-8') as f:
                f.writelines(heapq.merge(*streams, key=key))
        finally:
            for s in streams:
                s.close()


def download_and_verify(archive, digest):
    zip_path = RAW_DIR / (archive + '.zip')
    if not zip_path.exists():
        print('Downloading', archive, 'from Zenodo. This may take several minutes.', flush=True)
        part = zip_path.with_suffix('.part')  # only renamed once complete, so a dropped connection can't leave a bad zip
        for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
            try:
                urllib.request.urlretrieve(ZENODO.format(archive=archive), part)
                part.replace(zip_path)
                break
            except OSError as e:  # includes ContentTooShortError
                print(f'Download attempt {attempt}/{DOWNLOAD_ATTEMPTS} failed: {e}', flush=True)
                if attempt == DOWNLOAD_ATTEMPTS:
                    raise
    md5 = hashlib.md5()
    with zip_path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            md5.update(block)
    if md5.hexdigest() != digest:
        raise ValueError(f'Archive checksum mismatch. Delete {zip_path} and retry.')
    print('Checksum verified. Extracting required raw files.', flush=True)
    return zip_path


def prepare_raw(source):
    """Download, check, extract and sort the raw log. Returns the labels file path (HDFS only)."""
    spec = get_source(source)
    archive, digest, files = spec.archive, spec.md5, spec.files
    dest = RAW_DIR / archive
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = download_and_verify(archive, digest)
    with zipfile.ZipFile(zip_path) as z:
        for name in files:
            z.extract(name, dest)
    print('Sorting records chronologically...', flush=True)
    sort_file(dest / files[0], sorted_log_path(source), source)
    return dest / files[1] if len(files) > 1 else None  # separate label file (HDFS only)


def build_processed_dataset(source):
    labels = prepare_raw(source)
    print('Building sessions and features...', flush=True)
    df, audit, _ = process(sorted_log_path(source), source, labels)
    out = PROCESSED_DIR / f'{source}_sessions.csv.gz'
    # Numbers are saved with 8 significant digits to keep the file small.
    # This can change a score by a tiny amount (see README).
    df.to_csv(out, index=False, float_format='%.8g')
    (ROOT / 'results' / f'{source}_parse_audit.json').write_text(json.dumps(audit, indent=2))
    print(f'Wrote {out} ({len(df):,} sessions)', flush=True)
    write_bucket_inventory(source)


def write_bucket_inventory(source):
    """Save what each event_hash_NN feature counts to results/<SOURCE>_event_buckets.json."""
    print('Building event-bucket inventory...', flush=True)
    inventory = bucket_inventory(sorted_log_path(source), source)
    (ROOT / 'results' / f'{source}_event_buckets.json').write_text(json.dumps(inventory, indent=2))


def setup(source, process_only=False, raw_only=False):
    for folder in (PROCESSED_DIR, RAW_DIR, ROOT / 'models', ROOT / 'results'):
        folder.mkdir(parents=True, exist_ok=True)
    if raw_only:  # only (re)create the sorted raw log, e.g. for cluster example events
        prepare_raw(source)
        return
    if not (PROCESSED_DIR / f'{source}_sessions.csv.gz').exists():
        build_processed_dataset(source)
    # The dataset exists but the bucket inventory does not, so only rebuild the inventory.
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
    parser.add_argument('--raw-only', action='store_true', help='only download/sort the raw log (no processing or training)')
    args = parser.parse_args()
    setup(args.source, args.process_only, args.raw_only)
