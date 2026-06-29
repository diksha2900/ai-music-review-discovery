"""Thin Spotify Web API wrapper (only 2026-available endpoints).

All calls use the bearer token from auth.get_valid_token().
"""

import requests

import auth

API = "https://api.spotify.com/v1"


def _headers(app_ok=False):
    token = auth.get_valid_token()
    if not token and app_ok:
        token = auth.get_app_token()  # guest mode: public catalog only
    if not token:
        if app_ok and not auth.spotify_configured():
            raise RuntimeError(
                "Spotify API keys missing. In Streamlit Cloud → Settings → Secrets, "
                "set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET."
            )
        if app_ok:
            raise RuntimeError(
                "Could not connect to Spotify. Check SPOTIFY_CLIENT_ID and "
                "SPOTIFY_CLIENT_SECRET in Streamlit Secrets."
            )
        raise RuntimeError("Not authenticated with Spotify.")
    return {"Authorization": f"Bearer {token}"}


def _get(path, params=None, app_ok=False):
    resp = requests.get(f"{API}{path}", headers=_headers(app_ok), params=params, timeout=20)
    resp.raise_for_status()
    return resp.json() if resp.text else {}


def _post(path, json=None, params=None):
    resp = requests.post(f"{API}{path}", headers=_headers(), json=json, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json() if resp.text else {}


# ---------- Phase 0 ----------

def me() -> dict:
    """Current user's profile (GET /me)."""
    return _get("/me")


# ---------- Phase 1 ----------

def search_track(title: str, artist: str = "") -> dict | None:
    """Search for a single best-match track. Returns a simplified dict or None."""
    query = f"track:{title}"
    if artist:
        query += f" artist:{artist}"
    data = _get("/search", params={"q": query, "type": "track", "limit": 1}, app_ok=True)
    items = data.get("tracks", {}).get("items", [])
    if not items:
        # fallback: loose query
        data = _get("/search", params={"q": f"{title} {artist}".strip(), "type": "track", "limit": 1}, app_ok=True)
        items = data.get("tracks", {}).get("items", [])
    if not items:
        return None
    return _simplify_track(items[0])


def search_tracks(query: str, limit: int = 10) -> list[dict]:
    """Free-text search — multiple matches for autocomplete pickers. Works in guest mode."""
    q = query.strip()
    if not q:
        return []
    limit = min(max(limit, 1), 20)
    data = _get("/search", params={"q": q, "type": "track", "limit": limit}, app_ok=True)
    return [_simplify_track(t) for t in data.get("tracks", {}).get("items", []) if t]


def _simplify_track(t: dict) -> dict:
    return {
        "id": t["id"],
        "uri": t["uri"],
        "name": t["name"],
        "artist": ", ".join(a["name"] for a in t.get("artists", [])),
        "artist_ids": [a["id"] for a in t.get("artists", [])],
        "album_art": (t.get("album", {}).get("images") or [{}])[0].get("url"),
        "url": t.get("external_urls", {}).get("spotify"),
        "preview_url": t.get("preview_url"),
    }


# ---------- Phase 2 (personalization + exclusion) ----------

def recently_played(limit: int = 50) -> list[dict]:
    data = _get("/me/player/recently-played", params={"limit": min(limit, 50)})
    out = []
    for item in data.get("items", []):
        t = _simplify_track(item["track"])
        t["played_at"] = item.get("played_at")
        out.append(t)
    return out


def saved_tracks(limit: int = 50) -> list[dict]:
    data = _get("/me/tracks", params={"limit": min(limit, 50)})
    return [_simplify_track(item["track"]) for item in data.get("items", [])]


def top_artists(limit: int = 20, time_range: str = "medium_term") -> list[dict]:
    """GET /me/top/artists — used to build the taste profile."""
    data = _get("/me/top/artists", params={"limit": min(limit, 50), "time_range": time_range})
    return [
        {"name": a["name"], "genres": a.get("genres", []), "id": a["id"]}
        for a in data.get("items", [])
    ]


def top_tracks(limit: int = 20, time_range: str = "medium_term") -> list[dict]:
    """GET /me/top/tracks — taste profile."""
    data = _get("/me/top/tracks", params={"limit": min(limit, 50), "time_range": time_range})
    return [_simplify_track(t) for t in data.get("items", [])]


def build_taste_profile() -> dict:
    """Compact summary of the user's taste for grounding LLM proposals."""
    profile = {"top_artists": [], "top_genres": [], "top_tracks": [], "recent": []}
    try:
        artists = top_artists(limit=20)
        profile["top_artists"] = [a["name"] for a in artists]
        genre_counts = {}
        for a in artists:
            for g in a["genres"]:
                genre_counts[g] = genre_counts.get(g, 0) + 1
        profile["top_genres"] = [
            g for g, _ in sorted(genre_counts.items(), key=lambda x: -x[1])
        ][:12]
    except Exception:
        pass
    try:
        profile["top_tracks"] = [f"{t['name']} — {t['artist']}" for t in top_tracks(limit=15)]
    except Exception:
        pass
    try:
        profile["recent"] = [
            {"name": f"{t['name']} — {t['artist']}", "played_at": t.get("played_at")}
            for t in recently_played(limit=30)
        ]
    except Exception:
        pass
    return profile


# ---------- Phase 3/4 ----------

def currently_playing() -> dict | None:
    resp = requests.get(f"{API}/me/player/currently-playing", headers=_headers(), timeout=20)
    if resp.status_code == 204 or not resp.text:
        return None
    resp.raise_for_status()
    payload = resp.json()
    item = payload.get("item")
    if not item:
        return None
    track = _simplify_track(item)
    track["progress_ms"] = payload.get("progress_ms", 0)
    track["duration_ms"] = item.get("duration_ms", 0)
    track["is_playing"] = payload.get("is_playing", False)
    return track


def create_playlist(name: str, description: str = "", public: bool = False) -> dict:
    user_id = me()["id"]
    return _post(
        f"/users/{user_id}/playlists",
        json={"name": name, "description": description, "public": public},
    )


def add_tracks(playlist_id: str, uris: list[str]):
    if not uris:
        return
    _post(f"/playlists/{playlist_id}/tracks", json={"uris": uris})


def my_playlists(limit: int = 50) -> list[dict]:
    """The user's own (modifiable) playlists — for 'add to existing'."""
    uid = me()["id"]
    data = _get("/me/playlists", params={"limit": min(limit, 50)})
    out = []
    for p in data.get("items", []):
        if p.get("owner", {}).get("id") == uid:
            out.append({
                "id": p["id"],
                "name": p["name"],
                "url": p.get("external_urls", {}).get("spotify"),
            })
    return out
