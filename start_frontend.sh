#!/bin/bash
# KrishiLink - Start Vite Frontend (Accessible to all devices on the network)
set -e
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "🌐 Starting KrishiLink Frontend on http://0.0.0.0:3000..."
exec npm run dev -- --host 0.0.0.0 --port 3000
