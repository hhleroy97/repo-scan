"""Act stage: implement approved specs with tests as the hard gate (offline).

The "agent" is a stub script that creates files in the repo when invoked,
which is exactly the side-effect surface cmd_act expects from a real agent
CLI. Test commands assert on those files, so pass/fail flows are exercised
for real.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from repo_scan.config import DEFAULT_CONFIG, load_config
from repo_scan.hub.daemon import daemon_tick
from repo_scan.hub.state import (active_run, load_checkpoint, load_runs,
                                 save_meta, submit_decision)
from repo_scan.radar.act import act_problem, cmd_act, find_act_ticket
from repo_scan.tickets import append_ticket_note, load_tickets, set_ticket_status, write_ticket

import time  # noqa: E402


def _git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return r.stdout.strip()


def _stub_agent(tmp_path: Path, script: str) -> str:
    """An 'agent CLI' — a python script run as `script.py <prompt>`."""
    path = tmp_path / "agent.py"
    path.write_text(script)
    return f"{sys.executable} {path}"


IMPLEMENT_AGENT = """\
import sys
from pathlib import Path
Path("impl.py").write_text("VALUE = 42\\n")
print("Implemented the spec: created impl.py with VALUE = 42.")
"""

# appends one line per invocation — lets tests require N agent calls
COUNTING_AGENT = """\
import sys
from pathlib import Path
p = Path("counter.txt")
p.write_text(p.read_text() + "x\\n" if p.exists() else "x\\n")
print("ran")
"""


@pytest.fixture
def act_repo(tmp_repo: Path, tmp_path: Path):
    """tmp repo with an in-progress ticket linked to an approved spec."""
    specs = tmp_repo / "docs" / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "2026-01-01-fix-the-thing-spec.md").write_text(
        '---\ntype: "spec"\nstatus: "approved"\n---\n\n# Spec\n\n'
        "## Goal\nCreate impl.py with VALUE = 42.\n")
    write_ticket(tmp_repo, DEFAULT_CONFIG,
                 {"id": "tkt-0001", "title": "Fix the thing", "priority": "high",
                  "fingerprint": "x:1", "why": "w", "criteria": ["c"]})
    set_ticket_status(tmp_repo, DEFAULT_CONFIG, "tkt-0001", "in-progress")
    append_ticket_note(tmp_repo, DEFAULT_CONFIG, "tkt-0001",
                       "radar spec approved: [[2026-01-01-fix-the-thing-spec]]")
    # vault setup churn must not block act's clean-tree check
    subprocess.run(["git", "add", "-A"], cwd=tmp_repo, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "setup"], cwd=tmp_repo, capture_output=True)

    cfg = load_config(tmp_repo)
    cfg["act_enabled"] = True
    cfg["test_cmd"] = f"{sys.executable} -c \"import impl; assert impl.VALUE == 42\""
    return tmp_repo, cfg


def test_find_act_ticket(act_repo):
    root, cfg = act_repo
    ticket, stem = find_act_ticket(root, cfg)
    assert ticket["id"] == "tkt-0001"
    assert stem == "2026-01-01-fix-the-thing-spec"


def test_act_happy_path_commits_on_branch(act_repo, tmp_path):
    root, cfg = act_repo
    cfg["llm_cli"] = [_stub_agent(tmp_path, IMPLEMENT_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}

    assert cmd_act(root, cfg) == 0
    assert _git(root, "rev-parse", "--abbrev-ref", "HEAD") == "radar/tkt-0001"
    assert (root / "impl.py").exists()
    last = _git(root, "log", "-1", "--pretty=%s")
    assert last.startswith("radar: implement tkt-0001")
    # vault churn excluded from the implementation commit
    committed = _git(root, "show", "--stat", "--name-only", "HEAD")
    assert "impl.py" in committed and "docs/" not in committed

    body = Path(load_tickets(root, cfg)[0]["path"]).read_text()
    assert "implemented:" in body and "radar/tkt-0001" in body
    act_log = next((root / "docs" / "changelog").glob("*-act.md")).read_text()
    assert "outcome: **committed**" in act_log

    # terminal state cleared
    problem = act_problem("tkt-0001", "2026-01-01-fix-the-thing-spec")
    assert load_checkpoint(root, cfg, problem) == {}

    # every stage and LLM call landed in the shared agent feed
    from repo_scan.hub.state import load_events
    events = load_events(root, cfg, limit=50)
    stages = [e["text"] for e in events if e["kind"] == "stage"]
    assert any("[3/5] Implement" in s for s in stages)
    assert any("[4/5] Test" in s for s in stages)
    assert any(e["kind"] == "llm" for e in events)


def test_act_refuses_dirty_tree_outside_vault(act_repo, tmp_path):
    root, cfg = act_repo
    cfg["llm_cli"] = [_stub_agent(tmp_path, IMPLEMENT_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    (root / "uncommitted.py").write_text("x = 1\n")
    assert cmd_act(root, cfg) == 1


def test_act_pauses_and_resumes_via_inbox(act_repo, tmp_path):
    root, cfg = act_repo
    cfg["llm_cli"] = [_stub_agent(tmp_path, IMPLEMENT_AGENT)]
    problem = act_problem("tkt-0001", "2026-01-01-fix-the-thing-spec")

    # prompt gates, non-interactive -> pause at pre_implement before any work
    assert cmd_act(root, cfg) == 2
    pending_dir = root / "docs" / "research" / "pending"
    assert list(pending_dir.glob("pre_implement*.json"))
    assert not (root / "impl.py").exists()
    assert _git(root, "rev-parse", "--abbrev-ref", "HEAD") != "radar/tkt-0001"

    # approve pre_implement -> implements, tests pass, pauses at post_implement
    submit_decision(root, cfg, "pre_implement", problem, "approve")
    assert cmd_act(root, cfg) == 2
    assert (root / "impl.py").exists()
    pending = json.loads(next(pending_dir.glob("post_implement*.json")).read_text())
    assert "tests passed" in pending["payload"]["summary"]

    # approve post_implement -> resumes from checkpoint (agent NOT re-run), commits
    marker_mtime = (root / "impl.py").stat().st_mtime
    submit_decision(root, cfg, "post_implement", problem, "approve")
    assert cmd_act(root, cfg) == 0
    assert (root / "impl.py").stat().st_mtime == marker_mtime
    assert _git(root, "log", "-1", "--pretty=%s").startswith("radar: implement")


def test_act_rejection_keeps_branch_uncommitted(act_repo, tmp_path):
    root, cfg = act_repo
    cfg["llm_cli"] = [_stub_agent(tmp_path, IMPLEMENT_AGENT)]
    cfg["gates"] = {"pre_implement": "auto"}  # post_implement stays prompt
    problem = act_problem("tkt-0001", "2026-01-01-fix-the-thing-spec")

    assert cmd_act(root, cfg) == 2  # paused at post_implement
    submit_decision(root, cfg, "post_implement", problem, "reject", comment="not yet")
    assert cmd_act(root, cfg) == 2  # consumed rejection -> stopped
    assert "setup" in _git(root, "log", "-1", "--pretty=%s")  # nothing committed
    act_log = next((root / "docs" / "changelog").glob("*-act.md")).read_text()
    assert "outcome: **rejected**" in act_log


def test_act_fix_round_then_pass(act_repo, tmp_path):
    root, cfg = act_repo
    cfg["llm_cli"] = [_stub_agent(tmp_path, COUNTING_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    # passes only after the agent has been invoked twice (implement + 1 fix)
    cfg["test_cmd"] = (f"{sys.executable} -c \"from pathlib import Path; "
                       f"import sys; "
                       f"sys.exit(0 if Path('counter.txt').read_text().count('x') >= 2 else 1)\"")
    assert cmd_act(root, cfg) == 0
    assert (root / "counter.txt").read_text().count("x") == 2


def test_act_gives_up_after_fix_rounds(act_repo, tmp_path):
    root, cfg = act_repo
    cfg["llm_cli"] = [_stub_agent(tmp_path, COUNTING_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    cfg["act_fix_rounds"] = 1
    cfg["test_cmd"] = f"{sys.executable} -c \"import sys; sys.exit(1)\""  # never passes
    assert cmd_act(root, cfg) == 2
    act_log = next((root / "docs" / "changelog").glob("*-act.md")).read_text()
    assert "outcome: **tests-failed**" in act_log
    body = Path(load_tickets(root, cfg)[0]["path"]).read_text()
    assert "needs a human" in body


def test_daemon_runs_act_for_inprogress_ticket(act_repo, tmp_path):
    root, cfg = act_repo
    cfg["llm_cli"] = [_stub_agent(tmp_path, IMPLEMENT_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    cfg["max_parallel_acts"] = 1  # inline for determinism
    save_meta(root, cfg, {"last_scan": time.time()})  # skip scheduled scan

    actions = daemon_tick(root, cfg)
    assert any(a.startswith("act-started:") for a in actions)
    assert load_runs(root, cfg)[0]["status"] == "done"

    # daemon acts run in an isolated worktree: the main checkout is untouched,
    # the implementation lives on the radar branch, the worktree is pruned
    assert not (root / "impl.py").exists()
    assert _git(root, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert "VALUE = 42" in _git(root, "show", "radar/tkt-0001:impl.py")
    from repo_scan.radar.act import worktree_path
    assert not worktree_path(root, "tkt-0001").exists()

    # implemented ticket no longer a candidate -> next tick is a no-op
    assert daemon_tick(root, cfg) == []


def test_daemon_tick_survives_live_act_thread(act_repo):
    """Regression: a tick while an act thread is in flight must not crash
    (the daemon thread died on a bad iteration over _act_threads)."""
    import threading
    from repo_scan.hub import daemon as daemon_mod
    root, cfg = act_repo
    save_meta(root, cfg, {"last_scan": time.time()})
    t = threading.Thread(target=time.sleep, args=(1.0,), daemon=True)
    t.start()
    daemon_mod._act_threads["fake-run-id"] = t
    try:
        daemon_tick(root, cfg)  # must not raise
    finally:
        del daemon_mod._act_threads["fake-run-id"]


def test_reclaim_orphan_runs_resurrects_work(act_repo, tmp_path):
    """A run left 'running' by a dead process is reclaimed at startup and
    the next tick restarts the act from its checkpoints."""
    from repo_scan.hub.daemon import reclaim_orphan_runs
    from repo_scan.hub.state import create_run, update_run
    from repo_scan.radar.act import act_problem
    root, cfg = act_repo
    cfg["llm_cli"] = [_stub_agent(tmp_path, IMPLEMENT_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    cfg["max_parallel_acts"] = 1
    save_meta(root, cfg, {"last_scan": time.time()})

    problem = act_problem("tkt-0001", "2026-01-01-fix-the-thing-spec")
    run = create_run(root, cfg, problem, ticket="tkt-0001", kind="act")
    update_run(root, cfg, run["id"], "running")  # owner "died" here

    assert daemon_tick(root, cfg) == []  # starved: stale run blocks the slot
    assert reclaim_orphan_runs(root, cfg) == [run["id"]]
    actions = daemon_tick(root, cfg)
    assert any(a.startswith("act-started:") for a in actions)
    assert load_runs(root, cfg)[-1]["status"] == "done"
    assert "VALUE = 42" in _git(root, "show", "radar/tkt-0001:impl.py")


def test_daemon_fans_out_parallel_acts(act_repo, tmp_path):
    """Two approved specs -> two act runs in the same tick, isolated worktrees."""
    root, cfg = act_repo
    specs = root / "docs" / "specs"
    (specs / "2026-01-02-second-thing-spec.md").write_text(
        '---\ntype: "spec"\nstatus: "approved"\n---\n\n# Spec\n\n'
        "## Goal\nCreate impl.py with VALUE = 42.\n")
    write_ticket(root, DEFAULT_CONFIG,
                 {"id": "tkt-0002", "title": "Second thing", "priority": "low",
                  "fingerprint": "x:2", "why": "w", "criteria": ["c"]})
    set_ticket_status(root, DEFAULT_CONFIG, "tkt-0002", "in-progress")
    append_ticket_note(root, DEFAULT_CONFIG, "tkt-0002",
                       "radar spec approved: [[2026-01-02-second-thing-spec]]")
    subprocess.run(["git", "add", "-A"], cwd=root, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "more"], cwd=root, capture_output=True)

    cfg["llm_cli"] = [_stub_agent(tmp_path, IMPLEMENT_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    cfg["max_parallel_acts"] = 2
    save_meta(root, cfg, {"last_scan": time.time()})

    actions = daemon_tick(root, cfg)
    assert sum(a.startswith("act-started:") for a in actions) == 2

    deadline = time.time() + 60
    while time.time() < deadline:
        statuses = {r["status"] for r in load_runs(root, cfg)}
        if statuses == {"done"}:
            break
        time.sleep(0.2)
    assert {r["status"] for r in load_runs(root, cfg)} == {"done"}
    for tid in ("tkt-0001", "tkt-0002"):
        assert "VALUE = 42" in _git(root, "show", f"radar/{tid}:impl.py")
