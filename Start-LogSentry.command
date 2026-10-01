#!/bin/bash
# Double-click launcher for the existing macOS LogSentry installation.
set -eu
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$HOME/Downloads/LogSentry/logsentry_app"
if [ -f "$SCRIPT_DIR/logsentry_app/src/dashboard.py" ]; then
  APP_DIR="$SCRIPT_DIR/logsentry_app"
elif [ -f "$SCRIPT_DIR/src/dashboard.py" ]; then
  APP_DIR="$SCRIPT_DIR"
fi
pause_error() { echo; echo "$1"; read -r -p "Press Enter to close..." answer; exit 1; }
[ -f "$APP_DIR/src/dashboard.py" ] || pause_error "Application not found. Keep your project in ~/Downloads/LogSentry/logsentry_app, or place this launcher beside logsentry_app."
cd "$APP_DIR"
echo "Opening LogSentry in Visual Studio Code..."
if ! open -a "Visual Studio Code" "$APP_DIR" 2>/dev/null; then
  echo "VS Code could not be opened. The dashboard will still start."
fi
PYTHON_BIN="$APP_DIR/.venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
  command -v python3 >/dev/null 2>&1 || pause_error "Python 3 is required. Install Python, then open this launcher again."
  echo "Creating the Python environment..."
  python3 -m venv "$APP_DIR/.venv" || pause_error "Could not create the Python environment."
fi
if ! "$PYTHON_BIN" -c 'import flask,numpy,pandas,sklearn,joblib' 2>/dev/null; then
  [ -f requirements.txt ] || pause_error "requirements.txt is missing. Restore the complete application ZIP first."
  echo "Installing dependencies. This first-time step needs internet access..."
  "$PYTHON_BIN" -m pip install -r requirements.txt || pause_error "Dependency installation failed. See the message above."
fi
DASHBOARD_URL="http://127.0.0.1:5050"
if curl -fsS --max-time 2 "$DASHBOARD_URL/" 2>/dev/null | grep -q 'LogSentry'; then
  echo "LogSentry is already running. Opening the dashboard..."
  open "$DASHBOARD_URL/"
  exit 0
fi
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
echo "Starting the dashboard..."
"$PYTHON_BIN" -u -c "import sys; sys.path.insert(0, 'src'); from dashboard import app; app.run(host='127.0.0.1', port=5050)" &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT
trap 'exit 130' INT TERM
for attempt in {1..30}; do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    pause_error "Dashboard startup failed. Check the error above. Another service may be using port 5050."
  fi
  if curl -fsS --max-time 1 "$DASHBOARD_URL/" 2>/dev/null | grep -q 'LogSentry'; then
    open "$DASHBOARD_URL/"
    echo
    echo "LogSentry is ready. Keep this Terminal window open."
    echo "Press Ctrl+C here to stop the dashboard."
    echo "If no model is available, run setup_data.py --source HDFS in VS Code's Terminal before analysing logs."
    wait "$SERVER_PID"
    exit 0
  fi
  sleep 1
done
pause_error "The dashboard did not become ready within 30 seconds. Check the startup messages above."
