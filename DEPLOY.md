# Deploy & Share Your Workflow Link

Use **Streamlit Community Cloud** (free) to get a public URL like:

`https://your-app-name.streamlit.app`

---

## Step 1 — Push code to GitHub

Your repo: `https://github.com/diksha2900/ai-music-review-discovery`

From the project folder:

```bash
cd /Users/dikshasachdeva/Desktop/spotify-discovery-engine

git add app.py config.py README.md DEPLOY.md requirements.txt .gitignore .streamlit/
git add run_workflow.py rag_engine.py research_synthesis.py merge_all_sources.py
git add classify_reviews.py synthesize_insights.py build_embeddings.py twitter_utils.py
git add run_full_analysis.py scrape_*.py
git add data/embeddings.pkl data/unified_feedback.csv data/research_insights.md
git add data/research_questions.json data/classified_feedback.csv data/raw/
git add data/workflow_runs/

git commit -m "Prepare Streamlit app for public deployment"
git push origin main
```

**Important:** Do not commit `.env` (your API key). It is already in `.gitignore`.

Required data files for the demo (must be in GitHub):
- `data/embeddings.pkl` — RAG chat
- `data/unified_feedback.csv` — full dataset mode
- `data/research_insights.md` — cross-source report shown in the app

---

## Step 2 — Deploy on Streamlit Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub.
2. Click **Create app**.
3. Fill in:
   - **Repository:** `diksha2900/ai-music-review-discovery`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Click **Advanced settings** → **Secrets** and paste:

```toml
GROQ_API_KEY = "gsk_your_actual_key_here"
```

5. Click **Deploy**.

First launch takes **3–5 minutes** (installs dependencies + downloads the embedding model).

---

## Step 3 — Submit your deliverable link

After deploy succeeds, copy the URL from the browser, e.g.:

```
https://ai-music-review-discovery.streamlit.app
```

**What reviewers can test:**

| Tab | What to demo |
|-----|----------------|
| **Live Workflow** | Pick Play Store or Reddit → set 50 reviews → **Run Analysis** → see themed insights + 6 research question answers |
| **Research Chat (RAG)** | Ask: *"Why do users struggle to discover new music?"* |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| App crashes on startup | Check **Secrets** has `GROQ_API_KEY` |
| RAG tab error | Ensure `data/embeddings.pkl` was pushed to GitHub |
| Live workflow 429 error | Groq free tier daily limit — use pre-loaded report in Tab 1 or try later |
| Slow first load | Normal — Sentence Transformers model downloads on cold start |

---

## Alternative: run locally and share via tunnel (quick test only)

```bash
# Terminal 1
streamlit run app.py

# Terminal 2 (temporary public URL, not for final submission)
npx localtunnel --port 8501
```

For assignment submission, **Streamlit Cloud** is the recommended permanent link.
