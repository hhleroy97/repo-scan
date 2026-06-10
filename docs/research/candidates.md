# RADAR candidates
_Generated 2026-06-10 00:09 UTC_

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
    ranking.py: [0.98, 0.79]
    digest.py: [0.98, 0.30]
```

| File | Commits | Complexity | Priority |
|------|---------|------------|----------|
| `repo_scan/writers.py` | 2 | 43 | 86 |
| `repo_scan/ranking.py` | 2 | 34 | 68 |
| `repo_scan/digest.py` | 2 | 13 | 26 |
