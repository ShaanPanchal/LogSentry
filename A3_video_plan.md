# A3 video plan

**Target length: about 13 minutes.** The limit is 15. Anything not shown in the video earns no marks, including the security defences.

The "Say" points are talking points. Say them in your own words; reading code or notes aloud is marked down.

Every command and expected output below was run and checked on 3 November 2026.

---

## Before you record (about 15 minutes)

1. **Start the back end (Terminal 1).**
   Windows: `cd backend` then `.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
   Mac: `cd backend` then `.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
   (No `.venv` yet? Do README section 3 first.) Wait for `Application startup complete`.
2. **Start the front end (Terminal 2).** `cd frontend`, `npm ci`, `npm start`.
3. **Open Terminal 3 in the repository root.** All attack commands run from here.
4. **Open http://localhost:5173** in Chrome. Use `localhost`, not `127.0.0.1`, or CORS blocks every request.
5. **Make it readable.** Chrome zoom 125%. VS Code zoomed in. Big terminal font. Notifications off.

**On Windows, type `curl.exe`, not `curl`.** In PowerShell, `curl` is a different command and fails. On Mac, `curl` is fine.

**Files you will upload** (all in the repository):

| File | Used in |
|---|---|
| `data/supporting/sample_HDFS.log` | Segment 2 |
| `backend/manual_upload_tests/fixtures/empty.log` | Segment 3 |
| `backend/manual_upload_tests/fixtures/wrong_extension.exe` | Segment 3 |
| `backend/manual_upload_tests/fixtures/png_renamed.log` | Segment 3 |
| `backend/manual_upload_tests/fixtures/hdfs_content_for_bgl_source.log` | Segment 3 |
| `backend/manual_upload_tests/fixtures/xss_demo.log` | Segment 7 |

---

## Running order

| # | Segment | Time |
|---|---|---|
| 1 | Who it is for | 0:40 |
| 2 | Live: a valid upload | 1:45 |
| 3 | Live: invalid input and error pages | 1:15 |
| 4 | Live: phone layout | 0:40 |
| 5 | One request through the code and /docs | 2:15 |
| 6 | Design decisions | 1:45 |
| 7 | Threat model and malicious input | 1:00 |
| 8 | Attack 1: unsafe file upload | 1:00 |
| 9 | Attacks 2 and 3: denial of service and response size | 2:30 |
| 10 | What doesn't work yet, and what's next | 0:30 |
| | **Total** | **13:20** |

If you run over, shorten segment 6. Never cut segments 8 and 9.

---

### 1. Who it is for (0:40)

**Show:** the empty home page.

**Say:**
- For system operators and security analysts.
- Problem: logs are millions of lines long, and the one odd session that matters is easy to miss.
- You upload an HDFS or BGL log. LogSentry splits it into sessions, scores each one with our Assignment 2 model, flags the risky ones, and lets you read any session's original lines.
- React front end, FastAPI back end. The model is a black box; our work this time is the application around it, mainly making it hard to abuse.

---

### 2. Live: a valid upload (1:45)

**Do:**
1. Source **HDFS**, file `sample_HDFS.log`, upload. Point at the loading state.
2. Point at the result: **200 sessions, 40 flagged**, and the success message.
3. **Histogram:** hover a bar (tooltip), point at the dashed threshold line, click a high bar. The table below now shows only that score range. Click **Clear**.
4. **Timeline:** click a high point. That session's detail opens: score, decision, cluster, original log lines. Press **Close**.
5. **Table:** tick "flagged only", press **Apply**.

**Say:**
- The histogram answers "how are the scores spread, and where's the threshold?" The timeline answers "when did sessions start, and which scored high?"
- The score is the model's 0-to-1 score, not a probability. A session is flagged at the threshold saved with the model, not at 0.5.

---

### 3. Live: invalid input and error pages (1:15)

**Do:**
1. Choose `empty.log`. "This file is empty." appears beside the field. Nothing was sent.
2. **Drag** `wrong_extension.exe` onto the upload area (the file picker hides `.exe`). "Only .log and .txt files are accepted."
3. Upload `png_renamed.log` (source HDFS). The browser lets it through, but the back end refuses it: "This is a PNG file, not a text log."
4. Upload `hdfs_content_for_bgl_source.log` with source **BGL**. Refused: "This does not look like a BGL log..."
5. Go to http://localhost:5173/nothing-here. The "Page not found" page appears. Press its button to go back.
6. Open `frontend/src/ErrorBoundary.jsx` in VS Code. (This crash page can't be triggered by clicking, so show the code.)

**Say:**
- Front-end checks are for usability. Back-end checks are for security, because an attacker never uses our front end.
- Every back-end error has the same JSON shape, and the front end shows its message beside the field.
- If the page ever crashes while drawing, `ErrorBoundary` shows this page instead of a blank screen.

---

### 4. Live: phone layout (0:40)

**Do:**
1. Upload `sample_HDFS.log` again.
2. **F12** (Mac: Cmd+Option+I), then **Ctrl+Shift+M** (Mac: Cmd+Shift+M). Pick **iPhone 12 Pro**.
3. Scroll top to bottom. Open one session. Close DevTools.

**Say:** below 800 px wide the sidebar becomes a top bar and the panels stack into one column. Everything also works with the keyboard.

---

### 5. One request through the code and /docs (2:15)

Follow **one** upload through the code. At each step say what is **sent**, what is **returned**, and where errors are caught.

| Open | Point at | Say |
|---|---|---|
| `frontend/src/UploadForm.jsx` | `validate` | Quick checks in the browser, for usability only. |
| `frontend/src/api.js` | `createAnalysis` | **Sends** `POST /api/analyses`, multipart form: `source` and `file`. Any failure becomes a message safe to show. |
| `backend/app/main.py` | `BodyLimitMiddleware` (line 21), CORS (line 98) | Before our code runs: too-large bodies get 413, and only our front end can read replies. |
| `backend/app/schemas.py` | `AnalysisForm` (line 16) | Pydantic: `source` must be HDFS or BGL, otherwise 422. |
| `backend/app/routes.py` | `create_analysis` (line 104) | Take a slot or 503. Check name, save, check content. Analyse. Always delete the temp file. |
| `backend/app/model_service.py` | `__init__` (line 42), `analyse` (line 51) | Models loaded once at startup. The same A2 code as training builds the features, then the model scores each session against its saved threshold. |
| `backend/app/routes.py` | `_build` (line 69) | Results stored in memory under a random ID. **Returns** 201 with `analysis_id`, `summary` and every session's score. |
| `backend/app/errors.py` | `register_error_handlers` (line 52) | Every error, even a crash, comes back as `{"error", "detail"}`. No stack traces. |

**Then in /docs:**
1. Open http://127.0.0.1:8000/docs, open **POST /api/analyses**.
2. Point at the description and the listed errors (400, 413, 415, 422, 500, 503), each with an example.
3. **Try it out**: source `HDFS`, file `sample_HDFS.log`, **Execute**. Show the 201 response.
4. Point at the other three endpoints: GET one analysis (used on page reload), GET one session (the detail panel), DELETE (the Delete button).

---

### 6. Design decisions (1:45)

Each one needs **what we chose, what else we could have done, and why**. Show the code as you say it.

| Choice | Show | Instead of | Why |
|---|---|---|---|
| Reuse the A2 pipeline unchanged | `backend/app/a2.py` | Rewriting it for the API | The model only works with exactly the features it was trained on. |
| Load models once at startup | `lifespan` in `main.py` (line 76) | Loading per request | Fast requests, and a missing model file fails at startup, not on a user's upload. |
| Use the saved threshold | `model_service.py` line 67 | 0.5 | Scores aren't probabilities. The A2 threshold was tuned on validation data. |
| Results in memory, behind a random ID | `backend/app/store.py` | A database | No database to attack or set up. Cost: lost on restart. |
| Refuse with 503 when busy | `routes.py` lines 32 and 107 | Queueing extra requests | A queued request still holds a thread and its upload. |

---

### 7. Threat model and malicious input (1:00)

**Show:** README section 6 (Threat model).

**Say:**
- **Who attacks it:** an intruder on a monitored system who wants their activity missed, or anyone who calls the API directly, skipping our front end.
- **What they want:** their session scored as normal; a script in a log line run in the analyst's browser; the service knocked over; or to learn whether their log was flagged.
- **What they can do:** upload any file, name or size with curl; send many requests at once; measure response time or size.
- From the Section 2.7 list we defend **unsafe file upload** and **denial of service**. SQL injection, command injection and SSRF don't apply: no database, no system commands, no outbound requests. For Section 2.8 we chose the **response-size side channel**, because "was my log flagged?" is exactly what an intruder wants to know.

**Do:**
1. Upload `xss_demo.log` (source HDFS). Result: 12 sessions, 4 flagged.
2. In the table, search `6161574319804418055`, Apply, open that session.
3. Point at the first log line: `<img src=x onerror=alert(1)>` is shown as **text**. No alert pops up.

**Say:** React escapes all text and we never use `dangerouslySetInnerHTML`, so HTML in a log line is shown, never run. The other hygiene points: back-end size limits, CORS allows only `http://localhost:5173`, and no secrets in the repository.

---

### 8. Attack 1: unsafe file upload (1:00)

**Say the attack:** skip our front end and use curl to send `../evil.log` (to write outside the upload folder), a huge file, or an image renamed `.log`.

**Do (Terminal 3):**
1. Path traversal (Mac: `curl` instead of `curl.exe`):
   ```
   curl.exe -F source=HDFS -F "file=@data/supporting/sample_HDFS.log;filename=../evil.log" http://127.0.0.1:8000/api/analyses
   ```
   You get: `{"error":"bad_request","detail":"The file name must be a plain file name, not a path."}`
2. All 30 attack cases at once. Windows: `backend\.venv\Scripts\python backend\manual_upload_tests\run_upload_tests.py` (Mac: `backend/.venv/bin/python backend/manual_upload_tests/run_upload_tests.py`). Takes a few seconds. Scroll the table. It ends with `30 passed, 0 failed`.

**Show:** `backend/app/upload_safety.py`: `check_filename` (line 34), `save_upload` (line 54), `check_content` (line 92).

**Say how the code stops it:**
1. **Name:** paths, `..` and control characters get 400. And the name is never used: the file is saved under a name the server makes up.
2. **Size:** the middleware refuses an oversized request before it is read; `save_upload` stops copying past 5 MiB.
3. **Content:** the extension and Content-Type aren't trusted. The bytes are checked for file signatures (PNG, ZIP, executables...), binary data and valid UTF-8, and 90% of lines must match the chosen log format.

**Cost:** a real log in an odd format is refused, and unusual file names must be renamed.

---

### 9. Attacks 2 and 3: denial of service and response size (2:30)

Both attacks are shown **twice**: with the defences turned off (the attack works), then on (it fails). One server restart covers both.

**Say the two attacks first:**
- **Denial of service:** analysing a log costs far more than sending one. Send 12 big logs at once and the server is busy for everyone.
- **Response size:** HTTPS hides what a response says, not how long it is. If a flagged log's response is a different size, an eavesdropper can tell it was flagged. The script uploads two logs 100 times each (one all normal, one with a single flagged session) and tries to tell them apart by size. 50% accuracy means guessing.

**Do. Defences OFF:**
1. Terminal 1: **Ctrl+C**. Then start the server with both defences off.
   Windows:
   ```powershell
   $env:LOGSENTRY_MAX_CONCURRENT_ANALYSES=1000; $env:LOGSENTRY_UNIFORM_SIZE=0
   .venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
   Mac:
   ```bash
   LOGSENTRY_MAX_CONCURRENT_ANALYSES=1000 LOGSENTRY_UNIFORM_SIZE=0 .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
2. Terminal 3, Windows (Mac: use `backend/.venv/bin/python` and `/`):
   ```
   backend\.venv\Scripts\python backend\attacks\dos_demo.py --flood 12
   backend\.venv\Scripts\python backend\attacks\size_attack.py --label before
   ```
   Each takes about 10 seconds. Point at:
   - DoS part 2: `statuses: 201: 12`, and GET latency went up (we got median 128 ms, max 2005 ms).
   - Size: `normal_bytes` **3362** and `flagged_bytes` **3356** are different, `attack_accuracy` **1.0** (100%).

**Do. Defences ON:**
1. Terminal 1: **Ctrl+C**. Windows only: `Remove-Item Env:LOGSENTRY_MAX_CONCURRENT_ANALYSES, Env:LOGSENTRY_UNIFORM_SIZE`. Start the server with the normal command.
2. Run the same two commands, but `--label after`.
3. Point at:
   - DoS: `statuses: 201: 2, 503: 10`, and GET latency stayed low (we got median 22 ms, max 129 ms).
   - Size: both sizes **7168**, `attack_accuracy` **0.5**: guessing.

Your latency numbers will differ a little; the pattern is what matters.

**Show and say how the code stops each:**
- `backend/app/routes.py` line 32 (`_analysis_slots`) and lines 107 to 108: at most 2 analyses run at once. A third gets **503** straight away with `Retry-After: 5`, so the server never takes on more than it can handle. **Cost:** when it's busy, real users get a 503 and retry a few seconds later.
- `backend/app/routes.py` `_padded` (line 48) and `_analysis_response` (line 56): JSON ignores trailing spaces, so every response is padded with spaces to `2048 + 256 × sessions` bytes. The size then reveals only the session count, which the sender already knows. `backend/tests/test_size.py` checks the session-detail response the same way. **Cost:** responses are about twice as big, and gzip must stay off.
- **Why not timing:** we tried a timing attack first, but the extra work for a flagged session is 0.35 ms against 14 to 32 ms of network jitter. Accuracy ranged from 49% to 77%, so we couldn't show a reliable leak. The size leaked every time.

**After recording:** `size_attack.py` adds its results to `backend/attacks/size_results.json`. Undo that with `git checkout -- backend/attacks/size_results.json`.

---

### 10. What doesn't work yet, and what's next (0:30)

**Say:**
- Results are in memory only: lost on restart, and memory grows until then. Next: a database with a time limit.
- No user accounts, so anyone with an analysis ID can read or delete it. Next: accounts.
- No per-client rate limiting, and model files aren't checked against a hash. Next: add both.
- Only HDFS and BGL logs are supported.

---

## Before submitting

- [ ] Under 15:00.
- [ ] Segment 9 shows **both** the "off" and "on" runs.
- [ ] Named with the group name, e.g. `session-12-group-3-A3-video.mp4`, MP4 or AVI.
- [ ] Watched the exported file from start to end.
- [ ] Too big for Canvas? Upload to YouTube as **unlisted** and submit the link in `group-name-videolink.txt`.
