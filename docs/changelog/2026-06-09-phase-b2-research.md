# 2026-06-09 — Phase B2: LLM backend + radar research

The loop gets a brain: CLI-backed LLM completion and the first reasoning
command, `radar research <question>`.

## What changed

- **LLM backend** (`radar/llm.py`) — shells out to agent CLIs on PATH, no API
  keys or SDK deps. Default candidates: `cursor-agent -p --output-format text`,
  then `claude -p`; override per-repo with `"llm_cli"` in `.repo-scan.json`.
  `extract_json` tolerates code fences and surrounding prose; every failure
  mode (missing CLI, nonzero exit, timeout, empty/garbage output) raises a
  typed `LLMError` with a useful message.
- **Summarization** — `summarize_source` asks for structured JSON (summary,
  key claims, tags, relevance) and merges it into the Source; `radar ingest`
  now uses it by default (`--no-llm` to skip).
- **`radar research <question>`** (`radar/research.py`) — ReAct-shaped:
  1. Build compact repo context from `docs/scan.json` (A.5 paying off)
  2. LLM proposes up to N source refs as JSON, excluding already-ingested ids
  3. radar fetches + summarizes + writes each, collecting failures
  4. Index/tags rebuilt; run recorded to `docs/research/runs/{date}-{slug}.md`
     with strategy, ingested wikilinks, and failures — every session auditable.
- **Fake LLM harness** (`tests/fake_llm.py`) — env-driven canned responses
  (single response or a pop-per-call queue for multi-turn pipelines), making
  all LLM-path tests offline and deterministic.

## Verification

- 11 new tests (45 total): backend selection/failure modes, JSON extraction
  variants, summarize merge, research happy path via `file:` refs (no network),
  failure recording, run-log writing.
- `cursor-agent` detected on PATH as the live backend on this machine.

## Next

Phase B3: `gates.py` (prompt/auto/deny + file-backed pending state) and the
full `radar loop` pipeline — Research → Analyze → Gate 1 → Draft → Audit →
Gate 2 → Record.
