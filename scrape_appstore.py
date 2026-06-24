"""
Scrapes Spotify reviews from the Apple App Store.
Saves them to data/appstore_reviews.csv
"""

import pandas as pd
from app_store_scraper import AppStore
import os

# Spotify's details on the App Store
APP_NAME = "spotify-music-and-podcasts"
APP_ID = 324684580
COUNTRY = "us"

TARGET_COUNT = 600

print(f"Fetching up to {TARGET_COUNT} reviews for {APP_NAME}...")

spotify_app = AppStore(country=COUNTRY, app_name=APP_NAME, app_id=APP_ID)
spotify_app.review(how_many=TARGET_COUNT)

all_reviews = spotify_app.reviews

print(f"  Collected {len(all_reviews)} reviews total")

# Convert to a clean DataFrame
df = pd.DataFrame(all_reviews)
df = df[['title', 'review', 'rating', 'date', 'userName']]
df.columns = ['title', 'text', 'rating', 'date', 'user']
df['source'] = 'app_store'

# Make sure the data folder exists
os.makedirs('data', exist_ok=True)

output_path = 'data/appstore_reviews.csv'
df.to_csv(output_path, index=False)

print(f"\n✅ Done! Saved {len(df)} reviews to {output_path}")
print(f"\nSample of what we collected:")
print(df[['rating', 'text']].head(3))