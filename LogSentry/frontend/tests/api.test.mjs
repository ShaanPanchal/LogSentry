// api.js: every failure becomes a message that is safe to show, and the request is built correctly.
import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import { ApiError, createAnalysis, deleteAnalysis, getAnalysis, getSession, onConnectionChange } from '../src/api.js';

const realFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = realFetch; });

const reply = (status, body) => () => Promise.resolve(new Response(body === undefined ? null : JSON.stringify(body), { status }));
const rejected = async (promise) => { try { await promise; } catch (e) { return e; } assert.fail('expected a rejection'); };

test('a 4xx error shows the back end\'s own message', async () => {
  globalThis.fetch = reply(422, { error: 'invalid_input', detail: 'The log is not in time order.' });
  const e = await rejected(getAnalysis('x'));
  assert.ok(e instanceof ApiError);
  assert.equal(e.status, 422);
  assert.equal(e.message, 'The log is not in time order.');
});

test('a 404 keeps its status so the page can tell "not found" apart', async () => {
  globalThis.fetch = reply(404, { error: 'not_found', detail: 'Analysis not found.' });
  assert.equal((await rejected(getSession('a', 'b'))).status, 404);
});

test('a 5xx error never shows the response body, only a generic message', async () => {
  globalThis.fetch = reply(500, { error: 'internal_error', detail: 'Traceback: secret C:\\x\\y.py' });
  const e = await rejected(createAnalysis('HDFS', { name: 'a.log' }));
  assert.equal(e.status, 500);
  assert.match(e.message, /try again later/);
  assert.ok(!e.message.includes('Traceback') && !e.message.includes('secret'));
});

test('an error with no JSON body still gives a usable message', async () => {
  globalThis.fetch = () => Promise.resolve(new Response('<html>Bad gateway</html>', { status: 502 }));
  const e = await rejected(getAnalysis('x'));
  assert.match(e.message, /try again later/);
});

test('a network failure says the server could not be reached (status 0)', async () => {
  globalThis.fetch = () => Promise.reject(new TypeError('Failed to fetch'));
  const e = await rejected(getAnalysis('x'));
  assert.equal(e.status, 0);
  assert.match(e.message, /Could not reach the LogSentry server/);
});

test('DELETE succeeds with no body (204)', async () => {
  globalThis.fetch = reply(204);
  assert.equal(await deleteAnalysis('x'), null);
});

test('createAnalysis posts multipart form data and lets the browser set the content type', async () => {
  let seen;
  globalThis.fetch = (url, options) => { seen = { url, options }; return reply(201, { analysis_id: 'abc' })(); };
  const file = new File(['line\n'], 'a.log');
  assert.deepEqual(await createAnalysis('BGL', file), { analysis_id: 'abc' });
  assert.ok(seen.url.endsWith('/api/analyses'));
  assert.equal(seen.options.method, 'POST');
  assert.ok(seen.options.body instanceof FormData);
  assert.equal(seen.options.body.get('source'), 'BGL');
  assert.equal(seen.options.body.get('file').name, 'a.log');
  assert.equal(seen.options.headers, undefined);       // a hand-set Content-Type would lose the multipart boundary
});

test('ids in the URL are encoded', async () => {
  let url;
  globalThis.fetch = (u) => { url = u; return reply(200, {})(); };
  await getSession('a b', 'blk_-1/../x');
  assert.ok(url.endsWith('/api/analyses/a%20b/sessions/blk_-1%2F..%2Fx'), url);
});

test('connection listeners hear whether the server answered', async () => {
  const heard = [];
  const stop = onConnectionChange((ok) => heard.push(ok));
  globalThis.fetch = reply(404, { detail: 'no' });
  await rejected(getAnalysis('x'));                     // an error answer still means the server is reachable
  globalThis.fetch = () => Promise.reject(new TypeError('down'));
  await rejected(getAnalysis('x'));
  stop();
  assert.deepEqual(heard, [true, false]);
});
