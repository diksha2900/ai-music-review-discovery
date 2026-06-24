"""
Retries classification for any rows that failed in the first pass.
Reads data/classified_feedback.csv, finds rows with missing 'theme',
re-classifies just those, and updates the same file.
"""

import os
import json
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from tqdm import tqdm
import time

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

BATCH_SIZE = 5  # smaller batches this time, to reduce parse failures

THEMES = [
    "recommendation_quality",
    "repetition_fatigue",
    "discovery_effort",
    "trust_algorithm_distrust",
    "social_identity",
    "context_mismatch",
    "not_discovery_related"
]

SYSTEM_PROMPT = f"""You are analyzing user feedback about Spotify for a product research project on music discovery behavior.

For EACH review provided, classify it using this exact JSON structure:
{{
  "index": <the number of the review>,
  "is_discovery_related": <true or false>,
  "theme": <one of: {', '.join(THEMES)}>,
  "sentiment": <"positive", "negative", or "neutral">,
  "key_quote": <a short verbatim phrase (under 15 words) from the review that best supports the classification, or empty string if not discovery related>
}}

Return ONLY a JSON array of these objects, one per review, in the same order given. No other text, no markdown formatting, no explanation."""

def classify_batch(reviews_batch):
    numbered_reviews = "\n\n".join(
        [f"Review {i+1}: {text[:500]}" for i, text in enumerate(reviews_batch)]
    )
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": numbered_reviews}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception as e:
        print(f"  Batch error (will stay unclassified): {e}")
        return []

print("Loading classified feedback...")
df = pd.read_csv('data/classified_feedback.csv')

missing_mask = df['theme'].isna()
missing_indices = df[missing_mask].index.tolist()
print(f"Found {len(missing_indices)} unclassified rows. Retrying...\n")

for start in tqdm(range(0, len(missing_indices), BATCH_SIZE)):
    batch_indices = missing_indices[start:start + BATCH_SIZE]
    batch_texts = df.loc[batch_indices, 'text'].tolist()

    results = classify_batch(batch_texts)

    for r in results:
        idx_in_batch = r.get('index', 0) - 1
        if 0 <= idx_in_batch < len(batch_indices):
            real_idx = batch_indices[idx_in_batch]
            df.at[real_idx, 'is_discovery_related'] = r.get('is_discovery_related', False)
            df.at[real_idx, 'theme'] = r.get('theme', 'not_discovery_related')
            df.at[real_idx, 'sentiment'] = r.get('sentiment', 'neutral')
            df.at[real_idx, 'key_quote'] = r.get('key_quote', '')

    time.sleep(1)

df.to_csv('data/classified_feedback.csv', index=False)

still_missing = df['theme'].isna().sum()
print(f"\n✅ Done! {still_missing} rows still unclassified (if any, they likely failed twice — fine to leave as-is)")
print(f"\nUpdated theme breakdown:")
print(df['theme'].value_counts())
print(f"\nTotal discovery-related: {df['is_discovery_related'].sum()} / {len(df)}")