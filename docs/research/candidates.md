# RADAR candidates
_Generated 2026-06-10 00:21 UTC_

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
    writers.py: [0.98, 0.98]
    scanner.py: [0.75, 0.47]
    test_radar_pipeli…: [0.75, 0.44]
    sources.py: [0.75, 0.33]
    pipeline.py: [0.75, 0.26]
```

| File | Commits | Complexity | Priority |
|------|---------|------------|----------|
| `repo_scan/writers.py` | 4 | 43 | 172 |
| `repo_scan/scanner.py` | 3 | 20 | 60 |
| `tests/test_radar_pipeline.py` | 3 | 19 | 57 |
| `repo_scan/radar/sources.py` | 3 | 14 | 42 |
| `repo_scan/radar/pipeline.py` | 3 | 11 | 33 |
