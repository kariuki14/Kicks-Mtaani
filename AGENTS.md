# AGENTS.md — Kicks Mtaani

## Setup

- Run `./start.sh` to launch both backend (port 8001) and frontend (port 5500) simultaneously.
- Backend uses venv at `backend/venv/`; script falls back to `PROJECT_ROOT/.venv/` or system `python3`.
- Ensure `backend/.env` exists with at minimum `DATABASE_URL`, `ADMIN_API_KEY`, `JWT_SECRET_KEY`.
- Default dev JWT secret is detected and rejected for non-SQLite databases (auth will crash on startup if `JWT_SECRET_KEY` equals the default and DB is not sqlite).
- Schema is managed by Alembic. `./start.sh` runs `alembic upgrade head` before launching uvicorn.

## Development flow

1. `./start.sh` — starts both servers; Ctrl+C stops them cleanly.
2. Backend: `uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload` (from `backend/`); run migrations first.
3. Frontend: `python -m http.server 5500 --bind 127.0.0.1` (from `docs/`).
4. Seed products: `ADMIN_API_KEY=<key> python seed.py` (from `backend/`).
5. Upload images: `ADMIN_API_KEY=<key> python upload_images.py` (from `backend/`).

## Auth: admin access

- Two methods accepted by `verify_admin_access`:
  1. `X-API-Key` header matching `.env` `ADMIN_API_KEY`
  2. Bearer JWT token with `role=admin` claim
- API key tried first; then JWT. Both must be from an active admin user.

## API base

- All endpoints under `/api`: e.g., `GET /api/products`, `POST /api/auth/login`
- Base URL config: `BASE_URL=http://127.0.0.1:8001/api` (from `.env`)

## File uploads

- Upload dir: `backend/app/uploads/` (mounted at `/uploads`)
- Validations: content-type must be `image/jpeg|png|webp|gif`; magic bytes verified via `imghdr`; max 5MB
- Filenames sanitized to `uuid-hex<ext>` to prevent path traversal
- Images also accepted from `docs/images/` via `upload_images.py`

## DB notes

- Default: SQLite at `backend/kicks_mtaani.db`
- PostgreSQL supported: set `DATABASE_URL=postgresql://...` in `.env`
- If using Postgres remote (not localhost/127.0.0.1): `sslmode=require` is enforced
- `check_same_thread=False` required for SQLite connections
- Alembic owns the schema; `Base.metadata.create_all` is intentionally not called at startup
- Migrations live in `backend/migrations/versions/`; run commands from `backend/`:
  - `venv/bin/python -m alembic current`
  - `venv/bin/python -m alembic upgrade head`
  - `venv/bin/python -m alembic revision --autogenerate -m "description"`
- Existing pre-Alembic databases must be stamped with the baseline revision before upgrading:
  `venv/bin/python -m alembic stamp 97dffbc771e7`
- Docker backend runs `alembic upgrade head` before uvicorn via the container CMD.

## Rate limiting

- In-memory per-IP limit: 60 requests per 60-second window
- Register/login have lower limits (10/15 req/window) defined in `routes.py`

## Security conventions

- CORS: origins from `ALLOWED_ORIGINS` env var; regex allows `localhost` and `127.0.0.1` with any port
- Security headers: HSTS, X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy added on every response
- Passwords: bcrypt, truncated to 72 bytes max
- Default dev secrets are rejected for production-like setups