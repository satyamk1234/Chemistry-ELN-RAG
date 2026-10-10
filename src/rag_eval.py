"""Evaluate whether the expected literature source is retrieved in the top-k results."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_query import retrieve

APP_DIR = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Run retrieval-only RAG evaluation.")
    parser.add_argument("--dataset", type=Path, default=APP_DIR.parent / "data" / "rag_eval.json")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    cases = json.loads(args.dataset.read_text(encoding="utf-8"))
    hits = 0
    for index, case in enumerate(cases, start=1):
        sources = [metadata["doi"] for _text, metadata, _identifier in retrieve(case["question"], args.top_k)]
        hit = case["expected_doi"] in sources
        hits += hit
        print(f"{'PASS' if hit else 'FAIL'} {index:02d}: expected {case['expected_doi']} | retrieved {sources}")
    print(f"\nRecall@{args.top_k}: {hits}/{len(cases)} ({hits / len(cases):.0%})")


if __name__ == "__main__":
    main()
