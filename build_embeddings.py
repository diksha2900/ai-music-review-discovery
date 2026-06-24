"""
Generates embeddings for all classified, discovery-related reviews.
Saves them to data/embeddings.pkl for fast retrieval later.
"""

import pandas as pd
import pickle
import os
from sentence_transformers import SentenceTransformer

print("Loading classified feedback...")
df = pd.read_csv('data/classified_feedback.csv')

# Only embed rows that actually got classified (skip any still-pending ones)
df = df[df['theme'].notna()].reset_index(drop=True)

print(f"Building embeddings for {len(df)} classified records...")
print("(Downloading model on first run — this may take a minute)\n")

model = SentenceTransformer('all-MiniLM-L6-v2')  # small, fast, free, runs locally

# Embed the review text directly
texts = df['text'].fillna('').astype(str).tolist()
embeddings = model.encode(texts, show_progress_bar=True)

os.makedirs('data', exist_ok=True)
with open('data/embeddings.pkl', 'wb') as f:
    pickle.dump({
        'embeddings': embeddings,
        'df': df
    }, f)

print(f"\n✅ Done! Saved {len(df)} embeddings to data/embeddings.pkl")