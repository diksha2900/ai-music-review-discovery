#!/usr/bin/env python3
"""
End-to-end pipeline: merge all sources → classify → synthesize → rebuild RAG embeddings.

Usage:
  python run_full_analysis.py              # full pipeline
  python run_full_analysis.py --skip-classify   # merge + synthesize + embed only
"""

import argparse
import subprocess
import sys


def run_step(label, cmd):
    print(f"\n{'=' * 60}\n▶ {label}\n{'=' * 60}")
    result = subprocess.run(cmd, shell=False)
    if result.returncode != 0:
        print(f"⚠️  {label} exited with code {result.returncode} (continuing…)")
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run the full discovery analysis pipeline")
    parser.add_argument("--skip-classify", action="store_true", help="Skip Groq classification step")
    parser.add_argument("--skip-synthesize", action="store_true", help="Skip insight synthesis")
    args = parser.parse_args()

    python = sys.executable
    steps = [
        ("Merge all data sources", [python, "merge_all_sources.py"]),
    ]
    if not args.skip_classify:
        steps.append(("Classify reviews (Groq)", [python, "classify_reviews.py"]))
    if not args.skip_synthesize:
        steps.append(("Synthesize insights + research questions", [python, "synthesize_insights.py"]))
    steps.append(("Rebuild RAG embeddings", [python, "build_embeddings.py"]))

    for label, cmd in steps:
        run_step(label, cmd)

    print(f"\n{'=' * 60}")
    print("✅ Pipeline complete. Launch the app: streamlit run app.py")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
