"""Mermaid source for the hub agentic loop diagram (live stage highlighting).

Vault: docs/tickets/tkt-0034
Vault: docs/research/sources/gh-mermaid-js-mermaid
See docs/architecture/agentic-loop for the canonical loop description.
"""

from __future__ import annotations

_BASE = """graph TD
  subgraph lifecycle["Lifecycle"]
    lc_scan["repo-scan"]
    lc_ticket["tickets"]
    lc_loop["RADAR loop"]
    lc_spec["approved spec"]
    lc_act["radar act"]
    lc_merge["PR merge"]
    lc_rescan["rescan"]
    lc_scan --> lc_ticket --> lc_loop --> lc_spec --> lc_act --> lc_merge --> lc_rescan
    lc_rescan -.-> lc_scan
  end
  subgraph radar["RADAR loop — 7 stages"]
    rd_research["1 Research"]
    rd_analyze["2 Analyze"]
    rd_post_analyze{"post_analyze"}
    rd_draft["4 Draft"]
    rd_audit["5 Audit"]
    rd_post_audit{"post_audit"}
    rd_record["7 Record"]
    rd_research --> rd_analyze --> rd_post_analyze --> rd_draft
    rd_draft --> rd_audit --> rd_post_audit --> rd_record
  end
  subgraph actflow["radar act — 5 stages"]
    ac_pick["pick ticket + spec"]
    ac_pre{"pre_implement"}
    ac_impl["3 Implement"]
    ac_test["4 Test"]
    ac_post{"post_implement"}
    ac_commit["commit → merge"]
    ac_pick --> ac_pre --> ac_impl --> ac_test --> ac_post --> ac_commit
  end
  lc_loop -.-> rd_research
  lc_spec -.-> ac_pick
  classDef active fill:#1a3a5c,stroke:#4f9cf9,stroke-width:3px,color:#e8eef8
  classDef waiting fill:#3d3010,stroke:#e0a93e,stroke-width:2px,color:#fff8e8
  classDef completed fill:#0d2818,stroke:#3fb96d,stroke-width:2px,color:#b8e8c8
"""

_RADAR_STEPS = (
    "research", "analyze", "post_analyze", "draft", "audit", "post_audit", "record",
)
_ACT_STEPS = ("pick", "pre_implement", "implement", "test", "post_implement", "commit")

_STAGE_MARKS: dict[str, list[str]] = {
    "research": ["research", "[1/7]"],
    "analyze": ["analyze", "[2/7]"],
    "post_analyze": ["post_analyze", "post-analyze", "[3/7]", "gate 1"],
    "draft": ["draft", "[4/7]"],
    "audit": ["audit", "[5/7]"],
    "post_audit": ["post_audit", "post-audit", "[6/7]", "gate 2"],
    "record": ["record", "[7/7]"],
    "pick": ["pick", "branch", "[2/5]"],
    "pre_implement": ["pre_implement", "pre-implement", "[1/5]"],
    "implement": ["implement", "[3/5]"],
    "test": ["test", "[4/5]"],
    "post_implement": ["post_implement", "post-implement", "[5/5]"],
    "commit": ["commit", "[5/5]"],
}

_NODE_IDS: dict[str, str] = {
    "research": "rd_research",
    "analyze": "rd_analyze",
    "post_analyze": "rd_post_analyze",
    "draft": "rd_draft",
    "audit": "rd_audit",
    "post_audit": "rd_post_audit",
    "record": "rd_record",
    "pick": "ac_pick",
    "pre_implement": "ac_pre",
    "implement": "ac_impl",
    "test": "ac_test",
    "post_implement": "ac_post",
    "commit": "ac_commit",
}

_GATE_KEYS = {
    "post-analyze": "post_analyze",
    "post_analyze": "post_analyze",
    "post-audit": "post_audit",
    "post_audit": "post_audit",
    "pre-implement": "pre_implement",
    "pre_implement": "pre_implement",
    "post-implement": "post_implement",
    "post_implement": "post_implement",
}


def _match_stage(run: dict, step: str) -> bool:
    stage = (run.get("stage") or "").lower()
    gate = (run.get("gate") or "").lower().replace("-", "_")
    if run.get("status") == "waiting-on-gate" and gate == step:
        return True
    return any(m in stage or m in gate for m in _STAGE_MARKS.get(step, []))


def _completed_trail(run: dict) -> set[str]:
    """Node IDs for stages completed in the last finished run."""
    if not run:
        return set()
    steps = _ACT_STEPS if run.get("kind") == "act" else _RADAR_STEPS
    trail = set()
    for step in steps:
        trail.add(_NODE_IDS[step])
        if _match_stage(run, step):
            break
    return trail


def _active_nodes(run: dict | None, gates: list[dict]) -> tuple[set[str], set[str]]:
    active: set[str] = set()
    waiting: set[str] = set()
    for gate_row in gates:
        raw = (gate_row.get("gate") or "").replace("_", "-")
        key = _GATE_KEYS.get(raw, raw.replace("-", "_"))
        if key in _NODE_IDS:
            waiting.add(_NODE_IDS[key])
    if not run:
        return active, waiting
    steps = _ACT_STEPS if run.get("kind") == "act" else _RADAR_STEPS
    for step in steps:
        if _match_stage(run, step):
            active.add(_NODE_IDS[step])
    active.add("lc_act" if run.get("kind") == "act" else "lc_loop")
    return active, waiting


def build_agentic_loop_mermaid(live_runs: list[dict] | None = None,
                               gates: list[dict] | None = None,
                               last_completed_run: dict | None = None) -> str:
    """Return mermaid ``graph TD`` with classDef highlights for live hub state."""
    run = live_runs[0] if live_runs else None
    active, waiting = _active_nodes(run, gates or [])
    lines = [_BASE.rstrip()]
    if active:
        lines.append(f"  class {','.join(sorted(active))} active")
    waiting_only = waiting - active
    if waiting_only:
        lines.append(f"  class {','.join(sorted(waiting_only))} waiting")
    completed = _completed_trail(last_completed_run)
    completed -= active | waiting_only
    if completed:
        lines.append(f"  class {','.join(sorted(completed))} completed")
    return "\n".join(lines) + "\n"
