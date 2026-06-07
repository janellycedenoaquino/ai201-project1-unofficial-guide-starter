"""Document ingestion for The Unofficial Guide.

Stage 1 of the pipeline: load the Markdown case-study files, parse their YAML
frontmatter into metadata (title + source URL for attribution), and clean the
body down to substantive prose before chunking.

See planning.md (Document Ingestion / Chunking Strategy) for the rationale.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Where the 12 source case-study files live.
DOCS_DIR = Path(__file__).parent / "documents"


@dataclass
class Document:
    """A loaded, cleaned source document."""

    filename: str          # file on disk (fallback identifier)
    title: str             # human-readable title from frontmatter
    source: str            # source URL — used for attribution downstream
    text: str              # cleaned body, ready for chunking


# --- frontmatter -----------------------------------------------------------

# Matches the YAML block fenced by `---` at the very top of each file.
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    """Split a raw file into (metadata, body).

    Only the fields we actually use (title, source) are pulled out; the YAML
    here is simple key: "value" lines, so we parse it directly rather than add
    a YAML dependency. The frontmatter block is stripped from the returned body
    so it never ends up in a chunk.
    """
    # No frontmatter found: treat the whole file as body, no metadata.
    match = _FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw

    # Turn each `key: value` line into a dict entry, stripping wrapping quotes.
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"').strip()

    # Body is everything after the closing `---`.
    body = raw[match.end():]
    return meta, body


# --- cleaning --------------------------------------------------------------

_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_IFRAME_RE = re.compile(r"<iframe[^>]*>.*?</iframe>", re.DOTALL | re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")          # ![alt](url)  -> drop
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")          # [text](url)  -> text
_BLOCKQUOTE_RE = re.compile(r"^\s*>+\s?", re.MULTILINE)  # leading "> "
_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!\"~>])")  # \* \" \[  -> * " [
_FOOTER_RE = re.compile(r"^View more on .*»\s*$", re.MULTILINE)  # roundup footer
# eBiz Facts repeats a long newsletter/CTA footer block on its posts. It's
# full-sentence prose (line filters miss it), and on the roundup pages it
# recurs once per story. So we remove each block non-greedily, from its opening
# marker up to the next story heading / "View more" link / end of file — which
# preserves the real stories sitting between the repeated footers.
_EBIZ_FOOTER_RE = re.compile(
    r"First time seeing our Online Money Maker profiles"
    r".*?(?=\n#{1,6}\s|\n\[View more|\Z)",
    re.DOTALL,
)
_HR_RE = re.compile(r"^-{3,}\s*$", re.MULTILINE)         # standalone --- rules
# Site UI chrome that survives as its own line (optionally under a heading):
# like/upvote buttons, lone like-counts, and Goodreads' footer nav.
_UI_NOISE_RE = re.compile(
    r"^(?:#{1,6}\s+)?(?:Like|Upvote|Reply|Share|Save|Follow|[0-9]{1,3}|"
    r"Discover & read more|Sign up to get better recommendations[^\n]*)\s*$",
    re.MULTILINE,
)
_LEAD_WS_RE = re.compile(r"^[ \t]+", re.MULTILINE)       # leading ws (image gaps)
_MULTI_BLANK_RE = re.compile(r"\n{3,}")


def clean_text(body: str) -> str:
    """Strip non-content noise, keeping the substantive prose intact."""
    # Remove the eBiz Facts newsletter/CTA footer block first, while its
    # full-sentence markers are still intact.
    text = _EBIZ_FOOTER_RE.sub("", body)
    # Order matters: remove <script>/<style> blocks (with their contents)
    # before the generic tag-stripper, or we'd leave their inner text behind.
    text = _SCRIPT_STYLE_RE.sub("", text)
    text = _IFRAME_RE.sub("", text)
    text = _IMAGE_RE.sub("", text)          # drop image embeds (incl. emoji-images)
    text = _LINK_RE.sub(r"\1", text)        # keep link text, drop the URL
    text = _HTML_TAG_RE.sub("", text)       # any stray tags
    text = _BLOCKQUOTE_RE.sub("", text)     # unwrap blockquotes
    text = _FOOTER_RE.sub("", text)         # per-story "View more …»" boilerplate
    text = _HR_RE.sub("", text)             # standalone --- divider rules
    text = _UI_NOISE_RE.sub("", text)       # like/upvote/footer-nav UI lines
    text = _ESCAPE_RE.sub(r"\1", text)      # un-escape markdown (\* -> *)
    text = _LEAD_WS_RE.sub("", text)        # leading whitespace from removed images
    text = re.sub(r"[ \t]+\n", "\n", text)  # trailing whitespace
    text = _MULTI_BLANK_RE.sub("\n\n", text)
    return text.strip()


# --- loading ---------------------------------------------------------------

def load_documents(docs_dir: Path = DOCS_DIR) -> list[Document]:
    """Load and clean every .md file in `docs_dir`."""
    documents: list[Document] = []
    # sorted() keeps the load order stable across runs.
    for path in sorted(docs_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        documents.append(
            Document(
                filename=path.name,
                # Fall back to the filename if a doc has no title; un-escape \" etc.
                title=_ESCAPE_RE.sub(r"\1", meta.get("title") or path.stem),
                source=meta.get("source", ""),
                text=clean_text(body),
            )
        )
    return documents


if __name__ == "__main__":
    # Manual inspection harness: `python ingest.py` to eyeball the cleaned output
    # (per the milestone's "print a document and read it" verification step).
    docs = load_documents()
    print(f"Loaded {len(docs)} documents from {DOCS_DIR}\n")
    for d in docs:
        print(f"  {len(d.text):6,d} chars | {d.title[:60]}")
        if not d.source:
            print(f"         ⚠️  no source URL parsed for {d.filename}")

    # Dump one cleaned doc for eyeball inspection (a roundup — the tricky case).
    print("\n" + "=" * 70)
    sample = next((d for d in docs if "Roundup A" in d.filename), docs[0])
    print(f"CLEANED SAMPLE: {sample.title}\nsource: {sample.source}\n" + "=" * 70)
    print(sample.text[:1500])
