#!/bin/bash
# Deploy script: pull latest code, run migrations, restart app
# Run on remote server: bash scripts/deploy-pull.sh

set -e

# --- Configure these for your server ---
PROJECT_DIR="${PROJECT_DIR:-/home/pdapp/pd_api_server}"   # Change to your app path
BRANCH="${BRANCH:-model-adjustment}"
VENV_ACTIVATE="/home/pdapp/miniconda3/envs/pdapp/bin/activate"          # Set to "" if no venv
RESTART_CMD=""                                            # e.g. "sudo systemctl restart gunicorn"

# --- Pull and deploy ---
echo "==> Changing to project directory: $PROJECT_DIR"
cd "$PROJECT_DIR"

echo "==> Fetching from origin..."
git fetch origin

echo "==> Pulling branch: $BRANCH"
git pull origin "$BRANCH"

# Use venv Python explicitly (avoids using system Python 2 when script is run with sudo)
PYTHON_CMD="python"
if [ -n "$VENV_ACTIVATE" ] && [ -f "$VENV_ACTIVATE" ]; then
  echo "==> Activating virtualenv..."
  source "$VENV_ACTIVATE"
  VENV_BIN="$(dirname "$VENV_ACTIVATE")"
  if [ -x "$VENV_BIN/python" ]; then
    PYTHON_CMD="$VENV_BIN/python"
  fi
fi

echo "==> Running migrations..."
"$PYTHON_CMD" manage.py migrate --noinput

if [ -n "$RESTART_CMD" ]; then
  echo "==> Restarting application..."
  eval "$RESTART_CMD"
  echo "==> Done."
else
  echo "==> Done. Restart your app manually if needed (set RESTART_CMD in this script)."
fi
