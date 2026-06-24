"""
Merges App Store, Play Store, Reddit, and manually-curated sources
into one unified CSV ready for the classification pipeline.
"""

import json
import pandas as pd
import os

def load_jsonl(filepath):
    """Reads a .jsonl file (one JSON object per line) into a list of dicts."""
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

print("Loading all sources...")

app_store_v1 = load_jsonl('data/raw/app_store_reviews.jsonl')
app_store_v2 = load_jsonl('data/raw/app_store_reviews_v2.jsonl')
play_store = load_jsonl('data/raw/playstore_reviews_v2.jsonl')
reddit_v1 = load_jsonl('data/raw/reddit_posts.jsonl')
reddit_v2 = load_jsonl('data/raw/reddit_posts_v2.jsonl')
manual = pd.read_csv('data/raw/data/manual_sources.csv', on_bad_lines='skip', engine='python').to_dict('records')

print(f"  App Store (v1): {len(app_store_v1)} records")
print(f"  App Store (v2): {len(app_store_v2)} records")
print(f"  Play Store: {len(play_store)} records")
print(f"  Reddit (v1): {len(reddit_v1)} records")
print(f"  Reddit (v2): {len(reddit_v2)} records")
print(f"  Manual (forums + social): {len(manual)} records")

all_records = app_store_v1 + app_store_v2 + play_store + reddit_v1 + reddit_v2 + manual

unified = []
for r in all_records:
    unified.append({
        'id': r.get('id') or f"manual_{len(unified)}",
        'source': r.get('source'),
        'title': r.get('subsource') or r.get('title') or '',
        'text': r.get('text') or '',
        'rating': r.get('rating'),
        'published_at': r.get('published_at') or r.get('date_approx'),
        'url': r.get('url')
    })

df = pd.DataFrame(unified)

before = len(df)
df = df[df['text'].str.strip() != '']
after = len(df)
print(f"\nDropped {before - after} records with empty text")

before = len(df)
df = df.drop_duplicates(subset='text')
after = len(df)
print(f"Dropped {before - after} duplicate records")

os.makedirs('data', exist_ok=True)
output_path = 'data/unified_feedback.csv'
df.to_csv(output_path, index=False)

print(f"\n✅ Done! Saved {len(df)} unified records to {output_path}")
print(f"\nBreakdown by source:")
print(df['source'].value_counts())