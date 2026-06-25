"""
Parse Twitter CLI output saved as YAML (.json extension) into normalized records.
"""

import glob
import json
import os

import yaml

UNIFIED_COLUMNS = [
    "id", "source", "title", "text", "rating", "published_at", "url",
    "is_discovery_related", "theme", "sentiment", "key_quote",
]

DISCOVERY_KEYWORDS = [
    "discover", "recommend", "algorithm", "playlist", "repeat", "same song",
    "same music", "new music", "shuffle", "weekly", "bored", "stuck", "fresh",
    "suggestion", "radio", "mix", "explore", "genre", "listen", "music",
    "discover weekly", "release radar", "daily mix", "autoplay", "spotify wrapped",
]

SPAM_PATTERNS = [
    "distrokid", "linktree", "presave", "pre-save", "out now", "streaming everywhere",
    "follow me", "check out my", "new single", "new album", "available on all platforms",
    "smartlink", "ffm.to", "song.link",
]


def is_twitter_relevant(text: str) -> bool:
    """Keep tweets that mention Spotify and look discovery-related, not promo spam."""
    lower = text.lower()
    if "spotify" not in lower:
        return False

    discovery_hits = sum(1 for kw in DISCOVERY_KEYWORDS if kw in lower)
    is_spam = any(p in lower for p in SPAM_PATTERNS)

    if is_spam and discovery_hits < 2:
        return False
    return discovery_hits >= 1


def filter_relevant_tweets(records: list[dict]) -> list[dict]:
    return [r for r in records if is_twitter_relevant(r["text"])]

UNIFIED_COLUMNS = [
    "id", "source", "title", "text", "rating", "published_at", "url",
    "is_discovery_related", "theme", "sentiment", "key_quote",
]


def parse_twitter_file(path: str) -> list[dict]:
    """Parse one twitter CLI YAML file into normalized review dicts."""
    records = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"  Skipping {path}: {e}")
        return records

    if not isinstance(data, dict):
        return records

    for item in data.get("data") or []:
        text = (item.get("text") or "").strip()
        if not text:
            continue

        tweet_id = str(item.get("id", ""))
        author = item.get("author") or {}
        screen_name = author.get("screenName") or author.get("screen_name") or ""
        url = f"https://x.com/{screen_name}/status/{tweet_id}" if tweet_id and screen_name else ""

        records.append({
            "id": f"twitter:{tweet_id}",
            "source": "twitter",
            "title": None,
            "text": text,
            "rating": None,
            "published_at": item.get("createdAtISO") or item.get("createdAt") or "",
            "url": url,
            "is_discovery_related": None,
            "theme": None,
            "sentiment": None,
            "key_quote": None,
        })

    return records


def load_twitter_raw_files(pattern: str = "data/raw/twitter*.json") -> list[dict]:
    """Load and dedupe all scraped Twitter files matching pattern."""
    seen_ids: set[str] = set()
    seen_text: set[str] = set()
    records: list[dict] = []

    for path in sorted(glob.glob(pattern)):
        for record in parse_twitter_file(path):
            rid = record["id"]
            text_key = record["text"][:200]
            if rid in seen_ids or text_key in seen_text:
                continue
            seen_ids.add(rid)
            seen_text.add(text_key)
            records.append(record)

    return records


def save_twitter_jsonl(records: list[dict], path: str = "data/raw/twitter_reviews_v2.jsonl") -> int:
    """Write normalized Twitter records to JSONL (v2 schema)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            row = {
                "id": record["id"],
                "source": "twitter",
                "source_id": record["id"].replace("twitter:", ""),
                "text": record["text"],
                "title": None,
                "rating": None,
                "published_at": record["published_at"],
                "url": record["url"],
                "metadata": {},
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(records)
