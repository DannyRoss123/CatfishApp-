# Catfish Prototype (Phase 1.5)

We now have a tiny **FastAPI backend** plus a separate **React (Vite) frontend** so we can reason about API boundaries and persistence without extra complexity. The backend stores uploaded binaries in SQLite, and the frontend renders the “Catfish – fake or not?” mobile-style interface and calls the API.

## Structure

```
catfish_simple/
  backend/
    app/
      database.py   # SQLite engine + session factory
      main.py       # REST API (health, upload, list)
      models.py     # uploads table definition
    data/           # local SQLite file (gitignored)
    requirements.txt
  frontend/
    index.html
    package.json, vite.config.js
    src/            # React components + API helper
```

## Running the backend

```bash
cd catfish_simple/backend
python -m venv .venv && source .venv/bin/activate  # or use your existing env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Running the frontend

```bash
cd catfish_simple/frontend
npm install
npm run dev  # starts Vite dev server on http://localhost:5173
```

The Vite dev server proxies `/api/*` to `http://127.0.0.1:8000`, so with both processes running you can hit `http://localhost:5173`, tap “Store locally,” and the file will be POSTed to the FastAPI API and saved in SQLite (`catfish_simple/backend/data/catfish.db`). The “Recent uploads” list is populated by `GET /api/uploads` so you can see what’s been stored.

---

> **Next steps**
> We can layer in richer metadata, fake/not-fake labels, auth, etc., once you’re ready. For now this separation keeps the architecture transparent while staying very small.
