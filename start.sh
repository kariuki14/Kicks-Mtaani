#!/usr/bin/env bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
DOCS_DIR="$PROJECT_ROOT/docs"

echo "=================================================="
echo "Starting Kicks Mtaani Development Environment..."
echo "=================================================="

# 1. Clean up lingering processes on this project's ports only (8001 & 5500).
# Do not touch port 8000; it may belong to another project.
echo "Checking and freeing ports 8001 & 5500..."
fuser -k 8001/tcp 2>/dev/null || true
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

# 4. Resolve DATABASE_URL: prefer local .env, but never use the Docker 'db' hostname
#    when running outside Docker (use 127.0.0.1:5433 which is the host-exposed port).
BACKEND_ENV="$BACKEND_DIR/.env"
if grep -q "DATABASE_URL" "$BACKEND_ENV" 2>/dev/null; then
    RAW_DB_URL=$(grep "^DATABASE_URL=" "$BACKEND_ENV" | cut -d= -f2-)
else
    RAW_DB_URL="${DATABASE_URL:-}"
fi
# Replace Docker service hostname 'db' with localhost mapped port
if echo "$RAW_DB_URL" | grep -qE "@db(:|/)"; then
    export DATABASE_URL=$(echo "$RAW_DB_URL" | sed 's|@db:5432|@127.0.0.1:5433|g')
    echo "  [INFO] Rewrote DATABASE_URL: db:5432 → 127.0.0.1:5433"
else
    export DATABASE_URL="$RAW_DB_URL"
fi

# 5. Apply database migrations, then start Backend
cd "$BACKEND_DIR"
echo "Applying database migrations..."
$PYTHON_EXEC -m alembic upgrade head

echo "Launching FastAPI Backend on port 8001..."
$UVICORN_EXEC app.main:app --host 127.0.0.1 --port 8001 --reload &
BACKEND_PID=$!

# 6. Start Frontend
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
    fuser -k 8001/tcp 2>/dev/null || true
    fuser -k 5500/tcp 2>/dev/null || true
    echo "All servers stopped cleanly."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

echo ""
echo "Kicks Mtaani is live:"
echo "   - Storefront:  http://127.0.0.1:5500"
echo "   - Admin Panel: http://127.0.0.1:5500/admin.html"
echo "   - API Docs:    http://127.0.0.1:8001/docs"
echo ""
echo "Press Ctrl+C to stop all servers."

# Keep script running
wait $BACKEND_PID $FRONTEND_PID
