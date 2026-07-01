"""Spotify OAuth — signed stateless sessions (survives Render restarts)."""

import base64
import hashlib
import hmac
import json
import secrets
import time
import urllib.parse
from typing import Optional

import requests

from settings import (
    SPOTIFY_SCOPES,
    session_secret,
    spotify_client_id,
    spotify_client_secret,
    spotify_redirect_uri,
)

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

_APP_TOKEN: dict = {}


def _sign(data: str) -> str:
    return hmac.new(session_secret().encode(), data.encode(), hashlib.sha256).hexdigest()


def pack(data: dict) -> str:
    raw = base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":")).encode()).decode().rstrip("=")
    return f"{raw}.{_sign(raw)}"


def unpack(token: str) -> Optional[dict]:
    if not token or "." not in token:
        return None
    raw, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(_sign(raw), sig):
        return None
    try:
        pad = "=" * (-len(raw) % 4)
        return json.loads(base64.urlsafe_b64decode(raw + pad))
    except Exception:
        return None


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
    state = pack({"oauth": True, "ts": time.time()})
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
    data = unpack(state)
    if not data or not data.get("oauth"):
        return False
    return time.time() - float(data.get("ts", 0)) < 600


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
    sid = pack({
        "access_token": payload["access_token"],
        "refresh_token": payload.get("refresh_token"),
        "token_expires_at": time.time() + payload.get("expires_in", 3600),
    })
    return {"session_id": sid}


def get_token(session_id: Optional[str]) -> Optional[str]:
    sess = unpack(session_id or "")
    if not sess or "access_token" not in sess:
        return None
    if time.time() >= float(sess.get("token_expires_at", 0)) - 60:
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
    return sess.get("access_token")
