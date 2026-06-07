"""Retrieval evaluation harness for The Unofficial Guide.

Runs the 5 planning.md evaluation questions through the retriever and prints
the top-k chunks with their cosine distances and sources. Use it to sanity-
check retrieval quality (Milestone 4, item 5) before wiring up generation.

Run:  python eval_retrieval.py
"""

from __future__ import annotations

from retrieve import retrieve

# The 5 evaluation questions, verbatim from planning.md.
QUESTIONS = [
    "What business models or revenue streams did these founders use to make money?",
    "What technical backgrounds did these founders have — did building a profitable "
    "product require strong coding skills?",
    "How long did founders typically take to reach sustainable income?",
    "What were the biggest failure points or risks across these case studies?",
    "How did these founders find their first customers?",
]


def main() -> None:
    for i, question in enumerate(QUESTIONS, 1):
        results = retrieve(question)
        avg = sum(r.distance for r in results) / len(results)
        print("=" * 80)
        print(f"Q{i}: {question}")
        print(f"    top-5 avg distance: {avg:.3f}  (lower = more relevant)")
        print("-" * 80)
        for r in results:
            print(f"  [dist {r.distance:.3f}] {r.doc_title[:38]:38s} | {r.heading[:34]}")
            print(f"       {r.text[:110].replace(chr(10), ' ')}…")
        print()


if __name__ == "__main__":
    main()
