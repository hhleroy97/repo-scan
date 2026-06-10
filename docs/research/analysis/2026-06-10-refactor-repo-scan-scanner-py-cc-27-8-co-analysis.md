---
type: "analysis"
problem: "Refactor repo_scan/scanner.py (CC 27, 8 commits, untested). `repo_scan/scanner.py` is both high-churn (8 commits) and high-complexity (total CC 27) with no matching test file. Research current best practices and draft a spec for this work."
confidence: "medium"
sources: ["gh-ThoughtWorksInc-WorkingEffectivelyWithLegacyCode", "arxiv-2401.15298", "url-www-socratopia-app-library-software-engineering-craft-en-cha"]
generated_at: "2026-06-10 03:15 UTC"
---

# Analysis — Refactor repo_scan/scanner.py (CC 27, 8 commits, untested). `repo_scan/scanner.py` is both high-churn (8 commits) and high-complexity (total CC 27) with no matching test file. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 03:15 UTC — confidence: medium_

## Findings

- All three sources converge on the same sequence for untested legacy code: characterize current behavior first, then refactor under that safety net—tests are a prerequisite, not a follow-on (Feathers, Socratopia).
- `scan()` is a ~110-line orchestration monolith (CC ~28) whose existing `step()` labels already mark natural Extract Method boundaries—matching the arXiv EM-Assist finding that long multi-responsibility procedures should be decomposed into validated, behavior-preserving stage functions.
- The module is not wholly untested: `tests/test_scan.py` and several integration tests invoke `repo_scan.scan()` and assert artifact existence, but none pin intermediate pipeline state or stage outputs—leaving refactor risk concentrated inside `scan()` itself.
- A hidden change-coupling seam with `repo_scan/writers.py` (~67%, no import edge) means scanner refactors must keep `write_*` call order and signatures stable, mirroring the constraint already applied during the writers refactor.
- `collect_digest_inputs()` duplicates much of `scan()`'s collection logic without the write/ticket/radar branches—an extraction and deduplication target once characterization tests lock both entry points.
- Complexity is driven by feature-flag branches (`quiet`, `radar_enabled`, `tickets_enabled`, `include_handoff`, optional tool availability) rather than algorithmic depth; CC will only drop when conditionals move out of `scan()` into stage helpers or a context object.
- High churn (8–10 commits) on a coordination hub increases regression blast radius; characterization tests should treat full scan output (docs tree + `scan.json` subset) as the oracle, not individual helper signatures alone.
- The project's writers refactor spec establishes a proven local pattern—syrupy snapshots on deterministic fixtures, stub volatile metadata, one behavior-neutral extract commit per stage—that maps directly onto scanner work.

## Recommendation

Follow the Feathers change algorithm and the writers spec precedent: Phase 1 adds characterization tests—a fixed fixture repo with stubbed git/volatile helpers, syrupy snapshots of scan artifacts, and direct unit tests for `ranking_node_scores`, `collect_digest_inputs`, and `run_digest`—with no production changes. Phase 2 performs behavior-neutral Extract Method refactors aligned to existing `step()` boundaries, introducing a `ScanContext` (or similar) dataclass passed between stage functions, one commit per stage, re-running the full test suite after each extraction. Defer conditional simplification, digest/scan deduplication, and any signature changes until CC per function is verified below rank C and trend metrics confirm the drop.

## Risks

- Integration-level snapshots may miss stage-internal regressions that still produce superficially valid output.
- Coordinated edits with `writers.py` during parallel refactors could break the implicit orchestration contract despite stable signatures.
- Extracting helpers without relocating conditional branches will increase file churn without lowering measured CC.
- `scan()` and `collect_digest_inputs()` could diverge during partial extraction if deduplication is attempted before both paths are characterized.
- Optional-feature branches (radar, tickets, handoff, missing radon/lizard/cflow) multiply the fixture matrix needed for trustworthy characterization.
- Stubbing git and filesystem dependencies inconsistently will cause brittle snapshots or false greens, as seen in the writers spec audit.

## Evidence

- [[gh-ThoughtWorksInc-WorkingEffectivelyWithLegacyCode\|ThoughtWorksInc/WorkingEffectivelyWithLegacyCode — GitHub repository]]
- [[arxiv-2401.15298\|Together We Go Further: LLMs and IDE Static Analysis for Extract Method Refactoring]]
- [[url-www-socratopia-app-library-software-engineering-craft-en-cha\|Refactoring Under Test — The Safety Net Story | Software Engineering Craft]]
- research run: [[2026-06-10-refactor-repo-scan-scanner-py-cc-27-8-co]]
