"""
Scrapes Spotify-related Reddit posts using the Pullpush API
(a public Reddit archive — no login or API key needed).
Appends new unique posts to data/raw/reddit_posts_v2.jsonl
"""

import requests
import json
import os
import time
from datetime import datetime, timezone

SUBREDDITS = ["spotify", "spotifyplaylists", "musicsuggestions"]
SEARCH_TERMS = [
    "discover weekly", "recommendations", "algorithm",
    "same songs", "repeat", "discovery", "new music",
    "shuffle", "playlist", "boring", "stuck", "bored of",
    "tired of", "explore", "fresh music", "new artist"
]

HEADERS = {"User-Agent": "discovery-engine-research/1.0"}
BASE_URL = "https://api.pullpush.io/reddit/search/submission/"

output_path = "data/raw/reddit_posts_v2.jsonl"

# Load any existing posts so we don't duplicate
existing_ids = set()
existing_posts = []
if os.path.exists(output_path):
    with open(output_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                existing_posts.append(rec)
                existing_ids.add(rec.get("source_id"))

print(f"Found {len(existing_ids)} existing posts. Searching for more...\n")

new_posts = []

for sub_name in SUBREDDITS:
    print(f"Searching r/{sub_name}...")
    for term in SEARCH_TERMS:
        print(f"  Searching for: '{term}'")
        params = {
            "subreddit": sub_name,
            "q": term,
            "size": 50,
            "sort": "desc"
        }
        try:
            response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=30)
            if response.status_code != 200:
                print(f"    Skipped (status {response.status_code})")
                time.sleep(2)
                continue

            data = response.json()
            posts = data.get("data", [])

            for p in posts:
                post_id = p.get("id")
                if post_id in existing_ids:
                    continue
                existing_ids.add(post_id)

                created = p.get("created_utc")
                published_at = (
                    datetime.fromtimestamp(created, tz=timezone.utc).isoformat()
                    if created else None
                )

                new_posts.append({
                    "id": f"reddit:{post_id}",
                    "source": "reddit",
                    "source_id": post_id,
                    "text": p.get("selftext", "") or "",
                    "title": p.get("title", ""),
                    "rating": None,
                    "author": p.get("author", ""),
                    "published_at": published_at,
                    "url": f"https://www.reddit.com{p.get('permalink', '')}",
                    "locale": sub_name,
                    "metadata": {
                        "subreddit": sub_name,
                        "score": p.get("score", 0),
                        "num_comments": p.get("num_comments", 0),
                        "search_term": term,
                        "fetch_method": "pullpush"
                    },
                    "scraped_at": datetime.now(timezone.utc).isoformat()
                })

            time.sleep(1.5)

        except Exception as e:
            print(f"    Error: {e}")
            time.sleep(2)

all_posts = existing_posts + new_posts

with open(output_path, 'w', encoding='utf-8') as f:
    for post in all_posts:
        f.write(json.dumps(post) + "\n")

print(f"\n✅ Done! Added {len(new_posts)} new posts. Total now: {len(all_posts)} in {output_path}")