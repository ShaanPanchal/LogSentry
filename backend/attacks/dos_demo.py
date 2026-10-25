r"""Denial-of-service demo against a running backend (Section 2.7). Attack only your own machine.

1. Sends one deliberately expensive log (as large as the upload limit allows) and, while it runs, times GET requests,
   to show that other users are still answered promptly.
2. Fires many expensive uploads at once and counts how many are accepted (201) and refused (503).

Run it twice from the repository root, with the server restarted in between:

    without the defence:  set LOGSENTRY_MAX_CONCURRENT_ANALYSES=1000   (PowerShell: $env:LOGSENTRY_MAX_CONCURRENT_ANALYSES=1000)
    with the defence:     unset it (default 2)
    then:                 backend\.venv\Scripts\python backend\attacks\dos_demo.py [--flood 12]
"""
import argparse
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _client import post_log, request, SAMPLE_HDFS, big_hdfs_log  # noqa: E402

MAX_UPLOAD_BYTES = 5 * 1024 * 1024      # backend/app/config.py default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base-url', default='http://127.0.0.1:8000')
    ap.add_argument('--flood', type=int, default=12, help='expensive uploads sent at the same time')
    args = ap.parse_args()

    status, data, _, _ = post_log(args.base_url, SAMPLE_HDFS.read_bytes())
    if status != 201:
        sys.exit(f'Server not ready: POST of the sample returned {status} {data}')
    probe = f'/api/analyses/{data["analysis_id"]}'
    big = big_hdfs_log(MAX_UPLOAD_BYTES)
    print(f'Expensive log: {len(big) / 1e6:.2f} MB')

    # ---- 1. one expensive request: are other requests still answered promptly?
    baseline = [request(args.base_url, 'GET', probe)[2] for _ in range(10)]
    result = {}
    worker = threading.Thread(target=lambda: result.update(r=post_log(args.base_url, big)))
    worker.start()
    during = []
    while worker.is_alive():
        during.append(request(args.base_url, 'GET', probe)[2])
        time.sleep(0.05)
    worker.join()
    s, _, cost, _ = result['r']
    print(f'\n1. One expensive upload: status {s}, took {cost:.2f} s')
    print(f'   GET latency before: median {1000 * statistics.median(baseline):.0f} ms')
    print(f'   GET latency during: median {1000 * statistics.median(during):.0f} ms, '
          f'max {1000 * max(during):.0f} ms ({len(during)} requests)')

    # ---- 2. many expensive requests at once
    results = {}

    def probe_loop(stop):
        times = []
        while not stop.is_set():
            times.append(request(args.base_url, 'GET', probe, timeout=300)[2])
            time.sleep(0.05)
        results['probe'] = times

    stop = threading.Event()
    prober = threading.Thread(target=probe_loop, args=(stop,))
    prober.start()
    t0 = time.perf_counter()
    with ThreadPoolExecutor(args.flood) as pool:
        replies = list(pool.map(lambda _: post_log(args.base_url, big), range(args.flood)))
    total = time.perf_counter() - t0
    stop.set()
    prober.join()
    counts = {}
    for r in replies:
        counts[r[0]] = counts.get(r[0], 0) + 1
    refused = [r[2] for r in replies if r[0] == 503]
    probe_times = results['probe'] or [0]
    print(f'\n2. {args.flood} expensive uploads at once: finished in {total:.1f} s')
    print('   statuses: ' + ', '.join(f'{k}: {v}' for k, v in sorted(counts.items())))
    if refused:
        print(f'   503 answered in median {1000 * statistics.median(refused):.0f} ms')
    print(f'   GET latency meanwhile: median {1000 * statistics.median(probe_times):.0f} ms, '
          f'max {1000 * max(probe_times):.0f} ms')


if __name__ == '__main__':
    main()
