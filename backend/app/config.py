"""Settings and paths. Limits can be overridden with environment variables."""
import os
from pathlib import Path

# backend/app/config.py -> repository root is two levels above backend/
REPO_ROOT = Path(__file__).resolve().parents[2]
A2_SRC = REPO_ROOT / 'src'          # the Assignment 2 pipeline, reused unchanged
MODELS_DIR = REPO_ROOT / 'models'

SOURCES = ('HDFS', 'BGL')
ALLOWED_EXTENSIONS = ('.log', '.txt')

# The one origin (scheme + host + port) of the React front end that may read API responses. Never "*".
FRONTEND_ORIGIN = os.environ.get('LOGSENTRY_FRONTEND_ORIGIN', 'http://localhost:5173')

# The session detail view returns at most this many log lines per session (the rest are counted, not sent).
MAX_EVENTS_PER_SESSION = 200

# ---- Denial-of-service defence (Section 2.7). ----
# Analyses allowed to run at the same time; any more are refused at once with 503 instead of queueing. Scoring is
# CPU-bound, so a small number keeps the GET endpoints (and the analyses already running) fast on a laptop.
MAX_CONCURRENT_ANALYSES = int(os.environ.get('LOGSENTRY_MAX_CONCURRENT_ANALYSES', 2))

# ---- Response-size side-channel defence (Section 2.8). ----
# On: responses are padded with trailing spaces so their size does not depend on the decision. An analysis is padded
# to a size fixed by its session count; a session detail to the size of its longest possible outcome.
# Off only to measure the attack (backend/attacks/size_attack.py).
UNIFORM_SIZE = os.environ.get('LOGSENTRY_UNIFORM_SIZE', '1') != '0'
SIZE_PAD_BASE_BYTES = 2048          # room for the summary and parse audit
SIZE_PAD_PER_SESSION_BYTES = 256    # room for one session in the list (a real one is about 150)

# ---- Upload limits (the unsafe-file-upload defence, Section 2.7). All upload limits live here. ----
# Largest log file accepted. 5 MiB is about 12x the supplied sample logs (~0.4 MB). Provisional.
MAX_UPLOAD_BYTES = int(os.environ.get('LOGSENTRY_MAX_UPLOAD_BYTES', 5 * 1024 * 1024))
# A multipart request is larger than the file inside it (boundaries, part headers, the `source` field). The whole
# request may exceed the file limit by this much; the file itself is then checked against MAX_UPLOAD_BYTES exactly.
MULTIPART_OVERHEAD_BYTES = 64 * 1024
MAX_REQUEST_BYTES = MAX_UPLOAD_BYTES + MULTIPART_OVERHEAD_BYTES
# Longest filename accepted (characters).
MAX_FILENAME_LENGTH = 100
# Share of non-blank lines that must have the selected source's line format. In the full A2 datasets every line
# parsed (HDFS 11,175,629 of 11,175,629; BGL 4,747,963 of 4,747,963; results/*_parse_audit.json), but the format
# patterns in upload_safety.py are stricter than the A2 parser and have only been checked against the sample logs.
MIN_VALID_LINE_SHARE = 0.9
