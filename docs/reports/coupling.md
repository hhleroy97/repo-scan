# Change coupling
_Generated 2026-06-10 02:07 UTC_

Files that change together (≥4 shared commits, ≥50% degree).
Coupled pairs **without** an import edge are hidden seams — an implicit
contract the dependency graph can't see.

> [!warning] 2 hidden seam(s): coupled in history, no import edge
> - `pyproject.toml` ↔ `setup.py` (100% over 5 commits)
> - `repo_scan/scanner.py` ↔ `repo_scan/writers.py` (59% over 5 commits)

| File A | File B | Shared commits | Degree | Import edge |
|--------|--------|----------------|--------|-------------|
| `pyproject.toml` | `setup.py` | 5 | 100% | **none — seam** |
| `repo_scan/scanner.py` | `repo_scan/writers.py` | 5 | 59% | **none — seam** |
