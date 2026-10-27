# Kicks Mtaani

Nakuru's go-to spot for basketball merch.

## Structure

- `docs/` — HTML/CSS site & Admin Panel (deployed on GitHub Pages)
- `backend/` — FastAPI API (deployed on Render)

## Local Development

Start both frontend and backend servers with one command:

```bash
./start.sh
```

- **Storefront:** http://127.0.0.1:5500
- **Admin Panel:** http://127.0.0.1:5500/admin.html
- **API Docs:** http://127.0.0.1:8001/docs

Database schema is managed by Alembic. `./start.sh` applies pending migrations before starting the backend.

```bash
cd backend
venv/bin/python -m alembic upgrade head   # apply migrations
venv/bin/python -m alembic current        # show DB revision
```

## Live Links

- Frontend: https://kariuki14.github.io/kicks-mtaani/
- API: https://kicks-mtaani-api.onrender.com
