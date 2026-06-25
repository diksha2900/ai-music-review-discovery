"""
Rebuild data/unified_feedback.csv from all v2 JSONL sources, Twitter YAML, and manual CSV.

Run after scraping:
  python scrape_reddit_v2.py
  python scrape_twitter_bulk_fixed.py   # optional, for fresh tweets
  python merge_all_sources.py
"""

import glob
import json
import os

import pandas as pd

from twitter_utils import (
    UNIFIED_COLUMNS,
    filter_relevant_tweets,
    load_twitter_raw_files,
    save_twitter_jsonl,
)

UNIFIED_PATH = "data/unified_feedback.csv"
CLASSIFIED_PATH = "data/classified_feedback.csv"
MANUAL_PATH = "data/raw/data/manual_sources.csv"

JSONL_SOURCES = [
    "data/raw/playstore_reviews_v2.jsonl",
    "data/raw/app_store_reviews_v2.jsonl",
    "data/raw/reddit_posts_v2.jsonl",
    "data/raw/twitter_reviews_v2.jsonl",
]


def load_jsonl(path: str) -> list[dict]:
    records = []
    if not os.path.exists(path):
        print(f"  Skipping missing file: {path}")
        return records
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    print(f"  Loaded {len(records)} from {path}")
    return records


def export_reddit_fallback_from_unified() -> list[dict]:
    """If reddit v2 jsonl is missing, recover reddit rows from existing unified CSV."""
    reddit_path = "data/raw/reddit_posts_v2.jsonl"
    unified_path = UNIFIED_PATH
    if os.path.exists(reddit_path) or not os.path.exists(unified_path):
        return []

    unified = pd.read_csv(unified_path)
    reddit_rows = unified[unified["source"] == "reddit"]
    if len(reddit_rows) == 0:
        return []

    records = []
    for _, row in reddit_rows.iterrows():
        records.append({
            "id": row["id"],
            "source": "reddit",
            "source_id": str(row["id"]).replace("reddit:", ""),
            "text": row["text"],
            "title": row.get("title"),
            "rating": row.get("rating"),
            "published_at": row.get("published_at"),
            "url": row.get("url") or "",
        })
    print(f"  Recovered {len(records)} reddit rows from existing unified CSV")
    return records


def jsonl_to_unified(record: dict) -> dict:
    text = (record.get("text") or "").strip()
    title = record.get("title")
    if record.get("source") == "reddit" and title:
        combined = f"{title}\n\n{text}".strip() if text else str(title).strip()
        text = combined

    return {
        "id": record["id"],
        "source": record["source"],
        "title": title if title and str(title) != "nan" else None,
        "text": text,
        "rating": record.get("rating"),
        "published_at": record.get("published_at") or "",
        "url": record.get("url") or "",
        "is_discovery_related": None,
        "theme": None,
        "sentiment": None,
        "key_quote": None,
    }


def load_manual_sources() -> list[dict]:
    if not os.path.exists(MANUAL_PATH):
        print(f"  Skipping missing file: {MANUAL_PATH}")
        return []
    manual_df = pd.read_csv(MANUAL_PATH, on_bad_lines="skip", engine="python")
    records = []
    for i, row in manual_df.iterrows():
        text = str(row.get("text", "")).strip()
        if not text:
            continue
        source = row.get("source", "community_forum")
        records.append({
            "id": f"{source}:manual_{i}",
            "source": source,
            "title": row.get("subsource"),
            "text": text,
            "rating": None,
            "published_at": str(row.get("date_approx", "")),
            "url": "",
            "is_discovery_related": None,
            "theme": None,
            "sentiment": None,
            "key_quote": None,
        })
    print(f"  Loaded {len(records)} from {MANUAL_PATH}")
    return records


def preserve_classifications(unified_df: pd.DataFrame) -> pd.DataFrame:
    """Carry over valid classifications from existing classified_feedback.csv."""
    if not os.path.exists(CLASSIFIED_PATH):
        return unified_df

    classified = pd.read_csv(CLASSIFIED_PATH)
    valid_themes = {
        "recommendation_quality", "repetition_fatigue", "discovery_effort",
        "trust_algorithm_distrust", "social_identity", "context_mismatch",
        "not_discovery_related",
    }
    classify_cols = ["is_discovery_related", "theme", "sentiment", "key_quote"]
    keep = classified[classified["theme"].isin(valid_themes)][["id"] + classify_cols]

    merged = unified_df.drop(columns=classify_cols, errors="ignore").merge(
        keep, on="id", how="left"
    )
    preserved = merged["theme"].notna().sum()
    print(f"  Preserved {preserved} existing classifications")
    return merged


def merge_all_sources(unified_path: str = UNIFIED_PATH) -> pd.DataFrame:
    print("Building unified dataset from all sources...\n")

    # Twitter: parse YAML, filter, write jsonl for other tools
    print("Twitter:")
    all_twitter = load_twitter_raw_files()
    twitter_records = filter_relevant_tweets(all_twitter)
    print(f"  {len(all_twitter)} parsed → {len(twitter_records)} discovery-relevant")
    save_twitter_jsonl(twitter_records)

    records: list[dict] = []
    for path in JSONL_SOURCES:
        raw_records = load_jsonl(path)
        if not raw_records and path.endswith("reddit_posts_v2.jsonl"):
            raw_records = export_reddit_fallback_from_unified()
        for raw in raw_records:
            records.append(jsonl_to_unified(raw))

    records.extend(load_manual_sources())

    if not records:
        raise ValueError("No records loaded from any source.")

    df = pd.DataFrame(records)
    df = df[df["text"].fillna("").str.strip() != ""]
    df = df.drop_duplicates(subset=["id"], keep="first")
    df = df.reset_index(drop=True)

    for col in UNIFIED_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[UNIFIED_COLUMNS]

    df = preserve_classifications(df)

    os.makedirs("data", exist_ok=True)
    df.to_csv(unified_path, index=False)

    print(f"\n✅ Saved {len(df)} records to {unified_path}")
    print(df["source"].value_counts().to_string())
    return df


if __name__ == "__main__":
    merge_all_sources()
