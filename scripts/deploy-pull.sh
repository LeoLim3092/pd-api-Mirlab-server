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

if [ -n "$VENV_ACTIVATE" ] && [ -f "$VENV_ACTIVATE" ]; then
  echo "==> Activating virtualenv..."
  source "$VENV_ACTIVATE"
fi

echo "==> Running migrations..."
python manage.py migrate --noinput

if [ -n "$RESTART_CMD" ]; then
  echo "==> Restarting application..."
  eval "$RESTART_CMD"
  echo "==> Done."
else
  echo "==> Done. Restart your app manually if needed (set RESTART_CMD in this script)."
fi
