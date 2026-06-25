# Deploy on Streamlit Community Cloud (free public link)
# https://share.streamlit.io — see DEPLOY.md for step-by-step instructions

AI-powered review analysis system for Spotify's Growth Team. Scrapes user feedback from multiple sources, classifies it by music-discovery themes using Groq (Llama 3.3), and synthesizes insights that answer six core product research questions.

Built for **Part 1** of the PM assignment: understand *why users struggle with music discovery* before proposing any product solution.

---

## Problem Statement Mapping

| Assignment requirement | How this project addresses it |
|---|---|
| Analyze App Store + Play Store reviews | Live scrape via `run_workflow.py` |
| Analyze Reddit discussions | Live scrape via Pullpush API |
| Analyze community forums + social media | Curated CSV + scraped Twitter/X |
| AI-powered analysis at scale | Groq LLM classification + synthesis |
| Answer 6 research questions | `research_synthesis.py` → `research_insights.md` |
| Point at data → get insights | Streamlit **Live Workflow** tab |

### Six Research Questions

1. Why do users struggle to discover new music?
2. What are the most common frustrations with recommendations?
3. What listening behaviors are users trying to achieve?
4. What causes users to repeatedly listen to the same content?
5. Which user segments experience different discovery challenges?
6. What unmet needs emerge consistently across reviews?

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                            │
│  Play Store │ App Store │ Reddit │ Twitter │ Forum │ Social │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
              merge_all_sources.py
                           ▼
              data/unified_feedback.csv  (3,211 records)
                           ▼
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
  classify_reviews.py                  build_embeddings.py
  (Groq LLM themes)                    (RAG vector index)
         ▼                                   ▼
  classified_feedback.csv              data/embeddings.pkl
         ▼
  synthesize_insights.py
  (themes + 6 research Q answers)
         ▼
  research_insights.md
         ▼
  streamlit run app.py
  ├── Tab 1: Live Workflow (scrape → classify → synthesize)
  └── Tab 2: RAG Chat (explore full corpus)
```

---

## Quick Start

### 1. Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file:

```
GROQ_API_KEY=your_groq_api_key
```

### 2. Launch the app

```bash
streamlit run app.py
```

- **Tab 1 — Live Workflow:** Pick a source (or full dataset), set review count, click **Run Analysis**
- **Tab 2 — Research Chat:** Ask questions against the full 3,000+ review corpus

### 3. Full pipeline (CLI)

```bash
# Merge all scraped data into unified CSV
python merge_all_sources.py

# Classify all reviews (resumable, needs Groq quota)
python classify_reviews.py

# Generate theme insights + 6 research question answers
python synthesize_insights.py

# Rebuild RAG embeddings
python build_embeddings.py

# Or run everything at once:
python run_full_analysis.py
```

### 4. Single-source live workflow (CLI)

```bash
python run_workflow.py --source reddit --search-term "discover weekly" --limit 100
python run_workflow.py --source full_dataset --limit 200
python run_workflow.py --source twitter --limit 50
```

---

## Data Sources

| Source | Records | Collection method |
|---|---|---|
| Reddit | ~1,982 | Live scrape (`scrape_reddit_v2.py`, Pullpush API) |
| Play Store | ~600 | Live scrape (`scrape_playstore.py`) |
| App Store | ~500 | Live scrape (`scrape_appstore_v2.py`) |
| Twitter / X | ~80 | Scraped via `twitter` CLI → YAML parser |
| Community Forum | ~31 | Manually curated (`data/raw/data/manual_sources.csv`) |
| Social Media | ~18 | Manually curated |

### Spotify Community Forum

`community.spotify.com` has no public API and blocks automated scraping. Options:

1. **Manual curation** (recommended) — add threads to `manual_sources.csv`
2. **Reddit as proxy** — r/spotify mirrors most community complaints
3. **Google search** — `site:community.spotify.com discover weekly`, paste manually

---

## Discovery Theme Taxonomy

| Theme | What it captures |
|---|---|
| `recommendation_quality` | Good/bad/inaccurate recommendations |
| `repetition_fatigue` | Same songs/artists on repeat |
| `discovery_effort` | Difficulty finding new music |
| `trust_algorithm_distrust` | Skepticism toward the algorithm |
| `social_identity` | Playlists/taste as self-expression |
| `context_mismatch` | Wrong music for mood/activity |
| `not_discovery_related` | Ads, bugs, pricing, UI issues |

---

## Key Files

```
spotify-discovery-engine/
├── app.py                  # Streamlit UI (main entry point)
├── run_workflow.py         # Live scrape → classify → synthesize
├── run_full_analysis.py    # Full batch pipeline
├── merge_all_sources.py    # Merge all data into unified CSV
├── classify_reviews.py     # Batch classification (resumable)
├── synthesize_insights.py  # Theme + research question synthesis
├── research_synthesis.py   # Shared synthesis logic
├── rag_engine.py           # RAG retrieval + answers
├── build_embeddings.py     # Build vector index for chat
├── twitter_utils.py        # Twitter YAML parser
├── config.py               # API key (local .env + cloud secrets)
├── requirements.txt
├── DEPLOY.md               # How to get a public Streamlit link
└── data/
    ├── unified_feedback.csv
    ├── classified_feedback.csv
    ├── embeddings.pkl
    ├── research_insights.md
    └── raw/                # Scraped JSONL + Twitter YAML
```

### Scrapers (run manually to refresh data)

| Script | Output |
|---|---|
| `scrape_playstore.py` | Play Store reviews |
| `scrape_appstore_v2.py` | App Store reviews JSONL |
| `scrape_reddit_v2.py` | Reddit posts JSONL |
| `scrape_twitter_bulk_fixed.py` | Twitter YAML files |

---

## Outputs

| Output | Description |
|---|---|
| `data/workflow_runs/{timestamp}_classified.csv` | Per-run classified reviews |
| `data/workflow_runs/{timestamp}_insights.md` | Per-run insight report |
| `data/workflow_runs/{timestamp}_structured.json` | Themes + research Q JSON |
| `data/research_insights.md` | Cross-source research report |
| `data/research_questions.json` | Six research question answers |
| `data/embeddings.pkl` | RAG vector index |

---

## Tech Stack

- **LLM:** Groq — Llama 3.3 70B (classification + synthesis + RAG answers)
- **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`) — local, free
- **UI:** Streamlit + Plotly
- **Scraping:** google-play-scraper, iTunes RSS, Pullpush Reddit API, twitter CLI

---

## Notes

- Groq free tier has a **daily token limit**. `classify_reviews.py` is resumable — re-run when quota resets.
- RAG chat searches **all 3,211 reviews** by text similarity; theme labels appear where classification is complete.
- Twitter data requires running `scrape_twitter_bulk_fixed.py` first, then `merge_all_sources.py`.
