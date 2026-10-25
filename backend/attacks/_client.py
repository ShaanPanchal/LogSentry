"""Tiny standard-library HTTP client shared by the attack scripts. Local test utility, not application code."""
import http.client
import json
import re
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_HDFS = REPO_ROOT / 'data' / 'supporting' / 'sample_HDFS.log'


def request(base_url, method, path, body=b'', headers=None, timeout=120):
    """Send one request on a fresh connection. Returns (status, parsed JSON or None, seconds, response bytes)."""
    u = urlsplit(base_url)
    conn = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=timeout)
    try:
        t0 = time.perf_counter()
        conn.request(method, path, body=body, headers=headers or {})
        resp = conn.getresponse()
        raw = resp.read()
        elapsed = time.perf_counter() - t0
    finally:
        conn.close()
    try:
        data = json.loads(raw) if raw else None
    except ValueError:
        data = None
    return resp.status, data, elapsed, len(raw)


def post_log(base_url, content: bytes, source='HDFS', filename='attack.log'):
    boundary = uuid.uuid4().hex
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="source"\r\n\r\n{source}\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            'Content-Type: text/plain\r\n\r\n').encode() + content + f'\r\n--{boundary}--\r\n'.encode()
    return request(base_url, 'POST', '/api/analyses', body,
                   {'Content-Type': f'multipart/form-data; boundary={boundary}'})


def big_hdfs_log(max_bytes: int) -> bytes:
    """A valid HDFS log just under `max_bytes`: the sample repeated, each copy one day later with renamed blocks."""
    lines = SAMPLE_HDFS.read_bytes().decode().splitlines()
    out, size, day = [], 0, 0
    while True:
        copy = []
        for line in lines:
            stamp = datetime.strptime(line[:6], '%y%m%d') + timedelta(days=day)
            line = stamp.strftime('%y%m%d') + re.sub(r'blk_(-?)(\d+)', rf'blk_\g<1>{day + 1}\g<2>', line[6:])
            copy.append(line + '\n')
        chunk = ''.join(copy).encode()
        if size + len(chunk) > max_bytes:
            return b''.join(out)
        out.append(chunk)
        size += len(chunk)
        day += 1
