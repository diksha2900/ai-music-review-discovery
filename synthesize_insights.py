"""
Synthesizes classified feedback into answers for the 6 core research questions.
Reads data/classified_feedback.csv, groups by theme, and asks Groq to reason
about the underlying pattern behind each theme using real supporting quotes.
Saves results to data/research_insights.md
"""

import os
import time
import pandas as pd
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("Loading classified feedback...")
df = pd.read_csv('data/classified_feedback.csv')

# Only work with rows that were actually classified
df = df[df['theme'].notna()]
discovery_df = df[df['is_discovery_related'] == True]

print(f"Working with {len(discovery_df)} discovery-related records\n")

THEME_LABELS = {
    "recommendation_quality": "Recommendation Quality",
    "repetition_fatigue": "Repetition Fatigue",
    "discovery_effort": "Discovery Effort",
    "trust_algorithm_distrust": "Algorithm Trust/Distrust",
    "social_identity": "Social/Identity Signaling",
    "context_mismatch": "Context Mismatch"
}

RESEARCH_QUESTIONS = """
1. Why do users struggle to discover new music?
2. What are the most common frustrations with recommendations?
3. What listening behaviors are users trying to achieve?
4. What causes users to repeatedly listen to the same content?
5. Which user segments experience different discovery challenges?
6. What unmet needs emerge consistently across reviews?
"""

def synthesize_theme(theme_key, theme_label, quotes, sources, max_retries=3):
    quotes_text = "\n".join([f'- "{q}"' for q in quotes[:25] if q and str(q) != 'nan'])
    source_summary = sources.value_counts().to_dict()

    prompt = f"""You are a product research analyst. Below are real user feedback quotes, all tagged under the theme "{theme_label}", collected from Spotify app reviews and community discussions.

Source breakdown for this theme: {source_summary}

Quotes:
{quotes_text}

Based ONLY on these quotes, write a concise analysis (4-6 sentences) covering:
- The underlying root cause or job-to-be-done behind this pattern (not just a restatement of the complaints)
- Any distinct user behavior or segment hinted at in the quotes
- One representative quote (choose the single most illustrative one, max 20 words)

Be specific and grounded in the quotes. Do not generalize beyond what's actually said. Write in plain analytical prose, no headers or bullet points."""

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=400
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            wait_time = 90
            print(f"    Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
            time.sleep(wait_time)

    return f"[Synthesis failed after {max_retries} retries due to rate limits — re-run script later]"

print("Synthesizing insights per theme...\n")

report_sections = []

for theme_key, theme_label in THEME_LABELS.items():
    theme_data = discovery_df[discovery_df['theme'] == theme_key]
    if len(theme_data) == 0:
        continue

    print(f"  Analyzing: {theme_label} ({len(theme_data)} records)...")
    analysis = synthesize_theme(
        theme_key,
        theme_label,
        theme_data['key_quote'].tolist(),
        theme_data['source']
    )

    report_sections.append(f"## {theme_label} ({len(theme_data)} records)\n\n{analysis}\n")
    time.sleep(3)

# Build the final markdown report
report = f"""# Spotify Discovery Research Insights

**Generated from {len(df)} classified records ({len(discovery_df)} discovery-related) across Play Store, App Store, Reddit, Community Forum, and Social Media.**

## Research Questions Addressed
{RESEARCH_QUESTIONS}

---

# Findings by Theme

{chr(10).join(report_sections)}

---

# Overall Theme Distribution

{discovery_df['theme'].value_counts().to_string()}
"""

with open('data/research_insights.md', 'w', encoding='utf-8') as f:
    f.write(report)

print(f"\n✅ Done! Saved synthesis to data/research_insights.md")