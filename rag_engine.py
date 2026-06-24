"""
Core RAG logic: given a question, retrieves the most relevant reviews
and asks Groq to answer using only those reviews as context.
This file is imported by the Streamlit app — it doesn't run on its own.
"""

import os
import pickle
import numpy as np
from groq import Groq
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("Loading embeddings and model (this happens once when the app starts)...")
with open('data/embeddings.pkl', 'rb') as f:
    data = pickle.load(f)

EMBEDDINGS = data['embeddings']
REVIEWS_DF = data['df']
MODEL = SentenceTransformer('all-MiniLM-L6-v2')

print(f"Ready — {len(REVIEWS_DF)} reviews loaded for retrieval.")

def retrieve_relevant_reviews(question, top_k=15):
    """Finds the most semantically similar reviews to the question."""
    question_embedding = MODEL.encode([question])[0]

    # Cosine similarity between the question and every review
    norms = np.linalg.norm(EMBEDDINGS, axis=1) * np.linalg.norm(question_embedding)
    similarities = np.dot(EMBEDDINGS, question_embedding) / (norms + 1e-10)

    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = REVIEWS_DF.iloc[top_indices].copy()
    results['similarity'] = similarities[top_indices]
    return results

def answer_question(question):
    """Full RAG pipeline: retrieve relevant reviews, then generate a grounded answer."""
    relevant = retrieve_relevant_reviews(question, top_k=15)

    context_lines = []
    for _, row in relevant.iterrows():
        snippet = str(row['text'])[:300]
        context_lines.append(f"- [{row['source']}, theme: {row['theme']}] \"{snippet}\"")

    context = "\n".join(context_lines)

    prompt = f"""You are a product research assistant analyzing real user feedback about Spotify's music discovery features.

A researcher is asking: "{question}"

Here are the most relevant real user feedback excerpts retrieved for this question:

{context}

Using ONLY the excerpts above, write a clear, well-organized answer (5-8 sentences) to the researcher's question. Reference specific patterns you see. If the excerpts don't really address the question, say so honestly rather than making things up. Do not invent quotes or facts not present in the excerpts above."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=600
    )

    answer = response.choices[0].message.content.strip()
    return answer, relevant