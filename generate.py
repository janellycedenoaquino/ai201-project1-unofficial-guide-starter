"""Generation for The Unofficial Guide.

Stage 5 of the pipeline (item 2): connect the retrieved chunks to the LLM and
produce a *grounded* answer — the model must answer only from the retrieved
context, not its own training knowledge. Structured source attribution as a
returned field comes next (item 3).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from groq import Groq

from retrieve import TOP_K, retrieve

load_dotenv()  # pull GROQ_API_KEY from .env

MODEL = "llama-3.3-70b-versatile"  # Groq free tier — see planning.md

# Exact line the model must use when the context can't answer the question.
REFUSAL = "I don't have enough information on that."

# The grounding contract: answer only from context, and refuse cleanly when the
# context falls short (rather than inventing a plausible-sounding answer).
SYSTEM_PROMPT = (
    "You are a research assistant answering questions about how founders built "
    "profitable products and income streams. Answer the question using ONLY the "
    "information in the provided context. Do not use any outside knowledge. If the "
    f"context does not contain enough information to answer, reply exactly: \"{REFUSAL}\" "
    "When you do answer, ground each claim in the context and name the founders or "
    "sources you drew from."
)

@dataclass
class Answer:
    """A grounded answer plus the sources it was drawn from."""

    text: str
    sources: list[str]   # "doc title — url", deduplicated, in retrieval order


_client: Groq | None = None


def _get_client() -> Groq:
    """Init (and cache) the Groq client from the API key in .env."""
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


def _format_context(results) -> str:
    """Lay out retrieved chunks for the prompt.

    Each block is labelled with its doc title + source URL (DECISIONS #9): some
    chunks never name their own subject, so the label is what lets the model
    attribute a fact to the right founder.
    """
    return "\n\n---\n\n".join(
        f"[{r.doc_title} — {r.source}]\n{r.text}" for r in results
    )


def _collect_sources(results) -> list[str]:
    """Deduplicate the retrieved chunks' sources, keeping retrieval order.

    Built from chunk metadata (not the LLM's text), so the citations are
    guaranteed to be the documents we actually fed the model.
    """
    seen: set[tuple[str, str]] = set()
    sources: list[str] = []
    for r in results:
        key = (r.doc_title, r.source)
        if key not in seen:
            seen.add(key)
            sources.append(f"{r.doc_title} — {r.source}")
    return sources


def answer(query: str, k: int = TOP_K) -> Answer:
    """Retrieve context for `query` and return a grounded answer + its sources."""
    results = retrieve(query, k)
    context = _format_context(results)

    response = _get_client().chat.completions.create(
        model=MODEL,
        temperature=0.2,  # low: we want faithful, not creative
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n\n{context}\n\nQuestion: {query}"},
        ],
    )
    text = response.choices[0].message.content
    # Don't cite sources on a refusal — they weren't used to answer anything.
    sources = [] if REFUSAL.lower() in text.lower() else _collect_sources(results)
    return Answer(text=text, sources=sources)


if __name__ == "__main__":
    # Single-query smoke test (the fuller grounding tests are items 4 & 5).
    q = "What business models did these founders use to make money?"
    result = answer(q)
    print(f"Q: {q}\n")
    print(result.text)
    print("\nSources:")
    for s in result.sources:
        print(f"  • {s}")
