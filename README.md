# The Unofficial Guide — Project 1

A Retrieval-Augmented Generation (RAG) system over real, documented case studies of founders who built profitable products and income streams — built to test one claim: that coding skill was never the bottleneck to building income; ideas, distribution, and persistence were.

**Stack:** sentence-transformers (`all-MiniLM-L6-v2`) · ChromaDB · Groq (`llama-3.3-70b-versatile`) · Gradio.

**Run it:**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your Groq API key (free at console.groq.com)
python embed.py             # build the vector store (first run downloads ~80 MB)
python app.py               # open http://localhost:7860
```

---

## Domain

This system covers real, publicly documented case studies of people who built profitable products and income streams from scratch — indie hackers, solo founders, and automation consultants who shared their actual revenue numbers. The angle I care about: many of these founders started with little or no engineering ability (some shipped entirely on no-code tools or AI-written code), yet built products earning thousands to millions per month — which suggests coding skill was never the real bottleneck; ideas, distribution, and persistence over time were. This knowledge is valuable but hard to find through official channels because the useful detail — what they built, what they relied on instead of raw skill, how long it took, and what failed — is scattered across Indie Hackers posts, eBiz Facts roundups, and founder interviews rather than collected anywhere official, and the official "make money online" content tends to be generic or trying to sell you something.

---

## Document Sources

12 documents covering real automated/solo income case studies with verified revenue numbers, plus two contextual pieces.

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | NYT | News feature — Medvi, $1.8B AI telehealth run by 2 people | https://www.nytimes.com/2026/04/02/technology/ai-billion-dollar-company-medvi.html |
| 2 | Indie Hackers | Founder case study — Photo AI, $0→$132K MRR in 18mo, solo | https://www.indiehackers.com/post/photo-ai-by-pieter-levels-complete-deep-dive-case-study-0-to-132k-mrr-in-18-months-3a9a2b1579 |
| 3 | Indie Hackers | Founder case study — Postiz, open-source, $14.2K MRR solo | https://www.indiehackers.com/post/i-did-it-my-open-source-company-now-makes-14-2k-monthly-as-a-single-developer-f2fec088a4 |
| 4 | OneMillionGoal | Founder profile — Pieter Levels, ~$3.1M/yr, no employees | https://www.onemilliongoal.com/p/pieter-levels-the-king-of-indie-hacking |
| 5 | Indie Hackers | Founder case study — 30-app mobile portfolio, $22K/mo solo | https://www.indiehackers.com/post/tech/from-failed-app-to-30-app-portfolio-making-22k-mo-in-less-than-a-year-myy3U7K9evxGOVOHti8s |
| 6 | eBiz Facts (via Goodreads) | Income profile — FounderPal, no-code, $60K in 6mo | https://www.goodreads.com/author_blog_posts/24682095-their-no-code-tool-earned-60-000-in-6-months |
| 7 | eBiz Facts (via Goodreads) | Income profile — Mike Cardona, $20K/mo automation consulting | https://www.goodreads.com/author_blog_posts/23177017-20k-month-automation-alchemist |
| 8 | nicksaraev.com | Founder bio/case study — Nick Saraev, $100K/mo Make.com automations | https://nicksaraev.com/biography/ |
| 9 | Indie Hackers | Roundup — 2024 year-in-reviews, multiple founders, wins & failures | https://www.indiehackers.com/post/lifestyle/earned-1-2m-launched-5-startups-in-2024-indie-hackers-share-their-year-in-reviews-g61Lu08M3otlLESYu9m9 |
| 10 | GladLabs | Contextual explainer — how indie hackers actually make money, failure rates | https://www.gladlabs.io/posts/beyond-the-bootstrap-how-indie-hackers-actually-ma-f0a313a9 |
| 11 | eBiz Facts (via Goodreads) | Multi-founder roundup — ~10 short income case studies (blog pg 14) | https://www.goodreads.com/author/show/6577180.Niall_Doherty/blog?page=14 |
| 12 | eBiz Facts (via Goodreads) | Multi-founder roundup — ~10 short income case studies (blog pg 45) | https://www.goodreads.com/author/show/6577180.Niall_Doherty/blog?page=45 |

---

## Chunking Strategy

**Chunk size:** ~800 characters (~120–150 words), deliberately kept under all-MiniLM-L6-v2's 256-token (~1000 char) limit — the model silently truncates anything longer *before* embedding, so larger chunks would lose content invisibly.

**Overlap:** ~150 characters (~1–2 sentences), snapped to a word boundary so an overlap never starts mid-word, to preserve context across chunk boundaries.

**Why these choices fit your documents:** The corpus is heterogeneous — short single-story posts (~600 words), long multi-section deep-dives (~5,800 words), and two roundup pages that each pack ~10 *unrelated* mini-case-studies. A purely fixed-size split would merge two different founders' numbers into one chunk on the roundups, producing confused retrieval. So the splitter breaks on Markdown headings first (`##` / `###` / `####`), then paragraphs, then sentences, only falling back to a hard character cut when a section still exceeds the target. Each section's heading is prepended to its sub-chunks, so a mid-section chunk still carries its story's title. **Preprocessing before chunking:** parsed YAML frontmatter into metadata (title + source URL) then stripped it from the body, removed image embeds, converted inline links to their anchor text, stripped HTML/`<script>`/`<iframe>` junk, and removed site boilerplate (like/upvote chrome, horizontal rules, and the repeated eBiz Facts newsletter footer block).

**Final chunk count:** 236 chunks across 12 documents (avg ~656 chars/chunk; max under the 1,000-char embedding limit).

### Sample Chunks

Five representative chunks (one per document type), each with its source document. Note how the section heading is preserved at the top of each chunk:

**1. Multi-founder roundup — *Niall Doherty's Blog, page 14* (eBiz Facts)**
> #### He Makes $170K/Month Selling One Website Template
> paying up to $1,500/month for additional services (eg. Google Ads management, SEO). All the sites and automations are built on HighLevel (aff link). Kai says in the video… I'm not sitting here pretending this is easy, but it's super doable. I have very average intelligence. I have gnarly ADHD. I'm not super tech-savvy at all… if I can figure this out, anyone could.

**2. Long deep-dive — *Photo AI by Pieter Levels: $0 to $132K MRR in 18 Months* (Indie Hackers)**
> ### 📊 Traffic Sources (Estimated Breakdown)
> Based on available data: **Twitter/X: 50%** → Direct + social referrals · **Direct: 20%** → Brand searches, returning users · **Organic Search: 15%** → Growing over time · **Press/Media: 10%** → Podcast bumps · **Other Social: 5%** → Reddit, forums.

**3. Single case study — *Nick Saraev: From Medicine Dropout to $100K/Month Automation Empire* (nicksaraev.com)**
> ## LeftClick: Automation Consultancy — Productized to $72K/Month Solo
> After 1SecondCopy peaked, Nick and Noah started LeftClick, an AI automation consultancy. Initially they pursued complex custom projects, which required hiring skilled contractors — a problem they couldn't solve at scale. The turning point: a client requested a system Nick had already built…

**4. Short post — *Their No-Code Tool Earned $60,000 in 6 Months* (eBiz Facts)**
> #### Their No-Code Tool Earned $60,000 in 6 Months
> …current AI products only focus on generating cheesy email subject lines and spammy blog posts for SEO. 1. Solopreneurs need a strategic CMO, not a content marketing intern. 2. People prefer clicking buttons more than texting with ChatGPT…

**5. Year-in-review — *"Earned $1.2M, launched 5 startups" in 2024* (Indie Hackers)**
> ## The setbacks
> Of course, it wasn't all sunshine and rainbows… Jason Leow called it a year full of "dead ends" — consulting gigs that flopped, product launches that went nowhere, and a job hunt stuck in neutral. But he found a bright side: those dead ends pushed him to pivot…

---

## Embedding Model

**Model used:** all-MiniLM-L6-v2 via sentence-transformers — local, no API key or rate limits, 384-dim, fast on CPU. It's the free local stack the project calls for and is good enough for English short-form text. Vectors are stored in ChromaDB using **cosine** distance (the metric all-MiniLM is trained for).

**Production tradeoff reflection:** If I were deploying this for real users and cost weren't a constraint, the tradeoff I'd weigh first is **context length**. MiniLM's 256-token (~1000 char) cap is the single biggest constraint on this system — it forced the small ~800-char chunks and is the root of the roundup "story-bleed" risk. A long-context embedder (e.g. text-embedding-3-large at 8191 tokens, or Voyage/Cohere) would let a single chunk hold a whole case study, reducing boundary-splitting. Second, **domain accuracy on numeric/jargon-dense text**: these docs are saturated with "$X MRR" figures and tool names, and a small general-purpose model can map two different founders' revenue passages to nearly identical vectors. My evaluation confirmed this — abstract questions (Q4 failure points, Q5 first customers) couldn't retrieve the right concrete chunks, which ranked #22–53 instead of the top 5; a larger or domain-tuned model would bridge that abstract→concrete gap. Third, **local vs. API**: MiniLM is local, free, private, and rate-limit-free, but since this corpus is entirely public data, privacy isn't a real concern here, so a paid hosted model would be an acceptable trade for the quality gain (the cost being per-query latency and a third-party dependency). **Multilingual support** isn't relevant for this English-only corpus, though it would matter if I expanded to non-English founder stories.

---

## Retrieval Test Results

Three of the five evaluation questions run through the retriever (`eval_retrieval.py`), showing the top chunks returned and their cosine distances (lower = more similar). The full five-question run is in the Evaluation Report below.

**Q1 — "What business models or revenue streams did these founders use to make money?"** (top-5 avg distance **0.46**)

| dist | source document | section heading |
|------|-----------------|-----------------|
| 0.419 | Nick Saraev (nicksaraev.com) | Early Income Experiments |
| 0.464 | FounderPal (eBiz Facts) | Their No-Code Tool Earned $60,000 |
| 0.472 | Pieter Levels (OneMillionGoal) | $3.1M/yr startup empire |
| 0.475 | Medvi (NYT) | one-person $1B business |
| 0.485 | Nick Saraev (nicksaraev.com) | business models tested |

*Why these are relevant:* every chunk is a founder describing how they actually made money — Nick's income experiments, FounderPal's revenue, Pieter's portfolio, Medvi's middleman model. This is the system's strongest question; the retrieved content directly answers "how the money was made."

**Q2 — "…did building a profitable product require strong coding skills?"** (top-5 avg distance **0.49**)

| dist | source document | section heading |
|------|-----------------|-----------------|
| 0.470 | FounderPal (eBiz Facts) | Their No-Code Tool |
| 0.480 | FounderPal (eBiz Facts) | Their No-Code Tool |
| 0.493 | How Indie Hackers Make Money (GladLabs) | What You'll Learn |
| 0.493 | FounderPal (eBiz Facts) | Their No-Code Tool |
| 0.496 | Pieter Levels (OneMillionGoal) | Conclusion |

*Why these are relevant (and the catch):* the top hits are the FounderPal no-code story — directly on point ("Dan and Sveta didn't really know how to code"). But **3 of 5 are the same document**, so retrieval is relevant yet *narrow*: it surfaces the no-code side of the thesis but not the skilled-dev or AI-assisted sides needed for the full "it's a mix" answer.

**Q3 — "How long did founders typically take to reach sustainable income?"** (top-5 avg distance **0.57**)

| dist | source document | section heading |
|------|-----------------|-----------------|
| 0.558 | Photo AI (Indie Hackers) | Key Achievements |
| 0.561 | Photo AI (Indie Hackers) | What Actually Drove Growth |
| 0.574 | Nick Saraev (nicksaraev.com) | Make Money With Make community |

Relevant content (Photo AI's timeline milestones), though distances run higher — typical for an abstract "how long" question over concrete narrative chunks.

---

## Grounded Generation

**System prompt grounding instruction:** The exact system prompt sent to llama-3.3-70b:

> *You are a research assistant answering questions about how founders built profitable products and income streams. Answer the question using ONLY the information in the provided context. Do not use any outside knowledge. If the context does not contain enough information to answer, reply exactly: "I don't have enough information on that." When you do answer, ground each claim in the context and name the founders or sources you drew from.*

Structural choices that reinforce grounding: (1) the top-5 retrieved chunks are passed as the context, each **labelled with its `[doc title — source URL]`** — some chunks never name their own subject (e.g. a "Traffic Sources" chunk that never says "Photo AI"), so the label is what lets the model attribute a fact to the right founder; (2) **temperature 0.2**, to keep the model faithful rather than creative. Grounding was verified with an out-of-scope question ("What is the best programming language to learn in 2026?") — the system returned the refusal line rather than answering from the model's training knowledge.

**How source attribution is surfaced in the response:** Sources are built **programmatically from the retrieved chunks' metadata** (deduplicated `doc title — source URL`), *not* parsed from the LLM's text — so the citations are guaranteed to be the documents actually fed to the model, regardless of what the LLM writes. They're returned as a structured field alongside the answer and shown in the interface's "Sources" box. On a refusal, sources are suppressed, since none were used to answer.

---

## Example Responses

Two in-scope responses with source attribution visible, plus one out-of-scope refusal (from `eval_generate.py`).

**Example 1 — "Did building a profitable product require strong coding skills?"**
> According to the context, Dan and Sveta, the founders of FounderPal, did not have a strong coding background — "Being marketers, Dan and Sveta didn't really know how to code." Despite this, they built a profitable product using a no-code approach, paying $32/mo for Bubble to ship in 3 weeks. This suggests building a profitable product does not necessarily require strong coding skills.
>
> **Sources:**
> • Their No-Code Tool Earned $60,000 in 6 Months — https://www.goodreads.com/author_blog_posts/24682095-their-no-code-tool-earned-60-000-in-6-months
> • How Indie Hackers Actually Make Money in 2026 — https://www.gladlabs.io/posts/beyond-the-bootstrap-how-indie-hackers-actually-ma-f0a313a9
> • Pieter Levels: The King of Indie Hacking — https://www.onemilliongoal.com/p/pieter-levels-the-king-of-indie-hacking

**Example 2 — "What business models or revenue streams did these founders use to make money?"**
> The founders used a range of models: Nick Saraev (a door-to-door marketing agency that hit $20K in a single month, wedding videography at $10K/mo, online courses earning $80K+, and now a $100K/mo automation business); Sveta Bay and Dan Kulkov's no-code tool FounderPal ($60K in 6 months via one-time payments); Pieter Levels' portfolio of profitable products generating millions per year; and Matthew Gallagher's A.I.-powered middleman business for weight-loss drugs that became a $1.8B company.
>
> **Sources:**
> • Nick Saraev: From Medicine Dropout to $100K/Month Automation Empire — https://nicksaraev.com/biography/
> • Their No-Code Tool Earned $60,000 in 6 Months — https://www.goodreads.com/author_blog_posts/24682095-their-no-code-tool-earned-60-000-in-6-months
> • Pieter Levels: The King of Indie Hacking — https://www.onemilliongoal.com/p/pieter-levels-the-king-of-indie-hacking
> • How A.I. Helped One Man (and His Brother) Build a $1.8 Billion Company — https://www.nytimes.com/2026/04/02/technology/ai-billion-dollar-company-medvi.html

**Out-of-scope — "What is the best programming language to learn in 2026?"**
> I don't have enough information on that.
>
> *(No sources — the system correctly declined rather than answering from the model's general training knowledge.)*

---

## Query Interface

A minimal Gradio web app (`app.py`), launched with `python app.py` → http://localhost:7860.

**Input field**
- *Your question* — a single textbox; submit with the **Ask** button or by pressing Enter.

**Output fields**
- *Answer* — the grounded answer from llama-3.3-70b.
- *Sources* — the deduplicated source documents the answer drew from (shows "—" on a refusal).

**Sample interaction transcript**
```
Your question:  How did these founders find their first customers?

Answer:         Matthew Gallagher (Medvi) used A.I. to generate ads and handle
                customer service, gaining 300 customers in month one. Nick Saraev
                found his first customers through door-to-door marketing for his
                local agency, then used an SEO funnel and paid ads for his wedding
                videography business.

Sources:        • How Indie Hackers Actually Make Money in 2026 — gladlabs.io/...
                • How A.I. Helped One Man... Build a $1.8 Billion Company — nytimes.com/...
                • Their No-Code Tool Earned $60,000 in 6 Months — goodreads.com/...
                • Nick Saraev: ...$100K/Month Automation Empire — nicksaraev.com/biography
```

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What business models / revenue streams did founders use to make money? | Mostly recurring SaaS/MRR (Photo AI, Postiz, Pieter); plus paid communities & courses (Saraev), done-for-you services (Cardona, Saraev), one-time products (FounderPal), ad-supported newsletters, and middleman (Medvi). Recurring revenue = main path to scale. | Named services, courses, one-time payments (FounderPal), Pieter's portfolio, and Medvi's middleman model — but skewed heavily to Nick Saraev and never surfaced the "recurring revenue dominates" pattern. | Relevant | Partially accurate |
| 2 | Did building a profitable product require strong coding skills? | A mix — no-coders (FounderPal/Bubble), a first-time programmer using AI (Josh Mohrer), and skilled devs (Pieter, Postiz). Coding ability was *not* the differentiator. | Correctly concluded coding isn't required — but drew it *only* from FounderPal's no-code story; missed the first-time-programmer and skilled-dev sides, so it never showed the full "it's a mix." | Partially relevant | Partially accurate |
| 3 | How long did founders take to reach sustainable income? | Wide range; winners cluster ~6–18 mo (FounderPal 6mo, Photo AI 18mo, 30-app <1yr), but survivorship bias hides years of prior failures (Pieter). | Gave the timelines (Photo AI 18mo, FounderPal 6mo, Nick) *and* caught the survivorship nuance — "Pieter spent 10+ years building an audience first." | Relevant | Accurate |
| 4 | What were the biggest failure points / risks? | Over-building/scope, marketing neglect, competitor risk (Photo AI→Lensa, no iOS), key-person risk (Medvi lost ~200 customers; Postiz burnout), market concentration (Nick's COVID wipeout). | Returned *only* Pieter Levels' risks (perfectionism, burnout, single-project dependence). Missed Lensa, Medvi, and the COVID wipeout — retrieval surfaced only Pieter chunks. **(failure case)** | Off-target | Partially accurate |
| 5 | How did founders find their first customers? | Distribution preceded revenue: Photo AI on Hacker News, Postiz on Reddit/DEV, FounderPal on Twitter+Product Hunt, Nick via Twitter/YouTube/Skool, Cardona via cold outreach. | Got Medvi (AI-generated ads) and Nick (door-to-door, SEO, paid ads), but missed the marquee HN / Reddit / Product Hunt distribution stories and drifted into a "micro-acquisition" tangent. **(failure case)** | Off-target | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** "What were the biggest failure points or risks across these case studies?"

**What the system returned:** Only Pieter Levels' risks — perfectionism, mental-health/burnout, lack of market demand, and over-dependence on a single project. It missed every other documented failure the question calls for: Photo AI losing users to Lensa for lacking an iOS app, Medvi's solo operator breaking production and losing ~200 customers (key-person risk), Postiz's burnout, and Nick Saraev's wedding-video income dropping to $0 overnight when COVID shut down events (market concentration).

**Root cause (tied to a specific pipeline stage):** **Retrieval**, not generation. Ranking all 236 chunks for this query showed the expected-answer chunks *exist* but rank far below the top-5 cutoff — Photo-AI-vs-Lensa at #22, Postiz burnout #23, Nick's COVID wipeout #26, and Medvi's ~200-customer loss at #53. The abstract question wording ("biggest failure points / risks") doesn't lexically or semantically match the concrete narrative in those chunks ("lost to Lensa AI," "the downtime lost him around 200 potential customers"), and the small general-purpose embedding model (all-MiniLM-L6-v2) can't bridge that abstract→concrete gap. The LLM then grounded *correctly* on the only failure content it was handed (Pieter's), so the answer is single-source and incomplete — a retrieval failure surfacing as a thin answer, not a generation failure.

**What you would change to fix it:** Add **hybrid search** (BM25 keyword + semantic) — keyword matching would surface the chunks containing "Lensa," "COVID," and "200 potential customers" that pure semantic search ranks too low to retrieve. BM25 is free and runs locally (a listed stretch feature), so it's the practical next step. For a production system, a larger or domain-tuned embedding model would also close the abstract→concrete gap (the tradeoff noted in planning.md's production-deployment reflection), at the cost of a paid API.

---

## Spec Reflection

**One way the spec helped you during implementation:** Writing planning.md before any code meant the chunking strategy was already settled when I sat down to build. I knew to split on headings first — because the eBiz Facts roundup files pack ~10 unrelated stories each — and to cap chunks at ~800 characters because all-MiniLM truncates at 256 tokens. That spec became the literal prompt I handed the AI to generate `ingest.py` and `chunk.py`, so the generated code matched my design instead of being generic. Writing the five evaluation questions and their expected answers up front helped just as much: it gave me an honest measuring stick, so when retrieval came back weak on Q4 and Q5 I could recognize it as a real failure rather than talking myself into "good enough."

**One way your implementation diverged from the spec, and why:** The biggest divergence was the framing. My original plan leaned on "no-code tools to make money," and one of my eval questions literally asked which no-code tools showed up most. Partway through I realized that wasn't the point I cared about — as someone who can code, the interesting claim is that coding skill was never the bottleneck. So I reframed the domain around that thesis and swapped that question for "what business models did founders use to make money," which is coding-agnostic. I also added more cleaning than the spec anticipated (an entire eBiz Facts newsletter-footer block I only discovered by inspecting chunks), and chose cosine distance for the vector store — a detail the plan didn't specify but which matters because all-MiniLM is trained for cosine.

---

## AI Usage

**Instance 1 — Generating and debugging the ingestion + chunking pipeline**

- *What I gave the AI:* my planning.md Chunking Strategy section plus a recon of the actual files (heading levels, the ~120 image embeds, and injected browser-extension `<script>`/`<iframe>` junk).
- *What it produced:* `ingest.py` (loader + cleaner) and `chunk.py` (a heading-aware recursive splitter with overlap).
- *What I changed or overrode:* I inspected the output instead of trusting it, which is where the real work was. The first chunks still contained site boilerplate (a repeated eBiz Facts newsletter footer, plus like/upvote chrome) and a bug where the overlap started mid-word. I directed targeted fixes for each and re-ran the chunk inspection until the output was clean — and caught that a naive footer-removal regex was deleting real stories from a roundup, so I had it bound the removal per-block instead.

**Instance 2 — Wiring up retrieval/generation and handling weak retrieval honestly**

- *What I gave the AI:* my Retrieval Approach section and the architecture diagram, plus design decisions I'd already made (cosine distance, an idempotent collection rebuild, programmatic source attribution).
- *What it produced:* `embed.py`, `retrieve.py`, and `generate.py` implementing those.
- *What I changed or overrode:* when retrieval scored poorly on two questions, I did **not** let the AI tune the system to make those exact questions look better — that would overfit my own evaluation. Instead I directed a diagnostic, which showed the right chunks existed but ranked #22–53; I then chose to *document* the limitation (and name hybrid search as the real fix) rather than chase it, and had the system suppress source citations on refusals so a "no answer" wouldn't look falsely cited.
