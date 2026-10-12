"""Settings and paths. Limits can be overridden with environment variables."""
import os
from pathlib import Path

# backend/app/config.py -> repository root is two levels above backend/
REPO_ROOT = Path(__file__).resolve().parents[2]
A2_SRC = REPO_ROOT / 'src'          # the Assignment 2 pipeline, reused unchanged
MODELS_DIR = REPO_ROOT / 'models'

SOURCES = ('HDFS', 'BGL')
ALLOWED_EXTENSIONS = ('.log', '.txt')

# Basic request-size limit for the first version of the endpoint. 5 MiB is about 12x the supplied
# sample logs (~0.4 MB). Detailed upload and cost limits are a later stage.
MAX_UPLOAD_BYTES = int(os.environ.get('LOGSENTRY_MAX_UPLOAD_BYTES', 5 * 1024 * 1024))
