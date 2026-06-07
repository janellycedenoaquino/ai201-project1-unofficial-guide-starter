"""Retrieval for The Unofficial Guide.

Stage 4 of the pipeline: given a user query, embed it with the *same* model
used for indexing, then return the top-k most similar chunks from ChromaDB
along with their source metadata and distance scores. Generation (Milestone 5)
builds on top of this.
"""

from __future__ import annotations

from dataclasses import dataclass

import chromadb

from embed import COLLECTION, DB_DIR, get_model

TOP_K = 5  # planning.md: enough to synthesize across cases without flooding


@dataclass
class Result:
    """One retrieved chunk plus everything needed to cite and rank it."""

    text: str
    source: str        # source URL — for attribution in the answer
    doc_title: str
    filename: str
    position: int
    heading: str
    distance: float    # cosine distance; lower = more similar (≈0 best)


# Cached so we open the on-disk collection only once per process.
_collection: chromadb.Collection | None = None


def _get_collection() -> chromadb.Collection:
    """Open the persistent collection built by embed.py."""
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(DB_DIR))
        _collection = client.get_collection(COLLECTION)
    return _collection


def retrieve(query: str, k: int = TOP_K) -> list[Result]:
    """Return the k chunks most semantically similar to `query`."""
    # Embed the query with the same model used to build the index.
    query_embedding = get_model().encode([query])[0].tolist()

    res = _get_collection().query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # Chroma nests results one level deep (one list per query); we sent one.
    results: list[Result] = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        results.append(
            Result(
                text=doc,
                source=meta.get("source", ""),
                doc_title=meta.get("doc_title", ""),
                filename=meta.get("filename", ""),
                position=meta.get("position", -1),
                heading=meta.get("heading", ""),
                distance=dist,
            )
        )
    return results


if __name__ == "__main__":
    # Smoke test that the function runs end-to-end (the full eval is item 5).
    query = "What business models did these founders use to make money?"
    print(f"Query: {query}\n")
    for r in retrieve(query):
        print(f"[dist {r.distance:.3f}] {r.doc_title[:45]} — {r.heading[:50]}")
        print(f"   {r.text[:140].replace(chr(10), ' ')}…\n")
