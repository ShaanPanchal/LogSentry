"""The unsafe-file-upload defence (Assignment 3, Section 2.7).

Three checks, in the order the endpoint applies them:
1. check_filename: the submitted name must be a plain .log/.txt file name, never a path. It is only checked, never
   used: the file is saved under a name the server generates, in a private temporary folder (save_upload).
2. save_upload: the file is copied in chunks and refused with 413 as soon as it passes MAX_UPLOAD_BYTES. (The
   request as a whole is also capped while it streams in, by BodyLimitMiddleware in main.py.)
3. check_content: the extension and the Content-Type header are not trusted. The bytes must be UTF-8 text with no
   binary signature, NUL or control characters, and most lines must have the selected source's log line format.
"""
import os
import re
import tempfile

from . import config


class UploadRejected(Exception):
    """An upload that must be refused. `message` is written for the user and is safe to send."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status, self.message = status, message


# ---------------------------------------------------------------------------- 1. filename
_CONTROL = re.compile(r'[\x00-\x1f\x7f-\x9f]')                 # NUL, other C0 controls, DEL, C1 controls
_DRIVE_OR_UNC = re.compile(r'^(?:[A-Za-z]:|\\\\|//)')           # C:...  \\server\share  //server/share
# Letters, digits and a few punctuation marks seen in ordinary file names, e.g. "sample_HDFS (1).log".
# The first character may not be a dot, space or hyphen (hidden files, option-like names).
_ALLOWED_NAME = re.compile(r'^[A-Za-z0-9_(\[][A-Za-z0-9 ._()\[\]+,@=-]*$')


def check_filename(name: str) -> None:
    """Refuse anything that is not a plain, permitted .log/.txt file name."""
    if not name:
        raise UploadRejected(400, 'The uploaded file has no name.')
    if _CONTROL.search(name):
        raise UploadRejected(400, 'The file name contains control characters.')
    if '/' in name or '\\' in name or _DRIVE_OR_UNC.match(name) or '..' in name:
        raise UploadRejected(400, 'The file name must be a plain file name, not a path.')
    if len(name) > config.MAX_FILENAME_LENGTH:
        raise UploadRejected(400, f'The file name is longer than {config.MAX_FILENAME_LENGTH} characters.')
    if not _ALLOWED_NAME.match(name):
        raise UploadRejected(400, 'Use only letters, digits, spaces and . _ - ( ) [ ] + , @ = in the file name.')
    if not name.lower().endswith(config.ALLOWED_EXTENSIONS):
        raise UploadRejected(415, 'Upload a .log or .txt file.')


# ---------------------------------------------------------------------------- 2. saving
_CHUNK = 64 * 1024


def save_upload(source_file, folder: str) -> str:
    """Copy the upload into `folder` under a generated name. Returns the path. The caller must delete it."""
    # The folder is made at startup, but a temp-folder cleaner (e.g. Windows Storage Sense) may remove it while the
    # server runs. Recreate it, readable by this user only, rather than fail.
    os.makedirs(folder, mode=0o700, exist_ok=True)
    fd, path = tempfile.mkstemp(prefix='upload-', suffix='.log', dir=folder)
    written = 0
    try:
        with os.fdopen(fd, 'wb') as out:
            while chunk := source_file.read(_CHUNK):
                written += len(chunk)
                if written > config.MAX_UPLOAD_BYTES:
                    raise UploadRejected(413, f'The file is larger than {config.MAX_UPLOAD_BYTES // (1024 * 1024)} MiB.')
                out.write(chunk)
    except BaseException:
        os.remove(path)        # nothing is left behind if the copy fails or is refused
        raise
    return path


# ---------------------------------------------------------------------------- 3. content
# File types that are sometimes renamed .log. Checked on the first bytes, whatever the name or header says.
_SIGNATURES = [
    (b'\x1f\x8b', 'gzip'), (b'PK\x03\x04', 'zip'), (b'PK\x05\x06', 'zip'), (b'7z\xbc\xaf\x27\x1c', '7-Zip'),
    (b'Rar!', 'RAR'), (b'BZh', 'bzip2'), (b'\xfd7zXZ\x00', 'xz'), (b'%PDF', 'PDF'), (b'\x89PNG', 'PNG'),
    (b'\xff\xd8\xff', 'JPEG'), (b'GIF8', 'GIF'), (b'\x7fELF', 'ELF executable'), (b'MZ', 'Windows executable'),
    (b'\xff\xfe', 'UTF-16 text'), (b'\xfe\xff', 'UTF-16 text'),
]
_TEXT_CONTROL = re.compile(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]')   # controls other than tab, newline, carriage return
# The line layout of each source, as in the A2 datasets (see src/sources.py for the A2 parser).
#   HDFS: 081109 203518 143 INFO dfs.DataNode$PacketResponder: <message>
#   BGL:  - 1117838570 2005.06.03 R02-M1-N0-C:J12-U11 2005-06-03-15.42.50.675872 R02-M1-N0-C:J12-U11 RAS KERNEL INFO <message>
_LINE_FORMATS = {
    'HDFS': re.compile(r'^\d{6} \d{6} \d+ \w+ \S'),
    'BGL': re.compile(r'^\S+ \d+ \d{4}\.\d{2}\.\d{2} \S+ \d{4}-\d{2}-\d{2}-\d{2}\.\d{2}\.\d{2}\.\d+ \S+ \S+ \S+ \S+'),
}


def check_content(path: str, source: str) -> None:
    """Refuse files that are not UTF-8 text logs of the selected source. Reads at most MAX_UPLOAD_BYTES."""
    with open(path, 'rb') as f:
        data = f.read(config.MAX_UPLOAD_BYTES + 1)
    if not data.strip():
        raise UploadRejected(422, 'The file is empty.')
    for magic, kind in _SIGNATURES:
        if data.startswith(magic):
            raise UploadRejected(415, f'This is a {kind} file, not a text log.')
    if b'\x00' in data:
        raise UploadRejected(415, 'The file contains binary data (NUL bytes), not text.')
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        raise UploadRejected(415, 'The file is not UTF-8 text.') from None
    if _TEXT_CONTROL.search(text):
        raise UploadRejected(415, 'The file contains control characters, not plain text.')

    lines = [line for line in text.removeprefix('\ufeff').splitlines() if line.strip()]
    valid = sum(1 for line in lines if _LINE_FORMATS[source].match(line))
    if valid / len(lines) < config.MIN_VALID_LINE_SHARE:
        raise UploadRejected(422, f'This does not look like a {source} log: only {valid} of {len(lines)} lines have the '
                                  f'{source} log format. Check that the selected source matches the file.')
