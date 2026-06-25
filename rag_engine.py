"""
Core RAG logic: given a question, retrieves the most relevant reviews
and asks Groq to answer using only those reviews as context.
"""

import os
import pickle

import numpy as np
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

from config import get_groq_api_key

load_dotenv()

client = Groq(api_key=get_groq_api_key())
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

_EMBEDDINGS, _REVIEWS_DF = None, None


def _load_embeddings():
    global _EMBEDDINGS, _REVIEWS_DF
    if _EMBEDDINGS is not None:
        return
    with open("data/embeddings.pkl", "rb") as f:
        data = pickle.load(f)
    _EMBEDDINGS = data["embeddings"]
    _REVIEWS_DF = data["df"]


def get_corpus_stats():
    _load_embeddings()
    return {
        "total": len(_REVIEWS_DF),
        "by_source": _REVIEWS_DF["source"].value_counts().to_dict(),
        "classified": int(_REVIEWS_DF["theme"].notna().sum()),
    }


def retrieve_relevant_reviews(question, top_k=15, source_filter=None):
    _load_embeddings()
    df = _REVIEWS_DF
    embeddings = _EMBEDDINGS

    if source_filter:
        mask = df["source"] == source_filter
        if mask.any():
            df = df[mask]
            embeddings = embeddings[mask.values]

    question_embedding = MODEL.encode([question])[0]
    norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(question_embedding)
    similarities = np.dot(embeddings, question_embedding) / (norms + 1e-10)

    top_indices = np.argsort(similarities)[::-1][:top_k]
    results = df.iloc[top_indices].copy()
    results["similarity"] = similarities[top_indices]
    return results


def _format_source_label(row):
    source = str(row.get("source", "unknown")).replace("_", " ").title()
    theme = row.get("theme")
    if theme and str(theme) not in ("nan", ""):
        return f"{source}, theme: {theme}"
    return source


def answer_question(question, source_filter=None):
    relevant = retrieve_relevant_reviews(question, top_k=15, source_filter=source_filter)

    context_lines = []
    for _, row in relevant.iterrows():
        snippet = str(row["text"])[:300]
        context_lines.append(f'- [{_format_source_label(row)}] "{snippet}"')

    context = "\n".join(context_lines)

    prompt = f"""You are a product research assistant analyzing real user feedback about Spotify's music discovery features.

A researcher is asking: "{question}"

Here are the most relevant real user feedback excerpts retrieved for this question:

{context}

Using ONLY the excerpts above, write a clear, well-organized answer (5-8 sentences) to the researcher's question. Reference specific patterns you see across sources (Play Store, App Store, Reddit, Twitter, community forum). If the excerpts don't really address the question, say so honestly rather than making things up. Do not invent quotes or facts not present in the excerpts above."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=600,
    )

    return response.choices[0].message.content.strip(), relevant
