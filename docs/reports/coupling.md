# Change coupling
_Generated 2026-06-10 15:07 UTC_

Files that change together (≥4 shared commits, ≥50% degree).
Coupled pairs **without** an import edge are hidden seams — an implicit
contract the dependency graph can't see.

> [!warning] 4 hidden seam(s): coupled in history, no import edge
> - `repo_scan/radar/cli.py` ↔ `repo_scan/radar/gates.py` (80% over 4 commits)
> - `repo_scan/hub/daemon.py` ↔ `tests/test_act.py` (70% over 7 commits)
> - `repo_scan/hub/daemon.py` ↔ `tests/test_hub.py` (60% over 6 commits)
> - `repo_scan/config.py` ↔ `repo_scan/hub/daemon.py` (56% over 7 commits)

| File A | File B | Shared commits | Degree | Import edge |
|--------|--------|----------------|--------|-------------|
| `repo_scan/hub/server.py` | `repo_scan/hub/ui.py` | 7 | 88% | yes |
| `repo_scan/radar/cli.py` | `repo_scan/radar/gates.py` | 4 | 80% | **none — seam** |
| `repo_scan/hub/daemon.py` | `tests/test_act.py` | 7 | 70% | **none — seam** |
| `repo_scan/radar/pipeline.py` | `tests/test_radar_pipeline.py` | 6 | 67% | yes |
| `repo_scan/hub/daemon.py` | `tests/test_hub.py` | 6 | 60% | **none — seam** |
| `repo_scan/radar/act.py` | `tests/test_act.py` | 4 | 57% | yes |
| `repo_scan/config.py` | `repo_scan/hub/daemon.py` | 7 | 56% | **none — seam** |
| `repo_scan/scanner.py` | `repo_scan/writers.py` | 5 | 50% | yes |
| `repo_scan/graphs.py` | `repo_scan/scanner.py` | 4 | 50% | yes |
| `repo_scan/radar/gates.py` | `repo_scan/radar/pipeline.py` | 4 | 50% | yes |
