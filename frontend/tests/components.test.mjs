// The real components rendered to HTML: labels, visible states, charts, and the error and not-found pages.
import assert from 'node:assert/strict';
import { before, test } from 'node:test';
import { SESSIONS, fakeFile, loadComponents } from './helpers.mjs';

let c;
before(async () => { c = await loadComponents(); });
const html = (element) => c.renderToStaticMarkup(element);
const MB = 1024 * 1024;

// ---- 1. validation
test('validate: accepts .log and .txt (any case) within the size limit', () => {
  for (const name of ['a.log', 'a.txt', 'SAMPLE.LOG', 'Mixed.Txt']) assert.equal(c.validate(fakeFile(name, 1000)), null, name);
  assert.equal(c.validate(fakeFile('big.log', 5 * MB)), null);
});

test('validate: every refusal explains the problem in plain words', () => {
  assert.match(c.validate(null), /Choose a \.log or \.txt file/);
  for (const name of ['a.csv', 'a.exe', 'a', 'a.log.exe', 'a.log.png']) assert.match(c.validate(fakeFile(name, 10)), /Only \.log and \.txt/, name);
  assert.match(c.validate(fakeFile('a.log', 0)), /empty/);
  assert.match(c.validate(fakeFile('a.log', 5 * MB + 1)), /5\.0 MiB/);
  assert.match(c.validate(fakeFile('a.log', 6.2 * MB)), /6\.2 MiB.*limit is 5\.0 MiB/);
});

// ---- 7. labels and 2. loading state of the form
test('upload form: every control has a label and Analyse is disabled until a file is chosen', () => {
  const out = html(c.createElement(c.UploadForm, { busy: false, onSubmit() {}, serverError: null, onEdit() {} }));
  assert.match(out, /<label class="field-label" for="source">Log source<\/label>/);
  assert.match(out, /<select id="source"/);
  assert.match(out, /<label class="dropzone[^"]*" for="log-file">/);
  assert.match(out, /<input id="log-file"[^>]*type="file"/);
  assert.match(out, /<button class="button primary" type="submit" disabled="">Analyse log/);
  assert.match(out, /<button class="button secondary" type="button" disabled="">Clear file<\/button>/);
  assert.ok(!out.includes('role="alert"'), 'no error before anything is wrong');
});

test('upload form: while busy it shows the loading state and disables the controls', () => {
  const out = html(c.createElement(c.UploadForm, { busy: true, onSubmit() {}, serverError: null, onEdit() {} }));
  assert.match(out, /aria-busy="true"/);
  assert.match(out, /Analysing…/);
  assert.match(out, /role="progressbar"/);
  assert.match(out, /role="status"/);
  assert.match(out, /<select id="source"[^>]*disabled=""/);
  assert.match(out, /<input id="log-file"[^>]*disabled=""/);
});

test('upload form: a server error is announced next to the file field', () => {
  const out = html(c.createElement(c.UploadForm, { busy: false, onSubmit() {}, serverError: 'The log is not in time order.', onEdit() {} }));
  assert.match(out, /<div id="file-error" class="alert" role="alert"><strong>Error:<\/strong> The log is not in time order\./);
  assert.match(out, /aria-describedby="file-error"/);
});

// ---- 2. success / error / note messages
test('messages: kind is stated in words, and errors are announced at once', () => {
  assert.match(html(c.createElement(c.Notice, { kind: 'error' }, 'Bad')), /role="alert"><strong>Error:<\/strong> Bad/);
  assert.match(html(c.createElement(c.Notice, { kind: 'success' }, 'Done')), /role="status"><strong>Success:<\/strong> Done/);
  assert.match(html(c.createElement(c.Notice, { kind: 'info' }, 'FYI')), /role="status"><strong>Note:<\/strong> FYI/);
});

// ---- 3. scores, thresholds, flagged status
test('summary boxes: counts, share flagged, and dashes before an analysis', () => {
  const none = html(c.createElement(c.Metrics, { summary: null }));
  assert.match(none, /Awaiting log upload/);
  assert.equal((none.match(/<strong[^>]*>—<\/strong>/g) || []).length, 4);
  const summary = { source: 'HDFS', total_sessions: 200, flagged_sessions: 40, threshold: 0.95, audit: { raw_lines: 2819, malformed_lines: 0 } };
  const out = html(c.createElement(c.Metrics, { summary }));
  assert.match(out, /<strong class="danger">40<\/strong>/);
  assert.match(out, /20\.0% of analysed sessions/);
  assert.match(out, /HDFS · session groups/);
});

test('session table: flagged status is written in words, scores have 4 decimals, rows are inspectable by name', () => {
  const out = html(c.createElement(c.SessionTable, { sessions: SESSIONS, onSelect() {}, onDelete() {}, deleting: false }));
  assert.match(out, /<span class="badge flagged">Flagged<\/span>/);
  assert.match(out, /<span class="badge normal">Normal<\/span>/);
  assert.match(out, />0\.9999</);
  assert.match(out, /aria-label="Inspect blk_1"/);
  assert.match(out, /aria-label="Search session ID"/);
  assert.match(out, /aria-label="Sort sessions"/);
  assert.match(out, /3 matching sessions · page 1 of 1/);
  assert.match(out, /<button type="button" class="button secondary"[^>]*>Delete analysis<\/button>/);
});

test('session table: empty state before any log is analysed', () => {
  const out = html(c.createElement(c.SessionTable, { sessions: null, onSelect() {}, onDelete() {}, deleting: false }));
  assert.match(out, /No log analysed yet/);
  assert.ok(!out.includes('Delete analysis'));
});

// ---- 9. plain-text rendering
test('session ids and other text are escaped, never turned into HTML', () => {
  const hostile = '<img src=x onerror="alert(1)"><script>alert(2)</script>';
  const out = html(c.createElement(c.SessionTable, { sessions: [{ ...SESSIONS[0], session_id: hostile }], onSelect() {}, onDelete() {}, deleting: false }));
  assert.ok(!out.includes('<img'), 'no img element was created');
  assert.ok(!out.includes('<script'), 'no script element was created');
  assert.ok(out.includes('&lt;img src=x onerror=&quot;alert(1)&quot;&gt;'), 'shown as text');
});

// ---- 4. charts
test('score distribution chart: title, 10 named bars with their counts, axis wording and threshold legend', () => {
  const out = html(c.createElement(c.ScoreHistogram, { sessions: SESSIONS, threshold: 0.95 }));
  assert.match(out, /aria-label="Anomaly score distribution"/);
  assert.match(out, />ANOMALY SCORE DISTRIBUTION</);
  assert.equal((out.match(/class="bar"/g) || []).length, 10);
  assert.match(out, /aria-label="Scores 0\.0 to 0\.1: 1 session\. Filter/);
  assert.match(out, /aria-label="Scores 0\.9 to 1\.0: 1 session\. Filter/);
  assert.match(out, /aria-label="Scores 0\.5 to 0\.6: 1 session\. Filter/);
  assert.equal((out.match(/<button[^>]*class="bar"/g) || []).length, 10); // native buttons support focus, Enter and Space
  assert.match(out, /labelled by its lower edge/);
  assert.match(out, /square-root scaled/);
  assert.match(out, /Dashed line: decision threshold 0\.95/);
});

test('histogram: only the selected range is pressed and all bars target the explorer', () => {
  const out = html(c.createElement(c.ScoreHistogram, { sessions: SESSIONS, threshold: 0.5, selected: [0.9, 1], onSelect() {} }));
  assert.equal((out.match(/<button[^>]*class="bar/g) || []).length, 10);
  assert.equal((out.match(/aria-pressed="true"/g) || []).length, 1);
  assert.equal((out.match(/aria-controls="sessions"/g) || []).length, 10);
  assert.match(out, /class="bar on"[^>]*aria-pressed="true"[^>]*aria-label="Scores 0\.9 to 1\.0/);
});

test('session table: score filtering excludes other sessions and offers a clear control', () => {
  const out = html(c.createElement(c.SessionTable, { sessions: SESSIONS, scoreRange: [0.9, 1], onClearScoreRange() {} }));
  assert.match(out, /Showing scores 0\.9 to 1\.0/);
  assert.match(out, /aria-label="Clear score range filter"/);
  assert.match(out, /aria-label="Inspect blk_1"/);
  assert.doesNotMatch(out, /aria-label="Inspect blk_[23]"/);
  assert.match(out, /1 matching sessions · page 1 of 1/);
});

test('score bin boundaries: each exact edge belongs to one bin, including 0 and 1', () => {
  const sessions = Array.from({ length: 11 }, (_, i) => ({ ...SESSIONS[0], session_id: `edge_${i}`, score: i / 10 }));
  for (let i = 0; i < 10; i += 1) {
    const out = html(c.createElement(c.SessionTable, { sessions, scoreRange: [i / 10, (i + 1) / 10] }));
    const ids = [...out.matchAll(/aria-label="Inspect (edge_\d+)"/g)].map((match) => match[1]).sort();
    assert.deepEqual(ids, (i === 9 ? ['edge_9', 'edge_10'] : [`edge_${i}`]).sort());
  }
  const chart = html(c.createElement(c.ScoreHistogram, { sessions, threshold: 0.5 }));
  assert.match(chart, /Scores 0\.0 to 0\.1: 1 session/);
  assert.match(chart, /Scores 0\.9 to 1\.0: 2 sessions/);
});

test('score bins: a score just below an edge is counted and filtered in the same bar', () => {
  const sessions = [{ ...SESSIONS[0], session_id: 'near_edge', score: 0.8999999999999999 }];
  const chart = html(c.createElement(c.ScoreHistogram, { sessions, threshold: 0.5 }));
  const table = html(c.createElement(c.SessionTable, { sessions, scoreRange: [0.9, 1] }));
  assert.match(chart, /Scores 0\.9 to 1\.0: 1 session/);
  assert.match(table, /aria-label="Inspect near_edge"/);
});

test('session table: an empty score bin retains its clear control and shows no matches', () => {
  const out = html(c.createElement(c.SessionTable, { sessions: SESSIONS, scoreRange: [0.2, 0.3] }));
  assert.match(out, /No sessions match these filters/);
  assert.match(out, /0 matching sessions · page 1 of 1/);
  assert.match(out, /aria-label="Clear score range filter"/);
});

test('timeline: every session is a named keyboard button, with axes and legend retained', () => {
  const out = html(c.createElement(c.SessionTimeline, { sessions: SESSIONS, threshold: 0.5, onSelect() {} }));
  assert.equal((out.match(/class="point" tabindex="0" role="button"/g) || []).length, SESSIONS.length);
  for (const session of SESSIONS) assert.ok(out.includes(`aria-label="${session.session_id}, Score`));
  assert.match(out, /Press Enter or Space to open this session/);
  assert.match(out, /Session start time \(UTC\)/);
  assert.match(out, /Threshold 0\.5/);
  assert.match(out, /> Flagged</);
  assert.match(out, /> Normal</);
});

// ---- 10. not-found page and crash fallback
test('not-found page: says so, keeps the page frame, and links back to the dashboard', () => {
  const out = html(c.createElement(c.NotFound));
  assert.match(out, /<h1>Page not found<\/h1>/);
  assert.match(out, /<a class="button primary" href="\/">Go to the LogSentry dashboard<\/a>/);
  assert.match(out, /class="sidebar"/);
  assert.match(out, /href="\/#overview"/);                              // links go back to the home page, not to this address
});

test('crash fallback: a failed render shows a message and a way back, not a blank screen', () => {
  assert.deepEqual(c.ErrorBoundary.getDerivedStateFromError(new Error('boom')), { failed: true });
  const boundary = new c.ErrorBoundary({ children: 'fine' });
  assert.equal(boundary.render(), 'fine');                              // normal pages pass straight through
  boundary.state = { failed: true };
  const out = html(boundary.render());
  assert.match(out, /Something went wrong/);
  assert.match(out, /Reload LogSentry/);
  assert.ok(!out.includes('boom'), 'the error text is not shown to the user');
});
