# repo-scan — repo digest
_Generated 2026-06-10 00:00 UTC by repo-scan 0.2.0. Single-file context for LLM use._

**Remote:** https://github.com/hhleroy97/repo-scan.git  |  **Branch:** main  |  **Last commit:** 950e289 feat: Obsidian graph support — frontmatter metadata and provenance wikilinks across radar artifacts
**Files:** 65  |  **Lines:** 3,739  |  **Languages:** PY: 33

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

## Most important files

- `repo_scan/radar/pipeline.py` (score 51.3, pagerank 0.0778, 286 lines, imported by 2, 2 commits)
- `repo_scan/radar/sources.py` (score 46.1, pagerank 0.0681, 166 lines, imported by 2, 2 commits)
- `repo_scan/ranking.py` (score 42.9, pagerank 0.0649, 106 lines, imported by 1, 0 commits)
- `tests/test_radar_pipeline.py` (score 40.6, pagerank 0.0456, 113 lines, imported by 0, 2 commits)
- `repo_scan/config.py` (score 36.5, pagerank 0.1198, 42 lines, imported by 5, 0 commits)
- `repo_scan/complexity.py` (score 35.1, pagerank 0.1166, 29 lines, imported by 3, 0 commits)
- `repo_scan/radar/fetchers.py` (score 35.0, pagerank 0.0585, 170 lines, imported by 1, 2 commits)
- `repo_scan/radar/research.py` (score 32.9, pagerank 0.0552, 136 lines, imported by 1, 2 commits)
- `setup.py` (score 30.5, pagerank 0.0000, 13 lines, imported by 0, 5 commits)
- `pyproject.toml` (score 30.5, pagerank 0.0000, 14 lines, imported by 0, 5 commits)
- `tests/test_radar_ingest.py` (score 30.2, pagerank 0.0456, 141 lines, imported by 0, 2 commits)
- `repo_scan/graphs.py` (score 28.9, pagerank 0.0000, 111 lines, imported by 0, 0 commits)
- `repo_scan/writers.py` (score 28.0, pagerank 0.0000, 274 lines, imported by 0, 0 commits)
- `README.md` (score 24.0, pagerank 0.0000, 0 lines, imported by 0, 4 commits)
- `repo_scan/radar/gates.py` (score 21.9, pagerank 0.0649, 85 lines, imported by 1, 0 commits)

## Structure

```
repo-scan/
├── docs/
│   ├── architecture/
│   │   └── dependency-graph.md
│   ├── changelog/
│   │   ├── 2026-06-09-loop.md
│   │   ├── 2026-06-09-obsidian-graph.md
│   │   ├── 2026-06-09-pagerank-ranking.md
│   │   ├── 2026-06-09-phase-a.md
│   │   ├── 2026-06-09-phase-a2-split.md
│   │   ├── 2026-06-09-phase-b1-ingest.md
│   │   ├── 2026-06-09-phase-b2-research.md
│   │   ├── 2026-06-09-phase-b3-loop.md
│   │   └── 2026-06-09-phase-b4-autonomy.md
│   ├── reports/
│   │   ├── calls.md
│   │   ├── dependencies.md
│   │   └── health.md
│   ├── research/
│   │   ├── analysis/
│   │   ├── pending/
│   │   ├── runs/
│   │   ├── sources/
│   │   ├── candidates.md
│   │   ├── decisions.md
│   │   ├── index.md
│   │   └── tags.md
│   ├── specs/
│   │   └── 2026-06-09-should-repo-scan-replace-its-heuristic-i-spec.md
│   ├── digest.md
│   ├── index.md
│   ├── RADAR_CONTEXT.md
│   └── scan.json
├── repo_scan/
│   ├── radar/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── fetchers.py
│   │   ├── gates.py
│   │   ├── llm.py
│   │   ├── pipeline.py
│   │   ├── research.py
│   │   └── sources.py
│   ├── __init__.py
│   ├── churn.py
│   ├── cli.py
│   ├── complexity.py
│   ├── config.py
│   ├── digest.py
│   ├── graphs.py
│   ├── handoff.py
│   ├── hooks.py
│   ├── identity.py
│   ├── languages.py
│   ├── ranking.py
│   ├── scanner.py
│   ├── utils.py
│   └── writers.py
├── repo_scan.egg-info/
│   ├── dependency_links.txt
│   ├── entry_points.txt
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   └── top_level.txt
├── tests/
│   ├── conftest.py
│   ├── fake_llm.py
│   ├── test_phase_a.py
│   ├── test_radar_full.py
│   ├── test_radar_gates.py
│   ├── test_radar_ingest.py
│   ├── test_radar_llm.py
│   ├── test_radar_pipeline.py
│   └── test_scan.py
├── .gitignore
├── .repo-scan.json
├── pyproject.toml
├── README.md
├── setup.py
└── Untitled.canvas
```

## Complexity hotspots

- `repo_scan/scanner.py::scan` rank C (CC 20)
- `repo_scan/graphs.py::get_python_dep_edges` rank C (CC 19)
- `repo_scan/ranking.py::rank_files` rank C (CC 19)
- `repo_scan/writers.py::write_index` rank C (CC 19)
- `tests/test_radar_pipeline.py::test_loop_happy_path_auto_gates` rank C (CC 19)
- `repo_scan/languages.py::get_line_counts` rank C (CC 16)
- `repo_scan/ranking.py::_pagerank` rank C (CC 15)
- `repo_scan/identity.py::detect_entry_points` rank C (CC 14)

## Most changed files

- `docs/architecture/dependency-graph.md` (5 commits)
- `docs/index.md` (5 commits)
- `docs/reports/calls.md` (5 commits)
- `docs/reports/dependencies.md` (5 commits)
- `docs/reports/health.md` (5 commits)
- `pyproject.toml` (5 commits)
- `setup.py` (5 commits)
- `README.md` (4 commits)
