# repo-scan — repo digest
_Generated 2026-06-09 22:39 UTC by repo-scan 0.2.0. Single-file context for LLM use._

**Remote:** https://github.com/hhleroy97/repo-scan.git  |  **Branch:** main  |  **Last commit:** 1e69bb8 chore: baseline docs/ scan output, RADAR context, ignore .obsidian
**Files:** 16  |  **Lines:** 1,652  |  **Languages:** PY: 5

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

## Most important files

- `repo_scan.py` (score 85.0, 1131 lines, imported by 2, 1 commits)
- `setup.py` (score 30.1, 12 lines, imported by 0, 2 commits)
- `pyproject.toml` (score 30.1, 13 lines, imported by 0, 2 commits)
- `README.md` (score 15.0, 0 lines, imported by 0, 1 commits)
- `tests/test_scan.py` (score 0.7, 80 lines, imported by 0, 0 commits)
- `tests/test_phase_a.py` (score 0.7, 78 lines, imported by 0, 0 commits)
- `tests/conftest.py` (score 0.2, 28 lines, imported by 0, 0 commits)

## Structure

```
repo-scan/
├── docs/
│   ├── architecture/
│   │   └── dependency-graph.md
│   ├── changelog/
│   │   └── 2026-06-09-phase-a.md
│   ├── reports/
│   │   ├── calls.md
│   │   ├── dependencies.md
│   │   └── health.md
│   ├── research/
│   ├── digest.md
│   ├── index.md
│   ├── RADAR_CONTEXT.md
│   └── scan.json
├── repo_scan.egg-info/
│   ├── dependency_links.txt
│   ├── entry_points.txt
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   └── top_level.txt
├── tests/
│   ├── conftest.py
│   ├── test_phase_a.py
│   └── test_scan.py
├── .gitignore
├── pyproject.toml
├── README.md
├── repo_scan.py
└── setup.py
```

## Complexity hotspots

- `repo_scan.py::get_python_dep_edges` rank C (CC 19)
- `repo_scan.py::write_index` rank C (CC 19)
- `repo_scan.py::rank_files` rank C (CC 16)
- `repo_scan.py::get_line_counts` rank C (CC 16)
- `repo_scan.py::scan` rank C (CC 16)
- `repo_scan.py::detect_entry_points` rank C (CC 14)
- `repo_scan.py::write_digest` rank C (CC 13)
- `repo_scan.py::get_c_call_graph_mermaid` rank C (CC 12)

## Most changed files

- `.gitignore` (2 commits)
- `HANDOFF.md` (2 commits)
- `pyproject.toml` (2 commits)
- `setup.py` (2 commits)
- `docs/RADAR_CONTEXT.md` (1 commits)
- `docs/architecture/dependency-graph.md` (1 commits)
- `docs/index.md` (1 commits)
- `docs/reports/calls.md` (1 commits)
