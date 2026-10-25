# Attack scripts (local test utilities, not application code)

Run from the repository root against a backend you started yourself. Attack only your own machine. Standard library only.

| Script | Defence it tests | Code under test |
|---|---|---|
| `dos_demo.py` | Denial of service (§2.7, Advanced) | `_analysis_slots` in `backend/app/routes.py`, `MAX_CONCURRENT_ANALYSES` in `config.py` |
| `size_attack.py` | **Response-size side channel (§2.8, the one to be marked)** | `_padded`, `_analysis_response`, `_detail_response` in `backend/app/routes.py`, `UNIFORM_SIZE` in `config.py` |

Each script's docstring explains how to switch its defence off for the "before" run.

## Results (25 Oct 2026, Windows laptop, one uvicorn worker)

**Denial of service**: one 4.84 MB HDFS log (just under the 5 MiB upload cap) takes about 1 s to analyse. 12 of them were sent at once while GET requests were timed:

| | Statuses | Flood finished | GET median | GET max |
|---|---|---|---|---|
| Without the defence (`LOGSENTRY_MAX_CONCURRENT_ANALYSES=1000`) | 12 × 201 | 9.6 s | 150 ms | 1402 ms |
| With the defence (cap 2) | 2 × 201, 10 × 503 (median 113 ms) | 1.6 s | 26 ms | 432 ms |

Cost: when more than 2 analyses are running, legitimate users also get a 503 and have to retry (`Retry-After: 5`).

**Response-size side channel**: 100 uploads per outcome of two logs with 20 sessions each. The threshold is fitted on the first half of the runs and tested on the second half, so 50% means guessing. Raw numbers are in `size_results.json`.

| | Normal log | Flagged log | Attack accuracy |
|---|---|---|---|
| Before (`LOGSENTRY_UNIFORM_SIZE=0`) | 3362 bytes | 3356 bytes | 100% |
| After (default) | 7168 bytes | 7168 bytes | 50% |

How it works: an analysis is padded with trailing spaces to `2048 + 256 × sessions` bytes, so its size reveals only the session count, which the sender already knows. A session detail is padded to the size it would have with the widest score and the longest cluster description (about 2 KB of the 1–2 KB difference). `backend/tests/test_size.py` flips the decision on the same session and checks that the size stays the same.
Cost: analysis responses are about twice as large (7168 vs 3362 bytes here), and session details carry up to about 2 KB of padding. Gzip must stay off, because compression would reintroduce a size difference.

**Why not timing:** we tried the timing side channel first. The back end runs the cluster model only when a session is flagged, which costs about 0.35 ms. Over HTTP, with 200 requests per outcome, attack accuracy was inconsistent (49% to 77% across 5 runs), because request jitter (about 14 to 32 ms) is far larger than the leak. We could not show a reliable leak, so we chose the response size, which leaks on every request.
