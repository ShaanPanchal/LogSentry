// Bundled by tests/helpers.mjs so the tests can render the real components to HTML strings (no browser needed).
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import ErrorBoundary from '../src/ErrorBoundary.jsx';
import NotFound from '../src/NotFound.jsx';
import Notice from '../src/Notice.jsx';
import ScoreHistogram from '../src/ScoreHistogram.jsx';
import SessionTable from '../src/SessionTable.jsx';
import SessionTimeline from '../src/SessionTimeline.jsx';
import { Metrics } from '../src/Summary.jsx';
import UploadForm, { validate } from '../src/UploadForm.jsx';

export { createElement, renderToStaticMarkup, ErrorBoundary, NotFound, Notice, ScoreHistogram, SessionTable, SessionTimeline, Metrics, UploadForm, validate };
