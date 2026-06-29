"""ReccoBeats API client — the audio-feature (tempo/beat/energy) engine.

Free, no-auth replacement for Spotify's deprecated Audio Features endpoint.
Given Spotify track IDs it returns tempo (BPM), energy, danceability, acousticness,
valence, etc. — which lets us rank candidate songs by how closely their BEAT and
FEEL match an anchor song (the core of the 'cousins' idea).

Docs: https://reccobeats.com/docs/apis/get-track-audio-features
"""

import requests

API = "https://api.reccobeats.com/v1"


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def audio_features(spotify_ids: list[str]) -> dict:
    """Map Spotify track id -> audio-feature dict (tempo, energy, danceability…)."""
    out = {}
    ids = [i for i in dict.fromkeys(spotify_ids) if i]  # unique, drop falsy
    for chunk in _chunks(ids, 40):
        try:
            resp = requests.get(f"{API}/audio-features",
                                params={"ids": ",".join(chunk)}, timeout=20)
            resp.raise_for_status()
            for item in resp.json().get("content", []):
                href = item.get("href", "") or ""
                sid = href.rstrip("/").split("/")[-1] if href else None
                if sid:
                    out[sid] = item
        except Exception:
            continue
    return out


def feature_tag(f: dict) -> str:
    """A short human tag from audio features, e.g. '🥁 ~120 BPM · acoustic · chill'."""
    if not f:
        return ""
    bpm = f.get("tempo")
    energy = f.get("energy", 0)
    acoustic = f.get("acousticness", 0)
    energy_word = "chill" if energy < 0.4 else ("energetic" if energy > 0.7 else "mid-energy")
    texture = "acoustic" if acoustic > 0.5 else "produced"
    parts = []
    if bpm:
        parts.append(f"~{round(bpm)} BPM")
    parts.append(texture)
    parts.append(f"{energy_word} energy")
    return "🥁 " + " · ".join(parts)


def distance(a: dict, b: dict) -> float:
    """Weighted distance between two feature sets — lower = closer beat/feel."""
    if not a or not b:
        return 999.0
    def g(d, k):
        v = d.get(k)
        return float(v) if v is not None else None

    d = 0.0
    ta, tb = g(a, "tempo"), g(b, "tempo")
    if ta is not None and tb is not None:
        d += 2.2 * ((ta - tb) / 40.0) ** 2          # tempo/BPM matters most
    for key, w in (("energy", 1.6), ("danceability", 1.4),
                   ("acousticness", 1.2), ("valence", 0.7), ("instrumentalness", 0.6)):
        va, vb = g(a, key), g(b, key)
        if va is not None and vb is not None:
            d += w * (va - vb) ** 2
    return d
