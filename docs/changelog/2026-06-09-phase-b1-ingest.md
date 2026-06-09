# 2026-06-09 — Phase B1: radar ingest

First RADAR phase: the `radar` CLI exists and can pull external knowledge into
`docs/research/` in a normalized, Obsidian-linkable form.

## What changed

- **`radar` entry point** — second console script from the same package
  (`repo_scan/radar/` subpackage). Subcommands scaffolded: `ingest` (live),
  `research` / `loop` / `full` (arrive in B2–B4).
- **Source model** (`radar/sources.py`) — every source normalizes to one
  `Source` dataclass and one `docs/research/sources/{id}.md` file with a
  parseable ```source metadata block. Re-ingesting updates the generated block
  but **never touches anything from `## Notes` down** — human annotations survive.
- **Fetchers** (`radar/fetchers.py`) — `arxiv:ID` (export API), `github:owner/repo`
  (REST + README), `url:`/bare URLs (trafilatura when installed, stdlib HTML
  extractor fallback), `file:` (text/markdown; PDF via pymupdf when installed).
  All stdlib, 30s timeouts, fetch/parse split so tests never hit the network.
- **Research index** — `radar ingest` rebuilds `docs/research/index.md` (source
  table with wikilinks) and `docs/research/tags.md` (tag → sources) from the
  source files on disk, so the index never drifts from reality.

## Verification

- 11 new tests (34 total): id slugs, arXiv/GitHub parsers on canned payloads,
  HTML extractor, file fetcher, human-notes preservation, metadata round-trip,
  index/tags rebuild.
- Live check: `radar ingest github:yamadashy/repomix --no-llm` wrote
  `docs/research/sources/gh-yamadashy-repomix.md` + index + tags (committed as
  a working example).

## Notes

- `trafilatura` and `pymupdf` are optional enhancements and are **not installed**;
  the stdlib fallbacks are active. Say the word and I'll add them.
- `--no-llm` skips summarization; the LLM backend lands in B2.

## Next

Phase B2: `radar/llm.py` CLI-backed completion (cursor-agent/claude) and
`radar research <question>` ReAct-style loop.
