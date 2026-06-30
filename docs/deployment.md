# VibePilot Deployment Plan

**Architecture (mentor-approved):**

| Layer | Platform | URL example |
|-------|----------|-------------|
| Frontend | [Vercel](https://vercel.com/) | `https://vibepilot.vercel.app` |
| Backend | [Render](https://dashboard.render.com/) or [Railway](https://railway.com/) | `https://vibepilot-api.onrender.com` |

Streamlit is **deprecated** for production. The Python discovery engine in `vibepilot/` stays — it becomes a library used by the FastAPI backend.

---

## Repository layout

```
spotify-discovery-engine/
├── vibepilot/          # Discovery engine (unchanged logic)
├── backend/            # FastAPI → Render / Railway
├── frontend/           # Next.js → Vercel
└── docs/deployment.md
```

---

## Phase 1 — Backend (Render or Railway)

### Environment variables

```bash
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=https://vibepilot-api.onrender.com/auth/callback
FRONTEND_URL=https://vibepilot.vercel.app
GROQ_API_KEY=...
LASTFM_API_KEY=...
```

### Deploy on Render

1. [dashboard.render.com](https://dashboard.render.com/) → **New Web Service**
2. Repo: `ai-music-review-discovery`
3. **Root Directory:** `backend`
4. **Build:** `pip install -r requirements.txt`
5. **Start:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Python **3.11**, add env vars, Deploy
7. Test: `curl https://YOUR-API.onrender.com/health`

### Deploy on Railway

1. [railway.com](https://railway.com/) → Deploy from GitHub
2. Root: `backend`, start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Add env vars → Deploy

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/auth/login` | Spotify OAuth redirect |
| GET | `/auth/callback` | OAuth callback |
| POST | `/api/search` | `{ "q": "kabira" }` |
| POST | `/api/cousins` | `{ "title", "artist" }` or `{ "track_id" }` |
| POST | `/api/vibe` | `{ "text", "familiarity" }` |
| POST | `/api/break-loop` | `{ "tracks": [...] }` |

---

## Phase 2 — Frontend (Vercel)

### Environment

```bash
NEXT_PUBLIC_API_URL=https://vibepilot-api.onrender.com
```

### Deploy

1. [vercel.com](https://vercel.com/) → Import repo
2. **Root Directory:** `frontend`
3. Add `NEXT_PUBLIC_API_URL` → Deploy

### After deploy

1. Set backend `FRONTEND_URL` to Vercel URL
2. Add redirect URIs in Spotify Dashboard (backend + frontend URLs)

---

## Phase 3 — Retire Streamlit

Verify Vercel + Render work, then stop Streamlit Cloud app.

---

## Tomorrow checklist

**Backend first**
- [ ] `cd backend && pip install -r requirements.txt`
- [ ] Copy `.env.example` → `.env`
- [ ] `uvicorn main:app --reload --port 8000`
- [ ] Deploy Render → save API URL

**Frontend second**
- [ ] `cd frontend && npm install`
- [ ] Set `NEXT_PUBLIC_API_URL` in `.env.local`
- [ ] `npm run dev` then deploy Vercel

**Verify**
- [ ] Guest search + cousins
- [ ] Emoji / mood vibe
- [ ] Spotify login + save playlist

---

## Local dev

```bash
# Backend
cd backend && cp .env.example .env && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && cp .env.local.example .env.local && npm run dev
```
