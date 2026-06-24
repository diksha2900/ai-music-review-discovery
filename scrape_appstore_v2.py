"""
Scrapes Spotify reviews from Apple's official RSS feed endpoint.
No API key or login needed. Saves to data/raw/app_store_reviews_v2.jsonl
"""

import requests
import json
import os
import time
from datetime import datetime, timezone

APP_ID = 324684580
COUNTRY = "in"  # matches the data we already have (India reviews)
MAX_PAGES = 10  # Apple's RSS feed paginates; each page has ~50 reviews

HEADERS = {"User-Agent": "discovery-engine-research/1.0"}

output_path = "data/raw/app_store_reviews_v2.jsonl"

existing_ids = set()
existing_reviews = []
if os.path.exists(output_path):
    with open(output_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                existing_reviews.append(rec)
                existing_ids.add(rec.get("source_id"))

print(f"Found {len(existing_ids)} existing reviews. Fetching more...\n")

new_reviews = []

for page in range(1, MAX_PAGES + 1):
    url = f"https://itunes.apple.com/{COUNTRY}/rss/customerreviews/page={page}/id={APP_ID}/sortby=mostrecent/json"
    print(f"Fetching page {page}...")

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            print(f"  Skipped (status {response.status_code})")
            time.sleep(2)
            continue

        data = response.json()
        entries = data.get("feed", {}).get("entry", [])

        # The first entry on page 1 is sometimes app metadata, not a review — skip if it lacks a rating
        for entry in entries:
            if "im:rating" not in entry:
                continue

            review_id = entry.get("id", {}).get("label", "")
            if review_id in existing_ids:
                continue
            existing_ids.add(review_id)

            new_reviews.append({
                "id": f"app_store:{review_id}",
                "source": "app_store",
                "source_id": review_id,
                "text": entry.get("content", {}).get("label", ""),
                "title": entry.get("title", {}).get("label", ""),
                "rating": float(entry.get("im:rating", {}).get("label", 0)),
                "author": entry.get("author", {}).get("name", {}).get("label", ""),
                "published_at": entry.get("updated", {}).get("label", ""),
                "url": f"https://apps.apple.com/{COUNTRY}/app/id{APP_ID}",
                "locale": COUNTRY.upper(),
                "metadata": {
                    "app_id": APP_ID,
                    "app_version": entry.get("im:version", {}).get("label", ""),
                    "vote_count": entry.get("im:voteCount", {}).get("label", "0"),
                    "fetch_method": "apple_rss"
                },
                "scraped_at": datetime.now(timezone.utc).isoformat()
            })

        time.sleep(1.5)

    except Exception as e:
        print(f"  Error: {e}")
        time.sleep(2)

all_reviews = existing_reviews + new_reviews

with open(output_path, 'w', encoding='utf-8') as f:
    for r in all_reviews:
        f.write(json.dumps(r) + "\n")

print(f"\n✅ Done! Added {len(new_reviews)} new reviews. Total now: {len(all_reviews)} in {output_path}")