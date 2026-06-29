"""VibePilot frontend — CSS + HTML helpers only (no backend logic)."""

import streamlit as st

CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
  .stApp {
    background: radial-gradient(1200px 600px at 20% -10%, rgba(29,185,84,0.08), transparent 55%),
                radial-gradient(900px 500px at 90% 10%, rgba(29,185,84,0.05), transparent 50%),
                #0B0B0F !important;
  }
  #MainMenu, footer { visibility: hidden; }
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B0B0F 0%, #101218 100%) !important;
    border-right: 1px solid #1f2229 !important;
  }
  section[data-testid="stSidebar"] > div { padding-top: 1.2rem; }
  section[data-testid="stSidebar"] .stRadio label {
    background: transparent !important; border-radius: 14px !important;
    padding: 10px 14px !important; color: #B0B3B8 !important; font-weight: 500 !important;
  }
  section[data-testid="stSidebar"] .stRadio label:hover { color: #fff !important; background: #15171C !important; }
  section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-baseweb="radio"] {
    border: 1px solid transparent !important;
  }
  section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #6b7280; font-size: 0.78rem; }

  .vp-logo { font-size: 1.45rem; font-weight: 800; color: #fff; letter-spacing: -0.02em; margin-bottom: 1.5rem; }
  .vp-logo span { color: #1DB954; }
  .vp-tagline { color: #6b7280; font-size: 0.82rem; line-height: 1.45; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #1f2229; }
  .vp-tagline em { color: #1DB954; font-style: normal; font-weight: 600; }

  .vp-hero { text-align: center; padding: 2.5rem 1rem 2rem; max-width: 820px; margin: 0 auto 2rem; }
  .vp-hero h1 { font-size: 3rem; font-weight: 800; color: #fff; margin: 0 0 0.5rem; letter-spacing: -0.03em; }
  .vp-hero .vp-line { color: #1DB954; font-size: 1.15rem; font-weight: 600; margin-bottom: 1rem; }
  .vp-hero p { color: #B0B3B8; font-size: 1.05rem; line-height: 1.6; margin: 0; }

  .vp-section { background: #15171C; border: 1px solid #23262e; border-radius: 22px;
    padding: 1.75rem 1.5rem; margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.35); }
  .vp-section-hero { border-color: rgba(29,185,84,0.25);
    box-shadow: 0 12px 40px rgba(29,185,84,0.08), 0 8px 32px rgba(0,0,0,0.4); }
  .vp-section-sm { padding: 1.25rem 1.25rem; }
  .vp-section-dim { opacity: 0.72; border-style: dashed; }

  .vp-h2 { font-size: 1.65rem; font-weight: 800; color: #fff; margin: 0 0 0.35rem; letter-spacing: -0.02em; }
  .vp-h2 span { color: #1DB954; }
  .vp-sub { color: #B0B3B8; font-size: 0.95rem; margin: 0 0 1.25rem; line-height: 1.5; }

  .vp-anchor { display: flex; gap: 1.25rem; align-items: center;
    background: linear-gradient(135deg, rgba(29,185,84,0.12), rgba(29,185,84,0.03));
    border: 1px solid rgba(29,185,84,0.3); border-radius: 20px; padding: 1.25rem; margin: 1rem 0; }
  .vp-anchor-meta h3 { color: #fff; font-size: 1.35rem; font-weight: 800; margin: 0 0 0.25rem; }
  .vp-anchor-meta p { color: #B0B3B8; margin: 0 0 0.65rem; font-size: 0.95rem; }
  .vp-tags { display: flex; flex-wrap: wrap; gap: 6px; }
  .vp-tag {
    display: inline-block; background: #0B0B0F; border: 1px solid #2a2d35;
    color: #1DB954; font-size: 0.72rem; font-weight: 600; padding: 4px 10px;
    border-radius: 999px; text-transform: uppercase; letter-spacing: 0.04em;
  }

  .vp-cousin {
    background: #15171C; border: 1px solid #23262e; border-radius: 20px;
    padding: 0.85rem; height: 100%; transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
  }
  .vp-cousin:hover {
    transform: translateY(-3px); border-color: rgba(29,185,84,0.45);
    box-shadow: 0 12px 28px rgba(29,185,84,0.12);
  }
  .vp-cousin h4 { color: #fff; font-size: 0.98rem; font-weight: 700; margin: 0.55rem 0 0.15rem; }
  .vp-cousin .artist { color: #B0B3B8; font-size: 0.82rem; margin-bottom: 0.45rem; }
  .vp-cousin .why { color: #8a8f98; font-size: 0.75rem; line-height: 1.4; margin-top: 0.35rem; }
  .vp-cousin .actions { margin-top: 0.5rem; font-size: 0.75rem; color: #1DB954; }

  .vp-chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 0.75rem 0 1rem; }
  .vp-chip {
    display: inline-flex; align-items: center; gap: 6px;
    background: #0B0B0F; border: 1px solid #2a2d35; color: #fff;
    padding: 8px 14px; border-radius: 999px; font-size: 0.88rem; font-weight: 500;
  }
  .vp-chip-loop { border-color: rgba(29,185,84,0.35); background: rgba(29,185,84,0.08); }

  .vp-playlist-card {
    background: linear-gradient(135deg, #15171C, #101218);
    border: 1px solid rgba(29,185,84,0.25); border-radius: 20px;
    padding: 1.25rem 1.5rem; margin-top: 1rem;
  }
  .vp-playlist-card h3 { color: #fff; margin: 0 0 0.35rem; font-size: 1.2rem; }
  .vp-playlist-card .meta { color: #1DB954; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem; }
  .vp-playlist-card p { color: #B0B3B8; margin: 0; font-size: 0.9rem; }

  .vp-teaser { text-align: center; padding: 2rem 1.5rem; }
  .vp-teaser .mic {
    font-size: 2.5rem; margin-bottom: 0.75rem;
    filter: drop-shadow(0 0 12px rgba(29,185,84,0.5));
  }
  .vp-wave { display: flex; justify-content: center; gap: 4px; margin: 1rem 0; height: 28px; align-items: flex-end; }
  .vp-wave span {
    width: 4px; background: #1DB954; border-radius: 2px;
    animation: vpwave 1.2s ease-in-out infinite;
  }
  .vp-wave span:nth-child(2) { animation-delay: 0.15s; height: 18px; }
  .vp-wave span:nth-child(3) { animation-delay: 0.3s; height: 24px; }
  .vp-wave span:nth-child(4) { animation-delay: 0.45s; height: 14px; }
  .vp-wave span:nth-child(5) { animation-delay: 0.6s; height: 20px; }
  @keyframes vpwave { 0%,100% { height: 8px; opacity: 0.5; } 50% { height: 26px; opacity: 1; } }

  .vp-pillars { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 2rem 0 0; }
  .vp-pillar {
    background: #15171C; border: 1px solid #23262e; border-radius: 18px;
    padding: 1rem 0.75rem; text-align: center;
  }
  .vp-pillar h4 { color: #1DB954; margin: 0 0 6px; font-size: 0.88rem; font-weight: 700; }
  .vp-pillar p { color: #8a8f98; font-size: 0.75rem; margin: 0; line-height: 1.35; }

  div[data-baseweb="input"], div[data-baseweb="base-input"] {
    background: #0B0B0F !important; border-radius: 14px !important; border: 1px solid #2a2d35 !important;
  }
  div[data-baseweb="input"]:focus-within { border-color: #1DB954 !important; box-shadow: 0 0 0 1px rgba(29,185,84,0.3) !important; }
  .stTextInput input { color: #fff !important; background: transparent !important; }
  .stTextInput input::placeholder { color: #6b7280 !important; }

  div.stButton > button {
    border-radius: 999px !important; font-weight: 700 !important; transition: all 0.15s ease !important;
  }
  div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #1DB954, #1ed760) !important; color: #000 !important; border: none !important;
    box-shadow: 0 4px 20px rgba(29,185,84,0.35) !important;
  }
  div.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px); box-shadow: 0 6px 24px rgba(29,185,84,0.45) !important;
  }
  div.stButton > button[kind="secondary"] {
    background: #15171C !important; color: #e5e7eb !important; border: 1px solid #2a2d35 !important;
  }
  div.stButton > button[kind="secondary"]:hover { border-color: #1DB954 !important; color: #fff !important; }

  .stTabs [data-baseweb="tab-list"] { gap: 10px; background: transparent; border-bottom: none; }
  .stTabs [data-baseweb="tab"] {
    border-radius: 999px !important; padding: 10px 20px !important;
    background: #15171C !important; border: 1px solid #2a2d35 !important; color: #B0B3B8 !important;
  }
  .stTabs [aria-selected="true"] {
    background: #1DB954 !important; color: #000 !important; border-color: #1DB954 !important; font-weight: 700 !important;
  }
  .stSlider [data-baseweb="slider"] div[role="slider"] { background: #1DB954 !important; box-shadow: 0 0 12px rgba(29,185,84,0.6) !important; }
  .stSlider [data-baseweb="slider"] div[data-testid="stThumbValue"] { color: #1DB954 !important; }

  [data-testid="stStatusWidget"] { border-radius: 16px !important; border: 1px solid rgba(29,185,84,0.3) !important; }
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title: str = "VibePilot AI", line: str = "Same feel, different blood.", desc: str = ""):
    st.markdown(
        f'<div class="vp-hero"><h1>{title}</h1><div class="vp-line">{line}</div>'
        f'<p>{desc}</p></div>',
        unsafe_allow_html=True,
    )


def section_title(html: str, sub: str = ""):
    st.markdown(f'<div class="vp-h2">{html}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<p class="vp-sub">{sub}</p>', unsafe_allow_html=True)


def anchor_card(name: str, artist: str, tag_line: str, art_url: str | None = None):
    tags_html = "".join(f'<span class="vp-tag">{t.strip()}</span>' for t in tag_line.split("·") if t.strip())
    art = f'<img src="{art_url}" width="110" style="border-radius:14px;" />' if art_url else ""
    st.markdown(
        f'<div class="vp-anchor">{art}<div class="vp-anchor-meta">'
        f'<div style="color:#1DB954;font-size:0.72rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">Anchor song</div>'
        f"<h3>{name}</h3><p>{artist}</p><div class='vp-tags'>{tags_html}</div></div></div>",
        unsafe_allow_html=True,
    )


def cousin_card_html(name: str, artist: str, tags: str, why: str, url: str | None, preview: str | None):
    tag_html = "".join(f'<span class="vp-tag">{t.strip()}</span>' for t in tags.split("|") if t.strip())
    title = f'<a href="{url}" target="_blank" style="color:#fff;text-decoration:none;">{name}</a>' if url else name
    preview_link = f' · <a href="{preview}" target="_blank" style="color:#1DB954;">▶ preview</a>' if preview else ""
    return (
        f'<div class="vp-cousin"><div class="vp-tags">{tag_html}</div>'
        f"<h4>{title}</h4><div class='artist'>{artist}</div>"
        f"<div class='why'>Why this? {why or 'Same rhythm & emotional energy'}</div>"
        f"<div class='actions'>Open in Spotify{preview_link}</div></div>"
    )


def playlist_card(title: str, meta: str, blurb: str):
    st.markdown(
        f'<div class="vp-playlist-card"><h3>{title}</h3><div class="meta">{meta}</div><p>{blurb}</p></div>',
        unsafe_allow_html=True,
    )


def catch_that_teaser():
    st.markdown(
        """
        <div class="vp-section vp-section-dim vp-teaser">
          <div class="mic">🎙️</div>
          <div class="vp-h2">Coming Soon — <span>Catch That™</span></div>
          <p class="vp-sub">Hands-free voice capture for discovery moments.</p>
          <div class="vp-wave"><span></span><span></span><span></span><span></span><span></span></div>
          <p style="color:#8a8f98;font-size:0.85rem;margin:0;">
            Song playing → say “Catch that” → saved to your Caught playlist
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def about_pillars():
    st.markdown(
        """
        <div class="vp-pillars">
          <div class="vp-pillar"><h4>Same Feel</h4><p>Tempo, mood & musical DNA</p></div>
          <div class="vp-pillar"><h4>New Artists</h4><p>Songs you haven't heard</p></div>
          <div class="vp-pillar"><h4>Smart AI</h4><p>Vibe, not just genre</p></div>
          <div class="vp-pillar"><h4>You're in Control</h4><p>Break loops freely</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
