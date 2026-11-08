// Builds the React app with esbuild (JSX -> JavaScript, bundled into dist/).
//   npm start      builds, serves on http://localhost:5173 and rebuilds when a file changes
//   npm run build  one production build (minified) into dist/
import * as esbuild from 'esbuild';
import { cpSync, mkdirSync, rmSync } from 'node:fs';

const mode = process.argv[2];
const production = mode === 'build';
const PORT = 5173;   // must match the origin the backend allows for CORS (LOGSENTRY_FRONTEND_ORIGIN)

rmSync('dist', { recursive: true, force: true });
mkdirSync('dist');
cpSync('public/index.html', 'dist/index.html');

const options = {
  entryPoints: ['src/index.jsx'],
  bundle: true,
  outdir: 'dist',
  entryNames: 'bundle',                       // dist/bundle.js and dist/bundle.css (styles are imported by index.jsx)
  jsx: 'automatic',                           // lets us write JSX without importing React in every file
  loader: { '.js': 'jsx' },
  minify: production,
  sourcemap: !production,
  define: { 'process.env.NODE_ENV': JSON.stringify(production ? 'production' : 'development') },
  logLevel: 'info',
};

if (production) {
  await esbuild.build(options);
} else {
  const context = await esbuild.context(options);
  await context.watch();
  // `fallback` serves index.html for any other address, so the app itself can show its "page not found" page.
  await context.serve({ servedir: 'dist', host: 'localhost', port: PORT, fallback: 'dist/index.html' });
  console.log(`LogSentry front end running at http://localhost:${PORT}`);
}
