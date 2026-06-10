---
id: "gh-adamtornhill-code-maat"
type: "github"
url: "https://github.com/adamtornhill/code-maat"
raw_url: "https://github.com/adamtornhill/code-maat"
tags: ["adam-tornhill", "behavioral-code-analysis", "clojure", "code-churn", "git-log-analysis", "logical-coupling", "ownership-metrics", "repo", "repository-mining", "technical-debt", "version-control-mining"]
linked_files: []
relevance: "For a repo-scan project, Code Maat offers a proven, scriptable pipeline to turn Git history into coupling, ownership, and churn metrics that can flag hotspots, implicit dependencies, and maintenance risks worth prioritizing in scans or reports."
ingested_at: "2026-06-10 07:45 UTC"
---

# adamtornhill/code-maat — A command line tool to mine and analyze data from version-control systems

## Summary

Code Maat is a Clojure command-line tool by Adam Tornhill for mining and analyzing version-control history to study how code evolves over time. It supports Git, Mercurial, SVN, Perforce, and TFS logs and runs analyses such as logical coupling, author ownership, churn, and communication patterns. It underpins behavioral code analysis ideas from *Your Code as a Crime Scene* and *Software Design X-Rays*, and later evolved into CodeScene.

## Key claims

- VCS history reveals technical, social, and organizational patterns that a single code snapshot cannot.
- Analyzing change patterns can surface design issues, bottlenecks, and refactoring opportunities before they become costly.
- Logical coupling identifies modules that tend to change together, indicating hidden implicit dependencies.
- Modules touched by more distinct authors correlate with higher communication overhead and defect risk.
- Code Maat accepts pre-generated VCS log files and outputs CSV metrics via analyses including coupling, authors, churn, age, ownership, and summary.
- Git log generation supports legacy (`git`) and preferred faster (`git2`) formats, with pathspec exclusions to reduce noise from vendor or non-code paths.
- The tool is GPL v3 licensed, built with Leiningen, and also available as a standalone JAR or Docker image.

## Notes

_yours to annotate_
