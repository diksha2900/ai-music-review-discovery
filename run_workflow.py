"""
The AI-Powered Review Discovery Workflow.

Point this at a data source and search term, and it will:
  1. Scrape reviews from that source
  2. Classify them by discovery-related theme (using Groq)
  3. Synthesize the classified data into structured insights
"""

import argparse
import os
import json
import time
import pandas as pd
import requests
from groq import Groq
from dotenv import load_dotenv
from google_play_scraper import Sort, reviews

from config import get_groq_api_key

load_dotenv()
client = Groq(api_key=get_groq_api_key())

THEMES = [
    "recommendation_quality",
    "repetition_fatigue",
    "discovery_effort",
    "trust_algorithm_distrust",
    "social_identity",
    "context_mismatch",
    "not_discovery_related"
]

SYSTEM_PROMPT = f"""You are analyzing user feedback about a music streaming app for a product research project on music discovery behavior.

For EACH review provided, classify it using this exact JSON structure:
{{
  "index": <the number of the review>,
  "is_discovery_related": <true or false>,
  "theme": <one of: {', '.join(THEMES)}>,
  "sentiment": <"positive", "negative", or "neutral">,
  "key_quote": <a short verbatim phrase (under 15 words) from the review, or empty string>
}}

Return ONLY a JSON array of these objects, one per review, in the same order given. No other text."""

THEME_LABELS = {
    "recommendation_quality": "Recommendation Quality",
    "repetition_fatigue": "Repetition Fatigue",
    "discovery_effort": "Discovery Effort",
    "trust_algorithm_distrust": "Algorithm Trust/Distrust",
    "social_identity": "Social/Identity Signaling",
    "context_mismatch": "Context Mismatch"
}


# ---------- STAGE 1: SCRAPE ----------

def scrape_playstore(search_term, limit=200):
    """Scrapes Play Store reviews for an app. search_term is treated as the Play Store app ID."""
    print(f"\n[STAGE 1/3] Scraping Play Store reviews for '{search_term}'...")
    all_reviews = []
    continuation_token = None

    while len(all_reviews) < limit:
        try:
            result, continuation_token = reviews(
                search_term, lang='en', country='in', sort=Sort.NEWEST,
                count=200, continuation_token=continuation_token
            )
        except Exception as e:
            print(f"  Error: {e}")
            break
        if not result:
            break
        all_reviews.extend(result)
        print(f"  Collected {len(all_reviews)} so far...")
        if continuation_token is None:
            break

    all_reviews = all_reviews[:limit]
    if not all_reviews:
        df = pd.DataFrame(columns=['id', 'text', 'rating', 'published_at', 'source'])
    else:
        df = pd.DataFrame(all_reviews)
        df = df[['reviewId', 'content', 'score', 'at']]
        df.columns = ['id', 'text', 'rating', 'published_at']
        df['source'] = 'play_store'
    print(f"  ✅ Scraped {len(df)} reviews\n")
    return df


def scrape_appstore(search_term, limit=200):
    """Scrapes App Store reviews. search_term is the numeric App Store app ID for now (Spotify default: 324684580)."""
    print(f"\n[STAGE 1/3] Scraping App Store reviews for app ID '{search_term}'...")

    try:
        app_id = int(search_term)
    except (ValueError, TypeError):
        app_id = 324684580  # fallback to Spotify if a non-numeric term was given

    COUNTRY = "in"
    all_reviews = []
    page = 1

    while len(all_reviews) < limit and page <= 10:
        url = f"https://itunes.apple.com/{COUNTRY}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
        try:
            response = requests.get(url, headers={"User-Agent": "discovery-engine/1.0"}, timeout=20)
            if response.status_code != 200:
                break
            data = response.json()
            entries = data.get("feed", {}).get("entry", [])
            for entry in entries:
                if "im:rating" not in entry:
                    continue
                all_reviews.append({
                    "id": entry.get("id", {}).get("label", ""),
                    "text": entry.get("content", {}).get("label", ""),
                    "rating": float(entry.get("im:rating", {}).get("label", 0)),
                    "published_at": entry.get("updated", {}).get("label", "")
                })
            page += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"  Error: {e}")
            break

    df = pd.DataFrame(all_reviews[:limit])
    if len(df) == 0:
        df = pd.DataFrame(columns=['id', 'text', 'rating', 'published_at'])
    df['source'] = 'app_store'
    print(f"  ✅ Scraped {len(df)} reviews\n")
    return df


def scrape_reddit(search_term, limit=200):
    """Scrapes Reddit posts matching a search term across relevant subreddits via Pullpush."""
    print(f"\n[STAGE 1/3] Scraping Reddit for '{search_term}'...")

    SUBREDDITS = ["spotify", "spotifyplaylists", "musicsuggestions"]
    RELATED_TERMS = [search_term, "discover weekly", "recommendations", "algorithm", "repeat", "shuffle", "new music"]

    all_posts = []
    seen_ids = set()
    per_call_limit = max(20, limit // (len(SUBREDDITS) * 2))

    for sub in SUBREDDITS:
        for term in RELATED_TERMS:
            if len(all_posts) >= limit:
                break
            try:
                response = requests.get(
                    "https://api.pullpush.io/reddit/search/submission/",
                    headers={"User-Agent": "discovery-engine/1.0"},
                    params={"subreddit": sub, "q": term, "size": per_call_limit, "sort": "desc"},
                    timeout=20
                )
                if response.status_code == 200:
                    data = response.json()
                    for p in data.get("data", []):
                        post_id = p.get("id")
                        if post_id in seen_ids:
                            continue
                        seen_ids.add(post_id)
                        text = (p.get("selftext") or "") + " " + (p.get("title") or "")
                        all_posts.append({
                            "id": post_id,
                            "text": text.strip(),
                            "rating": None,
                            "published_at": p.get("created_utc")
                        })
                time.sleep(1)
            except Exception as e:
                print(f"  Skipped ({sub}, {term}): {e}")
                continue
        if len(all_posts) >= limit:
            break

    df = pd.DataFrame(all_posts[:limit])
    if len(df) == 0:
        df = pd.DataFrame(columns=['id', 'text', 'rating', 'published_at'])
    df['source'] = 'reddit'
    print(f"  ✅ Scraped {len(df)} posts\n")
    return df


def load_manual_source(source_type):
    """Loads the manually-curated community forum / social media data."""
    print(f"\n[STAGE 1/3] Loading manually-curated {source_type} data...")
    path = 'data/raw/data/manual_sources.csv'
    try:
        manual_df = pd.read_csv(path, on_bad_lines='skip', engine='python')
        filtered = manual_df[manual_df['source'] == source_type].copy()
        filtered = filtered.rename(columns={'date_approx': 'published_at'})
        filtered['id'] = [f"{source_type}_{i}" for i in range(len(filtered))]
        filtered['rating'] = None
        df = filtered[['id', 'text', 'rating', 'published_at', 'source']].reset_index(drop=True)
    except Exception as e:
        print(f"  Error loading manual data: {e}")
        df = pd.DataFrame(columns=['id', 'text', 'rating', 'published_at', 'source'])
    print(f"  ✅ Loaded {len(df)} records\n")
    return df


def load_twitter_scraped(limit=200):
    """Loads scraped Twitter/X data from data/raw/twitter*.json (YAML from twitter CLI)."""
    from twitter_utils import load_twitter_raw_files, filter_relevant_tweets

    print(f"\n[STAGE 1/3] Loading scraped Twitter/X data...")
    records = filter_relevant_tweets(load_twitter_raw_files())
    if limit:
        records = records[:limit]

    if not records:
        df = pd.DataFrame(columns=['id', 'text', 'rating', 'published_at', 'source'])
    else:
        df = pd.DataFrame(records)[['id', 'text', 'rating', 'published_at', 'source']]

    print(f"  ✅ Loaded {len(df)} tweets\n")
    return df


def load_full_dataset(limit=200, source_filter=None):
    """Loads the merged unified corpus (all sources). Optionally filter by source."""
    print(f"\n[STAGE 1/3] Loading full merged dataset...")
    path = 'data/unified_feedback.csv'
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found. Run: python merge_all_sources.py")

    df = pd.read_csv(path)
    df['text'] = df['text'].fillna('').astype(str)
    df = df[df['text'].str.strip() != '']

    if source_filter:
        df = df[df['source'] == source_filter]

    if limit:
        df = df.head(limit)

    out = df[['id', 'text', 'rating', 'published_at', 'source']].reset_index(drop=True)
    print(f"  ✅ Loaded {len(out)} records from unified corpus\n")
    return out


# ---------- STAGE 2: CLASSIFY ----------

def classify_batch(reviews_batch, max_retries=3):
    numbered = "\n\n".join([f"Review {i+1}: {str(t)[:500]}" for i, t in enumerate(reviews_batch)])
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": numbered}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except Exception as e:
            print(f"    Retry {attempt+1}/{max_retries} after error: {e}")
            time.sleep(5)
    return []


def classify_reviews(df, batch_size=10):
    print(f"[STAGE 2/3] Classifying {len(df)} reviews with Groq (Llama 3.3 70B)...")

    df = df.reset_index(drop=True)
    for col in ['is_discovery_related', 'theme', 'sentiment', 'key_quote']:
        df[col] = None

    for start in range(0, len(df), batch_size):
        batch_texts = df['text'].iloc[start:start + batch_size].tolist()
        results = classify_batch(batch_texts)
        for r in results:
            idx = start + r.get('index', 0) - 1
            if 0 <= idx < len(df):
                df.at[idx, 'is_discovery_related'] = r.get('is_discovery_related', False)
                df.at[idx, 'theme'] = r.get('theme', 'not_discovery_related')
                df.at[idx, 'sentiment'] = r.get('sentiment', 'neutral')
                df.at[idx, 'key_quote'] = r.get('key_quote', '')
        print(f"  Classified {min(start + batch_size, len(df))}/{len(df)}...")
        time.sleep(1)

    print(f"  ✅ Classification complete\n")
    return df


# ---------- STAGE 3: SYNTHESIZE ----------

def synthesize_theme(theme_label, quotes):
    quotes_text = "\n".join([f'- "{q}"' for q in quotes[:25] if q and str(q) != 'nan'])
    prompt = f"""You are a product research analyst. Below are real user feedback quotes tagged under the theme "{theme_label}".

Quotes:
{quotes_text}

Return ONLY a JSON object with this exact structure, no other text:
{{
  "root_cause": "<1-2 sentence root cause behind this pattern>",
  "user_behavior": "<1-2 sentence description of the distinct user behavior hinted at>",
  "representative_quote": "<the single most illustrative quote, max 20 words, verbatim>"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception as e:
        return {"root_cause": f"[Unavailable: {e}]", "user_behavior": "", "representative_quote": ""}


def synthesize_insights(df, source_label, include_research_questions=True):
    from research_synthesis import (
        build_full_report,
        build_theme_sections,
        synthesize_all_research_questions,
    )

    print(f"[STAGE 3/3] Synthesizing insights...")
    discovery_df = df[df['is_discovery_related'] == True]

    theme_sections, structured_results = build_theme_sections(discovery_df, structured=True)

    research_results = []
    if include_research_questions and len(discovery_df) > 0:
        print("  Synthesizing research question answers...")
        research_results = synthesize_all_research_questions(discovery_df)

    report = build_full_report(
        df, source_label, discovery_df, theme_sections, research_results, structured=True,
    )
    print(f"  ✅ Synthesis complete\n")
    return report, structured_results, research_results


# ---------- MAIN WORKFLOW ----------

def run_workflow(source, search_term=None, limit=200, source_filter=None):
    os.makedirs('data/workflow_runs', exist_ok=True)
    run_id = time.strftime("%Y%m%d_%H%M%S")

    if source == "playstore":
        df = scrape_playstore(search_term or "com.spotify.music", limit)
        source_label = f"Google Play Store — {search_term or 'com.spotify.music'}"
    elif source == "appstore":
        df = scrape_appstore(search_term or "324684580", limit)
        source_label = f"Apple App Store — app ID {search_term or '324684580'}"
    elif source == "reddit":
        df = scrape_reddit(search_term or "spotify", limit)
        source_label = f"Reddit — search: '{search_term or 'spotify'}'"
    elif source == "community_forum":
        df = load_manual_source("community_forum")
        source_label = "Spotify Community Forum (curated)"
    elif source == "social_media":
        df = load_manual_source("social_media")
        source_label = "Social Media — Twitter/X (curated)"
    elif source == "twitter":
        df = load_twitter_scraped(limit)
        source_label = "Twitter/X (scraped)"
    elif source == "full_dataset":
        df = load_full_dataset(limit, source_filter=source_filter or search_term)
        if source_filter or search_term:
            source_label = f"Full merged corpus — filter: {source_filter or search_term}"
        else:
            source_label = "Full merged corpus (all sources)"
    else:
        raise ValueError(f"Unsupported source: {source}")

    if len(df) == 0:
        raise ValueError("No data retrieved for this source/term. Try a different one.")

    df = classify_reviews(df)
    df.to_csv(f'data/workflow_runs/{run_id}_classified.csv', index=False)

    report, structured_results, research_results = synthesize_insights(df, source_label)

    report_path = f'data/workflow_runs/{run_id}_insights.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    structured_path = f'data/workflow_runs/{run_id}_structured.json'
    with open(structured_path, 'w', encoding='utf-8') as f:
        json.dump({"themes": structured_results, "research_questions": research_results}, f, indent=2)

    # Also refresh the main cross-source report when running full dataset
    if source == "full_dataset":
        with open('data/research_insights.md', 'w', encoding='utf-8') as f:
            f.write(report)
        with open('data/research_questions.json', 'w', encoding='utf-8') as f:
            json.dump(research_results, f, indent=2)

    print(f"{'='*60}")
    print(f"✅ WORKFLOW COMPLETE")
    print(f"   Classified data: data/workflow_runs/{run_id}_classified.csv")
    print(f"   Insights report: {report_path}")
    print(f"{'='*60}\n")

    return df, report, structured_results, research_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-Powered Review Discovery Workflow")
    parser.add_argument("--source", required=True, choices=[
        "playstore", "appstore", "reddit", "community_forum",
        "social_media", "twitter", "full_dataset",
    ])
    parser.add_argument("--search-term", default=None, help="App ID, keyword, or source filter for full_dataset")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    run_workflow(source=args.source, search_term=args.search_term, limit=args.limit)