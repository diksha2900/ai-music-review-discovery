"""Shared config: reads from Streamlit secrets or environment (.env)."""

import os

from dotenv import load_dotenv

load_dotenv()


def _get(key: str, default=None):
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st

        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


def get_spotify_client_id():
    return _get("SPOTIFY_CLIENT_ID")


def get_spotify_client_secret():
    return _get("SPOTIFY_CLIENT_SECRET")


def get_spotify_redirect_uri():
    return _get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8502")


def get_groq_api_key():
    return _get("GROQ_API_KEY")


def get_lastfm_api_key():
    return _get("LASTFM_API_KEY")


# Spotify scopes needed for the four mechanisms (Phase-gated).
SPOTIFY_SCOPES = [
    "user-read-private",            # profile (create playlist under user id)
    "user-read-currently-playing",  # Catch That + "Get the Vibe" from playing
    "user-read-recently-played",    # exclusion + time-of-day taste
    "user-top-read",                # taste profile (top artists/genres)
    "user-library-read",            # exclusion (Liked)
    "playlist-read-private",        # list user's own playlists (add-to-existing)
    "playlist-read-collaborative",
    "playlist-modify-private",      # save session + Caught playlist
    "playlist-modify-public",
]
