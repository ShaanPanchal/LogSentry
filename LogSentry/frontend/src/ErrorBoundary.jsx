import { Component } from 'react';

// Shows a fallback page if rendering ever crashes, so the user never gets a blank screen.
// (React only supports error boundaries as classes. Errors in API calls are handled where they happen.)
// It uses plain markup and the page's own styles, so it does not depend on the components that may have failed.
export default class ErrorBoundary extends Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error) {
    console.error('LogSentry front end error:', error);
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <main className="solo">
        <section className="intro">
          <h1>Something went wrong</h1>
        </section>
        <section className="panel">
          <p>LogSentry hit an unexpected problem and could not show this page.</p>
          <p>Reload the page to try again. A finished analysis stays on the server until it is deleted or the server restarts.</p>
          <button type="button" className="button primary" onClick={() => window.location.assign('/')}>Reload LogSentry</button>
        </section>
      </main>
    );
  }
}
