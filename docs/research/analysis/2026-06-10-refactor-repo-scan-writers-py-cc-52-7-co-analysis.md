---
type: "analysis"
problem: "Refactor repo_scan/writers.py (CC 52, 7 commits, untested). `repo_scan/writers.py` is both high-churn (7 commits) and high-complexity (total CC 52) with no matching test file. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["url-refactoring-com-catalog-extractfunction-html"]
generated_at: "2026-06-10 01:54 UTC"
linked_files: ["repo_scan/writers.py", "tests/test_visuals.py"]
---

# Analysis — Refactor repo_scan/writers.py (CC 52, 7 commits, untested). `repo_scan/writers.py` is both high-churn (7 commits) and high-complexity (total CC 52) with no matching test file. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 01:54 UTC — confidence: high_

## Findings

- writers.py aggregates CC 52 across ~15 functions, but complexity concentrates in write_health_report (CC ~28) and write_index (CC ~24)—both are long inline markdown assemblers with nested optional-section conditionals, matching the 'long method' smell that Extract Function / Extract Method is designed to address.
- The module mixes three concerns: Mermaid/callout visual helpers (partially covered in tests/test_visuals.py), seven report assemblers invoked sequentially from scanner.py, and scan.json/AGENTS.md sidecar writers; only helpers and write_agents_md have direct unit coverage, leaving most refactor surface unprotected despite RADAR priority (7 commits × CC 52 × untested).
- Existing integration tests assert fragments of generated markdown via full repo_scan.scan() but do not pin whole artifacts for write_coupling_report, write_scan_json, write_candidates, or the full bodies of write_health_report/write_index, so structural changes lack a regression baseline.
- Extract Function is the right first-pass technique: lift cohesive blocks (directory rollup, complexity/churn/behavior tables, alert callouts, index overview/ranking sections, scan.json payload assembly) into well-named pure helpers that return list[str] or dict, shrinking parent CC without changing output semantics.
- pytest-html's assembly/template/render split is a useful structural reference—separate data preparation from section rendering from write_doc I/O—without adopting HTML or a template engine for markdown-native outputs.
- Syrupy fits repo-scan: pytest is already the runner, snapshots commit alongside tests, missing snapshots fail the suite, and it can be a dev-only dependency preserving runtime zero-dependency constraints—ideal for characterization tests over health.md, index.md, coupling.md, candidates.md, and scan.json after normalizing volatile git/timestamp fields.
- scanner.py ↔ writers.py is a hidden seam (67% change coupling, no import edge); keeping public write_* signatures stable during extraction avoids widening that implicit contract.

## Recommendation

Before any structural refactor, add syrupy characterization snapshots for every write_* artifact using a fixed fixture repo and normalized volatile metadata (timestamps, branch, commit, remote), establishing a regression baseline. Then apply Extract Function to write_health_report and write_index first—extract pure section builders (e.g. health_sections, index_sections, scan_payload) while leaving thin write_* wrappers that call write_doc—following a data→sections→write split without introducing a template engine on the first pass.

## Risks

- Snapshots will be brittle unless timestamps, git branch/commit, and remote URL are stubbed or stripped via syrupy matchers/serializers before assertion.
- Over-extraction into many tiny helpers or a premature template layer could increase churn without lowering CC if section builders remain conditional-heavy.
- write_scan_json embeds live cfg and git metadata—full-file snapshot drift may mask intentional schema changes unless schema_version and field subsets are tested separately.
- Adding syrupy requires a new dev dependency and pyproject dev-deps wiring; CI must install it alongside pytest.
- Indirect fragment tests in test_visuals.py may duplicate or conflict with new snapshot tests unless scopes are clearly split (unit helpers vs. full artifact golden files).
- Refactoring the scanner↔writers seam without stable entry points risks breaking coordinated changes that currently happen across both modules.

## Evidence

- [[url-refactoring-com-catalog-extractfunction-html\|Extract Function]]
- research run: [[2026-06-10-refactor-repo-scan-writers-py-cc-52-7-co]]
