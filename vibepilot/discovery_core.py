"""Pure-Python discovery helpers — shared by Streamlit app and FastAPI backend."""

import re

import lastfm_client
import reccobeats_client
import spotify_client
import vibe_engine

COUSINS_N = 8
VIBE_N = 15


def _clean_title(title: str) -> str:
    t = re.split(r"\s*[\(\[]", title)[0]
    t = re.split(r"\s*-\s*[Ff]rom", t)[0]
    t = re.split(r"\s*[-–]\s*", t)[0] if " - " in t else t
    return t.strip() or title.strip()


def _artist_candidates(artist: str) -> list[str]:
    parts = re.split(r",|&|\bfeat\.?\b|\bft\.?\b|\bx\b", artist, flags=re.IGNORECASE)
    out, seen = [], set()
    for p in parts:
        p = p.strip()
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return out or [artist.strip()]


def lastfm_similar_robust(title: str, artist: str, limit: int = 60) -> list[dict]:
    clean = _clean_title(title)
    for cand in _artist_candidates(artist):
        pool = lastfm_client.similar_tracks(cand, clean, limit=limit)
        if pool:
            return pool
        if clean != title:
            pool = lastfm_client.similar_tracks(cand, title, limit=limit)
            if pool:
                return pool
    return []


def dedupe_filter(pool, exclude, want, discovery=False, taste=None, block_artists=None):
    excl = {e.lower() for e in (exclude or [])}
    known_artists = {a.lower() for a in (block_artists or [])}
    if discovery and taste:
        known_artists |= {a.lower() for a in taste.get("top_artists", [])}
    pool = sorted(pool, key=lambda t: t.get("match", 0), reverse=True)
    seen_keys, seen_artists, out = set(), set(), []
    for t in pool:
        name, art = t.get("name", "").strip(), t.get("artist", "").strip()
        if not name or not art:
            continue
        key = f"{name} — {art}".lower()
        al = art.lower()
        if key in excl or key in seen_keys or al in seen_artists:
            continue
        if discovery and al in known_artists:
            continue
        seen_keys.add(key)
        seen_artists.add(al)
        out.append({"title": name, "artist": art})
        if len(out) >= want + 10:
            break
    return out


def resolve_pool(picks, want):
    out = []
    for p in picks:
        try:
            tr = spotify_client.search_track(p["title"], p["artist"])
        except Exception:
            tr = None
        if tr:
            tr["why"] = p.get("why", "") if isinstance(p, dict) else ""
            out.append(tr)
        if len(out) >= want:
            break
    return out


def resolve_picks(picks):
    resolved = []
    for p in picks:
        try:
            track = spotify_client.search_track(p["title"], p["artist"])
        except Exception:
            track = None
        if track:
            track["why"] = p.get("why", "")
            resolved.append(track)
    return resolved


def rank_by_beat(anchor, candidates):
    anchor_id = anchor.get("id")
    ids = ([anchor_id] if anchor_id else []) + [c.get("id") for c in candidates]
    feats = reccobeats_client.audio_features(ids)
    a = feats.get(anchor_id) if anchor_id else None
    anchor_tag = reccobeats_client.feature_tag(a) if a else ""

    for c in candidates:
        f = feats.get(c.get("id"))
        if f:
            c["why"] = reccobeats_client.feature_tag(f)

    if not a:
        return candidates, anchor_tag

    graded = [c for c in candidates if feats.get(c.get("id"))]
    ungraded = [c for c in candidates if not feats.get(c.get("id"))]
    graded.sort(key=lambda c: reccobeats_client.distance(a, feats.get(c.get("id"))))
    return graded + ungraded, anchor_tag


def rank_by_centroid(seeds, candidates):
    seed_ids = [s.get("id") for s in seeds if s.get("id")]
    cand_ids = [c.get("id") for c in candidates]
    feats = reccobeats_client.audio_features(seed_ids + cand_ids)
    seed_feats = [feats[i] for i in seed_ids if feats.get(i)]
    if not seed_feats:
        return candidates

    keys = ("tempo", "energy", "danceability", "acousticness", "valence", "instrumentalness")
    centroid = {}
    for k in keys:
        vals = [f[k] for f in seed_feats if f.get(k) is not None]
        if vals:
            centroid[k] = sum(vals) / len(vals)

    graded = [c for c in candidates if feats.get(c.get("id"))]
    ungraded = [c for c in candidates if not feats.get(c.get("id"))]
    for c in graded:
        c["why"] = reccobeats_client.feature_tag(feats.get(c.get("id")))
    graded.sort(key=lambda c: reccobeats_client.distance(centroid, feats.get(c.get("id"))))
    return graded + ungraded


def attach_whys(tracks, context, kind):
    if not tracks:
        return
    items = [f"{t['name']} — {t['artist']}" for t in tracks]
    try:
        whys = vibe_engine.annotate_whys(items, context, kind=kind)
    except Exception:
        whys = []
    for i, t in enumerate(tracks):
        t["why"] = whys[i] if i < len(whys) else ""


def vibe_via_lastfm(vibe_text, label, taste, familiarity, exclude):
    plan = vibe_engine.vibe_plan(vibe_text, taste, n=5)
    pool = []
    for s in plan.get("seeds", []):
        pool += lastfm_similar_robust(s["title"], s["artist"], limit=50)
    if len(pool) < 30:
        for tag in plan.get("tags", [])[:4]:
            pool += lastfm_client.tag_top_tracks(tag, limit=40)
    if familiarity >= 8:
        for s in plan.get("seeds", []):
            pool.insert(0, {"name": s["title"], "artist": s["artist"], "match": 1.0})
    discovery = familiarity <= 4
    picks = dedupe_filter(pool, exclude, want=VIBE_N, discovery=discovery, taste=taste)
    tracks = resolve_pool(picks, VIBE_N)
    attach_whys(tracks, label, "vibe")
    return tracks


def find_cousins_for_anchor(anchor, taste=None, exclude=None, moment=None):
    title, artist = anchor["name"], anchor["artist"]
    exclude = exclude or []
    label = f"{title} — {artist}"
    anchor_tag = ""
    tracks = []

    if lastfm_client.is_configured():
        pool = lastfm_similar_robust(title, artist, limit=120)
        block = _artist_candidates(artist) + [artist]
        picks = dedupe_filter(
            pool, exclude, want=COUSINS_N * 4, discovery=True,
            taste=taste, block_artists=block,
        )
        candidates = resolve_pool(picks, COUSINS_N * 4)
        ranked, anchor_tag = rank_by_beat(anchor, candidates)
        tracks = ranked[:COUSINS_N]

    if not tracks:
        picks = vibe_engine.propose_cousins(
            f"'{label}'", n=COUSINS_N, taste=taste, exclude_names=exclude,
            moment=(f"{label} at {moment}" if moment else None),
        )
        tracks = resolve_picks(picks)

    return {"anchor": anchor, "anchor_tag": anchor_tag, "label": label, "tracks": tracks}


def build_vibe_session(text, familiarity=5, taste=None, exclude=None):
    exclude = exclude or []
    label = text[:40]

    if lastfm_client.is_configured():
        tracks = vibe_via_lastfm(text, label, taste, familiarity, exclude)
    else:
        picks = vibe_engine.propose_vibe_session(
            text, n=VIBE_N + 6, taste=taste, exclude_names=exclude, familiarity=familiarity,
        )
        tracks = resolve_picks(picks)[:VIBE_N]

    return {"label": label, "tracks": tracks}


def break_loop(seeds: list[dict], exclude=None):
    seeds = seeds[:8]
    if not seeds:
        raise ValueError("Add at least one song")

    exclude = list(exclude or [])
    block = []
    for s in seeds:
        block += _artist_candidates(s["artist"]) + [s["artist"]]
    exclude += [f"{s['name']} — {s['artist']}" for s in seeds]

    pool = []
    for s in seeds:
        pool += lastfm_similar_robust(s["name"], s["artist"], limit=60)
    picks = dedupe_filter(pool, exclude, want=VIBE_N * 3, discovery=True, taste=None, block_artists=block)
    candidates = resolve_pool(picks, VIBE_N * 3)
    tracks = rank_by_centroid(seeds, candidates)[:VIBE_N]

    if not tracks:
        names = ", ".join(f"{s['name']} ({s['artist']})" for s in seeds)
        llm_picks = vibe_engine.propose_cousins(
            f"songs that feel like: {names}", n=VIBE_N, exclude_names=exclude,
        )
        tracks = resolve_picks(llm_picks)

    return {"label": "Escape Your Loop", "tracks": tracks}
