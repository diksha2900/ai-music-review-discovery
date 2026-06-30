"""Spotify OAuth for FastAPI — no Streamlit session."""

import secrets
import time
import urllib.parse
from typing import Optional

import requests

from settings import (
    SPOTIFY_SCOPES,
    spotify_client_id,
    spotify_client_secret,
    spotify_redirect_uri,
)

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

# sid -> {access_token, refresh_token, token_expires_at}
_sessions: dict[str, dict] = {}
_oauth_states: dict[str, float] = {}
_APP_TOKEN: dict = {}


def get_app_token() -> Optional[str]:
    now = time.time()
    if _APP_TOKEN.get("token") and now < _APP_TOKEN.get("exp", 0) - 60:
        return _APP_TOKEN["token"]
    cid, secret = spotify_client_id(), spotify_client_secret()
    if not cid or not secret:
        return None
    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(cid, secret),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    if resp.status_code != 200:
        return None
    payload = resp.json()
    _APP_TOKEN["token"] = payload["access_token"]
    _APP_TOKEN["exp"] = now + payload.get("expires_in", 3600)
    return _APP_TOKEN["token"]


def build_login_url() -> tuple[str, str]:
    state = secrets.token_urlsafe(16)
    _oauth_states[state] = time.time()
    params = {
        "client_id": spotify_client_id(),
        "response_type": "code",
        "redirect_uri": spotify_redirect_uri(),
        "scope": " ".join(SPOTIFY_SCOPES),
        "state": state,
        "show_dialog": "true",
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}", state


def verify_state(state: str) -> bool:
    ts = _oauth_states.pop(state, None)
    return ts is not None and time.time() - ts < 600


def exchange_code(code: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": spotify_redirect_uri(),
        },
        auth=(spotify_client_id(), spotify_client_secret()),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    resp.raise_for_status()
    payload = resp.json()
    sid = secrets.token_urlsafe(24)
    _sessions[sid] = {
        "access_token": payload["access_token"],
        "refresh_token": payload.get("refresh_token"),
        "token_expires_at": time.time() + payload.get("expires_in", 3600),
    }
    return {"session_id": sid}


def get_token(session_id: Optional[str]) -> Optional[str]:
    if not session_id or session_id not in _sessions:
        return None
    sess = _sessions[session_id]
    if time.time() >= sess.get("token_expires_at", 0) - 60:
        rt = sess.get("refresh_token")
        if not rt:
            return None
        resp = requests.post(
            TOKEN_URL,
            data={"grant_type": "refresh_token", "refresh_token": rt},
            auth=(spotify_client_id(), spotify_client_secret()),
            timeout=20,
        )
        if resp.status_code != 200:
            return None
        p = resp.json()
        sess["access_token"] = p["access_token"]
        sess["token_expires_at"] = time.time() + p.get("expires_in", 3600)
    return sess["access_token"]
