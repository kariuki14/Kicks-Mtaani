#!/usr/bin/env bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
DOCS_DIR="$PROJECT_ROOT/docs"

echo "=================================================="
echo "Starting Kicks Mtaani Development Environment..."
echo "=================================================="

# 1. Clean up lingering processes on ports 8000 & 5500
echo "Checking and freeing ports 8000 & 5500..."
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 5500/tcp 2>/dev/null || true
sleep 1

# 2. Verify venv
if [ -d "$BACKEND_DIR/venv" ]; then
    PYTHON_EXEC="$BACKEND_DIR/venv/bin/python"
    UVICORN_EXEC="$BACKEND_DIR/venv/bin/uvicorn"
elif [ -d "$PROJECT_ROOT/.venv" ]; then
    PYTHON_EXEC="$PROJECT_ROOT/.venv/bin/python"
    UVICORN_EXEC="$PROJECT_ROOT/.venv/bin/uvicorn"
else
    PYTHON_EXEC="python3"
    UVICORN_EXEC="uvicorn"
fi

# 3. Ensure uploads dir exists
mkdir -p "$BACKEND_DIR/app/uploads"

# 4. Start Backend
echo "Launching FastAPI Backend on port 8000..."
cd "$BACKEND_DIR"
$UVICORN_EXEC app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# 5. Start Frontend
echo "Launching Frontend Server on port 5500..."
cd "$DOCS_DIR"
$PYTHON_EXEC -m http.server 5500 --bind 127.0.0.1 &
FRONTEND_PID=$!

# Trap signals to cleanly shutdown both servers on Ctrl+C
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill -TERM "$BACKEND_PID" 2>/dev/null || true
    kill -TERM "$FRONTEND_PID" 2>/dev/null || true
    fuser -k 8000/tcp 2>/dev/null || true
    fuser -k 5500/tcp 2>/dev/null || true
    echo "All servers stopped cleanly."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

echo ""
echo "Kicks Mtaani is live:"
echo "   - Storefront:  http://127.0.0.1:5500"
echo "   - Admin Panel: http://127.0.0.1:5500/admin.html"
echo "   - API Docs:    http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers."

# Keep script running
wait $BACKEND_PID $FRONTEND_PID
