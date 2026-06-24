"""
Scrapes Spotify reviews from the Google Play Store.
Saves them to data/playstore_reviews.csv
"""

import pandas as pd
from google_play_scraper import Sort, reviews
import os

# Spotify's app ID on the Play Store
APP_ID = "com.spotify.music"

# How many reviews to pull (you can increase this later if needed)
TARGET_COUNT = 1500

print(f"Fetching up to {TARGET_COUNT} reviews for {APP_ID}...")

all_reviews = []
continuation_token = None

# The library returns reviews in pages, so we loop until we hit our target
while len(all_reviews) < TARGET_COUNT:
    result, continuation_token = reviews(
        APP_ID,
        lang='en',
        country='us',
        sort=Sort.NEWEST,
        count=200,
        continuation_token=continuation_token
    )

    if not result:
        print("No more reviews available.")
        break

    all_reviews.extend(result)
    print(f"  Collected {len(all_reviews)} so far...")

    if continuation_token is None:
        break

# Trim to exactly our target count
all_reviews = all_reviews[:TARGET_COUNT]

# Convert to a clean DataFrame with only the columns we care about
df = pd.DataFrame(all_reviews)
df = df[['reviewId', 'content', 'score', 'at', 'thumbsUpCount']]
df.columns = ['review_id', 'text', 'rating', 'date', 'helpful_count']
df['source'] = 'play_store'

# Make sure the data folder exists
os.makedirs('data', exist_ok=True)

output_path = 'data/playstore_reviews.csv'
df.to_csv(output_path, index=False)

print(f"\n✅ Done! Saved {len(df)} reviews to {output_path}")
print(f"\nSample of what we collected:")
print(df[['rating', 'text']].head(3))
