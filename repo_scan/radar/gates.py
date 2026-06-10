"""Human-in-the-loop gates with progressive autonomy.

Per-repo config in .repo-scan.json:

    "gates": { "post_analyze": "prompt", "post_audit": "prompt" }

Modes:
- prompt — ask y/n on the CLI (the default; non-interactive runs pause instead)
- auto   — pass through silently (the gate "abstracted away" once trusted)
- deny   — always stop (hard checkpoint)

Pausing is file-backed: a pending gate writes docs/research/pending/{gate}.json
and the loop exits cleanly. Re-running the same loop command with --approve
<gate> consumes the pending file and continues — LangGraph-interrupt-shaped,
but plain files instead of a checkpointer.
"""

import json
import sys
from pathlib import Path

from ..utils import info, now_iso, ok, warn

GATE_NAMES = ("post_analyze", "post_audit", "pre_implement", "post_implement")
DEFAULT_GATES = {name: "prompt" for name in GATE_NAMES}


def gate_mode(name: str, cfg: dict) -> str:
    mode = str(cfg.get("gates", {}).get(name, "prompt")).lower()
    return mode if mode in ("prompt", "auto", "deny") else "prompt"


def gates_for_kind(cfg: dict, kind: str) -> dict:
    """Per-kind autonomy: trust earned per work type, not globally.

        "gates_by_kind": { "refactor": { "pre_implement": "auto" } }

    Returns a cfg copy whose gates merge the kind's overrides; unknown kinds
    pass through untouched."""
    overrides = cfg.get("gates_by_kind", {}).get(kind)
    if not overrides:
        return cfg
    return {**cfg, "gates": {**cfg.get("gates", {}), **overrides}}


def _pending_dir(root: Path, cfg: dict) -> Path:
    return root / cfg["docs_dir"] / "research" / "pending"


def pending_path(root: Path, cfg: dict, name: str, problem: str = "") -> Path:
    """Pending files are keyed by (gate, problem) so concurrent runs paused
    at the same gate never clobber each other."""
    suffix = ""
    if problem:
        from ..hub.state import problem_key
        suffix = f"-{problem_key(problem)}"
    return _pending_dir(root, cfg) / f"{name}{suffix}.json"


def write_pending(root: Path, cfg: dict, name: str, payload: dict) -> Path:
    problem = str(payload.get("problem", "") or payload.get("summary", ""))
    path = pending_path(root, cfg, name, problem)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"gate": name, "written_at": now_iso(), "payload": payload},
                               indent=2) + "\n", encoding="utf-8")
    return path


def clear_pending(root: Path, cfg: dict, name: str, problem: str = ""):
    # also sweep the legacy un-keyed filename so old pauses don't linger
    for path in (pending_path(root, cfg, name, problem),
                 _pending_dir(root, cfg) / f"{name}.json"):
        if path.exists():
            path.unlink()


def record_decision(root: Path, cfg: dict, name: str, decision: str, summary: str):
    """Append-only audit trail of every gate decision."""
    decisions = root / cfg["docs_dir"] / "research" / "decisions.md"
    decisions.parent.mkdir(parents=True, exist_ok=True)
    if not decisions.exists():
        decisions.write_text("# Gate decisions\n\n| When | Gate | Decision | Summary |\n"
                             "|------|------|----------|---------|\n", encoding="utf-8")
    with decisions.open("a", encoding="utf-8") as f:
        f.write(f"| {now_iso()} | {name} | {decision} | {summary[:120]} |\n")


def gate(name: str, payload: dict, cfg: dict, root: Path,
         approved: set[str] | None = None) -> bool:
    """Returns True to continue the pipeline, False to stop.

    `approved` carries gate names pre-approved via `--approve` (consumes any
    pending state from a previous paused run).
    """
    summary = str(payload.get("summary", ""))[:200]
    problem = str(payload.get("problem", "") or summary)
    mode = gate_mode(name, cfg)

    if approved and name in approved:
        clear_pending(root, cfg, name, problem)
        record_decision(root, cfg, name, "approved (--approve)", summary)
        ok(f"gate {name}: pre-approved")
        return True

    if mode == "auto":
        record_decision(root, cfg, name, "auto", summary)
        ok(f"gate {name}: auto-approved")
        return True

    if mode == "deny":
        record_decision(root, cfg, name, "denied (config)", summary)
        warn(f"gate {name}: denied by config")
        return False

    # prompt mode — check the decision inbox first so remote surfaces
    # (dashboard, future channels) count as answers, not just the terminal
    if problem:
        from ..hub.state import peek_decision
        inbox = peek_decision(root, cfg, name, problem)
        if inbox:
            clear_pending(root, cfg, name, problem)
            who = inbox.get("source", "remote")
            note = f" — {inbox['comment'][:80]}" if inbox.get("comment") else ""
            if inbox["decision"] == "approve":
                record_decision(root, cfg, name, f"approved ({who})", summary + note)
                ok(f"gate {name}: approved via {who}")
                return True
            record_decision(root, cfg, name, f"rejected ({who})", summary + note)
            warn(f"gate {name}: rejected via {who}")
            return False

    write_pending(root, cfg, name, payload)
    if not sys.stdin.isatty():
        info(f"gate {name}: paused (non-interactive) — pending state written to "
             f"docs/research/pending/{name}.json; re-run with --approve {name} to continue")
        record_decision(root, cfg, name, "paused", summary)
        return False

    print(f"\n  ── gate {name} " + "─" * 30)
    print(f"  {summary or '(no summary)'}")
    answer = input("  approve and continue? [y/N] ").strip().lower()
    if answer in ("y", "yes"):
        clear_pending(root, cfg, name, problem)
        record_decision(root, cfg, name, "approved", summary)
        return True
    record_decision(root, cfg, name, "rejected", summary)
    warn(f"gate {name}: rejected — pending state kept for review")
    return False
