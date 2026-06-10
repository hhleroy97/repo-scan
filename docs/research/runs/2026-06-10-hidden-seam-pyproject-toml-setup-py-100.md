---
type: "research-run"
question: "Hidden seam: pyproject.toml <-> setup.py (100% coupled). `pyproject.toml` and `setup.py` changed together in 5 commits (100% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
sources: ["url-packaging-python-org-en-latest-guides-modernize-setup-py-pro", "url-packaging-python-org-en-latest-discussions-single-source-ver", "gh-pypa-sampleproject"]
run_at: "2026-06-10 06:46 UTC"
---

# Research run — Hidden seam: pyproject.toml <-> setup.py (100% coupled). `pyproject.toml` and `setup.py` changed together in 5 commits (100% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Run 2026-06-10 06:46 UTC_

**Strategy:** This repo's setup.py duplicates static metadata already in pyproject.toml with no programmatic logic, so the primary fix is deletion per PyPA modernization guidance; if any setup.py must stay, single-source-version patterns make the link explicit via dynamic fields and a shared Python attr. Either path removes the hidden seam and should drop change-coupling below the coupling.md threshold.

## Ingested

- [[sources/url-packaging-python-org-en-latest-guides-modernize-setup-py-pro\|How to modernize a setup.py based project?¶]] — Official PyPA guidance on when static setup.py metadata can be fully replaced by pyproject.toml, eliminating the duplicate implicit contract this repo-scan seam detects.
- [[sources/url-packaging-python-org-en-latest-discussions-single-source-ver\|Single-sourcing the Project Version¶]] — Documents the shared-module alternative—single-sourcing version and metadata via dynamic [project] fields and tool.setuptools.dynamic attr imports—when setup.py must remain.
- [[sources/gh-pypa-sampleproject\|pypa/sampleproject — A sample project that exists for PyPUG's "Tutorial on Packaging and…]] — Canonical PyPA reference project showing modern pyproject.toml-only packaging without a parallel setup.py, providing a concrete target layout for this remediation.
