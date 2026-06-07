"""Chunking for The Unofficial Guide.

Stage 2 of the pipeline: split each cleaned document into retrieval-sized
chunks. Strategy (see planning.md): split on Markdown headings first so the
roundup files' ~10 mini-stories stay separated, then recursively split any
oversized section by paragraph -> sentence -> word, keeping each chunk under
the embedding model's ~256-token (~1000 char) window. A ~150-char overlap
preserves context across boundaries, and each section's heading is prepended
to its sub-chunks so a mid-section chunk still carries its story's title.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ingest import Document, load_documents

TARGET = 800     # chars per chunk (under MiniLM's ~1000-char truncation limit)
OVERLAP = 150    # chars carried between consecutive chunks within a section

# Coarsest-first separators for recursive splitting: prefer paragraph breaks,
# fall back to lines, then sentences, then words, then a hard character cut.
_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass
class Chunk:
    """A retrieval unit with the metadata needed for attribution."""

    text: str
    doc_title: str
    source: str       # source URL, carried from the document's frontmatter
    filename: str
    position: int     # 0-based index of this chunk within its document
    heading: str      # section heading this chunk came from ("" if none)


def _split_into_sections(text: str) -> list[tuple[str, str]]:
    """Break a document into (heading, body) sections on Markdown headings.

    This is the step that keeps each roundup mini-story self-contained: every
    `#`-`######` heading starts a new section.
    """
    sections: list[tuple[str, str]] = []
    heading = ""
    buf: list[str] = []
    for line in text.split("\n"):
        if re.match(r"^#{1,6}\s+", line):
            # Hit a new heading -> flush the section we were building.
            if buf or heading:
                sections.append((heading, "\n".join(buf).strip()))
            heading = line.strip()
            buf = []
        else:
            buf.append(line)
    if buf or heading:  # flush the final section
        sections.append((heading, "\n".join(buf).strip()))
    return sections


def _recursive_split(text: str, target: int, seps: list[str]) -> list[str]:
    """Split text to <= target chars, preferring coarse separators first."""
    if len(text) <= target:  # already small enough — done
        return [text]
    sep = seps[0]             # current separator to try (coarsest remaining)
    if sep == "":  # last resort: nothing left to split on, cut by char count
        return [text[i:i + target] for i in range(0, len(text), target)]

    # Greedily pack pieces back together up to `target`; recurse on any single
    # piece that is still too big using the next-finer separator.
    chunks: list[str] = []
    cur = ""
    for part in text.split(sep):
        piece = part if not cur else cur + sep + part
        if len(piece) <= target:
            cur = piece
        else:
            if cur:
                chunks.append(cur)
            if len(part) > target:
                chunks.extend(_recursive_split(part, target, seps[1:]))
                cur = ""
            else:
                cur = part
    if cur:
        chunks.append(cur)
    return chunks


def _add_overlap(chunks: list[str], overlap: int) -> list[str]:
    """Prepend the tail of each chunk to the next, for context continuity."""
    if overlap <= 0 or len(chunks) <= 1:
        return chunks
    out = [chunks[0]]
    for prev, cur in zip(chunks, chunks[1:]):
        tail = prev[-overlap:]
        if " " in tail:                       # snap to the next whole word
            tail = tail[tail.index(" ") + 1:]  # so overlap doesn't start mid-word
        out.append((tail + " " + cur).strip())
    return out


def chunk_document(doc: Document, target: int = TARGET, overlap: int = OVERLAP) -> list[Chunk]:
    """Chunk a single document into heading-aware, overlapped pieces."""
    chunks: list[Chunk] = []
    for heading, body in _split_into_sections(doc.text):
        if not body:  # skip heading-only sections with no content
            continue
        # We prepend the heading to every sub-chunk, so reserve room for it
        # — but never let a long heading shrink the body budget below 200 chars.
        prefix = f"{heading}\n\n" if heading else ""
        room = max(target - len(prefix), 200)
        pieces = _add_overlap(_recursive_split(body, room, _SEPARATORS), overlap)
        for piece in pieces:
            if not piece.strip():  # guard against empty chunks
                continue
            chunks.append(
                Chunk(
                    text=prefix + piece,
                    doc_title=doc.title,
                    source=doc.source,
                    filename=doc.filename,
                    position=len(chunks),
                    heading=heading,
                )
            )
    return chunks


def chunk_documents(docs: list[Document] | None = None) -> list[Chunk]:
    """Load (if needed) and chunk every document into one flat list."""
    if docs is None:
        docs = load_documents()
    all_chunks: list[Chunk] = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    return all_chunks


if __name__ == "__main__":
    # Inspection harness: counts, size distribution, and 5 roundup chunks to
    # confirm no story-bleed (the milestone's chunk-inspection step).
    chunks = chunk_documents()
    lengths = [len(c.text) for c in chunks]
    print(f"Total chunks: {len(chunks)}")
    print(f"Chunk size  : min {min(lengths)}, max {max(lengths)}, "
          f"avg {sum(lengths) // len(lengths)} chars\n")

    # How many chunks each document produced.
    from collections import Counter
    for title, n in Counter(c.doc_title for c in chunks).items():
        print(f"  {n:3d} chunks | {title[:60]}")

    # Eyeball 5 chunks from a roundup file — the story-bleed stress test.
    print("\n" + "=" * 70)
    print("5 SAMPLE CHUNKS FROM A ROUNDUP (checking for story-bleed)")
    print("=" * 70)
    roundup = [c for c in chunks if "Roundup A" in c.filename]
    for c in roundup[:5]:
        print(f"\n--- chunk #{c.position} | {len(c.text)} chars | "
              f"source: {c.source[:45]} ---")
        print(c.text)
