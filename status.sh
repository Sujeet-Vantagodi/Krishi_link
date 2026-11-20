#!/bin/bash
# KrishiLink - System & Database Live Status Checker
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "======================================================================"
echo "  KRISHILINK PLATFORM STATUS"
echo "======================================================================"

# 1. PostgreSQL status
echo -n "1. PostgreSQL Database (Port 5432): "
if /usr/lib/postgresql/18/bin/pg_ctl -D /home/sujeet/pgdata status > /dev/null 2>&1; then
  echo "🟢 RUNNING"
else
  echo "🔴 STOPPED"
fi

# 2. Backend API status
echo -n "2. FastAPI Backend (Port 8000):     "
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
  echo "🟢 ONLINE"
else
  echo "🔴 OFFLINE"
fi

# 3. Network IP
HOST_IP=$(hostname -I | awk '{print $1}')
echo "3. Network Device Host IP:          $HOST_IP"

echo ""
echo "4. Database User Directory Snapshot:"
./venv/bin/python view_db.py users
