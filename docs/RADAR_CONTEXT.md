# RADAR — research and implementation loop

## What this is

RADAR is a research-to-implementation pipeline designed to keep a codebase external knowledge (papers, tools, articles, repos) tightly coupled to its internal structure. It runs per-repository, writes into docs/, and is committed to git alongside the code it describes.

repo-scan (already built) produces the initial knowledge base. RADAR layers on top — ingesting external sources, linking them to specific files and modules, and driving a feedback loop from new theory through to implementation spec.

---

## The problem it solves

Three gaps exist in most engineering workflows:

1. No visibility into dep/call structure — unclear what imports what, what calls what, which files are highest-risk to change.
2. Research notes disconnected from code — papers and articles live in Notion or a browser tab, not next to the files they are relevant to.
3. No path from new information to action — a useful paper gets read and forgotten rather than triaged into a concrete implementation decision.

RADAR closes all three.

---

## Loop architecture

RADAR is a five-stage pipeline:

    R — Research    find and ingest relevant external sources
    A — Analyze     extract key claims, link to repo files and modules
    D — Draft       produce an implementation spec or ADR from the analysis
    A — Audit       self-critique the draft via a Reflexion loop
    R — Record      write final output to docs/, commit to git

### Trigger types

Three things can kick off the loop:

- Manual feed — hand it a URL, arXiv ID, GitHub repo, or local file
- Problem description — describe a problem in natural language; the Research agent finds relevant sources autonomously (primary use case)
- Metric threshold — a repo-scan health report flags a file as critically complex or high-churn; the loop fires to find improvement approaches

### Human-in-the-loop gates

The loop is designed to become progressively more autonomous. Phase 1 stops at two explicit gates:

- Gate 1 — after Analyze: sources and relevance surfaced, approval to proceed
- Gate 2 — after Audit: draft spec presented, approval to record

Gates are CLI prompts. As trust builds, individual gates can be removed via .repo-scan.json flags.

---

## Design influences

RADAR is a hybrid of three established patterns:

**Reflexion** (Shinn et al., 2023) — the Audit stage uses self-critique. The Draft agent evaluates its own output against defined quality criteria and retries if it falls below threshold.

**MAPE-K** (IBM autonomic computing) — Monitor / Analyze / Plan / Execute maps directly to the metric-triggered path. repo-scan is Monitor, Analysis agent is Analyze, Draft is Plan, Record is Execute. The docs/ folder is the shared Knowledge base.

**ReAct** (Yao et al., 2022) — the Research agent uses interleaved reasoning and action for open-ended search. Better suited to problem-description triggers than a fixed pipeline.

---

## Source types

RADAR ingests from any of these:

| Type | Fetcher | What gets extracted |
|------|---------|-------------------|
| arXiv / Semantic Scholar | Official APIs | Abstract, key claims, methodology |
| Web articles / blogs | trafilatura | Full text, author, date |
| GitHub repos | GitHub REST API | README, topics, language, stars |
| npm / PyPI packages | Registry APIs | Description, deps, downloads |
| HackerNews threads | Algolia HN API | Top comments, linked URLs |
| Local PDFs / docs | pymupdf, markitdown | Full text extraction |

Every source normalizes to the same Source object:

    id, type, url, title, summary, key_claims[], relevance,
    tags[], linked_files[], ingested_at, raw_url

Each becomes a single markdown file at docs/research/sources/{id}.md.
The LLM writes the first draft on ingestion. Human annotates inline.

---

## docs/ structure (full)

repo-scan creates the scaffold. RADAR populates the research layer.

    docs/
      index.md                        # dashboard — repo-scan
      reports/
        health.md                     # file sizes, complexity, churn
        dependencies.md               # Mermaid dep graphs
        calls.md                      # Mermaid call graphs
      architecture/
        dependency-graph.md           # stable dep graph
        overview.md                   # hand-written
        decisions/
          ADR-001-*.md                # architecture decision records
      research/
        sources/
          arxiv-{id}.md               # one file per ingested source
          gh-{owner}-{repo}.md
          url-{slug}.md
        index.md                      # auto: all sources by tag/date
        tags.md                       # auto: tag to source list
        theory.md                     # human: distilled understanding
        candidates.md                 # auto: high-complexity + high-churn files
      specs/
        {feature-name}.md             # agent-drafted, human-approved impl plans
      changelog/
        {YYYY-MM-DD}-loop.md          # one entry per RADAR run
      AGENTS.md                       # loop rules, file ownership, gate behavior

---

## AGENTS.md (minimum viable)

Every repo running RADAR should have AGENTS.md at root:

    ## Ownership
    - docs/research/  — RADAR writes, human annotates
    - docs/specs/     — RADAR drafts, human approves before merge
    - docs/reports/   — repo-scan writes, do not edit manually
    - src/            — human writes, RADAR never touches directly

    ## Gate behavior
    - Gate 1 (post-Analyze): always require approval
    - Gate 2 (post-Audit): always require approval

    ## Off-limits
    - Never modify files outside docs/ and scripts/
    - Never commit to main directly
    - Never delete existing source files in docs/research/sources/

    ## Diagram format
    Always output Mermaid for any diagram request.

---

## CLI (target interface)

    radar ingest arxiv:2305.10601
    radar ingest github:vercel/ai
    radar ingest url:https://example.com/article
    radar ingest file:./papers/note.pdf
    radar research "how do streaming LLM responses work in Next.js"
    radar loop "our agent orchestration layer has too much coupling"
    radar full

---

## Build order

    Phase 0  repo-scan          COMPLETE
    Phase 1  RADAR ingest       next — single-source ingestion, normalizer, Source writer
    Phase 2  RADAR research     multi-source search, ReAct agent
    Phase 3  RADAR loop         full pipeline, Reflexion audit, gate UI
    Phase 4  Automation         metric-triggered firing, progressive gate removal
