---
id: "url-www-ime-usp-br-gerosa-papers-changecoupling-pdf"
type: "url"
url: "https://www.ime.usp.br/~gerosa/papers/changecoupling.pdf"
raw_url: "https://www.ime.usp.br/~gerosa/papers/changecoupling.pdf"
tags: ["architecture-analysis", "article", "association-rules", "change-coupling", "connascence", "empirical-software-engineering", "git-history", "hidden-dependencies", "impact-analysis", "logical-dependencies", "refactoring", "software-evolution"]
linked_files: []
relevance: "Directly grounds repo-scan's git-history coupling analysis, degree thresholds, hidden-seam detection, and coupling visualizations as established practice for surfacing implicit module dependencies that static import graphs miss."
ingested_at: "2026-06-10 21:08 UTC"
---

# https://www.ime.usp.br/~gerosa/papers/changecoupling.pdf

## Summary

This source is Chapter 11 of a software-evolution reference by Oliva and Gerosa on change coupling—the tendency for software artifacts to be modified together over time, revealing implicit or evolutionary dependencies not visible in static structure. It surveys why artifacts co-change (grounded in Page-Jones's connascence), how to detect coupling from version-control history (raw co-change counting, association rules, and time-series methods), and major applications including change-impact prediction, refactoring guidance, architecture evaluation, and team coordination analysis. It also warns that commit practices such as tangled, incomplete, or merge commits can produce noisy or missing coupling signals.

## Key claims

- Change coupling is an implicit evolutionary dependency between artifacts that frequently change together; it is also called logical, evolutionary, or historical coupling.
- File-level change coupling can reveal hidden relationships absent from code structure or documentation, using only commit co-change data without parsing source code.
- Artifacts co-change largely because of connascence—elements that must change together to preserve correctness, whether via direct dependency, transitive dependency, or shared external constraints.
- Change coupling is often more effective than structural coupling for predicting change propagation and for recovering developer coordination requirements.
- Empirical studies link change coupling to defect proneness and software quality, sometimes more strongly than structural coupling alone.
- The dominant detection model treats two files as coupled when they appear in the same commit; strength can be quantified via co-change matrices, association-rule metrics (support, confidence, lift), or time-series similarity.
- Accurate coupling detection is hard because overloaded commits create artificial couplings, incomplete or split commits create missing couplings, and merge commits inflate spurious links.
- Primary applications include change-impact analysis ('what else must change?'), discovery of design flaws and refactoring hotspots, architecture evaluation against intended modularity, and socio-technical coordination analysis.

## Notes

_yours to annotate_
