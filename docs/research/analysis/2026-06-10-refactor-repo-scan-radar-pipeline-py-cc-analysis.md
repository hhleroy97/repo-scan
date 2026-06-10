---
type: "analysis"
problem: "Refactor repo_scan/radar/pipeline.py (CC 11, 3 commits). `repo_scan/radar/pipeline.py` is both high-churn (3 commits) and high-complexity (total CC 11). Acceptance criteria: Complexity of every function below rank C; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["url-refactoring-com-catalog-replacefunctionwithcommand-html", "url-refactoring-com-catalog-replacenestedconditionalwithguardcla"]
generated_at: "2026-06-10 07:59 UTC"
---

# Analysis — Refactor repo_scan/radar/pipeline.py (CC 11, 3 commits). `repo_scan/radar/pipeline.py` is both high-churn (3 commits) and high-complexity (total CC 11). Acceptance criteria: Complexity of every function below rank C; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 07:59 UTC — confidence: high_

## Findings

- Radon identifies exactly two rank-C hotspots in `repo_scan/radar/pipeline.py`: `cmd_loop` (CC 19) and `write_analysis` (CC 11); all other functions are already rank A or B, so the acceptance criterion reduces to refactoring those two.
- `cmd_loop` is a classic Replace Function with Command candidate: ~140 lines orchestrating seven stages while threading shared mutable state (`ckpt`, `result`, `gates_log`, `ingested`, `analysis`, `spec_text`, `audit`) that blocks clean Extract Method without long parameter lists.
- Checkpoint-resume branches (`if "ingested" in ckpt` / `if "analysis" in ckpt` / etc.) and gate early-exit paths (`if not gate(...): return 2`) are the main CC drivers in `cmd_loop`; Replace Nested Conditional with Guard Clauses maps directly to extracting per-stage `_run_or_resume_*` helpers that return early on resume.
- `write_analysis` CC comes from layered conditionals assembling markdown (risks block, empty ingested list, optional `run_log_path`); flattening with guard-style early appends or small pure `_analysis_body_*` builders should drop it below rank C without changing output shape.
- The sibling ticket `tkt-0009` (test_radar_pipeline refactor) already defines a proven repo playbook: Phase 1 radon + scan.json/`health.md` baseline, incremental extractions with green `pytest tests/test_radar_pipeline.py tests/test_hub.py tests/test_tickets_workflow.py tests/test_radar_full.py`, Phase 3 dogfood re-scan for trend delta.
- Public surface (`cmd_loop`, `cmd_full`, `ticket_problem`, `spec_for_problem`, `pick_candidate`) and the 0/1/2 return-code contract must remain stable; existing integration tests exercise full loop, gate pause/resume, revision round, and ticket workflow—behavior-preserving refactors only.
- File churn (5 commits in current `scan.json`) correlates with loop feature growth (checkpoints, gates, ticket integration); a command object localizes future stage edits and should reduce repeat hotspot accumulation.

## Recommendation

Introduce a private `RadarLoopRunner` (Replace Function with Command) that holds `root`, `cfg`, `problem`, `ckpt`, `result`, and `gates_log` as instance state and exposes one method per RADAR stage, each using guard-clause resume helpers instead of nested `if/else` checkpoint blocks. In the same pass, split `write_analysis` markdown assembly into small pure section builders. Verify with baseline radon, green pytest after each extraction, then a self-scan confirming no function exceeds rank B (CC ≤ 10) and `health.md`/`scan.json` complexity rows for `cmd_loop` and `write_analysis` drop versus baseline.

## Risks

- Checkpoint key semantics (`ingested`, `analysis`, `analysis_path`, `spec_text`, `audit`, `run_log`) must stay identical or paused loops will re-run expensive LLM stages or skip required artifacts.
- Gate stop vs reject branching (`_gate_paused` / `_finish_loop`) is easy to break when flattening early returns—return code 2 and changelog `outcome` must remain unchanged for pause and reject scenarios.
- Over-splitting into many tiny classes could obscure the linear 7-stage narrative; keep stage methods colocated in one runner module/class rather than scattering across new files.
- Derived file-level CC in `scan.json` sums all function complexities—trend delta verification must target per-function `complexity[]` rows and `health.md` hotspot lines, not aggregate file score alone.

## Evidence

- [[url-refactoring-com-catalog-replacefunctionwithcommand-html\|Replace Function with Command]]
- [[url-refactoring-com-catalog-replacenestedconditionalwithguardcla\|Replace Nested Conditional with Guard Clauses]]
- research run: [[2026-06-10-refactor-repo-scan-radar-pipeline-py-cc]]
