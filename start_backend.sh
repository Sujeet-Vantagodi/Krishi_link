#!/bin/bash
# KrishiLink - Start FastAPI Backend Server
set -e
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 1. Ensure PostgreSQL is active
if ! /usr/lib/postgresql/18/bin/pg_ctl -D /home/sujeet/pgdata status > /dev/null 2>&1; then
  echo "🌱 Starting PostgreSQL Server on 0.0.0.0:5432..."
  /usr/lib/postgresql/18/bin/pg_ctl -D /home/sujeet/pgdata -l /home/sujeet/pgdata/logfile start
  sleep 1
fi

echo "🚀 Starting KrishiLink Core API Backend on http://0.0.0.0:8000..."
exec ./venv/bin/uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload
