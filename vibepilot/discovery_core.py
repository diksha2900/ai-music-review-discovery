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


LANE_KEYWORDS: dict[str, set[str]] = {
    "devotional": {
        "devotional", "bhajan", "spiritual", "sufi", "gospel", "christian", "hindu",
        "mantra", "kirtan", "aarti", "aart", "arti", "worship", "prayer", "shabad",
        "qawwali", "gurbani", "keerthanam", "stotram", "stuti", "chalisa", "abhang",
        "carnatic", "hindustani classical", "indian classical",
        "shri", "shree", "jai ", " om ", "hare krishna", "hanuman", "balaji", "vishnu",
        "durga", "laxmi", "lakshmi", "saraswati", "ganpati", "ganesh", "murugan",
        "prabhu", "bhagwan", "devi", "krishna", "ram ", "shiva", "sai baba", "guru",
        "naam simran", "suprabhatam", "arthi", "archana",
    },
    "romantic": {
        "romance", "romantic", "love song", "heartbreak", "ballad", "soft rock",
        "pyaar", "pyar", "ishq", "mohabbat", "valentine", "darling", "girlfriend",
        "boyfriend", "love you", "fall in love", "breakup", "broken heart",
    },
    "hip_hop": {"hip hop", "rap", "trap", "drill", "desi hip hop"},
}

LANE_BLOCK: dict[str, set[str]] = {
    "devotional": {"romantic"},
    "romantic": {"devotional"},
}


def _detect_lanes(genres: set[str], title: str = "", artist: str = "") -> set[str]:
    blob = (" ".join(genres) + " " + title + " " + artist).lower()
    out: set[str] = set()
    for lane, kws in LANE_KEYWORDS.items():
        if any(k in blob for k in kws):
            out.add(lane)
    return out


def _lanes_compatible(anchor_lanes: set[str], cand_lanes: set[str]) -> bool:
    for lane in anchor_lanes:
        blocked = LANE_BLOCK.get(lane, set())
        if blocked & cand_lanes:
            return False
    return True


def _feature_align(a: dict, b: dict) -> float:
    """Bonus for matching mood profile (valence, acousticness, energy)."""
    if not a or not b:
        return 0.0
    bonus = 0.0
    for key, w in (("valence", 2.5), ("acousticness", 2.0), ("energy", 1.2)):
        va, vb = a.get(key), b.get(key)
        if va is not None and vb is not None:
            bonus += w * (1.0 - min(1.0, abs(va - vb)))
    return bonus


def _genre_tokens(genres: set[str]) -> set[str]:
    toks: set[str] = set()
    for g in genres:
        toks.update(g.replace("-", " ").split())
    return toks


def _genre_overlap(anchor_genres: set[str], cand_genres: set[str]) -> float:
    """1.0 = same lane, 0.0 = unrelated genre cluster."""
    if not anchor_genres or not cand_genres:
        return 0.35
    if anchor_genres & cand_genres:
        return 1.0
    at, ct = _genre_tokens(anchor_genres), _genre_tokens(cand_genres)
    shared = at & ct
    if shared:
        return 0.55 + min(0.45, len(shared) * 0.15)
    return 0.0


def rank_by_beat_and_genre(anchor, candidates):
    """Rank by tempo/feel, genre lane, and mood profile (valence/acousticness)."""
    ranked, anchor_tag = rank_by_beat(anchor, candidates)
    anchor_ids = anchor.get("artist_ids") or []
    anchor_genres: set[str] = set()
    for gs in spotify_client.batch_artist_genres(anchor_ids[:2]).values():
        anchor_genres.update(gs)

    anchor_lanes = _detect_lanes(anchor_genres, anchor.get("name", ""), anchor.get("artist", ""))
    cand_ids = [(c.get("artist_ids") or [None])[0] for c in ranked]
    genre_map = spotify_client.batch_artist_genres([i for i in cand_ids if i])

    anchor_id = anchor.get("id")
    feats = reccobeats_client.audio_features([anchor_id] + [c.get("id") for c in ranked if c.get("id")])
    a_feats = feats.get(anchor_id) if anchor_id else None

    def score(c):
        cf = feats.get(c.get("id"))
        beat = reccobeats_client.distance(a_feats, cf) if a_feats and cf else 50.0
        aid = (c.get("artist_ids") or [None])[0]
        cand_g = set(genre_map.get(aid, []))
        cand_lanes = _detect_lanes(cand_g, c.get("name", ""), c.get("artist", ""))
        if not _lanes_compatible(anchor_lanes, cand_lanes):
            return 999.0
        genre_bonus = _genre_overlap(anchor_genres, cand_g)
        mood_bonus = _feature_align(a_feats, cf)
        return beat - 8.0 * genre_bonus - mood_bonus

    graded = [c for c in ranked if feats.get(c.get("id"))]
    ungraded = [c for c in ranked if not feats.get(c.get("id"))]
    graded.sort(key=score)
    graded = [c for c in graded if score(c) < 100]
    # Devotional anchors: drop anything that still looks romantic by title/artist
    if "devotional" in anchor_lanes:
        graded = [
            c for c in graded
            if "romantic" not in _detect_lanes(set(), c.get("name", ""), c.get("artist", ""))
        ]
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
        ranked, anchor_tag = rank_by_beat_and_genre(anchor, candidates)
        tracks = ranked[:COUSINS_N]

    if not tracks:
        ag = spotify_client.batch_artist_genres((anchor.get("artist_ids") or [])[:2])
        genres = [g for gs in ag.values() for g in gs[:4]]
        anchor_desc = f"'{label}'"
        lanes = _detect_lanes(set(genres), title, artist)
        if lanes:
            anchor_desc += f" (MUST stay in lane: {', '.join(sorted(lanes))} — NOT romantic love songs if devotional)"
        elif genres:
            anchor_desc += f" (stay in genre lane: {', '.join(genres[:6])})"
        picks = vibe_engine.propose_cousins(
            anchor_desc, n=COUSINS_N, taste=taste, exclude_names=exclude,
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
