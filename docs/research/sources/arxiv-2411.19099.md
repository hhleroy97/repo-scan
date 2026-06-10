---
id: "arxiv-2411.19099"
type: "arxiv"
url: "https://arxiv.org/abs/2411.19099"
raw_url: "https://arxiv.org/pdf/2411.19099"
tags: ["arxiv", "change-impact-analysis", "co-change-analysis", "dependency-prediction", "java", "learning-to-rank", "paper", "pull-requests", "random-forest", "software-maintenance"]
linked_files: []
relevance: "A repo-scan or change-impact tool could use similar PR-level co-change ranking to suggest related methods or files when a developer edits code, improving review scope and reducing missed coupled changes."
ingested_at: "2026-06-10 18:49 UTC"
---

# Enhancing Software Maintenance: A Learning to Rank Approach for Co-changed Method Identification

## Summary

This arxiv paper proposes a learning-to-rank approach for identifying co-changed methods—methods that tend to be modified together—at the pull-request level rather than individual commits. It combines source code features with change history and evaluates multiple models on 150 Java projects with over 634,000 pull requests. The work matters because accurate co-change prediction can reduce false positives in maintenance tooling and help teams understand dependencies when making changes.

## Key claims

- Co-changed methods are important for understanding software dependencies, but existing approaches often return large result sets with high false positive rates.
- Analyzing co-change at the pull-request level captures related modifications more comprehensively than using individual commits alone.
- A learning-to-rank model combining source code features and change history can predict and rank co-changed methods for a given change.
- On 150 open-source Java projects (41.5M LOC, 634,216 pull requests), Random Forest achieved the best NDCG@5, outperforming other models by 2.5–12.8%.
- The proposed approach outperformed baselines including file proximity, code clones, FCP2Vec, and StarCoder 2 by 4.7–537.5%.
- Models trained on 90–180 days of history performed consistently, while accuracy declined after 60 days without retraining, suggesting bi-monthly retraining is needed.

## Notes

_yours to annotate_
