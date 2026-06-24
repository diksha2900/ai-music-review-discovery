"""
Classifies unified feedback using Groq (Llama 3.3 70B).
Tags each review with: is_discovery_related, theme, sentiment, and a supporting quote.
RESUMABLE: skips rows already classified in a previous run.
Saves results to data/classified_feedback.csv
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

BATCH_SIZE = 10
OUTPUT_PATH = 'data/classified_feedback.csv'

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

Theme definitions:
- recommendation_quality: complaints or praise about whether recommendations are good/bad/accurate
- repetition_fatigue: frustration about hearing the same songs/artists repeatedly
- discovery_effort: comments about how easy or hard it is to find new music
- trust_algorithm_distrust: skepticism or distrust toward the recommendation algorithm
- social_identity: comments about playlists/taste as self-expression or social signaling
- context_mismatch: recommendations not fitting the listening context (mood, activity, time)
- not_discovery_related: anything NOT about discovery/recommendations (ads, bugs, pricing, UI, etc.)

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
            max_tokens=2000
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception as e:
        print(f"  Batch error: {e}")
        return None  # None = stop entirely (likely quota wall); [] would mean "tried but failed"

print("Loading unified feedback...")
source_df = pd.read_csv('data/unified_feedback.csv')
source_df['text'] = source_df['text'].fillna('').astype(str)
source_df = source_df[source_df['text'].str.strip() != '']
source_df = source_df.reset_index(drop=True)

# Resume logic: if a classified file already exists, load it and only
# work on rows that don't have a theme yet.
if os.path.exists(OUTPUT_PATH):
    print("Found existing classified file — resuming...")
    df = pd.read_csv(OUTPUT_PATH)
    # Make sure it has the same number of rows as the source (in case source grew)
    if len(df) != len(source_df):
        print("  Source data size changed — merging carefully by text match...")
        df = source_df.merge(
            df[['text', 'is_discovery_related', 'theme', 'sentiment', 'key_quote']],
            on='text', how='left'
        )
else:
    df = source_df.copy()
    for col in ['is_discovery_related', 'theme', 'sentiment', 'key_quote']:
        df[col] = None

remaining_mask = df['theme'].isna()
remaining_indices = df[remaining_mask].index.tolist()

print(f"Total records: {len(df)}")
print(f"Already classified: {len(df) - len(remaining_indices)}")
print(f"Remaining to classify: {len(remaining_indices)}\n")

if len(remaining_indices) == 0:
    print("✅ Nothing left to classify — all done already!")
else:
    stopped_early = False

    for start in tqdm(range(0, len(remaining_indices), BATCH_SIZE)):
        batch_indices = remaining_indices[start:start + BATCH_SIZE]
        batch_texts = df.loc[batch_indices, 'text'].tolist()

        results = classify_batch(batch_texts)

        if results is None:
            print("\n⚠️  Stopping due to API error (likely daily quota reached).")
            print("Progress so far has been saved. Re-run this script later to continue.")
            stopped_early = True
            break

        for r in results:
            idx_in_batch = r.get('index', 0) - 1
            if 0 <= idx_in_batch < len(batch_indices):
                real_idx = batch_indices[idx_in_batch]
                df.at[real_idx, 'is_discovery_related'] = r.get('is_discovery_related', False)
                df.at[real_idx, 'theme'] = r.get('theme', 'not_discovery_related')
                df.at[real_idx, 'sentiment'] = r.get('sentiment', 'neutral')
                df.at[real_idx, 'key_quote'] = r.get('key_quote', '')

        # Save progress after every batch, so we never lose work
        df.to_csv(OUTPUT_PATH, index=False)
        time.sleep(1)

    if not stopped_early:
        print("\n✅ All records classified!")

still_missing = df['theme'].isna().sum()
print(f"\nFinal state: {len(df) - still_missing} classified, {still_missing} remaining")
print(f"\nDiscovery-related: {df['is_discovery_related'].sum()} / {len(df)}")
print(f"\nTheme breakdown:")
print(df['theme'].value_counts())