#!/bin/bash
# KrishiLink - Universal Startup (PostgreSQL + FastAPI Backend + Vite Frontend)
set -e
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "======================================================================"
echo "  KRISHILINK PLATFORM — STARTING LIVE SERVICES"
echo "======================================================================"

# 1. PostgreSQL
if /usr/lib/postgresql/18/bin/pg_ctl -D /home/sujeet/pgdata status > /dev/null 2>&1; then
  echo "✓ PostgreSQL Database is RUNNING on port 5432 (krishilink)"
else
  echo "🌱 Starting PostgreSQL on 0.0.0.0:5432..."
  /usr/lib/postgresql/18/bin/pg_ctl -D /home/sujeet/pgdata -l /home/sujeet/pgdata/logfile start
  sleep 1
  echo "✓ PostgreSQL Database started."
fi

# 2. Start FastAPI Backend in background
echo "🚀 Starting FastAPI Core Backend (0.0.0.0:8000)..."
nohup ./venv/bin/uvicorn services.api.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "✓ Backend running with PID $BACKEND_PID"

# 3. Detect IP for cross-device access
HOST_IP=$(hostname -I | awk '{print $1}')
echo ""
echo "======================================================================"
echo "  KrishiLink is LIVE for all devices on your local network!"
echo "  - Local URL:        http://localhost:3000"
if [ -n "$HOST_IP" ]; then
  echo "  - Mobile / Devices: http://$HOST_IP:3000"
  echo "  - Backend API:      http://$HOST_IP:8000/docs"
fi
echo "======================================================================"
echo ""

# 4. Start Vite Frontend in foreground
exec npm run dev -- --host 0.0.0.0 --port 3000
