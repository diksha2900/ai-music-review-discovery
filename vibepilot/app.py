"""VibePilot AI — Streamlit entry point.

Flow:
  Login → taste profile → pick an anchor (now-playing / inferred vibe / song / intent)
  → AI reveals its COUSINS: unheard songs that share the same musical family
    (any era, any country, hidden gems) → save them as a real Spotify playlist.
Run: streamlit run app.py --server.port 8502
"""

import datetime
import re

import streamlit as st

import auth
import capture
import lastfm_client
import reccobeats_client
import spotify_client
import time_utils
import ui
import vibe_engine

st.set_page_config(page_title="VibePilot AI", page_icon="🎧", layout="wide", initial_sidebar_state="expanded")
ui.inject()


# ----------------------------- OAuth redirect -----------------------------

def handle_redirect():
    params = st.query_params
    if "code" in params and not auth.is_logged_in():
        returned_state = params.get("state")
        expected_state = st.session_state.get("oauth_state")
        if expected_state and returned_state and returned_state != expected_state:
            st.error("OAuth state mismatch — please try logging in again.")
            st.query_params.clear()
            return
        if auth.exchange_code(params["code"]):
            st.query_params.clear()
            st.rerun()
        else:
            st.error(f"Login failed: {st.session_state.get('auth_error', 'unknown error')}")
            st.query_params.clear()


# ------------------------------- Login view -------------------------------

def render_login():
    ui.hero(
        desc="Give us a song you love — we'll find unheard songs with the same tempo, beat & vibe.",
    )
    st.markdown('<div class="vp-section" style="max-width:640px;margin:0 auto;">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✨ Try it now", type="primary", use_container_width=True):
            st.session_state["guest"] = True
            st.rerun()
        st.caption("No account needed.")
    with c2:
        if auth.spotify_configured():
            st.link_button("Log in with Spotify", auth.build_authorize_url(), use_container_width=True)
        else:
            st.button("Log in with Spotify", disabled=True, use_container_width=True)
        st.caption("Unlocks now-playing & save.")
    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------ Data loading ------------------------------

def ensure_profile():
    if "spotify_profile" not in st.session_state:
        st.session_state["spotify_profile"] = spotify_client.me()
    return st.session_state["spotify_profile"]


def ensure_taste():
    if "taste_profile" not in st.session_state:
        with st.spinner("Learning your taste…"):
            st.session_state["taste_profile"] = spotify_client.build_taste_profile()
    return st.session_state["taste_profile"]


# -------------------------------- Home view -------------------------------

VIBE_N = 15
COUSINS_N = 8
NAV_PAGES = ["Home", "Find Cousins", "Break My Loop", "Start From Vibe", "About"]

MOOD_CHIPS = {
    "😌 Chill": "chilled-out and laid-back — easy-going, breezy, relaxed",
    "🏋️ Gym": vibe_engine.INTENT_PRESETS["💪 Gym"],
    "🌧 Rain": "rainy day — soft, introspective, mellow, emotional",
    "🚗 Drive": vibe_engine.INTENT_PRESETS["🚗 Driving"],
    "🌙 Late Night": "late night — moody, slow, intimate, after midnight feel",
    "📚 Focus": vibe_engine.INTENT_PRESETS["🎯 Focus"],
    "💔 Heartbreak": "heartbreak — raw, emotional, bittersweet, not angry",
    "✨ Main Character": "main-character energy — cinematic, confident, epic",
}

DISCOVERY_MAP = {
    "Familiar favorites": 10,
    "Mostly familiar": 8,
    "Balanced": 5,
    "Mostly new": 3,
    "All new (discover)": 0,
}


def _render_sidebar(guest: bool, name: str | None = None):
    with st.sidebar:
        st.markdown('<div class="vp-logo">🎧 <span>VibePilot</span></div>', unsafe_allow_html=True)
        page = st.radio(
            "Navigate",
            NAV_PAGES,
            label_visibility="collapsed",
            key="vp_page",
        )
        st.markdown(
            '<p class="vp-tagline"><em>Same feel, different blood.</em></p>',
            unsafe_allow_html=True,
        )
        if name:
            st.caption(f"Signed in as **{name}**")
        elif guest and auth.spotify_configured():
            st.link_button("Log in with Spotify", auth.build_authorize_url(), use_container_width=True)
        elif not guest:
            if st.button("Log out", use_container_width=True):
                auth.logout()
                for k in ("spotify_profile", "taste_profile", "vibe_session", "shown_tracks",
                          "selected_intent", "pending_gen", "now_playing", "saved_playlist",
                          "my_playlists", "guest", "loop_queue", "cousin_hits", "loop_hits"):
                    st.session_state.pop(k, None)
                st.rerun()
    return page


def render_home():
    guest = st.session_state.get("guest") and not auth.is_logged_in()
    taste = None
    name = None

    if guest:
        if not auth.spotify_configured():
            st.error("⚠️ Spotify API keys missing in Streamlit Secrets — search won't work until fixed.")
    else:
        try:
            profile = ensure_profile()
            name = profile.get("display_name") or profile.get("id")
            taste = ensure_taste()
        except Exception as e:
            st.error(f"Couldn't load your Spotify profile: {e}")
            if st.button("Log out"):
                auth.logout()
                st.rerun()
            return

    page = _render_sidebar(guest, name)

    if page == "Home":
        _page_home()
    elif page == "Find Cousins":
        _page_find_cousins(guest)
    elif page == "Break My Loop":
        _page_break_loop()
    elif page == "Start From Vibe":
        _page_start_vibe(taste)
    elif page == "About":
        _page_about()

    _render_session(guest=guest)


def _page_home():
    ui.hero(
        desc="Give us a song you love. We'll find songs you've never heard with the same tempo, beat & vibe.",
    )
    c1, c2, c3 = st.columns([13, 4, 3])
    with c1:
        if st.button("✨ Find Cousins", type="primary", use_container_width=True):
            st.session_state["vp_page"] = "Find Cousins"
            st.rerun()
    with c2:
        if st.button("Break My Loop", type="secondary", use_container_width=True):
            st.session_state["vp_page"] = "Break My Loop"
            st.rerun()
    with c3:
        if st.button("Start From Vibe", type="secondary", use_container_width=True):
            st.session_state["vp_page"] = "Start From Vibe"
            st.rerun()
    ui.catch_that_teaser()


def _page_about():
    ui.section_title("About <span>VibePilot</span>", "One discovery engine — multiple entry points.")
    st.markdown(
        '<div class="vp-section"><p class="vp-sub" style="margin:0;">'
        "VibePilot finds songs with the <b>same feel</b> — tempo, beat, mood — not the same artist. "
        "Start with a song, break a loop, or describe a vibe.</p></div>",
        unsafe_allow_html=True,
    )
    ui.about_pillars()
    ui.catch_that_teaser()


def _page_header(title_html: str, subtitle: str = ""):
    ui.section_title(title_html.replace('<div class="vp-page-title">', "").replace("</div>", ""), subtitle)


def _adventure_slider(key: str = "cousins_adventure"):
    st.caption("How adventurous? · Familiar ← → Adventurous")
    return st.select_slider(
        "How adventurous?",
        options=list(DISCOVERY_MAP.keys()),
        value=st.session_state.get(key, "Balanced"),
        key=key,
        label_visibility="collapsed",
    )


def _resolve_spotify_link(url: str) -> dict | None:
    m = re.search(r"(?:spotify\.com|spotify:)track[/:]([A-Za-z0-9]+)", url.strip())
    if m:
        try:
            data = spotify_client._get(f"/tracks/{m.group(1)}", app_ok=True)
            return spotify_client._simplify_track(data)
        except Exception:
            pass
    return _resolve_song_query(url.strip())


def _show_selected_track(track: dict):
    tag = _track_bpm_tag(track)
    ui.anchor_card(track["name"], track["artist"], tag.replace(" · ", " · ") if tag else "Selected", track.get("album_art"))


def _track_bpm_tag(track: dict) -> str:
    tid = track.get("id")
    if not tid:
        return ""
    feats = reccobeats_client.audio_features([tid])
    f = feats.get(tid)
    return reccobeats_client.feature_tag(f) if f else ""


def _page_find_cousins(guest: bool):
    st.markdown('<div class="vp-section vp-section-hero">', unsafe_allow_html=True)
    ui.section_title("Find <span>Cousins</span>", "Same tempo, beat & feel — different artists.")
    _adventure_slider()

    tab_np, tab_search, tab_link = st.tabs(["Now Playing", "Search Song", "Paste Spotify Link"])
    with tab_np:
        if guest:
            st.info("Log in with Spotify to use now-playing.")
        else:
            _now_playing_card()
    with tab_search:
        _render_cousin_search()
    with tab_link:
        _render_cousin_link()
    st.markdown("</div>", unsafe_allow_html=True)


def _render_cousin_link():
    link = st.text_input(
        "Spotify link",
        placeholder="Paste open.spotify.com/track/…",
        key="cousin_link",
        label_visibility="collapsed",
    )
    if st.button("✨ Find Cousins", type="primary", key="cousin_link_go"):
        if not link.strip():
            st.warning("Paste a Spotify track link first.")
        else:
            track = _resolve_spotify_link(link)
            if track:
                _generate_cousins(track)
                st.rerun()
            else:
                st.error("Couldn't read that link — try Search Song instead.")


def _page_break_loop():
    st.markdown('<div class="vp-section vp-section-sm">', unsafe_allow_html=True)
    ui.section_title(
        "Stuck in the <span>same 5 songs?</span>",
        "Add songs you keep replaying — we'll break the loop.",
    )
    _render_break_loop_body()
    st.markdown("</div>", unsafe_allow_html=True)


def _page_start_vibe(taste):
    st.markdown('<div class="vp-section">', unsafe_allow_html=True)
    ui.section_title("Start from a <span>vibe</span>", "Pick a mood or describe it in words.")
    render_moment(taste)
    st.markdown("</div>", unsafe_allow_html=True)


def _now_playing_card():
    try:
        np = spotify_client.currently_playing()
    except Exception:
        np = None
    if np:
        pos = np.get("progress_ms", 0) // 1000
        mm, ss = divmod(pos, 60)
        tag = _track_bpm_tag(np)
        ui.anchor_card(np["name"], f"{np['artist']} · {mm}:{ss:02d}", tag or "Now playing", np.get("album_art"))
        if st.button("✨ Find Cousins", type="primary", use_container_width=True, key="np_cousins"):
            _generate_cousins(np, at=f"{mm}:{ss:02d}")
            st.rerun()
    else:
        st.markdown(
            '<p class="vp-sub">Press play on Spotify, then refresh.</p>',
            unsafe_allow_html=True,
        )
        if st.button("Refresh", type="secondary", key="np_refresh2"):
            st.rerun()


def _track_label(t: dict) -> str:
    return f"{t['name']} — {t['artist']}"


def _run_song_search(query: str, hits_key: str, err_key: str) -> list[dict]:
    """Fetch Spotify matches and cache in session (called on Search button click)."""
    q = query.strip()
    if len(q) < 2:
        st.session_state[hits_key] = []
        st.session_state[err_key] = "Type at least 2 characters."
        return []
    try:
        hits = spotify_client.search_tracks(q, limit=10)
        st.session_state[hits_key] = hits
        st.session_state.pop(err_key, None)
    except Exception as e:
        st.session_state[hits_key] = []
        st.session_state[err_key] = str(e)
    return st.session_state.get(hits_key, [])


def _render_spotify_hits(hits: list[dict], err_key: str, key_prefix: str, action_label: str) -> dict | None:
    """Show Spotify results as visible pickable rows. Returns track if user clicks action."""
    if not hits:
        err = st.session_state.get(err_key)
        if err:
            st.warning(f"Search failed: {err}")
        else:
            st.info("No songs found on Spotify — try another spelling or add the artist name.")
        return None

    st.markdown('<p style="color:#1DB954;font-size:0.75rem;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;margin:0.75rem 0;">Pick a match</p>', unsafe_allow_html=True)
    labels = [_track_label(t) for t in hits]
    pick = st.radio(
        "Spotify matches",
        labels,
        key=f"{key_prefix}_radio",
        label_visibility="collapsed",
    )
    idx = labels.index(pick)
    t = hits[idx]
    _show_selected_track(t)
    if st.button(action_label, type="primary", use_container_width=True, key=f"{key_prefix}_go"):
        return t
    return None


def _render_cousin_search():
    query = st.text_input(
        "Search song",
        placeholder="Search a song… e.g. kabira, cold mess",
        key="cousin_query",
        label_visibility="collapsed",
        autocomplete="off",
    )
    _, c2 = st.columns([3, 1])
    with c2:
        search_clicked = st.button("Search", type="secondary", use_container_width=True, key="cousin_search_btn")
    if search_clicked:
        _run_song_search(query, "cousin_hits", "cousin_err")

    hits = st.session_state.get("cousin_hits", [])
    if hits or st.session_state.get("cousin_hits") is not None:
        picked = _render_spotify_hits(hits, "cousin_err", "cousin", "✨ Find Cousins")
        if picked:
            _generate_cousins(picked)
            st.rerun()
    else:
        st.caption("Search → pick → Find Cousins")


def _render_break_loop_body():
    if "loop_queue" not in st.session_state:
        st.session_state["loop_queue"] = []

    lc1, lc2 = st.columns([4, 1])
    with lc1:
        lq = st.text_input(
            "Add repeating song",
            placeholder="Search a song you repeat…",
            key="loop_query",
            label_visibility="collapsed",
            autocomplete="off",
        )
    with lc2:
        st.write("")
        loop_search = st.button("Search", type="secondary", use_container_width=True, key="loop_search_btn")

    if loop_search:
        _run_song_search(lq, "loop_hits", "loop_err")

    hits = st.session_state.get("loop_hits", [])
    if hits or st.session_state.get("loop_hits") is not None:
        picked = _render_spotify_hits(hits, "loop_err", "loop", "Add to loop")
        if picked:
            key = _track_label(picked).lower()
            existing = {_track_label(x).lower() for x in st.session_state["loop_queue"]}
            if key not in existing:
                st.session_state["loop_queue"].append(picked)
            st.session_state.pop("loop_hits", None)
            st.rerun()

    queue = st.session_state["loop_queue"]
    if queue:
        chips = "".join(
            f'<span class="vp-chip vp-chip-loop">{t["name"]} · {t["artist"]}</span>'
            for t in queue
        )
        st.markdown(f'<div class="vp-chip-row">{chips}</div>', unsafe_allow_html=True)
        rm_cols = st.columns(min(len(queue), 4))
        for i, t in enumerate(queue[:4]):
            with rm_cols[i % len(rm_cols)]:
                if st.button(f"Remove {t['name'][:12]}…", key=f"rm_loop_{i}"):
                    st.session_state["loop_queue"].pop(i)
                    st.rerun()
        if len(queue) > 4:
            for i in range(4, len(queue)):
                if st.button(f"Remove {queue[i]['name']}", key=f"rm_loop_{i}"):
                    st.session_state["loop_queue"].pop(i)
                    st.rerun()
        if st.button("Break My Loop", type="primary", use_container_width=True):
            if len(queue) < 2:
                st.warning("Add at least 2 songs.")
            else:
                _generate_breakloop(queue)
                st.rerun()
    else:
        st.caption("Add 2+ songs you keep replaying.")


def _resolve_song_query(q: str) -> dict | None:
    """Turn free text like 'cold/mess — Prateek Kuhad' into a real Spotify track."""
    title, artist = q, ""
    for sep in (" — ", " - ", " by "):
        if sep in q:
            title, artist = q.split(sep, 1)
            break
    try:
        return spotify_client.search_track(title.strip(), artist.strip())
    except Exception:
        return None


# --------- The moment → vibe session (the easy, low-friction flow) ---------


def render_moment(taste):
    now = time_utils.local_now()
    time_str = time_utils.format_clock(now)
    band = vibe_engine.time_band_vibe(now)

    st.markdown(
        f'<div class="vp-section vp-section-sm" style="margin-bottom:1rem;">'
        f'<p style="color:#1DB954;font-size:0.78rem;font-weight:700;margin:0 0 6px;">IT\'S {time_str.upper()}</p>'
        f'<p style="color:#fff;font-size:1.15rem;font-weight:700;margin:0;">{band["mood"]}</p></div>',
        unsafe_allow_html=True,
    )

    action = None
    familiarity = DISCOVERY_MAP[_adventure_slider("vibe_adventure")]

    st.caption("Pick a mood")
    chip_cols = st.columns(4)
    for i, (label, vibe_text) in enumerate(MOOD_CHIPS.items()):
        with chip_cols[i % 4]:
            if st.button(label, use_container_width=True, key=f"mood_{label}", type="secondary"):
                action = (vibe_text, label, familiarity, False)

    vibe_text = st.text_input(
        "Describe your vibe",
        placeholder="rainy evening, coffee, soft heartbreak…",
        key="vibe_text",
        label_visibility="collapsed",
    )
    if st.button("Get My Vibe", type="primary", use_container_width=True):
        if vibe_text.strip():
            action = (vibe_text.strip(), vibe_text.strip()[:40], familiarity, False)
        else:
            action = (band["vibe"], band["label"], familiarity, True)

    if action:
        _generate_vibe(action[0], action[1], familiarity=action[2], use_usual=action[3])
        st.rerun()


# ----------------------------- Generation core ----------------------------

def _usual_at_this_hour(taste, window: int = 3) -> list[str]:
    """What the listener tends to play around now (from recently-played timestamps)."""
    recent = (taste or {}).get("recent", [])
    now_hour = time_utils.local_now().hour
    out = []
    for r in recent:
        pa = r.get("played_at")
        if not pa:
            continue
        try:
            dt = datetime.datetime.fromisoformat(pa.replace("Z", "+00:00")).astimezone()
            diff = abs(dt.hour - now_hour)
            if diff <= window or diff >= 24 - window:
                out.append(r["name"])
        except Exception:
            continue
    if not out:  # fall back to overall favorites
        out = [t for t in (taste or {}).get("top_tracks", [])]
    return out[:10]


def _generate_vibe(vibe_text, label, familiarity=5, use_usual=False):
    taste = st.session_state.get("taste_profile")
    exclude = _all_excludes()
    with st.spinner("Building your session…"):
        try:
            if lastfm_client.is_configured():
                tracks = _vibe_via_lastfm(vibe_text, label, taste, familiarity, exclude)
            else:
                usual = _usual_at_this_hour(taste) if use_usual else None
                picks = vibe_engine.propose_vibe_session(
                    vibe_text, n=VIBE_N + 6, taste=taste, usual_tracks=usual,
                    exclude_names=exclude, familiarity=familiarity,
                )
                tracks = _resolve_picks(picks)[:VIBE_N]
            _record_shown(tracks)
            st.session_state["vibe_session"] = {
                "kind": "vibe", "label": label, "tracks": tracks,
            }
            st.session_state.pop("saved_playlist", None)
        except Exception as e:
            st.error(f"Couldn't build the session: {e}")


def _vibe_via_lastfm(vibe_text, label, taste, familiarity, exclude):
    plan = vibe_engine.vibe_plan(vibe_text, taste, n=5)
    pool = []
    for s in plan.get("seeds", []):
        pool += _lastfm_similar_robust(s["title"], s["artist"], limit=50)
    if len(pool) < 30:  # augment with human mood-tag tracks
        for tag in plan.get("tags", [])[:4]:
            pool += lastfm_client.tag_top_tracks(tag, limit=40)
    if familiarity >= 8:  # comfort: surface the seeds themselves first
        for s in plan.get("seeds", []):
            pool.insert(0, {"name": s["title"], "artist": s["artist"], "match": 1.0})
    discovery = familiarity <= 4
    picks = _dedupe_filter(pool, exclude, want=VIBE_N, discovery=discovery, taste=taste)
    tracks = _resolve_pool(picks, VIBE_N)
    _attach_whys(tracks, label, "vibe")
    return tracks


def _generate_cousins(anchor, at=None):
    title, artist = anchor["name"], anchor["artist"]
    taste = st.session_state.get("taste_profile")
    exclude = _all_excludes()
    label = f"{title} — {artist}"
    anchor_tag = ""
    with st.status("Scanning musical DNA…", expanded=True) as status:
        status.update(label="Matching tempo…")
        try:
            tracks = []
            if lastfm_client.is_configured():
                status.update(label="Finding unheard cousins…")
                pool = _lastfm_similar_robust(title, artist, limit=120)
                block = _artist_candidates(artist) + [artist]
                picks = _dedupe_filter(pool, exclude, want=COUSINS_N * 4, discovery=True,
                                       taste=taste, block_artists=block)
                candidates = _resolve_pool(picks, COUSINS_N * 4)
                ranked, anchor_tag = _rank_by_beat(anchor, candidates)
                tracks = ranked[:COUSINS_N]
            if not tracks:
                status.update(label="Consulting AI musical memory…")
                picks = vibe_engine.propose_cousins(
                    f"'{label}'", n=COUSINS_N, taste=taste, exclude_names=exclude,
                    moment=(f"{label} at {at}" if at else None),
                )
                tracks = _resolve_picks(picks)
            _record_shown(tracks)
            st.session_state["vibe_session"] = {
                "kind": "cousins", "label": label, "tracks": tracks,
                "anchor_tag": anchor_tag, "anchor": anchor,
            }
            st.session_state.pop("saved_playlist", None)
            status.update(label="Done ✨", state="complete")
        except Exception as e:
            status.update(label="Something went wrong", state="error")
            st.error(f"Couldn't find cousins: {e}")


def _generate_breakloop(seeds: list[dict]):
    """Paste/build songs you repeat → unheard songs that match their combined feel."""
    with st.spinner("Breaking your loop — finding unheard songs that fit…"):
        try:
            seeds = seeds[:8]
            if not seeds:
                st.error("Add at least one song.")
                return

            block = []
            for s in seeds:
                block += _artist_candidates(s["artist"]) + [s["artist"]]
            exclude = [_track_label(s) for s in seeds] + _all_excludes()

            pool = []
            for s in seeds:
                pool += _lastfm_similar_robust(s["name"], s["artist"], limit=60)
            picks = _dedupe_filter(pool, exclude, want=VIBE_N * 3, discovery=True,
                                   taste=None, block_artists=block)
            candidates = _resolve_pool(picks, VIBE_N * 3)
            tracks = _rank_by_centroid(seeds, candidates)[:VIBE_N]

            if not tracks:  # Last.fm had nothing → LLM fallback on the combined vibe
                names = ", ".join(f"{s['name']} ({s['artist']})" for s in seeds)
                picks = vibe_engine.propose_cousins(
                    f"songs that feel like: {names}", n=VIBE_N, exclude_names=exclude)
                tracks = _resolve_picks(picks)

            _record_shown(tracks)
            st.session_state["vibe_session"] = {
                "kind": "cousins", "label": "Escape Your Loop",
                "tracks": tracks, "anchor_tag": "",
            }
            st.session_state.pop("saved_playlist", None)
        except Exception as e:
            st.error(f"Couldn't break the loop: {e}")


def _rank_by_centroid(seeds, candidates):
    """Rank candidates by closeness to the AVERAGE tempo/feel of the seed songs."""
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


def _rank_by_beat(anchor, candidates):
    """Rank candidates by how closely their tempo/energy/feel match the anchor (ReccoBeats).

    Returns (ranked_tracks, anchor_feature_tag). Falls back to Last.fm order if features
    are unavailable.
    """
    anchor_id = anchor.get("id")
    ids = ([anchor_id] if anchor_id else []) + [c.get("id") for c in candidates]
    feats = reccobeats_client.audio_features(ids)
    a = feats.get(anchor_id) if anchor_id else None
    anchor_tag = reccobeats_client.feature_tag(a) if a else ""

    # attach each candidate's own feature tag (proves the match in the UI)
    for c in candidates:
        f = feats.get(c.get("id"))
        if f:
            c["why"] = reccobeats_client.feature_tag(f)

    if not a:
        return candidates, anchor_tag  # can't rank; keep co-listening order

    # Songs we have real audio data for get ranked by beat/feel closeness and
    # come first; ones ReccoBeats doesn't know are only used as filler.
    graded = [c for c in candidates if feats.get(c.get("id"))]
    ungraded = [c for c in candidates if not feats.get(c.get("id"))]
    graded.sort(key=lambda c: reccobeats_client.distance(a, feats.get(c.get("id"))))
    return graded + ungraded, anchor_tag


def _all_excludes():
    """Recently played + everything already shown this session, so playlists never repeat."""
    taste = st.session_state.get("taste_profile") or {}
    recent = [r["name"] for r in taste.get("recent", [])]
    shown = st.session_state.get("shown_tracks", [])
    seen, merged = set(), []
    for name in shown + recent:  # shown first — highest priority to avoid repeats
        key = name.lower()
        if key not in seen:
            seen.add(key)
            merged.append(name)
    return merged[:55]


def _record_shown(tracks):
    shown = st.session_state.get("shown_tracks", [])
    existing = {s.lower() for s in shown}
    for t in tracks:
        key = f"{t['name']} — {t['artist']}"
        if key.lower() not in existing:
            shown.append(key)
            existing.add(key.lower())
    st.session_state["shown_tracks"] = shown[-250:]


def _resolve_picks(picks):
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


# ----- Last.fm candidate-pool helpers (real-data path) -----

def _clean_title(title: str) -> str:
    """Strip 'From …', '(feat …)', bracketed suffixes that break Last.fm matching."""
    t = re.split(r"\s*[\(\[]", title)[0]          # drop "(From ...)" / "[...]"
    t = re.split(r"\s*-\s*[Ff]rom", t)[0]          # drop "- From ..."
    t = re.split(r"\s*[-–]\s*", t)[0] if " - " in t else t
    return t.strip() or title.strip()


def _artist_candidates(artist: str) -> list[str]:
    """Bollywood tracks credit composer + many singers; try each to find the one Last.fm knows."""
    parts = re.split(r",|&|\bfeat\.?\b|\bft\.?\b|\bx\b", artist, flags=re.IGNORECASE)
    out, seen = [], set()
    for p in parts:
        p = p.strip()
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return out or [artist.strip()]


def _lastfm_similar_robust(title: str, artist: str, limit: int = 60) -> list[dict]:
    """Try each credited artist (and a cleaned title) until Last.fm returns similar tracks."""
    clean = _clean_title(title)
    for cand in _artist_candidates(artist):
        pool = lastfm_client.similar_tracks(cand, clean, limit=limit)
        if pool:
            return pool
        if clean != title:  # also try the raw title for that artist
            pool = lastfm_client.similar_tracks(cand, title, limit=limit)
            if pool:
                return pool
    return []


def _dedupe_filter(pool, exclude, want, discovery=False, taste=None, block_artists=None):
    """Rank a Last.fm candidate pool: dedupe, drop heard/already-shown, one per artist."""
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


def _resolve_pool(picks, want):
    """Resolve Last.fm candidates to real Spotify tracks, up to `want`."""
    out = []
    for p in picks:
        try:
            tr = spotify_client.search_track(p["title"], p["artist"])
        except Exception:
            tr = None
        if tr:
            tr["why"] = ""
            out.append(tr)
        if len(out) >= want:
            break
    return out


def _attach_whys(tracks, context, kind):
    if not tracks:
        return
    items = [f"{t['name']} — {t['artist']}" for t in tracks]
    try:
        whys = vibe_engine.annotate_whys(items, context, kind=kind)
    except Exception:
        whys = []
    for i, t in enumerate(tracks):
        t["why"] = whys[i] if i < len(whys) else ""


def _render_session(only_kind=None, guest=False):
    session = st.session_state.get("vibe_session")
    if not session:
        return
    if only_kind and session.get("kind") != only_kind:
        return
    tracks = session["tracks"]
    if not tracks:
        st.warning("Couldn't match those on Spotify. Try again.")
        return

    st.markdown('<div class="vp-section" style="margin-top:1.5rem;">', unsafe_allow_html=True)

    if session.get("kind") == "cousins":
        ui.section_title("Your <span>cousins</span>", f"{len(tracks)} unheard songs · same feel, new blood")
        anchor = session.get("anchor")
        if anchor:
            tag = session.get("anchor_tag") or _track_bpm_tag(anchor)
            ui.anchor_card(anchor["name"], anchor["artist"], tag or "Anchor", anchor.get("album_art"))
    else:
        mins = len(tracks) * 4
        ui.section_title(f"_{session['label']}_", f"{len(tracks)} songs · {mins // 60}h {mins % 60:02d}m")
        ui.playlist_card(session["label"], f"{len(tracks)} songs · {mins // 60}h {mins % 60:02d}m",
                         "Keeps your vibe. Removes repetition." if "loop" in session["label"].lower() else "Built for your mood.")

    cols = st.columns(2)
    for i, t in enumerate(tracks[:COUSINS_N if session.get("kind") == "cousins" else VIBE_N]):
        with cols[i % 2]:
            if t.get("album_art"):
                st.image(t["album_art"], use_container_width=True)
            bpm_tag = _track_bpm_tag(t)
            st.markdown(
                ui.cousin_card_html(
                    t["name"], t["artist"], bpm_tag.replace(" · ", " | ") if bpm_tag else "match",
                    t.get("why", ""), t.get("url"), t.get("preview_url"),
                ),
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    if guest:
        st.caption("Log in to save to a Spotify playlist.")
        return
    _render_save_controls(session, tracks)


def _render_save_controls(session, tracks):
    saved = st.session_state.get("saved_playlist")
    if saved and saved.get("for_label") == session["label"]:
        st.success(f"✅ Saved {len(tracks)} songs to **{saved['name']}**")
        if saved.get("url"):
            st.link_button("▶ Open playlist in Spotify", saved["url"])
        if st.button("Save again / elsewhere"):
            st.session_state.pop("saved_playlist", None)
            st.rerun()
        return

    is_cousins = session.get("kind") == "cousins"
    st.markdown("**💾 Save all these songs to a playlist**")
    mode = st.radio("Save to…", ["New playlist", "Existing playlist"],
                    horizontal=True, key="save_mode", label_visibility="collapsed")

    if mode == "New playlist":
        default_name = (f"Cousins of {session['label'][:40]}" if is_cousins
                        else f"{session['label'][:40]} · VibePilot")
        c1, c2 = st.columns([3, 1])
        with c1:
            playlist_name = st.text_input("Playlist name", value=default_name, key="save_name")
        with c2:
            st.write("")
            st.write("")
            if st.button("💾 Create & save", type="primary"):
                with st.spinner("Creating your playlist on Spotify…"):
                    try:
                        desc = (f"VibePilot AI · cousins of {session['label']}"
                                if is_cousins else f"VibePilot AI · {session['label']} session")
                        pl = capture.save_session_as_playlist(playlist_name, tracks, description=desc)
                        _mark_saved(pl.get("name", playlist_name),
                                    pl.get("external_urls", {}).get("spotify"), session["label"])
                    except Exception as e:
                        st.error(f"Couldn't save playlist: {e}")
    else:
        try:
            playlists = _ensure_my_playlists()
        except Exception as e:
            st.error(f"Couldn't load your playlists: {e}")
            return
        if not playlists:
            st.info("You have no editable playlists yet — create a new one above.")
            return
        names = [p["name"] for p in playlists]
        c1, c2 = st.columns([3, 1])
        with c1:
            sel = st.selectbox("Choose a playlist", names, key="existing_pl")
        with c2:
            st.write("")
            st.write("")
            if st.button("➕ Add to it", type="primary"):
                target = next(p for p in playlists if p["name"] == sel)
                with st.spinner(f"Adding {len(tracks)} songs to {sel}…"):
                    try:
                        capture.add_to_existing_playlist(target["id"], tracks)
                        _mark_saved(sel, target.get("url"), session["label"])
                    except Exception as e:
                        st.error(f"Couldn't add to playlist: {e}")


def _ensure_my_playlists():
    if "my_playlists" not in st.session_state:
        st.session_state["my_playlists"] = spotify_client.my_playlists()
    return st.session_state["my_playlists"]


def _mark_saved(name, url, label):
    st.session_state["saved_playlist"] = {"name": name, "url": url, "for_label": label}
    st.session_state.pop("my_playlists", None)  # refresh next time
    st.rerun()


# --------------------------------- Router ---------------------------------

def _missing_secrets() -> list[str]:
    import config

    need = {
        "SPOTIFY_CLIENT_ID": config.get_spotify_client_id(),
        "SPOTIFY_CLIENT_SECRET": config.get_spotify_client_secret(),
        "GROQ_API_KEY": config.get_groq_api_key(),
        "LASTFM_API_KEY": config.get_lastfm_api_key(),
    }
    return [k for k, v in need.items() if not v]


def main():
    missing = _missing_secrets()
    if missing:
        st.warning("Some API keys are missing in Streamlit Secrets — guest search / AI may fail.")
        with st.expander("Required secrets (Settings → Secrets)"):
            st.code("\n".join(f'{k} = "..."' for k in missing), language="toml")

    handle_redirect()
    if auth.is_logged_in() or st.session_state.get("guest"):
        render_home()
    else:
        render_login()


try:
    main()
except Exception as exc:
    st.error("VibePilot hit a startup error.")
    st.exception(exc)
    st.info(
        "If this persists: Streamlit Cloud → **Manage app** → **Logs**, "
        "set Python **3.11**, verify Secrets TOML, then **Reboot app**."
    )
