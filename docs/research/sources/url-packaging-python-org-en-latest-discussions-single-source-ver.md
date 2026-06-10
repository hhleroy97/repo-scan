---
id: "url-packaging-python-org-en-latest-discussions-single-source-ver"
type: "url"
url: "https://packaging.python.org/en/latest/discussions/single-source-version/"
raw_url: "https://packaging.python.org/en/latest/discussions/single-source-version/"
tags: ["article", "build-system", "importlib-metadata", "packaging", "pyproject-toml", "python", "single-source-of-truth", "testing", "vcs-tags", "versioning"]
linked_files: []
relevance: "Useful when repo-scan or similar tools need one authoritative project version that stays aligned across pyproject.toml, package __version__, and metadata at runtime."
ingested_at: "2026-06-10 06:45 UTC"
---

# Single-sourcing the Project Version¶

## Summary

Python packaging guidance on keeping distribution and import-package version strings in sync without manual duplication. It outlines three single-source approaches—VCS tags, pyproject.toml, or source files—and recommends automated tests to verify that __version__ matches importlib.metadata.version().

## Key claims

- Runtime __version__ on the import package should match importlib.metadata.version() for the distribution package
- Version numbers are often preferred from VCS tags (e.g. v1.2.3) rather than hand-edited in source
- Single-sourcing options: extract version from VCS, define it in pyproject.toml for the build system to propagate, or define it in source (_version.txt or __init__.py) for the build system to read at build time
- Some projects accept duplicated version fields and rely on automated tests to catch drift
- Projects should include a test asserting import_name.__version__ equals importlib.metadata.version("dist-name")
- The recommended approach depends on the chosen build system; consult its documentation for version handling

## Notes

_yours to annotate_
