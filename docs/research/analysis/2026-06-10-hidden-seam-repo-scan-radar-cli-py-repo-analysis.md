---
type: "analysis"
problem: "Hidden seam: repo_scan/radar/cli.py <-> repo_scan/radar/gates.py (80% coupled). `repo_scan/radar/cli.py` and `repo_scan/radar/gates.py` changed together in 4 commits (80% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["url-thoughtbot-com-blog-connascence-as-a-vocabulary-to-discuss-c", "arxiv-2302.09153", "gh-python-cpython"]
generated_at: "2026-06-10 17:32 UTC"
---

# Analysis — Hidden seam: repo_scan/radar/cli.py <-> repo_scan/radar/gates.py (80% coupled). `repo_scan/radar/cli.py` and `repo_scan/radar/gates.py` changed together in 4 commits (80% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 17:32 UTC — confidence: high_

## Findings

- The cli↔gates seam is connascence of meaning, not missing runtime logic: cli.py hard-codes gate names in --approve help strings (post_analyze/post_audit vs pre_implement/post_implement) and mode literals in --gates choices=["prompt", "auto", "deny"], while gates.py owns GATE_NAMES, DEFAULT_GATES, and gate_mode() validation — with no import edge between them.
- Co-change analysis (80% over 4 commits, no import) matches the Lefever et al. pattern for extracting a shared responsibility: the duplicated vocabulary is the implicit contract repo-scan's dependency graph cannot see.
- pipeline.py and act.py already import gates explicitly; cli.py is the outlier that only reaches gates transitively via lazy pipeline/act imports, which explains why gate CLI surface changes historically land in both files.
- gates.py already exports the canonical symbols (GATE_NAMES, gate_mode modes); a thin extension (e.g. GATE_MODES tuple or argparse parent builder) is sufficient — a separate gate_schema module is optional unless tkt-0017 (gates↔pipeline) needs the same surface.
- CPython argparse parents= is the idiomatic fix for three subcommands (loop, full, act) repeating --approve/--gates flags; importing shared constants weakens connascence to connascence of name per thoughtbot's refactor guidance.
- Acceptance criterion 'import edge appears' is immediately satisfiable; 'degree below 50%' in coupling.md is a historical git metric that may not move until post-refactor commits decouple the pair — rescan after implementation to confirm the edge, and treat degree as a lagging indicator.

## Recommendation

Add `from .gates import GATE_NAMES` (and a small GATE_MODES or `gate_arg_parser()` helper colocated in gates.py) and refactor cli.py to derive --approve metavar/help and --gates choices from those symbols, using an argparse parent for loop/full/act. Do not move gate execution logic into cli.py; keep cli as a thin argparse façade that imports the gate vocabulary module. Re-run repo-scan to verify an import edge cli→gates and document that co-change degree is expected to fall only as independent commits accumulate.

## Risks

- Historical co-change degree (80%) may remain above the 50% threshold immediately after refactor because it reflects past shared commits, not current structure.
- Eager-importing gates in cli.py is low risk (gates' top-level deps are lightweight; hub.state is lazy), but placing argparse helpers in gates.py slightly mixes CLI concerns with gate runtime — keep helpers minimal (constants + optional parent factory).
- Help text currently lists different gate subsets per subcommand (loop/full vs act); a naive single GATE_NAMES string in all helps would be a UX regression unless split into e.g. LOOP_GATE_NAMES vs ACT_GATE_NAMES derived from GATE_NAMES.
- Parallel seam tkt-0017 (gates↔pipeline) may need coordinated constants if pipeline also duplicates mode strings — scope this ticket narrowly to cli↔gates to avoid scope creep.

## Evidence

- [[url-thoughtbot-com-blog-connascence-as-a-vocabulary-to-discuss-c\|Connascence as a vocabulary to discuss Coupling]]
- [[arxiv-2302.09153\|Towards the Assisted Decomposition of Large-Active Files]]
- [[gh-python-cpython\|python/cpython — The Python programming language]]
- research run: [[2026-06-10-hidden-seam-repo-scan-radar-cli-py-repo]]
