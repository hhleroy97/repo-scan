# Act doc drift check

**Date:** 2026-06-10

## What changed

After the implement stage, if the agent changed public `repo_scan/` surface
(`cli.py`, `__init__.py`, `config.py`, `main.py`) without touching
`README.md`, act runs one bounded `doc_fix` round to sync documentation.

## Tests

- `tests/test_act.py::test_act_doc_fix_when_cli_changes_without_readme`
