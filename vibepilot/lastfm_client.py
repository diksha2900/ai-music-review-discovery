"""Last.fm API client — the real-data similarity engine.

This replaces LLM guesswork with actual co-listening data:
  • track.getSimilar  → "what people who like X also play" (YouTube-style radio)
  • tag.getTopTracks  → tracks humans actually tagged with a mood (chill, party…)

The LLM is reduced to picking a few accurate seed songs + writing rationales;
Last.fm does the heavy lifting of finding genuinely similar, on-vibe tracks.
"""

import requests

from config import get_lastfm_api_key

API = "https://ws.audioscrobbler.com/2.0/"


def is_configured() -> bool:
    return bool(get_lastfm_api_key())


def _get(method: str, **params) -> dict:
    params.update(method=method, api_key=get_lastfm_api_key(), format="json")
    resp = requests.get(API, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def similar_tracks(artist: str, track: str, limit: int = 60) -> list[dict]:
    """Songs Last.fm considers similar to a given track (real co-listening data)."""
    try:
        data = _get("track.getsimilar", artist=artist, track=track,
                    limit=limit, autocorrect=1)
        items = data.get("similartracks", {}).get("track", []) or []
        out = []
        for t in items:
            name = t.get("name")
            art = (t.get("artist") or {}).get("name")
            if name and art:
                out.append({"name": name, "artist": art, "match": float(t.get("match") or 0)})
        return out
    except Exception:
        return []


def tag_top_tracks(tag: str, limit: int = 60) -> list[dict]:
    """Tracks humans tagged with a mood/genre (e.g. 'chillout', 'party')."""
    try:
        data = _get("tag.gettoptracks", tag=tag, limit=limit)
        items = data.get("tracks", {}).get("track", []) or []
        out = []
        for t in items:
            name = t.get("name")
            art = (t.get("artist") or {}).get("name")
            if name and art:
                out.append({"name": name, "artist": art, "match": 0.0})
        return out
    except Exception:
        return []


def artist_top_tracks(artist: str, limit: int = 15) -> list[dict]:
    try:
        data = _get("artist.gettoptracks", artist=artist, limit=limit, autocorrect=1)
        items = data.get("toptracks", {}).get("track", []) or []
        return [{"name": t["name"], "artist": artist, "match": 0.0}
                for t in items if t.get("name")]
    except Exception:
        return []
