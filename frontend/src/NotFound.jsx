import Shell from './Shell.jsx';

// Shown for any address other than the home page, in the same page frame as the dashboard.
export default function NotFound() {
  return (
    <Shell home={false}>
      <section className="intro">
        <h1>Page not found</h1>
      </section>
      <section className="panel">
        <p>There is no page at this address.</p>
        <a className="button primary" href="/">Go to the LogSentry dashboard</a>
      </section>
    </Shell>
  );
}
