"""
Generates embeddings for the full unified feedback dataset (all sources).
Merges classification labels where available. Saves to data/embeddings.pkl.
"""

import os
import pickle

import pandas as pd
from sentence_transformers import SentenceTransformer

UNIFIED_PATH = "data/unified_feedback.csv"
CLASSIFIED_PATH = "data/classified_feedback.csv"
OUTPUT_PATH = "data/embeddings.pkl"

VALID_THEMES = {
    "recommendation_quality", "repetition_fatigue", "discovery_effort",
    "trust_algorithm_distrust", "social_identity", "context_mismatch",
    "not_discovery_related",
}
CLASSIFY_COLS = ["is_discovery_related", "theme", "sentiment", "key_quote"]


def load_rag_corpus() -> pd.DataFrame:
    print("Loading unified feedback...")
    df = pd.read_csv(UNIFIED_PATH)
    df["text"] = df["text"].fillna("").astype(str)
    df = df[df["text"].str.strip() != ""].copy()

    base_cols = [c for c in df.columns if c not in CLASSIFY_COLS]
    df = df[base_cols]

    if os.path.exists(CLASSIFIED_PATH):
        classified = pd.read_csv(CLASSIFIED_PATH).drop_duplicates(subset=["id"], keep="last")
        for col in CLASSIFY_COLS:
            if col not in classified.columns:
                classified[col] = None
        df = df.merge(classified[["id"] + CLASSIFY_COLS], on="id", how="left")

    for col in CLASSIFY_COLS:
        if col not in df.columns:
            df[col] = None

    invalid = df["theme"].notna() & ~df["theme"].isin(VALID_THEMES)
    df.loc[invalid, CLASSIFY_COLS] = None

    return df.reset_index(drop=True)


def main():
    df = load_rag_corpus()
    print(f"Building embeddings for {len(df)} records across all sources...")
    print(df["source"].value_counts().to_string())
    print("\n(Downloading model on first run — this may take a minute)\n")

    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = df["text"].tolist()
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        pickle.dump({"embeddings": embeddings, "df": df}, f)

    classified_count = df["theme"].isin(VALID_THEMES).sum()
    print(f"\n✅ Done! Saved {len(df)} embeddings to {OUTPUT_PATH}")
    print(f"   ({classified_count} with LLM classification, {len(df) - classified_count} unclassified)")


if __name__ == "__main__":
    main()
