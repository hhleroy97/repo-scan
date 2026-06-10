---
id: "url-packaging-python-org-en-latest-guides-modernize-setup-py-pro"
type: "url"
url: "https://packaging.python.org/en/latest/guides/modernize-setup-py-project/"
raw_url: "https://packaging.python.org/en/latest/guides/modernize-setup-py-project/"
tags: ["article", "build-isolation", "build-system", "packaging", "pip", "project-metadata", "pyproject-toml", "python", "setup-py", "setuptools"]
linked_files: []
relevance: "Useful when repo-scan or its dependencies still use setup.py and need a low-risk path to modern PEP 517/518 packaging without breaking installs, CI, or tools that expect setup.py to remain present."
ingested_at: "2026-06-10 06:45 UTC"
---

# How to modernize a setup.py based project?¶

## Summary

Official setuptools guidance on modernizing legacy setup.py projects without necessarily removing setup.py. The core recommendation is adding a pyproject.toml with a [build-system] table so build frontends use setuptools.build_meta, while static metadata can move to [project] and dynamic fields stay in a slim setup.py. It also covers build-time dependencies, pip build isolation, and keeping a minimal setup.py for tooling that still invokes it.

## Key claims

- A pyproject.toml with a [build-system] table is strongly recommended; the file alone adds little without that table
- setup.py remains valid in modern setuptools projects and does not need to be deleted
- Legacy python setup.py install-style commands are deprecated and should be replaced with pip/build-based workflows
- Build-time imports in setup.py must be declared in [build-system] requires so isolated builds can install them
- Any pyproject.toml (even empty) causes pip to use build isolation by default
- Static packaging metadata can live entirely in [project]; dynamic fields must be listed under dynamic with logic retained in setup.py
- A minimal setup.py containing only setuptools.setup() is acceptable when external processes still expect setup.py to exist

## Notes

_yours to annotate_
