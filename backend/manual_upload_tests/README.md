# Manual upload-security test kit

A repeatable way to check the unsafe-file-upload defence by hand, against a **running** LogSentry backend. The defence
is in `backend/app/upload_safety.py`, and the request-size limit is in `BodyLimitMiddleware` in `backend/app/main.py`.

This is a **local test utility, not production application code**. Nothing in `backend/app/` imports it. The pytest
suite does not collect it: `backend/pytest.ini` only looks in `tests/`. It never starts, stops or reconfigures the server. It only writes inside its own temporary folder
(`logsentry-manual-upload-*` in the system temp folder), which is deleted when the run ends.

## Contents

| Path | What it is |
|---|---|
| `run_upload_tests.py` | The runner. It sends each case to `POST /api/analyses` over a plain socket and prints a PASS/FAIL table. It uses only the Python standard library. |
| `fixtures/valid_hdfs.log` | First 120 lines of `data/supporting/sample_HDFS.log` (17 KB). Accepted, 12 sessions. |
| `fixtures/valid_bgl.log` | First 120 lines of `data/supporting/sample_BGL.log` (19 KB). Accepted, 5 sessions. |
| `fixtures/empty.log` | 0 bytes. |
| `fixtures/wrong_extension.exe` | Two lines of harmless plain text, named `.exe`. |
| `fixtures/png_renamed.log` | A PNG signature and IHDR header followed by harmless bytes. It is not a real image. |
| `fixtures/hdfs_content_for_bgl_source.log` | Lines 121 to 150 of the HDFS sample. The runner sends it with `source=BGL`. |
| `fixtures/bgl_content_for_hdfs_source.log` | Lines 121 to 150 of the BGL sample. The runner sends it with `source=HDFS`. |
| `fixtures/malformed_lines.log` | 5 real HDFS lines followed by 25 lines of plain text in no log format. Only 17% of lines are valid, and 90% are needed. |
| `fixtures/.gitattributes` | Stops git from converting line endings in the fixtures. |

The oversized files are **not stored** in the repository. The runner generates them in its temporary folder at run
time and deletes them afterwards. They are the valid fixture's harmless log lines, repeated:

- `oversized_file.log` is `MAX_UPLOAD_BYTES + 1` bytes (5,242,881).
- `oversized_request.log` is 1 MiB more than the whole-request limit.

All fixtures are small extracts of the sample logs already in the repository. None of them is a raw dataset or private data.

## Prerequisites

- The backend virtual environment with `backend/requirements.txt` installed: `backend\.venv`. The kit needs no extra packages.
- A running backend. In a separate terminal, from the repository root:

  ```powershell
  cd backend
  .venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
  ```

  Wait until uvicorn prints `Application startup complete` (the models load at startup).

## Running it

From the repository root:

```powershell
backend\.venv\Scripts\python backend\manual_upload_tests\run_upload_tests.py
```

Options:

| Option | Meaning |
|---|---|
| `--base-url URL` | The server to test. The default is `http://127.0.0.1:8000`, the address `frontend/src/config.js` uses. |
| `--source HDFS\|BGL` | The source used for the filename, size, malformed-lines and recovery cases. The default is HDFS. The two valid-log and two wrong-source cases always use their own fixed source. |
| `--max-upload-bytes N` | Only needed if the server was started with a non-default `LOGSENTRY_MAX_UPLOAD_BYTES`. By default the limits are read from `backend/app/config.py`. |
| `--timeout S` | How many seconds to wait for each reply. The default is 60. |
| `--verbose` | Also show the server's `error`/`detail` (or `analysis_id`) for passing cases. |
| `--keep-analyses` | Keep the analyses this run created. By default they are removed with `DELETE /api/analyses/{id}` at the end. |
| `--dry-run` | List the cases and show how the multipart parser treats each filename, without sending anything. |

## Reading the output

Each row shows the test, the expected and actual HTTP status, and the result:

- **PASS**: the status matched. For a refusal, the body also had exactly `{"error": "...", "detail": "..."}`, the
  `error` code matched the status (`bad_request`, `payload_too_large`, `unsupported_media_type` or `invalid_input`),
  and the `detail` gave the expected reason, so the file was refused for the right reason. For an acceptance, the
  body held an `analysis_id`.
- **FAIL**: the server answered, but not as expected. The line below the row shows what it said instead.
- **ERROR**: no reply could be obtained, for example because the connection was refused or reset, or timed out. This is never
  counted as a pass.

Before any case runs, the runner checks that `GET /openapi.json` lists `/api/analyses`. If the server is down, or
something else is on that port, it prints `SERVER UNAVAILABLE`, runs nothing and exits with code 2.

After the table it prints:

- the outcome of the Windows drive and UNC filename cases, and the name each one arrives as at the application;
- a read-only look at the server's private upload folders (`logsentry-uploads-*` in the temp folder). They should
  contain 0 files. Nothing there is ever deleted by the runner. This check is informational and does not change the
  exit code;
- how many of the analyses it created were deleted.

**Exit codes:**

| Code | Meaning |
|---|---|
| 0 | Every case passed. |
| 1 | At least one case failed: a genuine difference from the expected behaviour. |
| 2 | The server could not be reached, or at least one case ended in a network error. The defence was not fully verified. |

If a run has both failures and network errors, the exit code is 1.

## Expected outcomes

These were all observed against a local server on 2026-10-13: 30 of 30 passed with `--source HDFS`, and again with
`--source BGL`.

| # | Case | Expected | Why |
|---|---|---|---|
| 1 | valid HDFS log, source HDFS | 201 | Passes every check and is scored. |
| 2 | valid BGL log, source BGL | 201 | Same. |
| 3 | empty file | 422 | `The file is empty.` |
| 4 | text file named `.exe` | 415 | `Upload a .log or .txt file.` The extension is checked first. |
| 5 | PNG bytes renamed `.log` | 415 | `This is a PNG file, not a text log.` The extension and Content-Type are not trusted. |
| 6 | HDFS log sent with source BGL | 422 | `This does not look like a BGL log: only 0 of 30 lines ...` |
| 7 | BGL log sent with source HDFS | 422 | `This does not look like a HDFS log: only 0 of 30 lines ...` |
| 8 | mostly malformed lines | 422 | Only 5 of 30 lines are in the format (90% needed). |
| 9 | file of limit + 1 bytes | 413 | `The file is larger than 5 MiB.` The whole request is under the request limit, so the file is caught while it is copied. |
| 10 | request over the request limit | 413 | `Request body is too large.` The middleware refuses it on the declared Content-Length, before reading the body. |
| 11 | `../evil.log` | 400 | `The file name must be a plain file name, not a path.` |
| 12, 13 | `..\evil.log` (escaped, raw) | 400 | Same. |
| 14 | `../../outside.log` | 400 | Same. |
| 15 | `subfolder/evil.log` | 400 | Same. |
| 16, 17 | `subfolder\evil.log` (escaped, raw) | 400 | Same. |
| 18 | `C:evil.log` | 400 | Same (drive prefix). |
| 19 | `C:/Windows/evil.log` | 400 | Same. |
| 20 | `//server/share/evil.log` | 400 | Same (UNC prefix with forward slashes). |
| 21, 22 | `C:\Windows\evil.log` (escaped, raw) | **201** | Known limitation, see below. It arrives as `evil.log`. |
| 23 | `\\server\share\evil.log` (escaped) | **201** | Known limitation, see below. It arrives as `evil.log`. |
| 24 | `\\server\share\evil.log` (raw) | 400 | It arrives as `\server\share\evil.log` and is refused as a path. |
| 25 | `sample;whoami\|more&$(id).log` | 400 | `Use only letters, digits, spaces and ...` The name is never executed or used as a path, but it is refused anyway. |
| 26 | `sample<ESC>[31m.log` | 400 | `The file name contains control characters.` |
| 27 | `sample<NUL>.log` | 400 | Same. |
| 28 | `sample_HDFS (1).log` (or `sample_BGL (1).log`) | 201 | An ordinary name with a space and brackets is accepted. |
| 29 | valid upload after all the rejections | 201 | The application is still usable. |
| 30 | `GET` of that analysis | 200 | The stored result can be read back. |

**Escaped and raw filenames.** The runner writes each filename byte-for-byte into the multipart
`Content-Disposition` header. It does not use an HTTP client library, which could rewrite the name. Only for names that contain a
backslash, it sends two encodings, because python-multipart treats them differently:

- *escaped*: each `\` is written as `\\`. httpx (used by the pytest `TestClient`) and urllib3/requests do this.
- *raw*: `\` is written as it is. Browsers do this (WHATWG multipart/form-data encoding).

The control characters in cases 26 and 27 are also sent unchanged as raw bytes. A probe that recorded the name the
application received confirmed that they arrive intact, so the control-character rule is what refuses them.

## Known limitation: Windows drive and UNC names with backslashes

On Windows these names cannot be created as files, so the kit does not try. Instead it uploads `valid_hdfs.log` (or
`valid_bgl.log`) and sets only the multipart filename to the exact string.

python-multipart 0.0.31 (`python_multipart/multipart.py`, `parse_options_header`) changes the filename **before
FastAPI or LogSentry see it**:

1. It un-escapes the quoted value: `\\` becomes `\`.
2. Then it applies an old Internet Explorer 6 workaround. If the value starts with `X:\` or `\\`, it keeps only the
   text after the last backslash.

Observed results:

| Multipart filename sent | Encoding | Arrives at the app as | HTTP status |
|---|---|---|---|
| `C:\Windows\evil.log` | escaped | `evil.log` | **201, accepted** |
| `C:\Windows\evil.log` | raw | `evil.log` | **201, accepted** |
| `\\server\share\evil.log` | escaped | `evil.log` | **201, accepted** |
| `\\server\share\evil.log` | raw | `\server\share\evil.log` | 400, refused |

So the application **does not reject** `C:\Windows\evil.log` in either encoding, or the escaped
`\\server\share\evil.log`. It never receives the path text, so `check_filename` cannot see it. When
`check_filename` is called directly, it refuses both forms with 400 (`test_filename_check_unit_cases`).

The accepted uploads are still harmless:

- The path part was removed before the application ran.
- The uploaded file is never stored under the client's name. `save_upload` writes it to a server-generated
  `upload-*.log` in the private temporary folder and deletes it after scoring.
- No path is ever built from the filename.

The automated test `test_backslash_drive_and_unc_paths_are_cut_to_a_plain_name_by_the_multipart_parser` pins the
escaped behaviour. The runner's "arrives as" column is computed locally with the python-multipart installed in the
interpreter running the kit. Run the kit with `backend\.venv\Scripts\python` so it matches the server's version.

## What is covered where

| Behaviour | Live API (this kit) | Automated only (`backend/tests/`) |
|---|---|---|
| Valid HDFS/BGL uploads, empty file, wrong extension, PNG renamed `.log`, wrong source, malformed lines | yes | also covered |
| File one byte over the limit; request over the limit, refused on Content-Length | yes | also covered |
| Chunked body without Content-Length; understated Content-Length; invalid Content-Length | no | `test_upload_defence.py`, `test_upload_live.py` |
| File of exactly the limit is not refused for size | no | `test_file_at_the_limit_is_not_refused_for_size` |
| Path, drive, UNC, shell-character and control-character filenames | yes | also covered |
| Which name the server actually received (proof the crafted name arrived) | parser view only (computed locally) | `received_names` fixture in `test_upload_defence.py` |
| Refused uploads never reach the model | no | `pipeline_calls` fixture |
| Temporary file deleted after a refusal or a **model failure** | read-only folder check only | `nothing_left_behind` (autouse) and `test_temporary_file_is_removed_when_the_model_fails` |
| Upload stored under a generated name in the private folder | no | `test_upload_is_stored_under_a_generated_name_in_the_private_folder` |
| Upload folder recreated if a temp cleaner removed it | no | `test_upload_folder_is_recreated_if_a_temp_cleaner_deleted_it` |
| Binary variants (gzip, zip, PDF, ELF, EXE, JPEG, UTF-16), NUL in the text, Latin-1 bytes, BOM and CRLF | no | `test_upload_defence.py` |

### Model failure and cleanup

Do not crash or corrupt a running server to test this. The automated test does it safely, in an isolated in-process
`TestClient`:

- It replaces the model's `analyse` with a function that raises.
- It checks that the client gets the generic 500 `{"error": "internal_error", ...}`.
- The autouse `nothing_left_behind` fixture then checks that the private upload folder is empty.

From the repository root:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_upload_defence.py -k "model_fails or generated_name or temp_cleaner" -v
```

Every test in `test_upload_defence.py` also runs the empty-folder check. To run the whole upload defence, including
the real-socket size tests:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_upload_defence.py backend/tests/test_upload_live.py -v
```
