"""Discovery API glue — imports vibepilot engine, no Streamlit."""

import importlib.util
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
VIBEPILOT_DIR = BACKEND_DIR.parent / "vibepilot"
sys.path.insert(0, str(VIBEPILOT_DIR))

for key in ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "GROQ_API_KEY", "LASTFM_API_KEY"):
    if os.getenv(key):
        os.environ[key] = os.getenv(key)

# Load backend auth without conflicting with vibepilot.auth
_spec = importlib.util.spec_from_file_location("vp_backend_auth", BACKEND_DIR / "auth.py")
api_auth = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(api_auth)

import discovery_core  # noqa: E402
import spotify_client  # noqa: E402


def _patch_auth(user_token: str | None):
    import auth as vp_auth

    vp_auth.get_valid_token = lambda: user_token
    vp_auth.get_app_token = lambda: api_auth.get_app_token()
    vp_auth.is_logged_in = lambda: user_token is not None
    vp_auth.spotify_configured = lambda: bool(
        os.getenv("SPOTIFY_CLIENT_ID") and os.getenv("SPOTIFY_CLIENT_SECRET")
    )


def _taste_and_exclude(user_token: str | None):
    taste = None
    exclude: list[str] = []
    if user_token:
        try:
            taste = spotify_client.build_taste_profile()
            exclude = [r["name"] for r in taste.get("recent", [])]
        except Exception:
            pass
    return taste, exclude


def search_tracks(q: str, user_token: str | None = None) -> list[dict]:
    _patch_auth(user_token)
    return spotify_client.search_tracks(q, limit=10)


def find_cousins(title: str, artist: str, user_token: str | None = None) -> dict:
    _patch_auth(user_token)
    anchor = spotify_client.search_track(title, artist)
    if not anchor:
        raise ValueError("Track not found on Spotify")
    taste, exclude = _taste_and_exclude(user_token)
    return discovery_core.find_cousins_for_anchor(anchor, taste=taste, exclude=exclude)


def find_cousins_by_id(track_id: str, user_token: str | None = None) -> dict:
    _patch_auth(user_token)
    anchor = spotify_client.get_track(track_id)
    if not anchor:
        raise ValueError("Track not found on Spotify")
    taste, exclude = _taste_and_exclude(user_token)
    return discovery_core.find_cousins_for_anchor(anchor, taste=taste, exclude=exclude)


def vibe_session(text: str, familiarity: int = 5, user_token: str | None = None) -> dict:
    _patch_auth(user_token)
    taste, exclude = _taste_and_exclude(user_token)
    return discovery_core.build_vibe_session(text, familiarity=familiarity, taste=taste, exclude=exclude)


def break_loop(tracks: list[dict], user_token: str | None = None) -> dict:
    _patch_auth(user_token)
    _, exclude = _taste_and_exclude(user_token)
    return discovery_core.break_loop(tracks, exclude=exclude)
