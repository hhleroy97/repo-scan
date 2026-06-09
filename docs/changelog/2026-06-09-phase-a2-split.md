# 2026-06-09 — Phase A2: module split

The 1,380-line monolith `repo_scan.py` is now the `repo_scan/` package, following
the HANDOFF extension points. Pure refactor — all 23 tests passed unchanged
before and after.

## Structure

```
repo_scan/
  __init__.py    # re-exports public API; `repo_scan:main` entry point unchanged
  cli.py         # argparse main(), check_deps()
  scanner.py     # scan() orchestration + digest collection
  config.py      # VERSION, DEFAULT_CONFIG, load_config, write_default_config
  languages.py   # extensions, detect_languages, get_line_counts
  identity.py    # manifests, entry points, README summary, directory tree
  churn.py       # git log analysis
  complexity.py  # radon wrapper
  graphs.py      # dep edges (py + madge --json), mermaid, cflow call graph
  ranking.py     # composite important-files score
  writers.py     # health/dep/call/index reports, scan.json, candidates, AGENTS.md
  digest.py      # token-budgeted single-file export
  handoff.py     # HANDOFF.md generator
  hooks.py       # pre-commit hook installer
  utils.py       # run(), color helpers, git metadata, write_doc
```

## Packaging

- `pyproject.toml` / `setup.py`: `py-modules = ["repo_scan"]` → `packages = ["repo_scan"]`
- Console script stays `repo-scan = "repo_scan:main"` (re-exported from `cli.py`)
- Reinstalled editable; `repo-scan --version`, full scan, and `--digest` verified

## Why now

Per the HANDOFF rule ("do not refactor until the monolith is fully tested"), the
split waited for the Phase A test harness. The B phases (radar) land as a
`repo_scan/radar/` subpackage on this structure.
