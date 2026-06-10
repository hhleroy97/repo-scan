---
type: "research-run"
question: "Hidden seam: repo_scan/radar/cli.py <-> repo_scan/radar/gates.py (80% coupled). `repo_scan/radar/cli.py` and `repo_scan/radar/gates.py` changed together in 4 commits (80% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
sources: ["url-thoughtbot-com-blog-connascence-as-a-vocabulary-to-discuss-c", "arxiv-2302.09153", "gh-python-cpython"]
run_at: "2026-06-10 17:32 UTC"
---

# Research run — Hidden seam: repo_scan/radar/cli.py <-> repo_scan/radar/gates.py (80% coupled). `repo_scan/radar/cli.py` and `repo_scan/radar/gates.py` changed together in 4 commits (80% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Run 2026-06-10 17:32 UTC_

**Strategy:** Diagnose the seam as duplicated gate vocabulary (GATE_NAMES, mode choices, help strings in cli.py vs gates.py) rather than missing business logic; spec should have cli import those symbols from gates (or a thin gate_schema module) and centralize repeated argparse flags via parents, then rescan to confirm the import edge appears and co-change degree drops below the 50% threshold.

## Ingested

- [[sources/url-thoughtbot-com-blog-connascence-as-a-vocabulary-to-discuss-c\|Connascence as a vocabulary to discuss Coupling]] — Frames the cli↔gates seam as connascence of meaning (duplicated gate names and mode strings) and prescribes weakening it to connascence of name via shared named constants imported by both modules.
- [[sources/arxiv-2302.09153\|Towards the Assisted Decomposition of Large-Active Files]] — Empirical co-change-driven decomposition methodology that treats high co-change pairs as signals to extract a shared responsibility module, directly supporting the ticket's acceptance criterion to make the implicit contract explicit.
- [[sources/gh-python-cpython\|python/cpython — The Python programming language]] — Official argparse documentation shows the parents= pattern for sharing --approve and --gates flag definitions across loop, full, and act subcommands without duplicating literals that must stay in sync with gates.py.
