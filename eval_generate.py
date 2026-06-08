"""End-to-end generation evaluation harness for The Unofficial Guide.

Runs the 5 planning.md questions plus one out-of-scope question through the
full pipeline (retrieve -> ground -> generate) and prints each grounded answer
with its sources. Covers item 4 (grounded generation works end-to-end) and
item 5 (out-of-scope -> the system declines). Reused for the Milestone 6 report.

Run:  python eval_generate.py
"""

from __future__ import annotations

from generate import answer

# The 5 evaluation questions, verbatim from planning.md.
EVAL_QUESTIONS = [
    "What business models or revenue streams did these founders use to make money?",
    "What technical backgrounds did these founders have — did building a profitable "
    "product require strong coding skills?",
    "How long did founders typically take to reach sustainable income?",
    "What were the biggest failure points or risks across these case studies?",
    "How did these founders find their first customers?",
]

# Item 5: clearly outside the corpus — the system should decline, not answer
# from the LLM's general training knowledge.
OUT_OF_SCOPE = "What is the best programming language to learn in 2026?"


def show(question: str) -> None:
    result = answer(question)
    print("=" * 80)
    print(f"Q: {question}")
    print("-" * 80)
    print(result.text)
    print("\nSources:")
    for s in result.sources:
        print(f"  • {s}")
    print()


def main() -> None:
    for q in EVAL_QUESTIONS:
        show(q)
    print("#" * 80)
    print("# OUT-OF-SCOPE CHECK (expect: \"I don't have enough information on that.\")")
    print("#" * 80)
    show(OUT_OF_SCOPE)


if __name__ == "__main__":
    main()
