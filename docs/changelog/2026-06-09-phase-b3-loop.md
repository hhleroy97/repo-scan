---
type: changelog
date: 2026-06-09
tags:
  - changelog
  - radar
linked_files: ["[[repo_scan/radar/gates.py]]", "[[repo_scan/radar/pipeline.py]]"]
---
# 2026-06-09 — Phase B3: gates + the full RADAR loop

The core deliverable: `radar loop "<problem>"` runs Research → Analyze →
Gate 1 → Draft → Audit → Gate 2 → Record, with human gates that can be
progressively abstracted away.

## Gates (`radar/gates.py`)

- Three modes per gate via `.repo-scan.json` → `"gates"`: **prompt** (default,
  CLI y/n), **auto** (pass through silently — the gate "abstracted away" once
  trusted), **deny** (hard stop).
- **File-backed pausing** — in prompt mode without a TTY, the gate writes
  `docs/research/pending/{gate}.json` and the loop exits with code 2. Re-running
  with `--approve post_analyze` consumes the pending state and continues.
  LangGraph-interrupt-shaped, but plain files instead of a checkpointer.
- **Append-only decision trail** — every gate decision (auto/approved/rejected/
  paused/denied) lands in `docs/research/decisions.md` with timestamp + summary.

## Pipeline (`radar/pipeline.py`)

1. **Research** — reuses B2 `run_research` + run log
2. **Analyze** — LLM synthesizes ingested sources against the problem →
   findings/recommendation/confidence/risks → `docs/research/analysis/{date}-{slug}.md`
3. **Gate 1** — payload: the recommendation
4. **Draft** — LLM writes a bounded markdown spec (Goal/Approach/Changes/Risks/Out of scope)
5. **Audit** — second LLM pass critiques the spec; on `revise`, one revision
   round then re-audit (self-refine, capped to prevent loops)
6. **Gate 2** — payload: audit verdict + spec path; spec saved as `status: draft`
7. **Record** — spec flipped to `status: approved`, run appended to
   `docs/changelog/{date}-loop.md` (outcome, sources, confidence, gates)
- `--gates auto|prompt|deny` overrides both gates per run; LLM failures record
  a `failed` outcome rather than dying silently.

## Verification

- 11 new tests (56 total): all gate modes, pending-state lifecycle, decision
  trail, plus loop e2e via the fake-LLM response queue — happy path, pause at
  Gate 1 (exit 2), resume with `--approve`, audit revision round, and clean
  failure without a backend. Zero network, zero real LLM calls.

## Next

Phase B4: `radar full` (metric-triggered candidate → loop), hook integration
decision, CLI-level fake-LLM e2e.
