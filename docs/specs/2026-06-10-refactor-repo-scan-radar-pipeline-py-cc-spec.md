---
type: "spec"
problem: "Refactor repo_scan/radar/pipeline.py (CC 11, 3 commits). `repo_scan/radar/pipeline.py` is both high-churn (3 commits) and high-complexity (total CC 11). Acceptance criteria: Complexity of every function below rank C; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-refactor-repo-scan-radar-pipeline-py-cc-analysis]]"
drafted_at: "2026-06-10 13:44 UTC"
linked_files: ["repo_scan/radar/pipeline.py", "tests/test_hub.py", "tests/test_radar_full.py", "tests/test_radar_pipeline.py", "tests/test_tickets_workflow.py"]
---

# Spec — Refactor repo_scan/radar/pipeline.py (CC 11, 3 commits). `repo_scan/radar/pipeline.py` is both high-churn (3 commits) and high-complexity (total CC 11). Acceptance criteria: Complexity of every function below rank C; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 13:44 UTC by radar — **status: approved**_

## Goal

Lower cyclomatic complexity in `repo_scan/radar/pipeline.py` so every function is below radon rank C (CC ≤ 10), without changing RADAR loop behavior. Live `docs/scan.json` shows the only rank-C hotspots: `cmd_loop` (CC 19) and `write_analysis` (CC 11); derived `cc_by_file` for `repo_scan/radar/pipeline.py` is 30 (19+11), `ranking[].complexity` is 30, churn is 10. Ticket tkt-0006 / problem text citing CC 11 and 3 commits is stale—Phase 1 baseline overrides that title for implementers. Preserve the public API (`cmd_loop`, `cmd_full`, `ticket_problem`, `spec_for_problem`, `pick_candidate`) and the 0/1/2 return-code contract.

## Approach

Apply Fowler’s Replace Function with Command and Replace Nested Conditional with Guard Clauses, following the tkt-0009 playbook: baseline → incremental extraction with green pytest after each step → dogfood re-scan for trend delta.

**Phase 1 — Baseline.** Run `radon cc -s -a repo_scan/radar/pipeline.py`. Copy `docs/scan.json` to a dated artifact outside `docs/` (e.g. `/tmp/repo-scan-baselines/2026-06-10-pipeline-cc.json`); do not commit scan noise under `docs/research/`. Record derived `cc_by_file` (30), `ranking[].complexity` (30), and `health.md` row for `cmd_loop` only (`write_analysis` CC 11 is below the top-20 `complexity[]` cutoff and may be absent). Snapshot `docs/reports/trend.md`. Confirm green: `pytest tests/test_radar_pipeline.py tests/test_hub.py tests/test_tickets_workflow.py tests/test_radar_full.py`.

**Phase 2 — Refactor `cmd_loop`.** Introduce private `_RadarLoopRunner` holding `root`, `cfg`, `problem`, `approved`, `ckpt`, `result`, and `gates_log`. Thin `cmd_loop` to construct the runner, call `run()`, and map exceptions to return codes. One method per RADAR stage (`_stage_research` … `_stage_record`); each delegates resume vs fresh work to a `_run_or_resume_*` helper using guard clauses (`if key in ckpt: return cached`) instead of nested `if/else`. Extract gate early-exit (`_stop_at_gate`) to preserve pause vs reject branching via `_gate_paused` / `_finish_loop`. Move `LLMError` handling (`record_loop` with partial `gates_log`/`result`) and `gates_override` shallow `cfg` copy with the runner. One commit per stage extraction; re-run radon after each.

**Phase 2b — Refactor `write_analysis`.** Split markdown assembly into small pure builders (e.g. `_analysis_frontmatter`, `_analysis_findings_block`, `_analysis_risks_block`, `_analysis_evidence_block`) with guard-style optional sections. `write_analysis` becomes a thin coordinator calling builders and `write_doc`; preserve markdown shape/contracts (frontmatter keys, wikilink stems, empty-ingested sentinel)—observable equivalence via existing integration tests, not byte-identical output.

**Phase 3 — Verify.** Restore the Phase 1 `scan.json` copy to `docs/scan.json` immediately before the verification dogfood re-scan so `cc_movers` / scan-over-scan comparison is not confounded by mid-refactor mutations. Every function CC ≤ 10. Full regression pytest. Self-scan (`repo-scan` on this repo); compare against the Phase 1 baseline artifact—not live pre-scan state alone.

## Changes

- **`repo_scan/radar/pipeline.py`** — Add `_RadarLoopRunner` and per-stage `_run_or_resume_*` / `_stop_at_gate` helpers; slim `cmd_loop`. Add `_analysis_*` section builders; slim `write_analysis`. No changes to prompts, checkpoint key names, gate payloads, or exported function signatures.
- **`docs/scan.json`, `docs/reports/health.md`, `docs/reports/trend.md`, `docs/index.md`** — Updated by Phase 3 self-scan only; not hand-edited.

## Tests

| Criterion | Verification |
|-----------|--------------|
| Complexity of every function below rank C | `radon cc -s -a repo_scan/radar/pipeline.py` — no function at rank C or worse; specifically `cmd_loop`, every `_RadarLoopRunner` method/helper, `write_analysis`, and every `_analysis_*` builder CC ≤ 10. |
| Trend delta confirms complexity drop | Phase 1: baseline artifact, derived `cc_by_file` (30), `ranking[].complexity` (30), `health.md` `cmd_loop` row. Phase 3 (after baseline restore + re-scan): `cmd_loop` and `write_analysis` absent from `complexity[]`; derived `cc_by_file` drops (target 0); `ranking[].complexity` drops; `health.md` no longer lists `cmd_loop`; `docs/index.md` `cc_movers` shows `repo_scan/radar/pipeline.py` reduction; `trend.md` aggregate hotspot Δ only if baseline snapshot differs—do not assert per-file movers from `trend.md` alone. |

**Regression surface (green throughout Phase 2):**

- `tests/test_radar_pipeline.py` — `test_loop_happy_path_auto_gates`, `test_loop_pauses_at_gate1_noninteractive`, `test_loop_resumes_with_approve`, `test_loop_revision_round`, `test_loop_fails_cleanly_without_backend`, `test_spec_for_problem_matches_slug_not_mtime`
- `tests/test_hub.py` — `test_pause_checkpoints_then_resume_skips_llm_stages`, `test_inbox_rejection_ends_loop_and_clears_state`, `test_gate_consumes_inbox_*`
- `tests/test_tickets_workflow.py` — `test_radar_full_consumes_approved_ticket`, `test_radar_full_stopped_loop_keeps_ticket_approved`
- `tests/test_radar_full.py` — `test_pick_candidate_targets_top_priority`, `test_cmd_full_requires_radar_enabled`, `test_radar_cli_e2e_loop`

## Documentation

- **`cmd_loop` docstring** — Stage orchestration lives on `_RadarLoopRunner`; checkpoint keys and return codes unchanged.
- **`write_analysis` docstring** — Section builders own markdown shape; wikilink/provenance contract unchanged.
- **`_RadarLoopRunner` class docstring** — Seven-stage command object; resume via checkpoint guard clauses.
- No README changes unless a RADAR architecture section already documents `pipeline.py` (prefer docstrings only).

## Risks

- Checkpoint key semantics (`ingested`, `analysis`, `analysis_path`, `spec_text`, `audit`, `run_log`) must stay identical or paused loops re-run LLM stages or skip artifacts.
- Gate stop vs reject branching is fragile when flattening early returns; return code 2 and changelog `outcome` must stay unchanged for pause and reject paths (`test_loop_pauses_at_gate1_noninteractive`, hub inbox tests).
- Implicit `gates.py` ↔ `pipeline.py` coupling (53% co-change; no import edge per tkt-0017): gate payload shapes and pause/reject semantics must stay aligned when `cmd_loop` is decomposed.
- `LLMError` handler (`record_loop` with partial state) and `gates_override` shallow `cfg` copy must move with `_RadarLoopRunner` without changing exception return code 1 (`test_loop_fails_cleanly_without_backend`).
- Over-splitting obscures the seven-stage narrative; keep runner and builders in `pipeline.py`.
- A stage helper may land at rank C after first extraction; sub-split before the next commit.
- Mid-refactor self-scan overwrites `docs/scan.json`; Phase 3 comparisons require the Phase 1 baseline artifact and explicit restore before re-scan.

## Out of scope

- Refactoring other modules (`act.py`, `llm.py`, etc.) or non-pipeline rank-C hotspots elsewhere.
- Changing gate modes, LLM prompts, ticket workflow, or checkpoint storage format.
- New syrupy snapshots or direct unit tests for `_RadarLoopRunner` unless an extraction needs a focused builder test (prefer existing integration characterization).
- Rank-B optimization of functions already ≤ 10.
- Moving runner code to a new module file.

## Audit

> [!warning] Audit verdict: revise
> Radon/scan.json baselines (cmd_loop CC 19, write_analysis CC 11, derived cc_by_file 30, churn 10 vs stale tkt-0006), Fowler playbook, baseline-restore re-scan, and regression test names align with the repo; fix verification wording and add extraction risks before human review.
> - Phase 3 verification overstates `docs/index.md`: per-file movers come from `compute_delta` → `cc_movers`, but `trend_callout` only renders the top 3 by |diff|; `repo_scan/radar/pipeline.py` at −30 may be absent if larger movers exist on the same branch—assert derived `cc_by_file` (baseline artifact vs post-scan `scan.json`) instead of requiring a visible index callout line.
> - Acceptance table says `ranking[].complexity` 'drops' but does not pin the target (30 → 0, or pipeline row absent from `complexity[]`); sibling tkt-0009 audit treated that as a required ticket-facing metric.
> - Risks omit the stage-5 audit→revise→re-audit branch (runs only on fresh audit, not checkpoint resume); extracting it incorrectly breaks `test_loop_revision_round` while leaving resume paths green.
> - Risks omit `progress()` banner text/stage labels—the hub/daemon surface depends on them (`[n/7]` steps, gate-wait subtitles); runner extraction must preserve calls verbatim.
> - Risks omit concurrent metric drift: if other rank-C hotspots change on the branch between Phase 1 and Phase 3, global `hotspot_functions` Δ and `cc_movers` ordering can confound pipeline-only attribution despite baseline restore.
> - Phase 2b markdown contract lists empty-ingested and wikilink stems but not the empty-findings `_none_` sentinel (`write_analysis` line 127 precedence)—builders must preserve it for observable equivalence.

## Provenance

- analysis: [[2026-06-10-refactor-repo-scan-radar-pipeline-py-cc-analysis]]
