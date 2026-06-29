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
import vibe_engine

st.set_page_config(page_title="VibePilot", page_icon="🎧", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
      .stApp { background: linear-gradient(165deg, #070707 0%, #0e0e0e 45%, #0a1510 100%); }
      #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
      section[data-testid="stSidebar"] {
          background: linear-gradient(180deg, #0c0c0c 0%, #101010 100%) !important;
          border-right: 1px solid #222;
      }
      section[data-testid="stSidebar"] .stRadio label {
          background: transparent; border-radius: 12px; padding: 10px 12px; width: 100%;
      }
      section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-baseweb="radio"] {
          border: 1px solid transparent;
      }
      .vp-logo { font-size: 1.35rem; font-weight: 800; color: #fff; padding: 8px 4px 18px; }
      .vp-beta {
          font-size: 0.65rem; background: #1ed760; color: #000; padding: 2px 8px;
          border-radius: 999px; margin-left: 6px; vertical-align: middle; font-weight: 700;
      }
      .vp-page-title { font-size: 2rem; font-weight: 800; line-height: 1.2; margin: 0 0 8px; color: #fff; }
      .vp-page-title span { color: #1ed760; }
      .vp-sub { color: #9a9a9a; font-size: 1rem; margin-bottom: 18px; }
      .vp-mood {
          background: linear-gradient(135deg, rgba(29,185,84,0.18), rgba(29,185,84,0.04));
          border: 1px solid rgba(29,185,84,0.28); border-radius: 20px; padding: 22px 24px; margin-bottom: 14px;
      }
      .vp-time { color:#1ed760; font-size:0.82rem; letter-spacing:1px; text-transform:uppercase; font-weight:700; }
      .vp-moodline { font-size:1.45rem; font-weight:700; line-height:1.25; margin-top:4px; color:#fff; }
      .vp-or { text-align:center; color:#666; font-size:0.9rem; margin:18px 0; }
      .vp-def {
          background: rgba(255,255,255,0.03); border-left: 3px solid #1ed760;
          border-radius: 10px; padding: 12px 16px; margin: 0 0 20px; color: #cfcfcf; font-size: 0.95rem;
      }
      .vp-def b { color: #fff; }
      .vp-npname { font-size:1.25rem; font-weight:800; line-height:1.2; color:#fff; }
      .vp-npart { color:#b3b3b3; font-size:0.95rem; margin-top:2px; }
      .vp-selected {
          border: 1px solid rgba(29,185,84,0.5); border-radius: 16px; padding: 14px;
          background: rgba(29,185,84,0.08); margin: 12px 0;
      }
      .vp-tag { display:inline-block; background:#1a1a1a; border:1px solid #333;
          color:#1ed760; font-size:0.75rem; padding:3px 10px; border-radius:999px; margin-right:6px; }
      .vp-card { border:1px solid #282828; border-radius:16px; padding:12px;
          background: linear-gradient(180deg, #141414, #101010); margin-bottom:12px; }
      .vp-pillar { text-align:center; padding:12px 8px; }
      .vp-pillar h4 { color:#1ed760; margin:0 0 6px; font-size:0.95rem; }
      .vp-pillar p { color:#888; font-size:0.8rem; margin:0; line-height:1.35; }
      div[data-baseweb="input"], div[data-baseweb="base-input"] {
          background: #141414 !important; border-radius: 12px !important; border: 1px solid #333 !important;
      }
      div[data-baseweb="input"]:focus-within { border-color: #1ed760 !important; }
      .stTextInput input { color: #fff !important; background: transparent !important; }
      .vp-hits { border: 1px solid rgba(29,185,84,0.35); border-radius: 14px;
          padding: 12px; margin-top: 10px; background: rgba(29,185,84,0.05); }
      .vp-hits-title { color: #1ed760; font-size: 0.78rem; font-weight: 700;
          letter-spacing: 0.6px; text-transform: uppercase; margin-bottom: 8px; }
      div.stButton > button[kind="primary"] {
          background: linear-gradient(90deg, #1DB954, #1ed760); color: #000;
          border: none; border-radius: 999px; font-weight: 700;
      }
      div.stButton > button[kind="secondary"] {
          background: #1a1a1a; color: #ddd; border: 1px solid #3a3a3a; border-radius: 999px; font-weight: 600;
      }
      div.stButton > button[kind="secondary"]:hover { border-color: #1ed760; color: #fff; }
      .stTabs [data-baseweb="tab-list"] { gap: 8px; }
      .stTabs [data-baseweb="tab"] { border-radius: 999px; padding: 8px 18px; background: #1a1a1a; }
      .stTabs [aria-selected="true"] { background: #1ed760 !important; color: #000 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


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
    st.markdown(
        '<div class="vp-page-title">🎧 VibePilot <span class="vp-beta">Beta</span></div>'
        '<p class="vp-sub">Find songs with the same feel, not the same artist.</p>',
        unsafe_allow_html=True,
    )
    lc1, lc2 = st.columns(2)
    with lc1:
        if st.button("✨  Try it now — no login", type="primary", use_container_width=True):
            st.session_state["guest"] = True
            st.rerun()
        st.caption("Type any song → get its cousins. No account needed.")
    with lc2:
        st.link_button("🟢  Log in with Spotify", auth.build_authorize_url(),
                       use_container_width=True)
        st.caption("Unlocks now-playing & saving. Dev mode: allowlisted accounts only.")


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
NAV_PAGES = ["Find Cousins", "Break My Loop", "Start from Vibe", "Now Playing"]


def _render_sidebar(guest: bool, name: str | None = None):
    with st.sidebar:
        st.markdown(
            '<div class="vp-logo">🎧 VibePilot <span class="vp-beta">Beta</span></div>',
            unsafe_allow_html=True,
        )
        page = st.radio(
            "Navigate",
            NAV_PAGES,
            label_visibility="collapsed",
            key="vp_page",
        )
        st.divider()
        if name:
            st.caption(f"Signed in as **{name}**")
        elif guest:
            st.caption("👋 Guest mode")
        st.caption("🎙 Catch That — coming soon")
        st.divider()
        if guest:
            st.link_button("🟢 Log in with Spotify", auth.build_authorize_url(), use_container_width=True)
        else:
            if st.button("Log out", use_container_width=True):
                auth.logout()
                for k in ("spotify_profile", "taste_profile", "vibe_session", "shown_tracks",
                          "selected_intent", "pending_gen", "now_playing", "saved_playlist",
                          "my_playlists", "guest", "loop_queue", "cousin_hits", "loop_hits"):
                    st.session_state.pop(k, None)
                st.rerun()
    return page


def _render_footer():
    st.markdown("<br>", unsafe_allow_html=True)
    c = st.columns(4)
    pillars = [
        ("Same Feel", "Matches tempo, mood & musical DNA"),
        ("New Artists", "Discover songs you haven't heard"),
        ("Smart AI", "Understands vibe, not just genre"),
        ("You're in Control", "Break loops & explore freely"),
    ]
    for col, (title, blurb) in zip(c, pillars):
        with col:
            st.markdown(
                f'<div class="vp-pillar"><h4>{title}</h4><p>{blurb}</p></div>',
                unsafe_allow_html=True,
            )


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

    if page == "Find Cousins":
        _page_find_cousins(guest)
    elif page == "Break My Loop":
        _page_break_loop()
    elif page == "Start from Vibe":
        _page_start_vibe(taste)
    elif page == "Now Playing":
        _page_now_playing(guest)

    _render_session(guest=guest)
    _render_footer()


def _page_header(title_html: str, subtitle: str = ""):
    st.markdown(title_html, unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="vp-sub">{subtitle}</p>', unsafe_allow_html=True)


def _track_bpm_tag(track: dict) -> str:
    tid = track.get("id")
    if not tid:
        return ""
    feats = reccobeats_client.audio_features([tid])
    f = feats.get(tid)
    return reccobeats_client.feature_tag(f) if f else ""


def _show_selected_track(track: dict):
    tag = _track_bpm_tag(track)
    st.markdown(
        f'<div class="vp-selected"><div class="vp-time">selected song</div>'
        f'<div class="vp-npname">{track["name"]}</div>'
        f'<div class="vp-npart">{track["artist"]}</div></div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 3])
    with c1:
        if track.get("album_art"):
            st.image(track["album_art"], width=100)
    with c2:
        if tag:
            st.caption(tag)


def _page_find_cousins(guest: bool):
    _page_header(
        '<div class="vp-page-title">Find songs with the <span>same feel</span>, not the same artist</div>',
        "Pick a song → get unheard cousins that match its tempo, beat & mood.",
    )
    st.markdown(
        '<div class="vp-def">🧬 <b>Cousins</b> share your song\'s musical DNA — tempo, beat & mood — '
        "but from artists you've never heard. Same feel, different blood.</div>",
        unsafe_allow_html=True,
    )

    tab_np, tab_search = st.tabs(["▶ Now Playing", "🔎 Search Song"])
    with tab_np:
        if guest:
            st.info("🔒 Log in with Spotify to detect what's playing on your phone right now.")
        else:
            _now_playing_card()
    with tab_search:
        _render_cousin_search()


def _page_break_loop():
    _page_header(
        '<div class="vp-page-title">Break your <span>loop</span></div>',
        "Add songs you keep repeating — we'll find fresh tracks in the same vibe, different artists.",
    )
    _render_break_loop_body()


def _page_start_vibe(taste):
    _page_header(
        '<div class="vp-page-title">Start from a <span>vibe</span></div>',
        "No song in mind? Pick a mood and get a discovery playlist.",
    )
    render_moment(taste)


def _page_now_playing(guest: bool):
    _page_header(
        '<div class="vp-page-title">What\'s <span>playing</span> now</div>',
        "Find cousins of the song on Spotify right now.",
    )
    if guest:
        st.info("🔒 Log in with Spotify to use now-playing detection.")
    else:
        _now_playing_card()


def _now_playing_card():
    try:
        np = spotify_client.currently_playing()
    except Exception:
        np = None
    with st.container(border=True):
        if np:
            pos = np.get("progress_ms", 0) // 1000
            mm, ss = divmod(pos, 60)
            a, b, c = st.columns([1.2, 5, 3])
            with a:
                if np.get("album_art"):
                    st.image(np["album_art"], width=84)
            with b:
                st.markdown('<div class="vp-time">▶ now playing</div>', unsafe_allow_html=True)
                st.markdown(f"<div class='vp-npname'>{np['name']}</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='vp-npart'>{np['artist']} · "
                    f"<span style='color:#1DB954'>{mm}:{ss:02d}</span></div>",
                    unsafe_allow_html=True,
                )
                tag = _track_bpm_tag(np)
                if tag:
                    st.caption(tag)
            with c:
                if st.button("✨ Find Cousins →", type="primary", use_container_width=True, key="np_cousins"):
                    _generate_cousins(np, at=f"{mm}:{ss:02d}")
                    st.rerun()
                if st.button("🔄 Refresh", type="secondary", use_container_width=True, key="np_refresh"):
                    st.rerun()
        else:
            st.markdown('<div class="vp-time">▶ nothing playing</div>', unsafe_allow_html=True)
            st.markdown("<div class='vp-npname'>Press play on Spotify 🎧</div>", unsafe_allow_html=True)
            st.caption("Start any song in Spotify, then hit Refresh.")
            if st.button("🔄 Refresh", type="primary", key="np_refresh2"):
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

    st.markdown(
        f'<div class="vp-hits"><div class="vp-hits-title">🎵 results from spotify · pick one</div></div>',
        unsafe_allow_html=True,
    )
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
        picked = _render_spotify_hits(hits, "cousin_err", "cousin", "✨ Find Cousins →")
        if picked:
            _generate_cousins(picked)
            st.rerun()
    else:
        st.caption("Type a song → **Search** → pick the match → **Find Cousins**")


def _render_break_loop_body():
    """Build a list of songs you repeat → discovery playlist that breaks the loop."""
    if "loop_queue" not in st.session_state:
        st.session_state["loop_queue"] = []

    with st.container(border=True):
        lc1, lc2 = st.columns([4, 1])
        with lc1:
            lq = st.text_input(
                "Add repeating song",
                placeholder="search a song you repeat…",
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
            picked = _render_spotify_hits(hits, "loop_err", "loop", "➕ add this song to my loop")
            if picked:
                key = _track_label(picked).lower()
                existing = {_track_label(x).lower() for x in st.session_state["loop_queue"]}
                if key not in existing:
                    st.session_state["loop_queue"].append(picked)
                st.session_state.pop("loop_hits", None)
                st.rerun()

        queue = st.session_state["loop_queue"]
        if queue:
            st.markdown("**Your loop:**")
            for i, t in enumerate(queue):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"· {_track_label(t)}")
                with c2:
                    if st.button("✕", key=f"rm_loop_{i}"):
                        st.session_state["loop_queue"].pop(i)
                        st.rerun()
            if st.button("🔓 Break My Loop →", type="primary", use_container_width=True):
                if len(queue) < 2:
                    st.warning("Add at least 2 songs first 🙂")
                else:
                    _generate_breakloop(queue)
                    st.rerun()
        else:
            st.caption("Search and add songs above — need at least 2 to break the loop.")


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

DISCOVERY_MAP = {
    "Familiar favorites": 10,
    "Mostly familiar": 8,
    "Balanced": 5,
    "Mostly new": 3,
    "All new (discover)": 0,
}


def render_moment(taste):
    now = time_utils.local_now()
    time_str = time_utils.format_clock(now)
    band = vibe_engine.time_band_vibe(now)

    # Hero: time-aware suggestion + one big primary action
    st.markdown(
        f'<div class="vp-mood"><div class="vp-time">✨ it\'s {time_str.lower()}</div>'
        f'<div class="vp-moodline">{band["mood"]}</div></div>',
        unsafe_allow_html=True,
    )
    # Collect the chosen action, then generate ONCE at the end — outside any
    # column context — so the "building…" spinner spans full width (no glitch).
    action = None

    if st.button("▶  play this vibe", type="primary", use_container_width=True):
        action = (band["vibe"], band["label"], 3, True)

    st.markdown('<div class="vp-or">not feeling it? pick your own 👇</div>', unsafe_allow_html=True)

    choice = st.select_slider(
        "how adventurous?",
        options=list(DISCOVERY_MAP.keys()),
        value=st.session_state.get("discovery_choice", "Mostly new"),
        key="discovery_choice",
        help="← comfy familiar favorites · brand-new discoveries →",
    )
    familiarity = DISCOVERY_MAP[choice]

    intents = list(vibe_engine.INTENT_PRESETS.keys())
    cols = st.columns(4)
    for i, intent in enumerate(intents):
        with cols[i % 4]:
            if st.button(intent, use_container_width=True, key=f"intent_{intent}", type="secondary"):
                action = (vibe_engine.INTENT_PRESETS[intent], intent.split(" ", 1)[-1],
                          familiarity, False)

    # quirky: describe your mood in emojis 🎭
    st.markdown('<div class="vp-or">…or just vibe it in emojis 🎭</div>', unsafe_allow_html=True)
    ec1, ec2 = st.columns([4, 1])
    with ec1:
        emojis = st.text_input(
            "mood in emojis", placeholder="e.g.  🌧️😌☕   or   🔥🕺🎉",
            key="emoji_mood", label_visibility="collapsed",
        )
    with ec2:
        if st.button("✨ build it", use_container_width=True, type="primary"):
            if emojis.strip():
                action = (f"a mood best described by these emojis: {emojis.strip()}",
                          emojis.strip(), familiarity, False)
            else:
                st.warning("Drop a few emojis first 🙂")

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
    with st.spinner("Matching tempo, beat & feel…"):
        try:
            tracks = []
            if lastfm_client.is_configured():
                pool = _lastfm_similar_robust(title, artist, limit=120)
                # cousins must be DIFFERENT blood — never the same artist
                block = _artist_candidates(artist) + [artist]
                # pull a wide pool, then rank it down by real audio features
                picks = _dedupe_filter(pool, exclude, want=COUSINS_N * 4, discovery=True,
                                       taste=taste, block_artists=block)
                candidates = _resolve_pool(picks, COUSINS_N * 4)
                ranked, anchor_tag = _rank_by_beat(anchor, candidates)
                tracks = ranked[:COUSINS_N]
            if not tracks:  # Last.fm has no data for this song → fall back to the LLM
                picks = vibe_engine.propose_cousins(
                    f"'{label}'", n=COUSINS_N, taste=taste, exclude_names=exclude,
                    moment=(f"{label} at {at}" if at else None),
                )
                tracks = _resolve_picks(picks)
            _record_shown(tracks)
            st.session_state["vibe_session"] = {
                "kind": "cousins", "label": label, "tracks": tracks,
                "anchor_tag": anchor_tag,
            }
            st.session_state.pop("saved_playlist", None)
        except Exception as e:
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
                "kind": "cousins", "label": f"your loop · {len(seeds)} songs",
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
        st.warning("Couldn't match those on Spotify. Try again or pick another vibe.")
        return

    st.divider()
    if session.get("kind") == "cousins":
        st.markdown("#### Here are your cousins ✨")
        st.caption(f"**{session['label']}** — {len(tracks)} unheard songs that match the beat & feel")
    else:
        st.markdown(f"#### 🎶 Your _{session['label']}_ session")
        st.caption(f"{len(tracks)} songs tuned to your vibe")

    cols = st.columns(2)
    for i, t in enumerate(tracks):
        with cols[i % 2]:
            with st.container(border=True):
                if t.get("album_art"):
                    st.image(t["album_art"], use_container_width=True)
                link = t.get("url")
                title = f"**[{t['name']}]({link})**" if link else f"**{t['name']}**"
                st.markdown(title)
                st.caption(t["artist"])
                if t.get("why"):
                    st.caption(t["why"])

    st.divider()
    if guest:
        st.caption("🔒 Saving to a Spotify playlist is available on a logged-in account. "
                   "As a guest you can explore unlimited cousins — search another song above 👆")
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

handle_redirect()
if auth.is_logged_in() or st.session_state.get("guest"):
    render_home()
else:
    render_login()
