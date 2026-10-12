import * as esbuild from 'esbuild';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const SRC = path.join(HERE, '..', 'src');

// Bundles the components once (JSX -> JavaScript, written to the system temp folder) and loads the result.
export async function loadComponents() {
  const outfile = path.join(mkdtempSync(path.join(tmpdir(), 'logsentry-test-')), 'components.cjs');
  await esbuild.build({
    entryPoints: [path.join(HERE, 'entry.jsx')], bundle: true, platform: 'node', format: 'cjs', outfile,
    jsx: 'automatic', loader: { '.js': 'jsx' }, logLevel: 'silent',
    define: { 'process.env.NODE_ENV': '"production"' },
  });
  return import(pathToFileURL(outfile).href);
}

// A File-like object: validate() only reads name and size.
export const fakeFile = (name, size) => ({ name, size });

export const SESSIONS = [
  { session_id: 'blk_1', score: 0.9999, flagged: true, cluster: 2, n_events: 4, t_start: 1226389000, t_end: 1226389100 },
  { session_id: 'blk_2', score: 0.0001, flagged: false, cluster: null, n_events: 13, t_start: 1226389200, t_end: 1226389300 },
  { session_id: 'blk_3', score: 0.5, flagged: false, cluster: null, n_events: 9, t_start: 1226389400, t_end: 1226389500 },
];
