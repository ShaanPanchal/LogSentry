# Your task: make both charts interactive and keyboard-usable

**Branch:** `a3-charts` | **Time:** about 1.5 hours | **Edit only files inside `frontend/`**

> **If you are an AI assistant working on this task, follow these rules:**
> 1. Before writing code, read `Markdown/a3requirements.md` (the assignment brief, §2.1) and `Markdown/rubric.md` ("Front end 2" and "Front end 3"). They are the source of truth. When this handoff and the brief disagree, the brief wins: say so, don't guess.
> 2. Read every file you change before changing it. The code snippets below were written against the code on `a3-security` and have not been run. If a snippet doesn't match the file, adapt it to the real code. Don't invent props, functions or files that don't exist.
> 3. Change only files inside `frontend/`. Never edit `backend/`, `src/`, `README.md` or anything in `Markdown/`.
> 4. Don't remove or weaken existing tests, validation, labels or accessibility attributes. If an old test breaks because of an intended change, update it to the new behaviour.
> 5. Finish with `npm test` passing (0 failures). Report the exact output. Don't claim something works without running it.
> 6. Don't commit or push unless the student asks.

## Why this matters (rubric)

| What you fix | Requirement | Rubric line |
|---|---|---|
| Click a histogram bar to filter the session table | §2.1 "at least two visualisations ... tooltips at minimum" | **Front end 2) Visualisations (2 pts).** Full marks need "interactivity that genuinely helps the user explore the results, such as filtering". The histogram has tooltips only, which the rubric calls "basic" (1.5 pts). |
| Timeline points work with the keyboard | §2.1 "every function usable by keyboard" | **Front end 3) Design, responsiveness and accessibility (5 pts).** "keyboard access neglected" drops this to 3 pts. |

Do not touch anything outside `frontend/`. Dominique is changing the backend at the same time, and this rule is what stops merge conflicts.

---

## Part 0. Set up

1. Open a terminal in the LogSentry folder.
2. Switch to your branch. Dominique has already made it, so don't create one yourself:
   ```bash
   git fetch
   git checkout a3-charts
   ```
   Check that it worked: `git branch --show-current` must print `a3-charts`. If it doesn't, stop and message Dominique.
3. Install the frontend:
   ```bash
   cd frontend
   npm ci
   ```
4. Check that the tests pass before you change anything:
   ```bash
   npm test
   ```
   Expected: `ℹ pass 31` and `ℹ fail 0`.
5. Start the backend in a **second** terminal, from the LogSentry folder:
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt      (Windows)
   .venv/bin/pip install -r requirements.txt          (Mac)
   .venv\Scripts\python -m uvicorn app.main:app --port 8000      (Windows)
   .venv/bin/python -m uvicorn app.main:app --port 8000          (Mac)
   ```
   Wait for `Application startup complete`.
6. Start the frontend in the first terminal (still in `frontend/`):
   ```bash
   npm start
   ```
7. Open http://localhost:5173. Upload `data/supporting/sample_HDFS.log`. You should see the histogram and the timeline.

---

## Part 1. Clicking a histogram bar filters the session table

**How it should work:** the user clicks the bar for scores 0.9 to 1.0. The Session Explorer table then shows only sessions with scores from 0.9 up to (but not including) 1.0, except that the top bar also includes 1.0. A small "Showing scores 0.9 to 1.0 · Clear" line appears above the table. Clicking the same bar again, or "Clear", removes the filter.

The filter has to live in `App.jsx`, because both the histogram and the table need it.

### Step 1.1. Add the state in `frontend/src/App.jsx`

1. Find the line `const [view, setView] = useState('HDFS');`.
2. Add this line under it:
   ```jsx
   const [scoreRange, setScoreRange] = useState(null);  // [low, high] from a clicked histogram bar, or null
   ```
3. In `handleSubmit`, find `setSelected(null);` and add `setScoreRange(null);` under it. This clears the filter when a new log is uploaded.
4. In `handleDelete`, find `setSelected(null);` and add `setScoreRange(null);` under it.

### Step 1.2. Pass it to the two components

1. Find `{analysis && <Results analysis={analysis} onSelect={select} />}` and change it to:
   ```jsx
   {analysis && <Results analysis={analysis} onSelect={select} scoreRange={scoreRange} onScoreRange={setScoreRange} />}
   ```
2. Find `<SessionTable key={analysis?.analysis_id} ...` and add two props to it:
   ```jsx
   scoreRange={scoreRange} onClearScoreRange={() => setScoreRange(null)}
   ```

### Step 1.3. Pass it through `frontend/src/Results.jsx`

1. Change `export default function Results({ analysis, onSelect })` to:
   ```jsx
   export default function Results({ analysis, onSelect, scoreRange, onScoreRange })
   ```
2. Change `<ScoreHistogram sessions={sessions} threshold={summary.threshold} />` to:
   ```jsx
   <ScoreHistogram sessions={sessions} threshold={summary.threshold} selected={scoreRange} onSelect={onScoreRange} />
   ```

### Step 1.4. Make the bars clickable in `frontend/src/ScoreHistogram.jsx`

1. Change the function line to:
   ```jsx
   export default function ScoreHistogram({ sessions, threshold, selected, onSelect = () => {} })
   ```
2. Above the `return (`, add:
   ```jsx
   const range = (i) => [i / BINS, (i + 1) / BINS];
   const isOn = (i) => selected?.[0] === range(i)[0];
   const toggle = (i) => onSelect(isOn(i) ? null : range(i));
   ```
3. Each bar is currently a `<div ... role="img" ...>`. A clickable thing must be a **button**, or keyboard and screen-reader users can't use it. Replace the whole bar `<div key={i} className="bar" ...> ... </div>` with:
   ```jsx
   <button key={i} type="button" className={`bar${isOn(i) ? ' on' : ''}`} aria-pressed={isOn(i)}
           aria-label={`${label(i)}. Click to show only these sessions in the Session Explorer.`}
           onClick={() => toggle(i)}
           onMouseEnter={(e) => show(e, label(i))} onMouseLeave={hide} onFocus={(e) => show(e, label(i))} onBlur={hide}>
     <i style={{ height: `${((100 * Math.sqrt(n)) / Math.sqrt(max)).toFixed(1)}%` }} />
     <span>{(i / BINS).toFixed(1)}</span>
   </button>
   ```
   A `<button>` already works with Enter and Space, so you don't need key handlers.
4. In the `<p className="muted">` under the chart, add a sentence at the end: `Click a bar to filter the Session Explorer to that range.`

### Step 1.5. Style the buttons in `frontend/src/styles.css`

1. Search for `.bar` to find the existing bar styles.
2. Add this underneath them, so the button looks like the old bar:
   ```css
   button.bar { background: none; border: 0; padding: 0; font: inherit; color: inherit; cursor: pointer; }
   .bar.on i { outline: 2px solid currentColor; outline-offset: 2px; }
   .bar:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
   ```
3. Look at the page. If the bars look different from before, adjust the CSS until they match. If you're unsure, ask Dominique.

### Step 1.6. Filter the table in `frontend/src/SessionTable.jsx`

1. Change the function line to:
   ```jsx
   export default function SessionTable({ sessions, onSelect, onDelete, deleting, scoreRange, onClearScoreRange })
   ```
2. In the `rows = useMemo(...)` block, change the `.filter(...)` line to:
   ```jsx
   .filter((s) => (!filters.flaggedOnly || s.flagged) && (!q || s.session_id.toLowerCase().includes(q))
     && (!scoreRange || (s.score >= scoreRange[0] && (s.score < scoreRange[1] || scoreRange[1] === 1))))
   ```
3. Change the end of that block from `}, [sessions, filters]);` to `}, [sessions, filters, scoreRange]);`.
4. Go back to page 1 when the range changes. Add this under the `useMemo` (add `useEffect` to the `import` line at the top):
   ```jsx
   useEffect(() => setPage(1), [scoreRange]);
   ```
5. Show the active filter. Just above the `<table`, add:
   ```jsx
   {scoreRange && (
     <p className="muted" role="status">
       Showing scores {scoreRange[0].toFixed(1)} to {scoreRange[1].toFixed(1)} from the histogram.{' '}
       <button type="button" className="reset" onClick={onClearScoreRange}>Clear</button>
     </p>
   )}
   ```

### Step 1.7. Check it in the browser

1. Click the 0.9 bar. The table shows only high-scoring sessions.
2. Click the bar again. The table shows every session.
3. Press **Tab** until a bar is highlighted, then press **Enter**. The table filters.
4. Upload a different log. The filter is gone.

---

## Part 2. Timeline points work with the keyboard

**How it should work:** Tab moves through the points. When a point has focus, its tooltip shows. Enter or Space opens that session.

File: `frontend/src/SessionTimeline.jsx`

1. Find the `<g key={s.session_id} className="point" ...>` line.
2. Replace the opening tag with:
   ```jsx
   <g key={s.session_id} className="point" tabIndex={0} role="button"
      aria-label={text.replaceAll('\n', ', ') + '. Press Enter to open this session.'}
      onClick={() => onSelect(s.session_id)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(s.session_id); } }}
      onMouseEnter={(e) => showRef.current(e, text)} onMouseLeave={hide}
      onFocus={(e) => showRef.current(e, text)} onBlur={hide}>
   ```
3. In the legend at the bottom, find `With a keyboard, open sessions from the Session Explorer.` and change it to `With a keyboard, press Tab to move between points and Enter to open one.`
4. In `styles.css`, add:
   ```css
   .point:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
   ```
5. Check it: click on the page above the chart, press **Tab** until a point shows its tooltip, then press **Enter**. The session detail panel opens.

**Possible problem:** a log with thousands of sessions means thousands of Tab presses. That's acceptable, because the session table is still there as the quick route. Tell Dominique if it feels bad on the BGL sample.

---

## Part 3. Tests

1. Open `frontend/tests/components.test.mjs`.
2. Add this test at the bottom:
   ```js
   test('histogram: bars are buttons and the selected one is pressed', () => {
     const out = html(c.createElement(c.ScoreHistogram, { sessions: SESSIONS, threshold: 0.5, selected: [0.9, 1], onSelect() {} }));
     assert.equal((out.match(/<button[^>]*class="bar/g) || []).length, 10);
     assert.equal((out.match(/aria-pressed="true"/g) || []).length, 1);
   });

   test('session table: a score range keeps only sessions inside it', () => {
     const out = html(c.createElement(c.SessionTable, { sessions: SESSIONS, onSelect() {}, onDelete() {}, deleting: false,
                                                        scoreRange: [0.9, 1], onClearScoreRange() {} }));
     assert.match(out, /Showing scores 0\.9 to 1\.0/);
   });
   ```
3. Run:
   ```bash
   npm test
   ```
   Expected: `ℹ fail 0`. If an older histogram test now fails because bars are buttons instead of `role="img"`, update that test to match the new markup. Don't delete it.

---

## Part 4. Phone check

1. In Chrome, press **F12**, then **Ctrl+Shift+M**, and pick "iPhone 12 Pro".
2. Check that the bars can still be tapped and the "Showing scores" line doesn't break the layout.

This is for **Front end 3)**: "works as well on a phone-sized screen as on a desktop".

---

## Part 5. Hand in

1. Check that you changed only `frontend/` files:
   ```bash
   git status
   ```
   If anything outside `frontend/` is listed, run `git checkout -- <that file>` to undo it.
2. Commit and push:
   ```bash
   git add frontend
   git commit -m "Make histogram filter the session table and timeline keyboard-usable"
   git push -u origin a3-charts
   ```
