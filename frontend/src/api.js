// The four API calls, using the browser's built-in fetch. Every failure becomes an ApiError with a message
// that is safe to show to the user.
import { API_BASE_URL } from './config.js';

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;   // 0 means the server could not be reached
  }
}

const SERVER_PROBLEM = 'Something went wrong on the server. Please try again later.';

// The "Server running" indicator in the page header follows the result of the latest request (true = got an answer).
const listeners = new Set();
export function onConnectionChange(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
const report = (reachable) => listeners.forEach((listener) => listener(reachable));

async function request(path, options) {
  let response;
  try {
    response = await fetch(API_BASE_URL + path, options);
  } catch {
    report(false);
    throw new ApiError('Could not reach the LogSentry server. Check that the back end is running, then try again.', 0);
  }
  report(true);
  if (response.status === 204) return null;

  let body = null;
  try {
    body = await response.json();
  } catch {
    // not JSON: handled below
  }
  if (!response.ok) {
    // The back end always answers errors as {"error": "...", "detail": "..."}. Its detail text for 4xx errors is
    // written for users. For 5xx errors we show our own generic text.
    const detail = body && typeof body.detail === 'string' ? body.detail : null;
    throw new ApiError(response.status < 500 && detail ? detail : SERVER_PROBLEM, response.status);
  }
  return body;
}

export function createAnalysis(source, file) {
  const form = new FormData();
  form.append('source', source);
  form.append('file', file);          // no Content-Type header: the browser adds it, with the multipart boundary
  return request('/api/analyses', { method: 'POST', body: form });
}

export const getAnalysis = (id) => request(`/api/analyses/${encodeURIComponent(id)}`);

export const getSession = (id, sessionId) =>
  request(`/api/analyses/${encodeURIComponent(id)}/sessions/${encodeURIComponent(sessionId)}`);

export const deleteAnalysis = (id) => request(`/api/analyses/${encodeURIComponent(id)}`, { method: 'DELETE' });
