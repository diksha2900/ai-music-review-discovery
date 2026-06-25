"""
Synthesizes classified feedback into theme insights + answers to the 6 research questions.
Reads data/classified_feedback.csv (merged with unified for full corpus labels).
Saves results to data/research_insights.md and data/research_questions.json
"""

import json
import os

import pandas as pd
from dotenv import load_dotenv

from research_synthesis import (
    RESEARCH_QUESTIONS,
    VALID_THEMES,
    THEME_LABELS,
    build_full_report,
    build_theme_sections,
    synthesize_all_research_questions,
)

load_dotenv()

OUTPUT_MD = "data/research_insights.md"
OUTPUT_JSON = "data/research_questions.json"


def load_classified_discovery_data():
    """Load classified rows, falling back to unified + classified merge."""
    if os.path.exists("data/classified_feedback.csv"):
        df = pd.read_csv("data/classified_feedback.csv")
    elif os.path.exists("data/unified_feedback.csv"):
        df = pd.read_csv("data/unified_feedback.csv")
    else:
        raise FileNotFoundError("No classified_feedback.csv or unified_feedback.csv found.")

    df = df[df["theme"].isin(VALID_THEMES)].copy()
    return df, df[df["is_discovery_related"] == True]


def main():
    print("Loading classified feedback...")
    df, discovery_df = load_classified_discovery_data()
    print(f"  {len(df)} classified records, {len(discovery_df)} discovery-related\n")

    if len(discovery_df) == 0:
        print("⚠️  No discovery-related classified records. Run classify_reviews.py first.")
        return

    source_label = "Full merged corpus (Play Store, App Store, Reddit, Twitter, Forum, Social)"

    print("Synthesizing themes...")
    theme_sections, _ = build_theme_sections(discovery_df, structured=False)

    print("\nSynthesizing research question answers...")
    research_results = synthesize_all_research_questions(discovery_df)

    report = build_full_report(
        df, source_label, discovery_df, theme_sections, research_results, structured=False,
    )

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(report)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(research_results, f, indent=2)

    print(f"\n✅ Saved insights to {OUTPUT_MD}")
    print(f"✅ Saved research Q&A to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
