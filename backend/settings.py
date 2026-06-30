"""Backend settings — environment variables only (no Streamlit)."""

import os

from dotenv import load_dotenv

load_dotenv()


def get(key: str, default=None):
    return os.getenv(key, default)


def spotify_client_id():
    return get("SPOTIFY_CLIENT_ID")


def spotify_client_secret():
    return get("SPOTIFY_CLIENT_SECRET")


def spotify_redirect_uri():
    return get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8000/auth/callback")


def frontend_url():
    return get("FRONTEND_URL", "http://127.0.0.1:3000").rstrip("/")


def groq_api_key():
    return get("GROQ_API_KEY")


def lastfm_api_key():
    return get("LASTFM_API_KEY")


SPOTIFY_SCOPES = [
    "user-read-private",
    "user-read-currently-playing",
    "user-read-recently-played",
    "user-top-read",
    "user-library-read",
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
    "playlist-modify-public",
]
