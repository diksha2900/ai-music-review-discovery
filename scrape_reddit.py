"""
Scrapes Spotify-related discussions from Reddit using public JSON endpoints.
No API key or login required.
Saves them to data/reddit_posts.csv
"""

import requests
import pandas as pd
import os
import time

# Subreddits relevant to Spotify discovery discussions
SUBREDDITS = ["spotify", "spotifyplaylists", "musicsuggestions"]

# Keywords to find discovery-related discussions
SEARCH_TERMS = [
    "discover weekly",
    "recommendations",
    "algorithm",
    "same songs",
    "repeat",
    "discovery",
    "new music"
]

HEADERS = {
    "User-Agent": "discovery-engine-script/1.0"
}

all_posts = []

for sub_name in SUBREDDITS:
    print(f"\nSearching r/{sub_name}...")

    for term in SEARCH_TERMS:
        print(f"  Searching for: '{term}'")

        url = f"https://www.reddit.com/r/{sub_name}/search.json"
        params = {
            "q": term,
            "restrict_sr": "1",   # search only within this subreddit
            "sort": "relevance",
            "limit": 30
        }

        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)

            if response.status_code != 200:
                print(f"    Skipped (status code {response.status_code})")
                time.sleep(2)
                continue

            data = response.json()
            posts = data.get("data", {}).get("children", [])

            for post in posts:
                p = post["data"]
                all_posts.append({
                    "post_id": p.get("id"),
                    "title": p.get("title", ""),
                    "text": p.get("selftext", ""),
                    "score": p.get("score", 0),
                    "num_comments": p.get("num_comments", 0),
                    "date": p.get("created_utc"),
                    "subreddit": sub_name,
                    "search_term": term
                })

            time.sleep(2)  # be polite, avoid getting rate-limited

        except Exception as e:
            print(f"    Skipped due to error: {e}")
            time.sleep(2)

# Convert to DataFrame and remove duplicate posts
df = pd.DataFrame(all_posts)
df = df.drop_duplicates(subset="post_id")
df["source"] = "reddit"

os.makedirs("data", exist_ok=True)
output_path = "data/reddit_posts.csv"
df.to_csv(output_path, index=False)

print(f"\n✅ Done! Saved {len(df)} unique Reddit posts to {output_path}")
print(f"\nSample of what we collected:")
print(df[["subreddit", "title"]].head(5))