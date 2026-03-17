#!/bin/bash
# Deploy script: pull latest code, run migrations, restart app
# Run on remote server: bash scripts/deploy-pull.sh

set -e

# --- Configure these for your server ---
PROJECT_DIR="${PROJECT_DIR:-/home/pdapp/pd_api_server}"   # Change to your app path
BRANCH="${BRANCH:-model-adjustment}"
# Conda env: use python path directly (reliable in scripts). Or set VENV_ACTIVATE to env's bin/activate.
VENV_PYTHON="${VENV_PYTHON:-/home/pdapp/miniconda3/envs/pdapp/bin/python}"   # Full path to env python
RESTART_CMD=""                                             # e.g. "sudo systemctl restart gunicorn"

# --- Pull and deploy ---
echo "==> Changing to project directory: $PROJECT_DIR"
cd "$PROJECT_DIR"

echo "==> Fetching from origin..."
git fetch origin

echo "==> Pulling branch: $BRANCH"
git pull origin "$BRANCH"

# Use env Python explicitly (avoids wrong Python when conda activate doesn't run in script)
PYTHON_CMD="python"
if [ -n "$VENV_PYTHON" ] && [ -x "$VENV_PYTHON" ]; then
  PYTHON_CMD="$VENV_PYTHON"
  echo "==> Using Python: $PYTHON_CMD"
elif [ -n "$VENV_ACTIVATE" ] && [ -f "$VENV_ACTIVATE" ]; then
  echo "==> Activating virtualenv..."
  source "$VENV_ACTIVATE"
  VENV_BIN="$(dirname "$VENV_ACTIVATE")"
  [ -x "$VENV_BIN/python" ] && PYTHON_CMD="$VENV_BIN/python"
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
