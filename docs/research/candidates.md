# RADAR candidates
_Generated 2026-06-10 03:06 UTC_

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
    scanner.py: [0.98, 0.98]
    test_radar_pipeli…: [0.40, 0.68]
    pipeline.py: [0.50, 0.98]
```

| File | Commits | Complexity | Tests | Priority |
|------|---------|------------|-------|----------|
| `repo_scan/scanner.py` | 10 | 28 | **no** (2x) | 560 |
| `tests/test_radar_pipeline.py` | 4 | 19 | **no** (2x) | 152 |
| `repo_scan/radar/pipeline.py` | 5 | 28 | yes | 140 |
