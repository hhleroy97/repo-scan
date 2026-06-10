---
id: "url-wiki-apidesign-org-wiki-configurationobject"
type: "url"
url: "https://wiki.apidesign.org/wiki/ConfigurationObject"
raw_url: "https://wiki.apidesign.org/wiki/ConfigurationObject"
tags: ["api-design", "api-evolution", "article", "backward-compatibility", "builder-pattern", "configuration-object", "cumulative-factory", "java", "java-beans", "javascript", "options-object"]
linked_files: ["repo_scan/config.py"]
relevance: "When designing repo-scan CLI flags, scan configuration, or radar/LLM settings, prefer a single options object or structured config over growing positional parameters so new scan dimensions and knobs can be added without breaking callers."
ingested_at: "2026-06-10 17:14 UTC"
---

# ConfigurationObject

## Summary

This APIDesign article explains the ConfigurationObject pattern: replacing growing positional function arguments with a single object of named properties so APIs can evolve without breaking call sites. It traces the typical failure mode from one argument to many, then compares Java realizations—JavaBeans, fluent builders, and CumulativeFactory—and argues builders match JavaScript ergonomics while preserving type safety.

## Key claims

- APIs often start with a single argument and accumulate positional parameters until the interface becomes hard to use and evolve.
- Named properties on a configuration object are easier to extend than adding more positional arguments in a fixed order.
- JavaBean-style getters and setters are familiar to Java developers but are verbose compared to JavaScript object-literal usage.
- A fluent builder with chained property methods can match JavaScript ConfigurationObject ergonomics while keeping Java type safety.
- Prefer CumulativeFactory (immutable) when the build step is final; prefer a mutable builder when the object must be observed or modified after build.
- Annotation-driven code generation (e.g. DukeScript @Model) can reduce boilerplate for defining configuration objects without improving end-user API ergonomics by itself.

## Notes

_yours to annotate_
