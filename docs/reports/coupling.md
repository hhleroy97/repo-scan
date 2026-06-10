# Change coupling
_Generated 2026-06-10 09:06 UTC_

Files that change together (≥4 shared commits, ≥50% degree).
Coupled pairs **without** an import edge are hidden seams — an implicit
contract the dependency graph can't see.

> [!warning] 7 hidden seam(s): coupled in history, no import edge
> - `repo_scan/hub/server.py` ↔ `repo_scan/hub/ui.py` (88% over 7 commits)
> - `repo_scan/radar/cli.py` ↔ `repo_scan/radar/gates.py` (80% over 4 commits)
> - `repo_scan/config.py` ↔ `repo_scan/hub/daemon.py` (58% over 7 commits)
> - `repo_scan/scanner.py` ↔ `repo_scan/writers.py` (53% over 5 commits)
> - `repo_scan/radar/gates.py` ↔ `repo_scan/radar/pipeline.py` (53% over 4 commits)

| File A | File B | Shared commits | Degree | Import edge |
|--------|--------|----------------|--------|-------------|
| `repo_scan/hub/server.py` | `repo_scan/hub/ui.py` | 7 | 88% | **none — seam** |
| `repo_scan/radar/cli.py` | `repo_scan/radar/gates.py` | 4 | 80% | **none — seam** |
| `repo_scan/radar/pipeline.py` | `tests/test_radar_pipeline.py` | 6 | 71% | yes |
| `repo_scan/hub/daemon.py` | `tests/test_act.py` | 6 | 67% | yes |
| `repo_scan/radar/act.py` | `tests/test_act.py` | 4 | 62% | yes |
| `repo_scan/config.py` | `repo_scan/hub/daemon.py` | 7 | 58% | **none — seam** |
| `repo_scan/hub/daemon.py` | `tests/test_hub.py` | 5 | 56% | yes |
| `repo_scan/scanner.py` | `repo_scan/writers.py` | 5 | 53% | **none — seam** |
| `repo_scan/radar/gates.py` | `repo_scan/radar/pipeline.py` | 4 | 53% | **none — seam** |
| `repo_scan/hub/daemon.py` | `repo_scan/radar/gates.py` | 4 | 50% | **none — seam** |
| `repo_scan/radar/act.py` | `repo_scan/radar/pipeline.py` | 4 | 50% | **none — seam** |
