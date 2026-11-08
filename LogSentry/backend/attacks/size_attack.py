r"""Response-size side channel in the decision (Section 2.8). Attack only your own machine.

The attacker sees only the size of the traffic (HTTPS hides content, not length) and wants to know whether their log
was flagged. They send two logs: A has only normal sessions, B swaps one normal session
for a flagged one with the same number of lines. A threshold on the analysis response's size is fitted on the first
half of the runs and tested on the second half (50% = guessing).

The session-detail response is covered by backend/tests/test_size.py instead: two different sessions have different
log lines, so over HTTP their detail sizes would differ because of the input, not the decision. The test flips the
decision on the same session and checks that the size does not change.

From the repository root, with the server restarted in between:

    before:  $env:LOGSENTRY_UNIFORM_SIZE=0, start the server, run with --label before
    after:   Remove-Item Env:LOGSENTRY_UNIFORM_SIZE, start the server, run with --label after
    run:     backend\.venv\Scripts\python backend\attacks\size_attack.py --label before
Results are appended to backend/attacks/size_results.json.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _client import post_log, request, SAMPLE_HDFS  # noqa: E402

OUT = Path(__file__).resolve().parent / 'size_results.json'
N_SESSIONS = 20


def build_logs(base_url):
    status, data, _, _ = post_log(base_url, SAMPLE_HDFS.read_bytes())
    if status != 201:
        sys.exit(f'Server not ready: POST of the sample returned {status} {data}')
    lines = SAMPLE_HDFS.read_text(encoding='utf-8').splitlines(keepends=True)
    block = [m.group(0) if (m := re.search(r'blk_-?\d+', line)) else None for line in lines]
    sessions = data['sessions']
    normal = [s for s in sessions if not s['flagged']]
    flagged_by_size = {s['n_events']: s for s in sessions if s['flagged']}
    # A flagged session with the same line count as one of the normal ones, so the two logs have the same shape.
    swap = next(n for n in normal if n['n_events'] in flagged_by_size)
    flag = flagged_by_size[swap['n_events']]
    keep = [n['session_id'] for n in normal if n is not swap][:N_SESSIONS - 1]

    def log(ids):
        ids = set(ids)
        return ''.join(line for line, b in zip(lines, block) if b in ids).encode()

    return log(keep + [swap['session_id']]), log(keep + [flag['session_id']])


def best_threshold(sizes, labels):
    """The size cut-off (and direction) that best separates the two outcomes on the training runs."""
    best = (0.0, 0, True)
    for t in sorted(sizes):
        for larger_is_flagged in (True, False):
            acc = sum(((x > t) == larger_is_flagged) == y for x, y in zip(sizes, labels)) / len(sizes)
            best = max(best, (acc, t, larger_is_flagged))
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base-url', default='http://127.0.0.1:8000')
    ap.add_argument('--reps', type=int, default=100, help='uploads per outcome')
    ap.add_argument('--label', required=True, help='for example "before" or "after"')
    args = ap.parse_args()

    normal_log, flagged_log = build_logs(args.base_url)
    runs = []                                            # (is_flagged, response bytes)
    for _ in range(args.reps):
        for is_flagged, content in ((False, normal_log), (True, flagged_log)):
            status, data, _, size = post_log(args.base_url, content)
            assert status == 201 and (data['summary']['flagged_sessions'] > 0) == is_flagged, (status, data)
            runs.append((is_flagged, size))
            request(args.base_url, 'DELETE', f'/api/analyses/{data["analysis_id"]}')

    half = len(runs) // 2
    _, cut, larger = best_threshold([r[1] for r in runs[:half]], [r[0] for r in runs[:half]])
    test = runs[half:]
    accuracy = sum(((r[1] > cut) == larger) == r[0] for r in test) / len(test)
    result = {'label': args.label, 'reps_per_outcome': args.reps,
              'normal_bytes': sorted({r[1] for r in runs if not r[0]}),
              'flagged_bytes': sorted({r[1] for r in runs if r[0]}),
              'attack_accuracy': round(accuracy, 3)}
    print(json.dumps(result, indent=2))
    history = json.loads(OUT.read_text()) if OUT.exists() else []
    OUT.write_text(json.dumps(history + [result], indent=2) + '\n')


if __name__ == '__main__':
    main()
