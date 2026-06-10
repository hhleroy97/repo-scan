---
type: "analysis"
problem: "Refactor repo_scan/graphs.py (CC 56, 3 commits, untested). `repo_scan/graphs.py` is both high-churn (3 commits) and high-complexity (total CC 56) with no matching test file. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["gh-David-OConnor-pydeps", "gh-pahen-madge"]
generated_at: "2026-06-10 03:27 UTC"
linked_files: ["repo_scan/graphs.py", "tests/test_graphs.py"]
---

# Analysis — Refactor repo_scan/graphs.py (CC 56, 3 commits, untested). `repo_scan/graphs.py` is both high-churn (3 commits) and high-complexity (total CC 56) with no matching test file. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 03:27 UTC — confidence: high_

## Findings

- graphs.py (160 lines, total CC 56) mixes three concerns: pure Mermaid rendering (edges_to_mermaid, CC 13), external-tool adapters (get_ts_dep_edges via madge, get_c_call_graph_mermaid via cflow), and intra-repo Python edge extraction (get_python_dep_edges, CC 19 — the primary hotspot).
- get_python_dep_edges uses line-by-line string heuristics (startswith import/from) rather than stdlib ast; this drives most complexity and likely misses or mis-parses relative imports, multiline imports, and parenthesized forms that mature tools resolve structurally.
- The madge integration already aligns with pahen/madge best practice: --json --extensions ts,tsx,js,jsx, src-dir discovery, and re-anchoring paths to repo root so PageRank keys match — a regression here silently breaks hub tinting.
- David-OConnor/pydeps is not a drop-in replacement (install-based PyPI resolution with server caching) but validates the design direction: resolve imports via proper parsing, not metadata/regex shortcuts; for repo-scan that means ast over regex while keeping zero runtime deps.
- Coverage is partial, not absent: edges_to_mermaid and get_python_dep_graph_mermaid have tests (test_visuals.py, test_scan.py); get_ts_dep_edges has an integration test gated on madge (test_portability.py); get_python_dep_edges and get_c_call_graph_mermaid lack dedicated unit/characterization tests — matching the ticket's 'no matching test file' intent.
- The repo's approved refactor precedent (writers, scanner specs) is snapshot-then-extract: Phase 1 locks behavior with fixture-backed golden tests and monkeypatched tool probes; Phase 2 extracts pure functions and simplifies hotspots without changing scan artifacts.
- graphs.py feeds scanner ranking via node_scores and writers' dependencies.md / architecture/dependency-graph.md; any edge-set or Mermaid-format drift propagates to PageRank tiers and health/radar signals.

## Recommendation

Follow the established two-phase pattern: first add tests/test_graphs.py with fixture repos covering Python import variants, madge JSON fixtures (monkeypatched run), cflow output fixtures, and edges_to_mermaid golden strings — no production changes. Then extract module_path helpers and an ast-based import walker to replace get_python_dep_edges regex logic, keeping madge/cflow as thin shell adapters and preserving the (src, dst) edge contract and Mermaid output byte-for-byte unless characterization reveals bugs.

## Risks

- Replacing regex with ast may change the edge set on relative imports, __init__.py packages, and conditional imports — characterization must capture current behavior before switching parsers.
- madge and cflow are optional external tools; without monkeypatching, CI coverage stays flaky or skip-gated.
- Path re-anchoring between src_dir and repo root is fragile; a refactor that moves prefix logic could break PageRank node matching without obvious test failure.
- Splitting the module may touch scanner.py import surface and __init__.py re-exports, increasing coupling blast radius during a 3-commit high-churn window.
- Focusing only on CC reduction without locking Mermaid/PageRank-tier output risks regressions in dependencies.md visuals that E2E scan tests may not isolate.

## Evidence

- [[gh-David-OConnor-pydeps\|David-OConnor/pydeps — Store dependency info for each PyPi package]]
- [[gh-pahen-madge\|pahen/madge — Create graphs from your CommonJS, AMD or ES6 module dependencies]]
- research run: [[2026-06-10-refactor-repo-scan-graphs-py-cc-56-3-com]]
