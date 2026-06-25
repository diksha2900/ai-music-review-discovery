"""
Spotify Discovery Review Engine — Streamlit app.
Tab 1: Live scrape → classify → synthesize workflow
Tab 2: RAG chat over the full historical corpus
"""

import glob
import json
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Spotify Discovery Engine",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

SOURCES = [
    {
        "label": "Play Store",
        "key": "playstore",
        "icon": "📱",
        "desc": "Live scrape from Google Play (India)",
        "needs_input": True,
        "input_label": "Play Store App ID",
        "input_default": "com.spotify.music",
        "input_help": "e.g. com.spotify.music",
    },
    {
        "label": "App Store",
        "key": "appstore",
        "icon": "🍎",
        "desc": "Live scrape from Apple App Store RSS (India)",
        "needs_input": True,
        "input_label": "App Store numeric App ID",
        "input_default": "324684580",
        "input_help": "Spotify = 324684580",
    },
    {
        "label": "Reddit",
        "key": "reddit",
        "icon": "🔴",
        "desc": "Live search across r/spotify, r/spotifyplaylists, r/musicsuggestions",
        "needs_input": True,
        "input_label": "Search keyword",
        "input_default": "spotify discover weekly",
        "input_help": "Discovery-related search term",
    },
    {
        "label": "Twitter / X",
        "key": "twitter",
        "icon": "🐦",
        "desc": "Loads scraped tweets from data/raw/ (run scrape_twitter_bulk_fixed.py to refresh)",
        "needs_input": False,
    },
    {
        "label": "Community Forum",
        "key": "community_forum",
        "icon": "💬",
        "desc": "Manually curated Spotify Community posts",
        "needs_input": False,
    },
    {
        "label": "Social Media",
        "key": "social_media",
        "icon": "📣",
        "desc": "Manually curated Twitter/X quotes",
        "needs_input": False,
    },
]

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(165deg, #0a0a0a 0%, #121212 45%, #0d1f12 100%); color: #fff; }
    .hero {
        background: linear-gradient(135deg, rgba(29,185,84,0.15) 0%, rgba(29,185,84,0.03) 100%);
        border: 1px solid rgba(29,185,84,0.25); border-radius: 16px;
        padding: 28px 32px; margin-bottom: 24px;
    }
    .hero h1 { color: #fff !important; font-size: 2rem; font-weight: 700; margin: 0 0 8px 0; }
    .hero p { color: #b3b3b3; margin: 0; font-size: 1.05rem; line-height: 1.6; }
    .step-card {
        background: #181818; border: 1px solid #282828; border-radius: 14px;
        padding: 20px; text-align: center; height: 100%;
    }
    .step-num {
        background: #1DB954; color: #000; font-weight: 700;
        width: 32px; height: 32px; border-radius: 50%;
        display: inline-flex; align-items: center; justify-content: center;
        margin-bottom: 10px; font-size: 0.9rem;
    }
    .step-title { color: #1DB954; font-weight: 600; margin-bottom: 6px; }
    .step-desc { color: #b3b3b3; font-size: 0.85rem; line-height: 1.4; }
    .source-pill {
        display: inline-block; background: #282828; border-radius: 20px;
        padding: 4px 12px; font-size: 0.78rem; color: #b3b3b3; margin: 2px 4px 2px 0;
    }
    .theme-card {
        background: linear-gradient(145deg, #1a1a1a 0%, #141414 100%);
        border: 1px solid #282828; border-left: 4px solid #1DB954;
        border-radius: 14px; padding: 22px 24px; margin-bottom: 16px;
    }
    .theme-card h4 { color: #1DB954; margin: 0 0 16px 0; font-size: 1.05rem; }
    .theme-card .label {
        color: #1DB954; font-weight: 600; font-size: 0.75rem;
        text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px;
    }
    .theme-card .value { color: #e8e8e8; line-height: 1.6; margin-bottom: 14px; font-size: 0.95rem; }
    .theme-card .quote {
        color: #a0a0a0; font-style: italic;
        border-left: 3px solid #333; padding-left: 14px; margin-top: 4px;
    }
    div[data-testid="stMetric"] {
        background: #181818; border: 1px solid #282828; border-radius: 12px; padding: 16px;
    }
    div[data-testid="stMetricValue"] { color: #1DB954 !important; font-size: 2rem !important; }
    div[data-testid="stMetricLabel"] { color: #b3b3b3 !important; }
    .stTabs [data-baseweb="tab"] { color: #b3b3b3; font-weight: 500; }
    .stTabs [aria-selected="true"] { color: #1DB954 !important; border-bottom-color: #1DB954 !important; }
    div.stButton > button {
        background: linear-gradient(90deg, #1DB954, #1ed760) !important;
        color: #000 !important; border: none !important;
        border-radius: 24px !important; font-weight: 600 !important;
    }
    .stChatMessage { background: #181818 !important; border: 1px solid #282828; border-radius: 14px; }
    div[data-testid="stSidebar"] { background: #0a0a0a; border-right: 1px solid #282828; }
    .rag-stat { color: #1DB954; font-weight: 600; font-size: 1.4rem; }
    .rag-label { color: #727272; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; }
    h2, h3 { color: #fff !important; }
    hr { border-color: #282828; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_corpus_stats():
    if not os.path.exists("data/unified_feedback.csv"):
        return {"total": 0, "by_source": {}}
    df = pd.read_csv("data/unified_feedback.csv")
    return {"total": len(df), "by_source": df["source"].value_counts().to_dict()}


def render_theme_cards(structured_results):
    for item in structured_results:
        root = str(item.get("root_cause", "")).replace('"', "&quot;")
        behavior = str(item.get("user_behavior", "")).replace('"', "&quot;")
        quote = str(item.get("representative_quote", "")).replace('"', "&quot;")
        heading = f"{item.get('theme', '')} · {item.get('count', 0)} records"
        st.markdown(f"""
        <div class="theme-card">
            <h4>{heading}</h4>
            <div class="label">Root Cause</div>
            <div class="value">{root}</div>
            <div class="label">User Behavior</div>
            <div class="value">{behavior}</div>
            <div class="quote">"{quote}"</div>
        </div>
        """, unsafe_allow_html=True)


def load_structured_run(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data, []
    return data.get("themes", []), data.get("research_questions", [])


def render_research_questions(research_results):
    if not research_results:
        return
    st.subheader("📋 Research Question Answers")
    for item in research_results:
        st.markdown(f"**{item.get('question', '')}**")
        st.markdown(item.get("answer", ""))
        st.divider()


def render_theme_chart(structured_results, chart_key="chart"):
    if not structured_results:
        return
    pairs = sorted([(i["theme"], i["count"]) for i in structured_results], key=lambda x: x[1])
    themes, counts = zip(*pairs)
    colors = [f"rgba(29,185,84,{0.4 + 0.6 * (c / max(counts))})" for c in counts]
    fig = go.Figure(go.Bar(
        x=list(counts), y=list(themes), orientation="h",
        marker=dict(color=colors, line=dict(color="#1DB954", width=1)),
        text=list(counts), textposition="outside", textfont=dict(color="#fff"),
    ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#fff"), margin=dict(l=10, r=40, t=10, b=10),
        height=max(280, len(themes) * 65),
        xaxis=dict(showgrid=True, gridcolor="#282828", title="Records"),
        yaxis=dict(showgrid=False),
    )
    st.plotly_chart(fig, use_container_width=True, key=chart_key)


with st.sidebar:
    st.markdown("### 🎧 Discovery Engine")
    st.markdown("Spotify Growth · Music Discovery Research")
    st.divider()
    stats = load_corpus_stats()
    st.markdown(
        f'<div class="rag-stat">{stats["total"]:,}</div>'
        f'<div class="rag-label">Total reviews in corpus</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")
    if stats["by_source"]:
        st.markdown("**Corpus by source**")
        for src, count in sorted(stats["by_source"].items(), key=lambda x: -x[1]):
            label = src.replace("_", " ").title()
            st.markdown(f'<span class="source-pill">{label}: {count:,}</span>', unsafe_allow_html=True)
    st.divider()
    st.caption("Groq Llama 3.3 · Sentence Transformers RAG")

st.markdown("""
<div class="hero">
    <h1>🎧 AI-Powered Review Discovery Engine</h1>
    <p>Point at any data source, scrape reviews live, and get LLM-classified insights on why users struggle with music discovery — or explore the full corpus via chat.</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔄 Live Workflow", "💬 Research Chat (RAG)"])

with tab1:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="step-card"><div class="step-num">1</div>'
            '<div class="step-title">Input</div>'
            '<div class="step-desc">Pick source or full dataset + review count</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="step-card"><div class="step-num">2</div>'
            '<div class="step-title">Process</div>'
            '<div class="step-desc">Scrape → Classify → Synthesize</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="step-card"><div class="step-num">3</div>'
            '<div class="step-title">Output</div>'
            '<div class="step-desc">Themes + 6 research question answers</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    workflow_mode = st.radio(
        "Analysis mode",
        ["Single source (live scrape)", "Full merged dataset (all sources)"],
        horizontal=True,
    )

    left, right = st.columns([1, 1])
    demo_input = None
    source_key = "full_dataset"
    selected_label = "Full merged dataset"

    with left:
        if workflow_mode.startswith("Single"):
            source_labels = [s["label"] for s in SOURCES]
            selected_label = st.selectbox("Data source", options=source_labels)
            source_cfg = next(s for s in SOURCES if s["label"] == selected_label)
            source_key = source_cfg["key"]
            st.caption(f"{source_cfg['icon']} {source_cfg['desc']}")
            if source_cfg.get("needs_input"):
                demo_input = st.text_input(
                    source_cfg["input_label"],
                    value=source_cfg.get("input_default", ""),
                    help=source_cfg.get("input_help"),
                )
        else:
            st.markdown("**📊 Full merged corpus**")
            st.caption("Analyzes pre-merged data from Play Store, App Store, Reddit, Twitter, Forum & Social Media.")
            stats = load_corpus_stats()
            if stats["by_source"]:
                for src, count in sorted(stats["by_source"].items(), key=lambda x: -x[1]):
                    st.markdown(f"- {src.replace('_', ' ').title()}: **{count:,}**")
            corpus_filter = st.selectbox(
                "Filter by source (optional)",
                ["All sources", "reddit", "play_store", "app_store", "twitter", "community_forum", "social_media"],
                format_func=lambda x: "All sources" if x == "All sources" else x.replace("_", " ").title(),
            )
            demo_input = None if corpus_filter == "All sources" else corpus_filter

        demo_limit = st.slider("Number of reviews to analyze", min_value=10, max_value=500, value=100, step=10)
        run_clicked = st.button("▶ Run Analysis", type="primary", use_container_width=True)

    with right:
        st.markdown("**What you'll get**")
        st.markdown(
            "- Each review tagged with a discovery theme\n"
            "- Root cause + user behavior per theme\n"
            "- **Direct answers to all 6 research questions**"
        )
        st.info(
            "Live scrape: Play Store, App Store, Reddit. "
            "Full dataset uses merged corpus. Twitter/Forum/Social are pre-collected.",
            icon="ℹ️",
        )

    if run_clicked:
        label = selected_label if workflow_mode.startswith("Single") else "Full merged dataset"
        with st.spinner(f"Analyzing {demo_limit} reviews from {label}… (1–5 min)"):
            try:
                from run_workflow import run_workflow
                wf_source = source_key if workflow_mode.startswith("Single") else "full_dataset"
                live_df, live_report, live_structured, live_research = run_workflow(
                    source=wf_source,
                    search_term=demo_input,
                    limit=demo_limit,
                    source_filter=demo_input if wf_source == "full_dataset" else None,
                )
                st.session_state["live_structured"] = live_structured
                st.session_state["live_research"] = live_research
                st.session_state["live_report"] = live_report
                st.session_state["live_count"] = len(live_df)
                st.session_state["live_discovery_count"] = int(live_df["is_discovery_related"].sum())
                st.session_state["live_source"] = label
                st.success("Analysis complete!")
            except Exception as e:
                st.error(f"Workflow error: {e}")

    if "live_structured" in st.session_state:
        st.divider()
        st.subheader(f"Results · {st.session_state.get('live_source', 'Latest run')}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Reviews Processed", st.session_state.get("live_count", 0))
        m2.metric("Discovery-Related", st.session_state.get("live_discovery_count", 0))
        m3.metric("Themes Found", len(st.session_state["live_structured"]))
        m4.metric("Research Qs Answered", len(st.session_state.get("live_research", [])))
        render_theme_chart(st.session_state["live_structured"], chart_key="live_chart")
        render_theme_cards(st.session_state["live_structured"])
        render_research_questions(st.session_state.get("live_research", []))

    # Cross-source research report (pre-computed)
    st.divider()
    st.subheader("📑 Cross-Source Research Report")
    insights_path = "data/research_insights.md"
    rq_path = "data/research_questions.json"

    if os.path.exists(insights_path):
        with open(insights_path, encoding="utf-8") as f:
            insights_md = f.read()
        with st.expander("View full research_insights.md", expanded=True):
            st.markdown(insights_md)
    else:
        st.info("No cross-source report yet. Run **Full merged dataset** analysis or `python synthesize_insights.py`.")

    if os.path.exists(rq_path):
        with open(rq_path, encoding="utf-8") as f:
            rq_data = json.load(f)
        with st.expander("Research questions (JSON)", expanded=False):
            render_research_questions(rq_data)

    structured_files = sorted(glob.glob("data/workflow_runs/*_structured.json"), reverse=True)
    if structured_files:
        with st.expander("📁 Previous workflow runs", expanded=False):
            latest = structured_files[0]
            run_id = os.path.basename(latest).replace("_structured.json", "")
            st.caption(f"Latest: `{run_id}`")
            themes, research = load_structured_run(latest)
            if themes:
                render_theme_chart(themes, chart_key="prev_chart")
                render_theme_cards(themes)
            render_research_questions(research)

with tab2:
    try:
        from rag_engine import answer_question, get_corpus_stats
        rag_ok = True
    except Exception as e:
        rag_ok = False
        st.error(f"RAG engine failed to load: {e}. Run `python build_embeddings.py` first.")

    if rag_ok:
        try:
            rag_stats = get_corpus_stats()
        except FileNotFoundError:
            st.warning("No embeddings found. Run: `python build_embeddings.py`")
            rag_ok = False

    if rag_ok:
        rs1, rs2, rs3, rs4 = st.columns(4)
        rs1.metric("Corpus Size", f"{rag_stats['total']:,}")
        rs2.metric("Classified", f"{rag_stats['classified']:,}")
        rs3.metric("Sources", len(rag_stats["by_source"]))
        rs4.metric("Twitter / X", rag_stats["by_source"].get("twitter", 0))

        filter_options = ["All sources"] + [
            s.replace("_", " ").title() for s in rag_stats["by_source"]
        ]
        source_filter_display = st.selectbox("Filter by source (optional)", filter_options)
        source_filter = None
        if source_filter_display != "All sources":
            source_filter = source_filter_display.lower().replace(" ", "_")

        examples = [
            "Why do users struggle to discover new music?",
            "What are the most common frustrations with recommendations?",
            "What causes users to repeatedly listen to the same content?",
            "Do users trust Spotify's algorithm?",
            "What do users say about Discover Weekly?",
        ]
        st.markdown("**Try an example question:**")
        eq_cols = st.columns(5)
        clicked_q = None
        for i, q in enumerate(examples):
            with eq_cols[i]:
                short = q[:30] + "…" if len(q) > 30 else q
                if st.button(short, key=f"eq_{i}", use_container_width=True):
                    clicked_q = q

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "sources" in msg:
                    with st.expander(f"📄 {len(msg['sources'])} supporting quotes"):
                        for _, row in msg["sources"].iterrows():
                            theme = row.get("theme") or "unclassified"
                            if str(theme) == "nan":
                                theme = "unclassified"
                            src = str(row.get("source", "")).replace("_", " ").title()
                            st.markdown(f"**{src}** · _{theme}_")
                            st.markdown(f"> {str(row['text'])[:350]}")
                            st.divider()

        question = st.chat_input("Ask anything about Spotify discovery feedback…")
        if clicked_q:
            question = clicked_q

        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("Searching corpus & generating answer…"):
                    answer, sources = answer_question(question, source_filter=source_filter)
                    st.markdown(answer)
                    with st.expander(f"📄 {len(sources)} supporting quotes"):
                        for _, row in sources.iterrows():
                            theme = row.get("theme") or "unclassified"
                            if str(theme) == "nan":
                                theme = "unclassified"
                            src = str(row.get("source", "")).replace("_", " ").title()
                            sim = row.get("similarity", 0)
                            st.markdown(f"**{src}** · _{theme}_ · {sim:.0%} match")
                            st.markdown(f"> {str(row['text'])[:350]}")
                            st.divider()
            st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})

        with st.expander("ℹ️ About Spotify Community Forum data"):
            st.markdown("""
**Why isn't the Community Forum live-scraped?**

Spotify Community (`community.spotify.com`) uses a closed Khoros platform that requires login, has no public API, and blocks automated access.

**Best alternatives:**

1. **Manual curation** (current) — add threads to `data/raw/data/manual_sources.csv`
2. **Reddit as proxy** — your corpus already has **1,982** r/spotify posts covering the same complaints
3. **Google search** — `site:community.spotify.com discover weekly`, paste top threads manually
4. **Browser automation** (Playwright + login) — possible but fragile and likely against ToS

After adding forum posts: `python merge_all_sources.py && python build_embeddings.py`
            """)
