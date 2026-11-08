// The one place front-end settings live.

// Where the FastAPI back end runs. Change it here only (the back end's CORS setting must allow this page's origin).
export const API_BASE_URL = 'http://127.0.0.1:8000';

// Same as the back end's upload limit (LOGSENTRY_MAX_UPLOAD_BYTES, 5 MiB by default). This is only used to warn
// the user early. The back end enforces the real limit.
export const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;

export const SOURCES = [
  { value: 'HDFS', label: 'HDFS (Hadoop file system logs)' },
  { value: 'BGL', label: 'BGL (Blue Gene/L supercomputer logs)' },
];
