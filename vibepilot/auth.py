"""Spotify OAuth — Authorization Code flow (confidential client) for Streamlit.

We use the standard Authorization Code flow with the client secret rather than
PKCE, because Streamlit wipes session_state during the full-page redirect back
from Spotify — so a stored PKCE verifier wouldn't survive. With a confidential
client, token exchange only needs the returned `code` + client credentials,
which all live in config (not session), so login works across the redirect.

Flow:
  1. build_authorize_url() -> return Spotify consent URL
  2. user approves, redirected back with ?code=...
  3. exchange_code(code) -> swap code for access/refresh tokens
  4. get_valid_token() -> return a live access token, refreshing if expired
"""

import secrets
import time
import urllib.parse

import requests
import streamlit as st

from config import (
    SPOTIFY_SCOPES,
    get_spotify_client_id,
    get_spotify_client_secret,
    get_spotify_redirect_uri,
)

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

# App-level (Client Credentials) token — lets ANYONE use public catalog calls
# (e.g. /search) with no user login. Powers "Guest mode". Cached module-side.
_APP_TOKEN: dict = {}


def get_app_token():
    """Client-Credentials token for public-catalog calls (search). No user login needed."""
    now = time.time()
    if _APP_TOKEN.get("token") and now < _APP_TOKEN.get("exp", 0) - 60:
        return _APP_TOKEN["token"]
    cid = get_spotify_client_id()
    secret = get_spotify_client_secret()
    if not cid or not secret:
        return None
    try:
        resp = requests.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(cid, secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=20,
        )
    except Exception:
        return None
    if resp.status_code != 200:
        return None
    payload = resp.json()
    _APP_TOKEN["token"] = payload["access_token"]
    _APP_TOKEN["exp"] = now + payload.get("expires_in", 3600)
    return _APP_TOKEN["token"]


def spotify_configured() -> bool:
    """True if Client ID + Secret are present (needed for guest search)."""
    return bool(get_spotify_client_id() and get_spotify_client_secret())


def build_authorize_url() -> str:
    cid = get_spotify_client_id()
    redirect = get_spotify_redirect_uri()
    if not cid:
        return "https://developer.spotify.com/dashboard"
    state = secrets.token_urlsafe(16)
    st.session_state["oauth_state"] = state
    params = {
        "client_id": cid,
        "response_type": "code",
        "redirect_uri": redirect,
        "scope": " ".join(SPOTIFY_SCOPES),
        "state": state,
        "show_dialog": "true",
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code(code: str) -> bool:
    """Exchange an authorization code for tokens. Returns True on success."""
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": get_spotify_redirect_uri(),
    }
    resp = requests.post(
        TOKEN_URL,
        data=data,
        auth=(get_spotify_client_id(), get_spotify_client_secret()),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    if resp.status_code != 200:
        body = resp.text
        if "invalid_client" in body or "Invalid client secret" in body:
            st.session_state["auth_error"] = (
                "Spotify rejected the Client Secret. In Streamlit Cloud → Settings → Secrets, "
                "re-copy SPOTIFY_CLIENT_SECRET from developer.spotify.com/dashboard → your app → Settings."
            )
        else:
            st.session_state["auth_error"] = f"{resp.status_code}: {body}"
        return False
    _store_token(resp.json())
    return True


def _store_token(payload: dict):
    st.session_state["access_token"] = payload["access_token"]
    if "refresh_token" in payload:
        st.session_state["refresh_token"] = payload["refresh_token"]
    st.session_state["token_expires_at"] = time.time() + payload.get("expires_in", 3600)


def _refresh() -> bool:
    refresh_token = st.session_state.get("refresh_token")
    if not refresh_token:
        return False
    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        auth=(get_spotify_client_id(), get_spotify_client_secret()),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    if resp.status_code != 200:
        return False
    _store_token(resp.json())
    return True


def get_valid_token():
    """Return a live access token, refreshing if near expiry. None if not logged in."""
    token = st.session_state.get("access_token")
    if not token:
        return None
    if time.time() >= st.session_state.get("token_expires_at", 0) - 60:
        if not _refresh():
            return None
    return st.session_state.get("access_token")


def is_logged_in() -> bool:
    return get_valid_token() is not None


def logout():
    for key in (
        "access_token",
        "refresh_token",
        "token_expires_at",
        "oauth_state",
        "spotify_profile",
    ):
        st.session_state.pop(key, None)
