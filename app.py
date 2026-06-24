"""
Spotify Discovery Review Engine — Workflow Demonstration
Primary view: the scrape -> classify -> synthesize workflow and its output.
Secondary view: a chat tool to explore the full historical dataset further.
"""

import streamlit as st
import pandas as pd
import os
import glob
import json
import plotly.graph_objects as go

st.set_page_config(page_title="Spotify Discovery Workflow", page_icon="🎧", layout="wide")

# ---------- SPOTIFY-THEMED STYLING ----------
st.markdown("""
<style>
    .stApp { background-color: #0a0a0a; color: #ffffff; }
    h1, h2, h3 { color: #1DB954 !important; }
    .stTabs [data-baseweb="tab"] { color: #ffffff; }
    .stTabs [aria-selected="true"] { color: #1DB954 !important; border-bottom-color: #1DB954 !important; }
    div[data-testid="stMetricValue"] { color: #1DB954; }
    .stAlert { background-color: #181818; border-left: 4px solid #1DB954; }
    div[data-testid="stExpander"] { background-color: #181818; border-radius: 8px; }
    .stChatMessage { background-color: #181818; border-radius: 12px; }
    a { color: #1DB954 !important; }
    .theme-card {
        background-color: #181818;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        border-left: 4px solid #1DB954;
    }
    .theme-card h4 { color: #1DB954; margin-top: 0; margin-bottom: 14px; }
    .theme-card .label { color: #1DB954; font-weight: 600; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px; }
    .theme-card .value { color: #e0e0e0; line-height: 1.5; margin-bottom: 12px; }
    .theme-card .quote { color: #b0b0b0; font-style: italic; border-left: 2px solid #444; padding-left: 12px; margin-top: 8px; }
    div.stButton > button {
        background-color: #1DB954;
        color: #000000;
        border-radius: 24px;
        font-weight: 600;
        border: none;
    }
    div.stButton > button:hover { background-color: #1ed760; color: #000000; }
</style>
""", unsafe_allow_html=True)

# ---------- HEADER WITH SPOTIFY LOGO ----------
header_col1, header_col2 = st.columns([1, 10])
with header_col1:
    st.markdown("""
    <svg width="60" height="60" viewBox="0 0 24 24" fill="#1DB954">
        <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.020-.12-1.140-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.6.18-1.2.72-1.38 4.26-1.26 11.28-1.02 15.12 1.26.539.3.719 1.02.419 1.56-.3.421-1.02.599-1.559.3z"/>
    </svg>
    """, unsafe_allow_html=True)
with header_col2:
    st.title("AI-Powered Review Discovery Workflow")

st.caption("Point this workflow at a data source — it scrapes reviews, classifies them by discovery-related theme using an LLM (Groq/Llama 3.3), and synthesizes the findings into insights.")

tab1, tab2 = st.tabs(["🔄 Workflow", "💬 Explore Further (RAG chat)"])


def render_theme_cards(structured_results):
    """Renders each theme as a styled card with labeled sections."""
    for item in structured_results:
        root_cause = str(item.get('root_cause', '')).replace('"', '&quot;')
        user_behavior = str(item.get('user_behavior', '')).replace('"', '&quot;')
        quote = str(item.get('representative_quote', '')).replace('"', '&quot;')
        heading = f"{item.get('theme', '')} ({item.get('count', 0)} records)"

        card_html = (
            '<div class="theme-card">'
            f'<h4>{heading}</h4>'
            '<div class="label">Root Cause</div>'
            f'<div class="value">{root_cause}</div>'
            '<div class="label">User Behavior</div>'
            f'<div class="value">{user_behavior}</div>'
            f'<div class="quote">"{quote}"</div>'
            '</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)


def render_theme_chart(structured_results, chart_key="chart"):
    """Renders a clean horizontal bar chart of theme frequency."""
    if not structured_results:
        return
    themes = [item['theme'] for item in structured_results]
    counts = [item['count'] for item in structured_results]

    sorted_pairs = sorted(zip(themes, counts), key=lambda x: x[1])
    themes_sorted = [p[0] for p in sorted_pairs]
    counts_sorted = [p[1] for p in sorted_pairs]

    fig = go.Figure(go.Bar(
        x=counts_sorted,
        y=themes_sorted,
        orientation='h',
        marker=dict(color='#1DB954'),
        text=counts_sorted,
        textposition='outside',
        textfont=dict(color='#ffffff')
    ))
    fig.update_layout(
        plot_bgcolor='#0a0a0a',
        paper_bgcolor='#0a0a0a',
        font=dict(color='#ffffff'),
        margin=dict(l=10, r=10, t=10, b=10),
        height=max(250, len(themes_sorted) * 60),
        xaxis=dict(showgrid=True, gridcolor='#2a2a2a', title="Number of Records"),
        yaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig, use_container_width=True, key=chart_key)


# ============ TAB 1: THE WORKFLOW ============
with tab1:
    st.header("Workflow: Input → Process → Output")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**1. INPUT**\n\nChoose a data source + search term")
    with col2:
        st.info("**2. PROCESS**\n\nScrape →\nClassify (Groq) →\nSynthesize (Groq)")
    with col3:
        st.info("**3. OUTPUT**\n\nThemed insights\nwith root causes & quotes")

    st.divider()

    # ---------- LIVE DEMO ----------
    st.subheader("🎬 Try it live")
    st.caption("Choose a data source and search term, then run the full workflow live — real scraping, real Groq classification, real synthesis.")

    demo_source_display = st.selectbox(
        "1. Choose a data source",
        options=["Play Store", "App Store", "Reddit", "Community Forum (curated)", "Social Media (curated)"]
    )

    SOURCE_MAP = {
        "Play Store": "playstore",
        "App Store": "appstore",
        "Reddit": "reddit",
        "Community Forum (curated)": "community_forum",
        "Social Media (curated)": "social_media"
    }
    source_key = SOURCE_MAP[demo_source_display]

    if source_key == "playstore":
        demo_input = st.text_input("2. Play Store App ID", value="com.spotify.music",
                                     help="e.g. com.spotify.music, com.whatsapp, com.netflix.mediaclient")
    elif source_key == "appstore":
        demo_input = st.text_input("2. App Store numeric App ID", value="324684580",
                                     help="Find this in an App Store URL: apps.apple.com/.../id THIS_NUMBER")
    elif source_key == "reddit":
        demo_input = st.text_input("2. Search keyword", value="spotify discover weekly",
                                     help="Searches r/spotify, r/spotifyplaylists, r/musicsuggestions for this term")
    else:
        demo_input = None
        st.caption("This source uses pre-collected, manually curated data (no live search term needed).")

    demo_limit = st.slider("3. Number of reviews to analyze", min_value=50, max_value=500, value=200, step=50)

    if st.button("▶️ Run live workflow"):
        with st.spinner(f"Running workflow live on {demo_source_display} — this may take 1-3 minutes for {demo_limit} reviews..."):
            try:
                from run_workflow import run_workflow
                live_df, live_report, live_structured = run_workflow(
                    source=source_key, search_term=demo_input, limit=demo_limit
                )
                st.session_state['live_structured'] = live_structured
                st.session_state['live_count'] = len(live_df)
                st.session_state['live_discovery_count'] = int(live_df['is_discovery_related'].sum())
                st.success("✅ Live run complete! See results below.")
            except Exception as e:
                st.error(f"Live run hit an error: {e}")

    if 'live_structured' in st.session_state:
        st.divider()
        st.subheader("📊 Live Run Results")
        col1, col2, col3 = st.columns(3)
        col1.metric("Reviews Processed", st.session_state.get('live_count', 0))
        col2.metric("Discovery-Related", st.session_state.get('live_discovery_count', 0))
        col3.metric("Themes Identified", len(st.session_state['live_structured']))
        render_theme_chart(st.session_state['live_structured'], chart_key="live_chart")
        render_theme_cards(st.session_state['live_structured'])

    st.divider()

    # ---------- LATEST FULL WORKFLOW RUN (pre-computed) ----------
    structured_files = sorted(glob.glob('data/workflow_runs/*_structured.json'), reverse=True)

    if structured_files:
        latest_structured_path = structured_files[0]
        run_id = os.path.basename(latest_structured_path).replace('_structured.json', '')
        classified_path = f'data/workflow_runs/{run_id}_classified.csv'

        st.subheader(f"📊 Latest pre-computed run: `{run_id}`")

        if os.path.exists(classified_path):
            run_df = pd.read_csv(classified_path)
            col1, col2, col3 = st.columns(3)
            col1.metric("Reviews Processed", len(run_df))
            col2.metric("Discovery-Related", int(run_df['is_discovery_related'].sum()))
            col3.metric("Themes Identified", run_df['theme'].nunique())

        with open(latest_structured_path, 'r', encoding='utf-8') as f:
            structured_results = json.load(f)

        render_theme_chart(structured_results, chart_key="latest_run_chart")
        render_theme_cards(structured_results)
    else:
        st.warning("No pre-computed workflow runs found yet.")

    st.divider()
    st.caption("💡 This workflow is parameterized by data source and search term — point it at any app or keyword and it runs the same pipeline.")

# ============ TAB 2: RAG CHAT (secondary) ============
with tab2:
    st.caption("This tool lets you query the full historical dataset for deeper exploration beyond a single workflow run.")

    EXAMPLE_QUESTIONS = [
        "Why do users struggle to discover new music?",
        "What are the most common frustrations with recommendations?",
        "What causes users to repeatedly listen to the same content?",
        "Do users trust Spotify's algorithm?",
        "What do users say about Discover Weekly specifically?"
    ]

    st.markdown("**💡 Example questions:**")
    example_cols = st.columns(len(EXAMPLE_QUESTIONS))
    clicked_question = None
    for i, q in enumerate(EXAMPLE_QUESTIONS):
        with example_cols[i]:
            if st.button(q, key=f"example_q_{i}", use_container_width=True):
                clicked_question = q

    try:
        from rag_engine import answer_question
        rag_available = True
    except Exception as e:
        rag_available = False
        st.error(f"RAG engine could not be loaded: {e}")

    if rag_available:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sources" in message:
                    with st.expander(f"📄 View {len(message['sources'])} supporting quotes"):
                        for _, row in message["sources"].iterrows():
                            st.markdown(f"**[{row['source']}]** _{row['theme']}_")
                            st.markdown(f"> {str(row['text'])[:300]}")
                            st.markdown("---")

        question = st.chat_input("Ask a deeper question about the full dataset...")

        if clicked_question:
            question = clicked_question

        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Searching reviews and generating answer..."):
                    answer, sources = answer_question(question)
                    st.markdown(answer)
                    with st.expander(f"📄 View {len(sources)} supporting quotes"):
                        for _, row in sources.iterrows():
                            st.markdown(f"**[{row['source']}]** _{row['theme']}_")
                            st.markdown(f"> {str(row['text'])[:300]}")
                            st.markdown("---")

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources
            })