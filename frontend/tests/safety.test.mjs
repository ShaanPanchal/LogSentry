// Uploaded log text must only ever be shown as plain text. This scans the front-end source for the ways React code
// can bypass its automatic escaping, or send the user somewhere an uploaded file chose.
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { SRC } from './helpers.mjs';

const files = readdirSync(SRC).filter((f) => /\.(jsx?|css)$/.test(f)).map((f) => [f, readFileSync(path.join(SRC, f), 'utf8')]);
const code = files.filter(([f]) => !f.endsWith('.css'));
const strip = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\{\/\*[\s\S]*?\*\/\}/g, '');

test('the source is scanned (guards against the test silently checking nothing)', () => {
  assert.ok(code.length >= 15, `only ${code.length} source files found`);
});

for (const [name, pattern] of [
  ['dangerouslySetInnerHTML', /dangerouslySetInnerHTML/],
  ['innerHTML / outerHTML / insertAdjacentHTML', /\.(innerHTML|outerHTML)\b|insertAdjacentHTML/],
  ['document.write', /document\.write/],
  ['eval / new Function', /\beval\s*\(|new Function\s*\(/],
  ['window.open', /window\.open\s*\(/],
  ['href or src built from a variable', /\b(href|src)=\{(?!`\$\{prefix\}#\$\{n\.id\}`)/],
  ['javascript: URLs', /javascript:/i],
]) {
  test(`no use of ${name}`, () => {
    const hits = code.filter(([, text]) => pattern.test(strip(text))).map(([f]) => f);
    assert.deepEqual(hits, []);
  });
}

test('the only navigation in code goes to a fixed address', () => {
  const navigation = /(?:window\.)?location\.(?:assign|replace|href\s*=)[^;\n]*/g;
  const uses = code.flatMap(([f, text]) => (strip(text).match(navigation) || []).map((m) => `${f}: ${m}`));
  assert.equal(uses.length, 1, uses.join('\n'));
  assert.ok(uses[0].startsWith('ErrorBoundary.jsx') && uses[0].includes("assign('/')"), uses[0]);
});
