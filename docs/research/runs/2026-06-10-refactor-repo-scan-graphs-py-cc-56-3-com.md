---
type: "research-run"
question: "Refactor repo_scan/graphs.py (CC 56, 3 commits, untested). `repo_scan/graphs.py` is both high-churn (3 commits) and high-complexity (total CC 56) with no matching test file. Research current best practices and draft a spec for this work."
sources: ["gh-David-OConnor-pydeps", "gh-pahen-madge"]
run_at: "2026-06-10 03:26 UTC"
---

# Research run — Refactor repo_scan/graphs.py (CC 56, 3 commits, untested). `repo_scan/graphs.py` is both high-churn (3 commits) and high-complexity (total CC 56) with no matching test file. Research current best practices and draft a spec for this work.
_Run 2026-06-10 03:26 UTC_

**Strategy:** Follow the repo’s established snapshot-then-extract pattern (Feathers + syrupy, already ingested): Phase 1 adds fixture-backed golden tests for Mermaid output and monkeypatched madge/cflow adapters without changing behavior; Phase 2 splits pure renderers (`edges_to_mermaid`) from tool parsers and replaces regex import scanning with stdlib `ast` using pydeps/RefExpo as design oracles while keeping the module zero-deps.

## Ingested

- [[sources/gh-David-OConnor-pydeps\|David-OConnor/pydeps — Store dependency info for each PyPi package]] — Reference implementation of intra-repo Python import-edge extraction via `ast` traversal—the main CC hotspot (`get_python_dep_edges`, CC 19) and the clearest extract-and-simplify target.
- [[sources/gh-pahen-madge\|pahen/madge — Create graphs from your CommonJS, AMD or ES6 module dependencies]] — Authoritative source for the `madge --json --extensions` contract that `get_ts_dep_edges` already shells out to, including path anchoring and empty-output edge cases worth locking in characterization tests.

## Failed

- `arxiv:2407.02620` — fetch failed for http://export.arxiv.org/api/query?id_list=2407.02620: The read operation timed out
