---
type: "research-run"
question: "Refactor repo_scan/radar/pipeline.py (CC 11, 3 commits). `repo_scan/radar/pipeline.py` is both high-churn (3 commits) and high-complexity (total CC 11). Acceptance criteria: Complexity of every function below rank C; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work."
sources: ["url-refactoring-com-catalog-replacefunctionwithcommand-html", "url-refactoring-com-catalog-replacenestedconditionalwithguardcla"]
run_at: "2026-06-10 07:58 UTC"
---

# Research run — Refactor repo_scan/radar/pipeline.py (CC 11, 3 commits). `repo_scan/radar/pipeline.py` is both high-churn (3 commits) and high-complexity (total CC 11). Acceptance criteria: Complexity of every function below rank C; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work.
_Run 2026-06-10 07:58 UTC_

**Strategy:** Reuse the repo's established refactor playbook—radon baseline plus docs/scan.json snapshot, green pytest after each extraction—without re-ingesting Feathers, Extract Method, or Split Loop already in the corpus. Target cmd_loop first via a LoopRunner/command object with per-stage methods, then Split Loop or small extractors for write_analysis's markdown assembly; verify every function CC ≤ 10 and a trend delta against the Phase 1 baseline.

## Ingested

- [[sources/url-refactoring-com-catalog-replacefunctionwithcommand-html\|Replace Function with Command]] — cmd_loop (CC 19) is a long orchestrator whose intertwined locals—ckpt, result, gates_log, ingested, analysis—block clean Extract Method, making Fowler's Replace Function with Command the canonical pattern for isolating each RADAR stage without polluting the module namespace.
- [[sources/url-refactoring-com-catalog-replacenestedconditionalwithguardcla\|Replace Nested Conditional with Guard Clauses]] — The checkpoint-resume branches (`if "ingested" in ckpt` …) and gate early-return paths that inflate cmd_loop and write_analysis CC are best flattened with guard-clause exits before deeper nesting, preserving the existing return-code contract (0/1/2).

## Failed

- `arxiv:2405.20551` — fetch failed for http://export.arxiv.org/api/query?id_list=2405.20551: <urlopen error _ssl.c:990: The handshake operation timed out>
