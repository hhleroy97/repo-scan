"""Hub daemon: scheduler tick, budget gates, vault autocommit, orphan reclaim."""

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from repo_scan.config import DEFAULT_CONFIG, load_config
from repo_scan.hub import daemon as daemon_mod
from repo_scan.hub.daemon import (commit_vault, daemon_tick, over_budget,
                                  reclaim_orphan_runs)
from repo_scan.hub.state import (active_run, create_run, load_events, load_runs,
                                 save_meta, submit_decision, update_run)
from repo_scan.radar.llm import record_usage
from repo_scan.radar.pipeline import ticket_problem
from repo_scan.tickets import (append_ticket_note, load_tickets, set_ticket_status,
                               write_ticket)

from tests.test_radar_pipeline import FAKE_LLM, happy_path_responses, queue_responses

PROBLEM = "how should gates work?"


def _git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return r.stdout.strip()


def _stub_agent(tmp_path: Path, script: str) -> str:
    path = tmp_path / "agent.py"
    path.write_text(script)
    return f"{sys.executable} {path}"


IMPLEMENT_AGENT = """\
import sys
from pathlib import Path
Path("impl.py").write_text("VALUE = 42\\n")
print("Implemented the spec: created impl.py with VALUE = 42.")
"""

TESTS_ON_RETRY_AGENT = """\
from pathlib import Path
if Path("impl.py").exists():
    Path("tests").mkdir(exist_ok=True)
    Path("tests/test_impl.py").write_text("import impl\\n\\ndef test_v():\\n    assert impl.VALUE == 42\\n")
    print("added acceptance tests")
else:
    Path("impl.py").write_text("VALUE = 42\\n")
    print("implemented")
"""


@pytest.fixture(autouse=True)
def _clear_run_threads():
    """Isolate tests from module-level thread registry."""
    daemon_mod._run_threads.clear()
    yield
    daemon_mod._run_threads.clear()


@pytest.fixture
def loop_env(tmp_repo, tmp_path, monkeypatch):
    note = tmp_repo / "note.md"
    note.write_text("# Note\nGates should be file-backed.\n")
    queue = tmp_path / "queue"
    monkeypatch.delenv("RADAR_FAKE_RESPONSE", raising=False)
    monkeypatch.setenv("RADAR_FAKE_RESPONSES_DIR", str(queue))
    cfg = load_config(tmp_repo)
    cfg["llm_cli"] = [FAKE_LLM]
    return tmp_repo, cfg, note, queue


@pytest.fixture
def act_repo(tmp_repo: Path, tmp_path: Path):
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
    subprocess.run(["git", "add", "-A"], cwd=tmp_repo, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "setup"], cwd=tmp_repo, capture_output=True)
    cfg = load_config(tmp_repo)
    cfg["act_enabled"] = True
    cfg["test_cmd"] = f"{sys.executable} -c \"import impl; assert impl.VALUE == 42\""
    return tmp_repo, cfg


@pytest.fixture
def feature_act_repo(tmp_repo: Path):
    specs = tmp_repo / "docs" / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "2026-01-01-csv-spec.md").write_text(
        '---\ntype: "spec"\nstatus: "approved"\n---\n\n# Spec\n\n'
        "## Goal\nCreate impl.py with VALUE = 42.\n\n"
        "## Tests\n- tests/test_impl.py::test_v — exports all rows\n")
    write_ticket(tmp_repo, DEFAULT_CONFIG,
                 {"id": "tkt-0001", "title": "Add CSV export", "priority": "high",
                  "fingerprint": "feature:add-csv-export", "why": "w",
                  "criteria": ["exports all rows"]})
    set_ticket_status(tmp_repo, DEFAULT_CONFIG, "tkt-0001", "in-progress")
    append_ticket_note(tmp_repo, DEFAULT_CONFIG, "tkt-0001",
                       "radar spec approved: [[2026-01-01-csv-spec]]")
    subprocess.run(["git", "add", "-A"], cwd=tmp_repo, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "setup"], cwd=tmp_repo, capture_output=True)
    cfg = load_config(tmp_repo)
    cfg["act_enabled"] = True
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    cfg["test_cmd"] = f"{sys.executable} -c \"import impl; assert impl.VALUE == 42\""
    return tmp_repo, cfg


def _approved_ticket(root: Path) -> dict:
    ticket = {"id": "tkt-0001", "title": "Fix the thing", "priority": "high",
              "fingerprint": "x:1", "why": "It is broken.", "criteria": ["fixed"]}
    write_ticket(root, DEFAULT_CONFIG, ticket)
    set_ticket_status(root, DEFAULT_CONFIG, "tkt-0001", "approved")
    return ticket


# --- full tick cycle -----------------------------------------------------------

def test_daemon_full_cycle(loop_env, monkeypatch):
    root, cfg, note, queue = loop_env
    cfg["radar_enabled"] = True
    cfg["max_parallel_loops"] = 1
    save_meta(root, cfg, {"last_scan": time.time()})
    ticket = _approved_ticket(root)
    problem = ticket_problem({**ticket, "status": "approved"})

    queue_responses(queue, happy_path_responses(note)[:3])
    actions = daemon_tick(root, cfg)
    assert any(a.startswith("started:") for a in actions)
    run = active_run(root, cfg)
    assert run["status"] == "waiting-on-gate" and run["gate"] == "post_analyze"

    assert daemon_tick(root, cfg) == []

    submit_decision(root, cfg, "post_analyze", problem, "approve")
    queue_responses(queue, happy_path_responses(note)[3:5])
    actions = daemon_tick(root, cfg)
    assert any(a.startswith("resumed:") for a in actions)
    run = active_run(root, cfg)
    assert run["status"] == "waiting-on-gate" and run["gate"] == "post_audit"

    submit_decision(root, cfg, "post_audit", problem, "approve")
    actions = daemon_tick(root, cfg)
    assert any(a.startswith("resumed:") for a in actions)
    assert active_run(root, cfg) is None
    assert load_runs(root, cfg)[0]["status"] == "done"
    ticket = load_tickets(root, cfg)[0]
    assert ticket["status"] == "in-progress"
    body = Path(ticket["path"]).read_text()
    assert "-spec]]" in body


def test_daemon_scheduled_scan(tmp_repo: Path):
    cfg = load_config(tmp_repo)
    actions = daemon_tick(tmp_repo, cfg)
    assert "scanned" in actions
    assert (tmp_repo / "docs" / "scan.json").exists()
    assert "scanned" not in daemon_tick(tmp_repo, cfg)


# --- resume / orphans ----------------------------------------------------------

def test_reclaim_orphan_runs_resurrects_work(act_repo, tmp_path):
    from repo_scan.radar.act import act_problem
    root, cfg = act_repo
    cfg["llm_cli"] = [_stub_agent(tmp_path, IMPLEMENT_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    cfg["max_parallel_acts"] = 1
    save_meta(root, cfg, {"last_scan": time.time()})

    problem = act_problem("tkt-0001", "2026-01-01-fix-the-thing-spec")
    run = create_run(root, cfg, problem, ticket="tkt-0001", kind="act")
    update_run(root, cfg, run["id"], "running")

    assert daemon_tick(root, cfg) == []
    assert reclaim_orphan_runs(root, cfg) == [run["id"]]
    actions = daemon_tick(root, cfg)
    assert any(a.startswith("act-started:") for a in actions)
    assert load_runs(root, cfg)[-1]["status"] == "done"
    assert "VALUE = 42" in _git(root, "show", "radar/tkt-0001:impl.py")


def test_daemon_tick_survives_live_act_thread(act_repo):
    root, cfg = act_repo
    save_meta(root, cfg, {"last_scan": time.time()})
    t = threading.Thread(target=time.sleep, args=(1.0,), daemon=True)
    t.start()
    daemon_mod._run_threads["fake-run-id"] = t
    daemon_tick(root, cfg)


# --- fan-out -------------------------------------------------------------------

def test_daemon_fans_out_parallel_loops(loop_env, monkeypatch):
    root, cfg, note, queue = loop_env
    cfg["radar_enabled"] = True
    cfg["max_parallel_loops"] = 2
    save_meta(root, cfg, {"last_scan": time.time()})
    _approved_ticket(root)
    write_ticket(root, DEFAULT_CONFIG,
                 {"id": "tkt-0002", "title": "Second thing", "priority": "low",
                  "fingerprint": "x:2", "why": "Also broken.", "criteria": ["ok"]})
    set_ticket_status(root, DEFAULT_CONFIG, "tkt-0002", "approved")

    monkeypatch.setenv("RADAR_FAKE_RESPONSE", json.dumps({
        "sources": [{"ref": f"file:{note}", "why": "design note"}],
        "notes": "use local note",
        "summary": "Note about gates.", "key_claims": ["file-backed gates"],
        "tags": ["design"], "relevance": "directly relevant",
        "findings": ["gates should be file-backed"],
        "recommendation": "Use pending-state files.",
        "confidence": "high", "risks": [],
    }))

    actions = daemon_tick(root, cfg)
    assert sum(a.startswith("started:") for a in actions) == 2

    deadline = time.time() + 60
    while time.time() < deadline:
        runs = load_runs(root, cfg)
        if len(runs) == 2 and all(r["status"] == "waiting-on-gate" for r in runs):
            break
        time.sleep(0.2)
    runs = load_runs(root, cfg)
    assert len(runs) == 2
    assert all(r["status"] == "waiting-on-gate" and r["gate"] == "post_analyze"
               for r in runs)
    assert {r["ticket"] for r in runs} == {"tkt-0001", "tkt-0002"}


def test_daemon_fans_out_parallel_acts(act_repo, tmp_path):
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


def test_daemon_runs_act_for_inprogress_ticket(act_repo, tmp_path):
    root, cfg = act_repo
    cfg["llm_cli"] = [_stub_agent(tmp_path, IMPLEMENT_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    cfg["max_parallel_acts"] = 1
    save_meta(root, cfg, {"last_scan": time.time()})

    actions = daemon_tick(root, cfg)
    assert any(a.startswith("act-started:") for a in actions)
    assert load_runs(root, cfg)[0]["status"] == "done"

    assert not (root / "impl.py").exists()
    assert _git(root, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert "VALUE = 42" in _git(root, "show", "radar/tkt-0001:impl.py")
    from repo_scan.radar.act import worktree_path
    assert not worktree_path(root, "tkt-0001").exists()

    assert daemon_tick(root, cfg) == []


# --- budget --------------------------------------------------------------------

def test_over_budget_tokens(tmp_repo):
    cfg = load_config(tmp_repo)
    cfg["budget_daily_tokens"] = 100
    assert over_budget(tmp_repo, cfg) is None
    record_usage(tmp_repo, cfg, {"ts": time.time(), "role": "act",
                                 "model": "m", "input_tokens": 80,
                                 "output_tokens": 30})
    reason = over_budget(tmp_repo, cfg)
    assert reason and "token budget" in reason


def test_over_budget_acts_per_day(tmp_repo):
    cfg = load_config(tmp_repo)
    cfg["max_acts_per_day"] = 1
    assert over_budget(tmp_repo, cfg) is None
    create_run(tmp_repo, cfg, "p1", ticket="tkt-0001", kind="act")
    reason = over_budget(tmp_repo, cfg)
    assert reason and "act cap" in reason


def test_daemon_blocks_new_work_when_over_budget(feature_act_repo, tmp_path):
    root, cfg = feature_act_repo
    cfg["llm_cli"] = [_stub_agent(tmp_path, TESTS_ON_RETRY_AGENT)]
    cfg["max_parallel_acts"] = 1
    cfg["budget_daily_tokens"] = 1
    record_usage(root, cfg, {"ts": time.time(), "role": "act", "model": "m",
                             "input_tokens": 5, "output_tokens": 5})
    save_meta(root, cfg, {"last_scan": time.time()})

    assert daemon_tick(root, cfg) == []
    events = load_events(root, cfg, limit=10)
    assert any("budget" in e["text"] for e in events)
    assert daemon_tick(root, cfg) == []
    assert sum("budget" in e["text"] for e in load_events(root, cfg, limit=10)) == 1


# --- vault ---------------------------------------------------------------------

def test_commit_vault_commits_docs_only(tmp_repo):
    cfg = load_config(tmp_repo)
    (tmp_repo / "docs").mkdir(exist_ok=True)
    (tmp_repo / "docs" / "new-artifact.md").write_text("# spec\n")
    (tmp_repo / "wip.py").write_text("# human's half-done work\n")
    subprocess.run(["git", "add", "wip.py"], cwd=tmp_repo, capture_output=True)

    assert commit_vault(tmp_repo, cfg, "vault: test artifacts") is True
    show = subprocess.run(["git", "show", "--name-only", "--pretty=%s", "HEAD"],
                          cwd=tmp_repo, capture_output=True, text=True).stdout
    assert "vault: test artifacts" in show
    assert "docs/new-artifact.md" in show
    assert "wip.py" not in show
    status = subprocess.run(["git", "status", "--porcelain"], cwd=tmp_repo,
                            capture_output=True, text=True).stdout
    assert "wip.py" in status
    assert any("vault committed" in e["text"] for e in load_events(tmp_repo, cfg))


def test_commit_vault_noop_when_clean_or_disabled(tmp_repo):
    cfg = load_config(tmp_repo)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_repo,
                          capture_output=True, text=True).stdout
    assert commit_vault(tmp_repo, cfg, "vault: nothing") is False
    (tmp_repo / "docs").mkdir(exist_ok=True)
    (tmp_repo / "docs" / "x.md").write_text("x\n")
    cfg2 = dict(cfg, vault_autocommit=False)
    assert commit_vault(tmp_repo, cfg2, "vault: disabled") is False
    head2 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_repo,
                           capture_output=True, text=True).stdout
    assert head == head2


# --- phase isolation -----------------------------------------------------------

def test_resume_phase_skips_busy_runs(loop_env):
    """A waiting-on-gate run already on a live thread is not resumed again."""
    root, cfg, note, queue = loop_env
    cfg["radar_enabled"] = True
    cfg["max_parallel_loops"] = 1
    save_meta(root, cfg, {"last_scan": time.time()})
    ticket = _approved_ticket(root)
    problem = ticket_problem({**ticket, "status": "approved"})
    queue_responses(queue, happy_path_responses(note)[:3])
    daemon_tick(root, cfg)
    submit_decision(root, cfg, "post_analyze", problem, "approve")

    run = active_run(root, cfg)
    assert run["status"] == "waiting-on-gate"
    t = threading.Thread(target=time.sleep, args=(2.0,), daemon=True)
    t.start()
    daemon_mod._run_threads[run["id"]] = t

    actions = daemon_tick(root, cfg)
    assert not any(a.startswith("resumed:") for a in actions)


def test_scan_phase_skips_when_threads_alive(act_repo):
    """Scheduled scan is skipped while this process owns live run threads."""
    root, cfg = act_repo
    cfg["act_enabled"] = False
    save_meta(root, cfg, {})  # scan is due
    t = threading.Thread(target=time.sleep, args=(2.0,), daemon=True)
    t.start()
    daemon_mod._run_threads["busy"] = t

    actions = daemon_tick(root, cfg)
    assert "scanned" not in actions


def test_midflight_blocks_new_work(loop_env):
    """Foreign-owned queued/running runs block starting new work."""
    root, cfg, note, queue = loop_env
    cfg["radar_enabled"] = True
    cfg["max_parallel_loops"] = 1
    save_meta(root, cfg, {"last_scan": time.time()})
    _approved_ticket(root)
    problem = ticket_problem({"id": "tkt-0001", "title": "Fix", "why": "w",
                              "criteria": [], "status": "approved"})
    run = create_run(root, cfg, problem, ticket="tkt-0001")
    update_run(root, cfg, run["id"], "running")

    actions = daemon_tick(root, cfg)
    assert actions == []
    assert not any(a.startswith("started:") for a in actions)


def test_act_fanout_skips_loop_same_tick(loop_env, tmp_path):
    """Non-empty actions after act fan-out or resume skip loop fan-out same tick."""
    root, cfg, note, queue = loop_env
    cfg["radar_enabled"] = True
    cfg["act_enabled"] = True
    cfg["max_parallel_loops"] = 1
    cfg["max_parallel_acts"] = 1
    cfg["llm_cli"] = [_stub_agent(tmp_path, IMPLEMENT_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    cfg["test_cmd"] = f"{sys.executable} -c \"import impl; assert impl.VALUE == 42\""
    save_meta(root, cfg, {"last_scan": time.time()})

    specs = root / "docs" / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "2026-01-01-fix-the-thing-spec.md").write_text(
        '---\ntype: "spec"\nstatus: "approved"\n---\n\n# Spec\n\n'
        "## Goal\nCreate impl.py with VALUE = 42.\n")
    write_ticket(root, DEFAULT_CONFIG,
                 {"id": "tkt-act", "title": "Act me", "priority": "high",
                  "fingerprint": "x:act", "why": "w", "criteria": ["c"]})
    set_ticket_status(root, DEFAULT_CONFIG, "tkt-act", "in-progress")
    append_ticket_note(root, DEFAULT_CONFIG, "tkt-act",
                       "radar spec approved: [[2026-01-01-fix-the-thing-spec]]")
    subprocess.run(["git", "add", "-A"], cwd=root, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "act setup"], cwd=root, capture_output=True)

    _approved_ticket(root)  # loop candidate tkt-0001

    actions = daemon_tick(root, cfg)
    assert any(a.startswith("act-started:") for a in actions)
    assert not any(a.startswith("started:") for a in actions)


def test_resume_actions_skip_loop_same_tick(loop_env):
    """Resume actions alone skip loop fan-out even when another ticket is approved."""
    root, cfg, note, queue = loop_env
    cfg["radar_enabled"] = True
    cfg["act_enabled"] = True  # early return after act phase checks all prior actions
    cfg["max_parallel_loops"] = 1
    save_meta(root, cfg, {"last_scan": time.time()})
    ticket = _approved_ticket(root)
    problem = ticket_problem({**ticket, "status": "approved"})
    queue_responses(queue, happy_path_responses(note)[:3])
    daemon_tick(root, cfg)
    write_ticket(root, DEFAULT_CONFIG,
                 {"id": "tkt-0002", "title": "Second thing", "priority": "low",
                  "fingerprint": "x:2", "why": "Also broken.", "criteria": ["ok"]})
    set_ticket_status(root, DEFAULT_CONFIG, "tkt-0002", "approved")
    submit_decision(root, cfg, "post_analyze", problem, "approve")
    queue_responses(queue, happy_path_responses(note)[3:5])
    resumed = daemon_tick(root, cfg)
    assert any(a.startswith("resumed:") for a in resumed)
    assert not any(a.startswith("started:") for a in resumed)
