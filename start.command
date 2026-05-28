#!/bin/bash
# Home Hub — double-click this file in Finder to start the app.

cd "$(dirname "$0")"

echo ""
echo "🏠  Home Hub starting..."
echo ""

# ─── Backend ─────────────────────────────────────────────────────────────────
echo "→  Backend  (http://localhost:8000)"
cd backend

if [ ! -d ".venv" ]; then
    echo "   First run: setting up Python environment..."
    python3 -m venv .venv
    .venv/bin/pip install -q --upgrade pip
    .venv/bin/pip install -q -r requirements.txt
    echo "   Done."
fi

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "   ⚠  No .env file found — created one from .env.example."
    echo "   Edit backend/.env with your Arlo credentials, then restart."
    echo ""
fi

.venv/bin/uvicorn main:app --port 8000 --log-level warning &
BACKEND_PID=$!
cd ..

# ─── Frontend ────────────────────────────────────────────────────────────────
echo "→  Frontend (http://localhost:5173)"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "   First run: installing packages..."
    npm install --silent
    echo "   Done."
fi

npm run dev &
FRONTEND_PID=$!
cd ..

# ─── Open browser ────────────────────────────────────────────────────────────
sleep 2
open "http://localhost:5173"

echo ""
echo "✓  Home Hub is running at http://localhost:5173"
echo "   Close this window (or press Ctrl+C) to stop."
echo ""

# ─── Cleanup on exit ─────────────────────────────────────────────────────────
cleanup() {
    echo ""
    echo "Stopping Home Hub..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
    wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
    echo "Stopped."
    exit 0
}
trap cleanup INT TERM

wait
