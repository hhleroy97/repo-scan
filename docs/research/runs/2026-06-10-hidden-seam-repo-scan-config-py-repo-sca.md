---
type: "research-run"
question: "Hidden seam: repo_scan/config.py <-> repo_scan/hub/daemon.py (58% coupled). `repo_scan/config.py` and `repo_scan/hub/daemon.py` changed together in 7 commits (58% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
sources: ["gh-seddonym-import-linter", "url-wiki-apidesign-org-wiki-configurationobject", "gh-xlab-uiuc-cdep-fse-ae"]
run_at: "2026-06-10 17:16 UTC"
---

# Research run — Hidden seam: repo_scan/config.py <-> repo_scan/hub/daemon.py (58% coupled). `repo_scan/config.py` and `repo_scan/hub/daemon.py` changed together in 7 commits (58% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Run 2026-06-10 17:16 UTC_

**Strategy:** Follow the repo's tkt-0008 precedent: extract hub-owned keys and defaults into a shared `repo_scan/hub/settings.py`, have `daemon.py` import it (and `config.py` merge those defaults/keys at load time), then land ≥2 post-refactor commits that touch only one side so change-coupling degree falls strictly below the 50% threshold in coupling.md.

## Ingested

- [[sources/gh-seddonym-import-linter\|seddonym/import-linter — Lint your Python architecture.]] — Python import contracts make implicit module dependencies explicit and enforceable—exactly what turning the config↔daemon string-key contract into a visible import edge requires.
- [[sources/url-wiki-apidesign-org-wiki-configurationobject\|ConfigurationObject]] — The Configuration Object pattern replaces scattered string keys and magic defaults with a named, evolvable namespace owned by the consuming subsystem (hub/daemon), matching how RADAR_CONFIG_KEYS should be split out of the global loader.
- [[sources/gh-xlab-uiuc-cdep-fse-ae\|xlab-uiuc/cdep-fse-ae — Configuration dependency analysis for cloud software]] — cDep treats cross-component configuration dependencies as first-class relationships invisible to static import graphs—the same class of hidden seam this ticket detects between config.py and daemon.py.
