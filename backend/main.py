"""VibePilot FastAPI backend — deploy to Render or Railway."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

import auth
import settings
import discovery

app = FastAPI(title="VibePilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url(), "http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    q: str


class CousinsRequest(BaseModel):
    title: str | None = None
    artist: str | None = None
    track_id: str | None = None


class VibeRequest(BaseModel):
    text: str
    familiarity: int = Field(default=5, ge=1, le=10)


class BreakLoopRequest(BaseModel):
    tracks: list[dict]


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "vibepilot-api",
        "spotify_redirect_uri": settings.spotify_redirect_uri(),
        "frontend_url": settings.frontend_url(),
    }


@app.get("/auth/login")
def login():
    url, _ = auth.build_login_url()
    return RedirectResponse(url)


@app.get("/auth/callback")
def callback(code: str = Query(...), state: str = Query(...)):
    if not auth.verify_state(state):
        raise HTTPException(400, "Invalid OAuth state")
    try:
        result = auth.exchange_code(code)
    except Exception as e:
        raise HTTPException(400, f"Token exchange failed: {e}") from e
    sid = result["session_id"]
    # Pass session in URL — cross-site cookies (Vercel ↔ Render) are blocked by browsers.
    response = RedirectResponse(f"{settings.frontend_url()}/?session={sid}")
    cross_site = settings.frontend_url().startswith("https://") and "127.0.0.1" not in settings.frontend_url()
    response.set_cookie(
        key="vp_session",
        value=sid,
        httponly=True,
        secure=cross_site,
        samesite="none" if cross_site else "lax",
        max_age=60 * 60 * 24 * 30,
    )
    return response


def _session_id(
    vp_session: str | None = Cookie(default=None),
    x_vp_session: str | None = Header(default=None, alias="X-VP-Session"),
) -> str | None:
    return x_vp_session or vp_session


@app.get("/auth/me")
def me(sid: str | None = Depends(_session_id)):
    token = auth.get_token(sid)
    if not token:
        return {"logged_in": False}
    discovery._patch_auth(token)
    try:
        import spotify_client

        profile = spotify_client.me()
        return {"logged_in": True, "display_name": profile.get("display_name")}
    except Exception:
        return {"logged_in": True}


@app.post("/auth/logout")
def logout(sid: str | None = Depends(_session_id)):
    response = {"ok": True}
    from fastapi.responses import JSONResponse

    resp = JSONResponse(response)
    resp.delete_cookie("vp_session")
    return resp


def _token(sid: str | None = Depends(_session_id)) -> str | None:
    return auth.get_token(sid)


@app.post("/api/search")
def api_search(body: SearchRequest, token: str | None = Depends(_token)):
    try:
        return {"tracks": discovery.search_tracks(body.q.strip(), token)}
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@app.post("/api/cousins")
def api_cousins(body: CousinsRequest, token: str | None = Depends(_token)):
    try:
        if body.track_id:
            return discovery.find_cousins_by_id(body.track_id, token)
        if not body.title:
            raise HTTPException(400, "title or track_id required")
        return discovery.find_cousins(body.title, body.artist or "", token)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@app.post("/api/vibe")
def api_vibe(body: VibeRequest, token: str | None = Depends(_token)):
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "text required")
    try:
        return discovery.vibe_session(text, body.familiarity, token)
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@app.post("/api/break-loop")
def api_break_loop(body: BreakLoopRequest, token: str | None = Depends(_token)):
    try:
        return discovery.break_loop(body.tracks, token)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(500, str(e)) from e
