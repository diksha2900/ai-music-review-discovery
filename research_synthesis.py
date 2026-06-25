"""
Shared research synthesis: theme analysis + 6 core research question answers.
Used by synthesize_insights.py, run_workflow.py, and the Streamlit app.
"""

import json
import time

from groq import Groq
from dotenv import load_dotenv
import os

from config import get_groq_api_key

load_dotenv()
client = Groq(api_key=get_groq_api_key())

THEME_LABELS = {
    "recommendation_quality": "Recommendation Quality",
    "repetition_fatigue": "Repetition Fatigue",
    "discovery_effort": "Discovery Effort",
    "trust_algorithm_distrust": "Algorithm Trust/Distrust",
    "social_identity": "Social/Identity Signaling",
    "context_mismatch": "Context Mismatch",
}
VALID_THEMES = set(THEME_LABELS) | {"not_discovery_related"}

RESEARCH_QUESTIONS = [
    {
        "id": "q1",
        "question": "Why do users struggle to discover new music?",
        "themes": ["discovery_effort", "recommendation_quality", "context_mismatch"],
        "segment_focus": False,
    },
    {
        "id": "q2",
        "question": "What are the most common frustrations with recommendations?",
        "themes": ["recommendation_quality", "repetition_fatigue", "trust_algorithm_distrust"],
        "segment_focus": False,
    },
    {
        "id": "q3",
        "question": "What listening behaviors are users trying to achieve?",
        "themes": ["social_identity", "discovery_effort", "context_mismatch"],
        "segment_focus": False,
    },
    {
        "id": "q4",
        "question": "What causes users to repeatedly listen to the same content?",
        "themes": ["repetition_fatigue", "recommendation_quality", "discovery_effort"],
        "segment_focus": False,
    },
    {
        "id": "q5",
        "question": "Which user segments experience different discovery challenges?",
        "themes": None,  # all discovery-related
        "segment_focus": True,
    },
    {
        "id": "q6",
        "question": "What unmet needs emerge consistently across reviews?",
        "themes": None,
        "segment_focus": False,
    },
]


def _groq_call(prompt, max_tokens=500, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"    Rate limited, retrying in 60s ({attempt + 1}/{max_retries})...")
                time.sleep(60)
            else:
                return f"[Synthesis unavailable: {e}]"
    return "[Synthesis failed]"


def synthesize_theme_structured(theme_label, quotes):
    quotes_text = "\n".join([f'- "{q}"' for q in quotes[:25] if q and str(q) != "nan"])
    prompt = f"""You are a product research analyst. Below are real user feedback quotes tagged under "{theme_label}".

Quotes:
{quotes_text}

Return ONLY a JSON object:
{{
  "root_cause": "<1-2 sentence root cause>",
  "user_behavior": "<1-2 sentence user behavior pattern>",
  "representative_quote": "<single best quote, max 20 words, verbatim>"
}}"""
    try:
        content = _groq_call(prompt, max_tokens=300)
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception as e:
        return {"root_cause": str(e), "user_behavior": "", "representative_quote": ""}


def synthesize_theme_prose(theme_label, quotes, sources):
    quotes_text = "\n".join([f'- "{q}"' for q in quotes[:25] if q and str(q) != "nan"])
    source_summary = sources.value_counts().to_dict() if hasattr(sources, "value_counts") else {}
    prompt = f"""You are a product research analyst. Quotes tagged "{theme_label}" from sources: {source_summary}

Quotes:
{quotes_text}

Write 4-6 sentences covering root cause, user behavior, and one representative quote (max 20 words).
Plain prose only, no headers."""
    return _groq_call(prompt, max_tokens=400)


def _gather_quotes(discovery_df, theme_keys=None, max_quotes=30):
    if theme_keys:
        subset = discovery_df[discovery_df["theme"].isin(theme_keys)]
    else:
        subset = discovery_df
    quotes = []
    for _, row in subset.iterrows():
        q = row.get("key_quote") or row.get("text", "")
        if q and str(q) != "nan":
            quotes.append(str(q)[:300])
    if not quotes:
        for _, row in subset.head(max_quotes).iterrows():
            quotes.append(str(row.get("text", ""))[:300])
    return quotes[:max_quotes]


def synthesize_research_question(discovery_df, q_config):
    quotes = _gather_quotes(
        discovery_df,
        theme_keys=q_config.get("themes"),
        max_quotes=30,
    )
    if not quotes:
        return "Insufficient classified discovery-related data to answer this question."

    quotes_text = "\n".join([f'- "{q}"' for q in quotes])
    source_breakdown = discovery_df["source"].value_counts().to_dict()

    segment_instruction = ""
    if q_config.get("segment_focus"):
        segment_instruction = """
IMPORTANT: Explicitly identify distinct user segments hinted at in the quotes, such as:
- Power listeners vs casual listeners
- Playlist creators vs passive listeners
- Users listening for others (babies, parties, work) vs personal taste
- Premium vs free tier frustrations
- Genre-specific listeners (e.g. classical, EDM, regional music)
Name each segment and describe their unique discovery challenge."""

    prompt = f"""You are a Spotify product research analyst answering this research question:

"{q_config['question']}"

Source breakdown in dataset: {source_breakdown}

Supporting user quotes:
{quotes_text}
{segment_instruction}

Write a clear, grounded answer in 5-8 sentences. Reference patterns across sources.
Use ONLY evidence from the quotes. Do not invent data."""

    return _groq_call(prompt, max_tokens=500)


def synthesize_all_research_questions(discovery_df):
    results = []
    for q in RESEARCH_QUESTIONS:
        print(f"  Research Q: {q['question'][:60]}...")
        answer = synthesize_research_question(discovery_df, q)
        results.append({"id": q["id"], "question": q["question"], "answer": answer})
        time.sleep(2)
    return results


def build_theme_sections(discovery_df, structured=False):
    sections = []
    structured_results = []
    for theme_key, theme_label in THEME_LABELS.items():
        theme_data = discovery_df[discovery_df["theme"] == theme_key]
        if len(theme_data) == 0:
            continue
        print(f"  Theme: {theme_label} ({len(theme_data)} records)...")
        if structured:
            analysis = synthesize_theme_structured(theme_label, theme_data["key_quote"].tolist())
            structured_results.append({
                "theme": theme_label,
                "count": len(theme_data),
                **analysis,
            })
            sections.append(
                f"## {theme_label} ({len(theme_data)} records)\n\n"
                f"**Root cause:** {analysis.get('root_cause', '')}\n\n"
                f"**User behavior:** {analysis.get('user_behavior', '')}\n\n"
                f"**Representative quote:** \"{analysis.get('representative_quote', '')}\"\n"
            )
        else:
            analysis = synthesize_theme_prose(
                theme_label,
                theme_data["key_quote"].tolist(),
                theme_data["source"],
            )
            sections.append(f"## {theme_label} ({len(theme_data)} records)\n\n{analysis}\n")
        time.sleep(2)
    return sections, structured_results


def build_full_report(df, source_label, discovery_df, theme_sections, research_results, structured=False):
    rq_text = "\n".join(
        f"### {r['question']}\n\n{r['answer']}\n" for r in research_results
    )
    rq_list = "\n".join(f"{i + 1}. {q['question']}" for i, q in enumerate(RESEARCH_QUESTIONS))

    report = f"""# Spotify Discovery Research Insights

**Data source:** {source_label}
**Total records analyzed:** {len(df)}
**Discovery-related records:** {len(discovery_df)}

---

# Research Questions — Direct Answers

{rq_text}

---

# Findings by Theme

{chr(10).join(theme_sections)}

---

# Research Questions Reference

{rq_list}

---

# Theme Distribution

{discovery_df['theme'].value_counts().to_string() if len(discovery_df) > 0 else 'No discovery-related records'}
"""
    return report
