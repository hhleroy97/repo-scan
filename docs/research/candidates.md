# RADAR candidates
_Generated 2026-06-10 00:38 UTC_

Files that are both high-churn and high-complexity — the most valuable
targets for external research. Consumed by `radar` as a trigger feed.

```mermaid
quadrantChart
    title Candidate zone (top-right)
    x-axis Low churn --> High churn
    y-axis Low complexity --> High complexity
    quadrant-1 RADAR candidates
    quadrant-2 Complex but stable
    quadrant-3 Quiet
    quadrant-4 Hot but simple
    writers.py: [0.86, 0.79]
    scanner.py: [0.98, 0.43]
    graphs.py: [0.43, 0.98]
    languages.py: [0.43, 0.32]
    sources.py: [0.43, 0.25]
    pipeline.py: [0.43, 0.20]
```

| File | Commits | Complexity | Tests | Priority |
|------|---------|------------|-------|----------|
| `repo_scan/writers.py` | 6 | 44 | **no** (2x) | 528 |
| `repo_scan/scanner.py` | 7 | 24 | **no** (2x) | 336 |
| `repo_scan/graphs.py` | 3 | 56 | **no** (2x) | 336 |
| `repo_scan/languages.py` | 3 | 18 | **no** (2x) | 108 |
| `repo_scan/radar/sources.py` | 3 | 14 | **no** (2x) | 84 |
| `repo_scan/radar/pipeline.py` | 3 | 11 | yes | 33 |
