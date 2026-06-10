# RADAR candidates
_Generated 2026-06-10 09:06 UTC_

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
    daemon.py: [0.98, 0.98]
    pipeline.py: [0.91, 0.79]
```

| File | Commits | Complexity | Tests | Priority |
|------|---------|------------|-------|----------|
| `repo_scan/hub/daemon.py` | 11 | 38 | **no** (2x) | 836 |
| `repo_scan/radar/pipeline.py` | 10 | 30 | yes | 300 |
