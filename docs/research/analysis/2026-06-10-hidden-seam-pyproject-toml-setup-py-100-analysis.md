---
type: "analysis"
problem: "Hidden seam: pyproject.toml <-> setup.py (100% coupled). `pyproject.toml` and `setup.py` changed together in 5 commits (100% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["url-packaging-python-org-en-latest-guides-modernize-setup-py-pro", "url-packaging-python-org-en-latest-discussions-single-source-ver", "gh-pypa-sampleproject"]
generated_at: "2026-06-10 06:47 UTC"
---

# Analysis — Hidden seam: pyproject.toml <-> setup.py (100% coupled). `pyproject.toml` and `setup.py` changed together in 5 commits (100% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 06:47 UTC — confidence: high_

## Findings

- repo-scan's setup.py is a byte-for-byte duplicate of static metadata already declared in pyproject.toml (name, version, packages, entry points, python_requires, extras_require) with no dynamic build logic, extension modules, or custom setup() code—exactly the case PyPA's modernization guide says can live entirely in [project].
- pyproject.toml already defines a PEP 517/518 build via setuptools.build_meta; CI installs with pip install -e ".[dev]" and never invokes setup.py, so setup.py provides no functional capability today.
- pypa/sampleproject and current PyPA guidance treat pyproject.toml as the canonical packaging surface; a parallel setup.py is legacy redundancy, not a required companion file.
- repo-scan's hidden-seam detector only recognizes Python import edges (module paths), so no refactor can create an import edge between pyproject.toml and setup.py while both files remain—shared-module single-sourcing (e.g. dynamic version via repo_scan attr) would link setup.py to Python source, not to pyproject.toml.
- Keeping a minimal setup.py containing only setuptools.setup() would still leave 100% historical change coupling (7/7 shared commits) and no import edge, failing both acceptance criteria; freezing setup.py does not decay degree because degree = shared / min(revisions).
- Deleting setup.py removes it from the tracked file set used by analyze_history(), eliminating the pyproject.toml ↔ setup.py coupling pair entirely—the only fix that satisfies both 'explicit dependency' (contract removed) and 'degree below threshold' under the current scanner model.
- Version is already triplicated across pyproject.toml, setup.py, and repo_scan/config.py (VERSION = "0.2.0"); removing setup.py reduces drift surface, and PyPA single-source-version guidance recommends optionally wiring pyproject dynamic version from the package attr plus a test asserting __version__ matches importlib.metadata.version().

## Recommendation

Delete setup.py and treat pyproject.toml as the sole packaging manifest, matching PyPA modernization and sampleproject patterns. Verify with pip install -e ".[dev]", pytest, and a repo-scan run that coupling.md no longer lists the pyproject.toml ↔ setup.py seam; optionally follow up by declaring version dynamically from repo_scan.config.VERSION to collapse the remaining pyproject/config duplication.

## Risks

- Older pip versions on some platforms may still hit editable-install quirks (README already documents --no-build-isolation as a fallback).
- Downstream scripts or docs that assume setup.py exists (e.g. python setup.py develop) will break, though that workflow is deprecated.
- Version strings in pyproject.toml and repo_scan/config.py remain manually duplicated until a dynamic-version follow-up is implemented.
- Generated docs (index.md, digest.md) and identity.detect_manifests still list setup.py as a manifest type for scanned repos—only repo-scan's own setup.py is removed, not detection of setup.py in other projects.

## Evidence

- [[url-packaging-python-org-en-latest-guides-modernize-setup-py-pro\|How to modernize a setup.py based project?¶]]
- [[url-packaging-python-org-en-latest-discussions-single-source-ver\|Single-sourcing the Project Version¶]]
- [[gh-pypa-sampleproject\|pypa/sampleproject — A sample project that exists for PyPUG's "Tutorial on Packaging and…]]
- research run: [[2026-06-10-hidden-seam-pyproject-toml-setup-py-100]]
