---
type: "research-run"
question: "Refactor repo_scan/hub/daemon.py (CC 38, 11 commits, untested). `repo_scan/hub/daemon.py` is both high-churn (11 commits) and high-complexity (total CC 38) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work."
sources: ["url-refactoring-com-catalog-decomposeconditional-html", "url-refactoring-com-catalog-consolidateduplicateconditionalfragm"]
run_at: "2026-06-10 13:15 UTC"
---

# Research run — Refactor repo_scan/hub/daemon.py (CC 38, 11 commits, untested). `repo_scan/hub/daemon.py` is both high-churn (11 commits) and high-complexity (total CC 38) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work.
_Run 2026-06-10 13:15 UTC_

**Strategy:** Follow the repo's characterization-then-extract playbook already used on writers/scanner: radon baseline first, migrate/extend hub daemon tests into a dedicated test_daemon.py covering untested paths (over_budget, reclaim_orphan_runs, act fan-out), then decompose daemon_tick by phase and unify the duplicated run-outcome handlers before re-running radon and scan.json trend delta.

## Ingested

- [[sources/url-refactoring-com-catalog-decomposeconditional-html\|Decompose Conditional]] — daemon_tick is a rank-E sequential conditional (resume → scan → budget → act fan-out → loop fan-out); Decompose Conditional is the canonical Fowler move for extracting each phase into a helper without changing scheduler behavior.
- [[sources/url-refactoring-com-catalog-consolidateduplicateconditionalfragm\|Slide Statements]] — _run_loop and _run_act share nearly identical rc→status/notify branches; consolidating that duplication is a concrete, test-preserving CC reduction before further extraction from the orchestrator.

## Failed

- `github:radon-sh/radon` — fetch failed for https://api.github.com/repos/radon-sh/radon: HTTP Error 404: Not Found
