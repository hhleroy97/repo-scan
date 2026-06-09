# repo-scan — repo digest
_Generated 2026-06-09 22:54 UTC by repo-scan 0.2.0. Single-file context for LLM use._

**Remote:** https://github.com/hhleroy97/repo-scan.git  |  **Branch:** main  |  **Last commit:** 6a140a5 feat: phase B3 — file-backed gates and full radar loop pipeline
**Files:** 53  |  **Lines:** 3,432  |  **Languages:** PY: 33

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

## Most important files

- `repo_scan/config.py` (score 36.5, 42 lines, imported by 5, 0 commits)
- `setup.py` (score 30.5, 13 lines, imported by 0, 5 commits)
- `pyproject.toml` (score 30.5, 14 lines, imported by 0, 5 commits)
- `repo_scan/graphs.py` (score 29.1, 111 lines, imported by 0, 0 commits)
- `repo_scan/radar/pipeline.py` (score 29.1, 248 lines, imported by 2, 1 commits)
- `repo_scan/writers.py` (score 28.5, 272 lines, imported by 0, 0 commits)
- `repo_scan/handoff.py` (score 26.7, 156 lines, imported by 3, 0 commits)
- `repo_scan/radar/sources.py` (score 26.6, 132 lines, imported by 2, 0 commits)
- `tests/test_radar_pipeline.py` (score 16.9, 102 lines, imported by 0, 1 commits)
- `repo_scan/radar/llm.py` (score 16.3, 90 lines, imported by 1, 1 commits)
- `repo_scan/radar/gates.py` (score 16.1, 85 lines, imported by 1, 1 commits)
- `repo_scan/scanner.py` (score 15.7, 103 lines, imported by 0, 0 commits)
- `repo_scan/radar/cli.py` (score 14.9, 80 lines, imported by 0, 2 commits)
- `repo_scan/radar/fetchers.py` (score 13.1, 167 lines, imported by 1, 0 commits)
- `README.md` (score 12.0, 0 lines, imported by 0, 2 commits)

## Structure

```
repo-scan/
├── docs/
│   ├── architecture/
│   │   └── dependency-graph.md
│   ├── changelog/
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
│   │   ├── sources/
│   │   ├── candidates.md
│   │   ├── index.md
│   │   └── tags.md
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
└── setup.py
```

## Complexity hotspots

- `repo_scan/scanner.py::scan` rank C (CC 20)
- `repo_scan/graphs.py::get_python_dep_edges` rank C (CC 19)
- `repo_scan/writers.py::write_index` rank C (CC 19)
- `repo_scan/languages.py::get_line_counts` rank C (CC 16)
- `repo_scan/ranking.py::rank_files` rank C (CC 16)
- `repo_scan/identity.py::detect_entry_points` rank C (CC 14)
- `repo_scan/digest.py::write_digest` rank C (CC 13)
- `repo_scan/radar/sources.py::rebuild_research_index` rank C (CC 13)

## Most changed files

- `pyproject.toml` (5 commits)
- `setup.py` (5 commits)
- `docs/architecture/dependency-graph.md` (3 commits)
- `docs/index.md` (3 commits)
- `docs/reports/calls.md` (3 commits)
- `docs/reports/dependencies.md` (3 commits)
- `docs/reports/health.md` (3 commits)
- `repo_scan.py` (3 commits)
