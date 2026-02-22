#!/bin/bash
set -e

# Start nginx in background
nginx &

# Start uvicorn
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --app-dir /app/backend
