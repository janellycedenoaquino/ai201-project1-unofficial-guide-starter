"""Embedding + vector store for The Unofficial Guide.

Stage 3 of the pipeline (see planning.md: Retrieval Approach). Loads the
embedding model, embeds every chunk, and (re)builds a persistent ChromaDB
collection with the metadata needed for attribution downstream.
"""

from __future__ import annotations

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from chunk import chunk_documents

# Local, 384-dim model with a ~256-token window (the constraint behind our
# ~800-char chunks). No API key, no rate limits — see planning.md.
MODEL_NAME = "all-MiniLM-L6-v2"

DB_DIR = Path(__file__).parent / "chroma_db"   # persisted store (gitignored)
COLLECTION = "unofficial_guide"

# Cached so the (heavy) model is loaded only once per process.
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Load (and cache) the embedding model.

    The first call downloads ~80 MB from Hugging Face; afterwards it loads
    from the local cache. Cached in a module global so repeated calls reuse
    the same instance.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def build_collection() -> chromadb.Collection:
    """Embed all chunks and (re)build the ChromaDB collection from scratch.

    Idempotent: any existing collection is deleted first, so re-running yields
    exactly the corpus once instead of appending duplicate chunks (DECISIONS
    #10). Distance is cosine to match all-MiniLM and the milestone's score
    thresholds (DECISIONS #11).
    """
    chunks = chunk_documents()
    model = get_model()
    # One batched encode call over all chunk texts — far faster than per-chunk.
    embeddings = model.encode([c.text for c in chunks], show_progress_bar=True)

    # PersistentClient writes the index to disk so query-time code can reuse it.
    client = chromadb.PersistentClient(path=str(DB_DIR))
    # Idempotent rebuild: drop the old collection if it exists, then recreate.
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass  # nothing to delete on a first run
    collection = client.create_collection(
        COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    # Store vector + text + attribution metadata. IDs are stable
    # (filename + position) so the build is reproducible.
    collection.add(
        ids=[f"{c.filename}::{c.position}" for c in chunks],
        embeddings=[e.tolist() for e in embeddings],
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "source": c.source,
                "doc_title": c.doc_title,
                "filename": c.filename,
                "position": c.position,
                "heading": c.heading,
            }
            for c in chunks
        ],
    )
    return collection


if __name__ == "__main__":
    # item 3 verification: build, confirm the count, and inspect one record.
    collection = build_collection()
    print(f"\nCollection '{COLLECTION}' built: {collection.count()} chunks "
          f"(expected 236)")

    sample = collection.get(limit=1, include=["metadatas", "documents"])
    print("\nSample stored record:")
    print("  metadata:", sample["metadatas"][0])
    print("  text    :", sample["documents"][0][:120].replace("\n", " "), "…")
