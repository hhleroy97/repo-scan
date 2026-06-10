"""Hub: run state, decision inbox, checkpointed resume, daemon, server."""

import json
import threading
import time
import urllib.request
from pathlib import Path

import pytest

from repo_scan.config import DEFAULT_CONFIG, load_config
from repo_scan.hub.daemon import daemon_tick
from repo_scan.hub.server import build_state, make_handler
from repo_scan.hub.state import (active_run, clear_decisions, create_run,
                                 get_token, load_checkpoint, load_runs,
                                 peek_decision, problem_key, save_checkpoint,
                                 save_meta, submit_decision, update_run)
from repo_scan.radar.gates import gate
from repo_scan.radar.pipeline import cmd_loop, ticket_problem
from repo_scan.tickets import load_tickets, set_ticket_status, write_ticket

from tests.test_radar_pipeline import FAKE_LLM, happy_path_responses, queue_responses

PROBLEM = "how should gates work?"


# --- state ------------------------------------------------------------------

def test_decision_submit_peek_clear(tmp_repo: Path):
    cfg = DEFAULT_CONFIG
    assert peek_decision(tmp_repo, cfg, "post_analyze", PROBLEM) is None
    submit_decision(tmp_repo, cfg, "post_analyze", PROBLEM, "approve",
                    comment="lgtm", source="test")
    d = peek_decision(tmp_repo, cfg, "post_analyze", PROBLEM)
    assert d["decision"] == "approve" and d["comment"] == "lgtm"

    # first write wins — a second submit cannot flip the decision
    submit_decision(tmp_repo, cfg, "post_analyze", PROBLEM, "reject")
    assert peek_decision(tmp_repo, cfg, "post_analyze", PROBLEM)["decision"] == "approve"

    clear_decisions(tmp_repo, cfg, PROBLEM)
    assert peek_decision(tmp_repo, cfg, "post_analyze", PROBLEM) is None

    with pytest.raises(ValueError):
        submit_decision(tmp_repo, cfg, "post_analyze", PROBLEM, "maybe")


def test_run_lifecycle(tmp_repo: Path):
    cfg = DEFAULT_CONFIG
    run = create_run(tmp_repo, cfg, PROBLEM, ticket="tkt-0001")
    assert run["status"] == "queued" and run["id"] == problem_key(PROBLEM)
    assert active_run(tmp_repo, cfg)["id"] == run["id"]

    update_run(tmp_repo, cfg, run["id"], "waiting-on-gate", gate="post_analyze")
    r = active_run(tmp_repo, cfg)
    assert r["status"] == "waiting-on-gate" and r["gate"] == "post_analyze"

    update_run(tmp_repo, cfg, run["id"], "done")
    assert active_run(tmp_repo, cfg) is None
    assert load_runs(tmp_repo, cfg)[0]["status"] == "done"

    # restarting the same problem reuses its slot (no duplicate records)
    create_run(tmp_repo, cfg, PROBLEM)
    assert len([r for r in load_runs(tmp_repo, cfg)
                if r["id"] == run["id"]]) == 1


def test_token_is_stable(tmp_repo: Path):
    t1 = get_token(tmp_repo, DEFAULT_CONFIG)
    t2 = get_token(tmp_repo, DEFAULT_CONFIG)
    assert t1 == t2 and len(t1) >= 16


# --- gates consume the inbox --------------------------------------------------

def test_gate_consumes_inbox_approval(tmp_repo: Path):
    cfg = load_config(tmp_repo)
    payload = {"problem": PROBLEM, "summary": "do it"}
    submit_decision(tmp_repo, cfg, "post_analyze", PROBLEM, "approve",
                    source="dashboard")
    assert gate("post_analyze", payload, cfg, tmp_repo) is True
    decisions = (tmp_repo / "docs" / "research" / "decisions.md").read_text()
    assert "approved (dashboard)" in decisions
    # no pending file left behind
    assert not (tmp_repo / "docs" / "research" / "pending" / "post_analyze.json").exists()


def test_gate_consumes_inbox_rejection(tmp_repo: Path):
    cfg = load_config(tmp_repo)
    payload = {"problem": PROBLEM, "summary": "do it"}
    submit_decision(tmp_repo, cfg, "post_analyze", PROBLEM, "reject",
                    comment="not now", source="dashboard")
    assert gate("post_analyze", payload, cfg, tmp_repo) is False
    decisions = (tmp_repo / "docs" / "research" / "decisions.md").read_text()
    assert "rejected (dashboard)" in decisions
    assert "not now" in decisions
    assert not (tmp_repo / "docs" / "research" / "pending" / "post_analyze.json").exists()


# --- checkpointed resume -------------------------------------------------------

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


def test_pause_checkpoints_then_resume_skips_llm_stages(loop_env):
    root, cfg, note, queue = loop_env
    queue_responses(queue, happy_path_responses(note)[:3])
    assert cmd_loop(root, cfg, PROBLEM) == 2  # paused at gate 1

    ckpt = load_checkpoint(root, cfg, PROBLEM)
    assert "ingested" in ckpt and "analysis" in ckpt

    # resume via inbox approval: only draft + audit responses are needed —
    # research/analyze must come from the checkpoint, not the queue
    submit_decision(root, cfg, "post_analyze", PROBLEM, "approve")
    queue_responses(queue, happy_path_responses(note)[3:5])
    cfg["gates"] = {"post_audit": "auto"}
    assert cmd_loop(root, cfg, PROBLEM) == 0
    assert not sorted(queue.glob("*.txt"))  # every queued response consumed

    # loop finished -> resume state dropped
    assert load_checkpoint(root, cfg, PROBLEM) == {}
    assert peek_decision(root, cfg, "post_analyze", PROBLEM) is None
    spec = next((root / "docs" / "specs").glob("*.md")).read_text()
    assert "status: approved" in spec


def test_inbox_rejection_ends_loop_and_clears_state(loop_env):
    root, cfg, note, queue = loop_env
    queue_responses(queue, happy_path_responses(note)[:3])
    assert cmd_loop(root, cfg, PROBLEM) == 2

    submit_decision(root, cfg, "post_analyze", PROBLEM, "reject", comment="no")
    assert cmd_loop(root, cfg, PROBLEM) == 2  # stopped, not paused
    assert not (root / "docs" / "research" / "pending" / "post_analyze.json").exists()
    assert load_checkpoint(root, cfg, PROBLEM) == {}  # rejection is terminal


# --- daemon --------------------------------------------------------------------

def _approved_ticket(root: Path) -> dict:
    ticket = {"id": "tkt-0001", "title": "Fix the thing", "priority": "high",
              "fingerprint": "x:1", "why": "It is broken.", "criteria": ["fixed"]}
    write_ticket(root, DEFAULT_CONFIG, ticket)
    set_ticket_status(root, DEFAULT_CONFIG, "tkt-0001", "approved")
    return ticket


def test_daemon_full_cycle(loop_env, monkeypatch):
    root, cfg, note, queue = loop_env
    cfg["radar_enabled"] = True
    save_meta(root, cfg, {"last_scan": time.time()})  # skip the scheduled scan
    ticket = _approved_ticket(root)
    problem = ticket_problem({**ticket, "status": "approved"})

    # tick 1: picks up the approved ticket, pauses at gate 1
    queue_responses(queue, happy_path_responses(note)[:3])
    actions = daemon_tick(root, cfg)
    assert any(a.startswith("started:") for a in actions)
    run = active_run(root, cfg)
    assert run["status"] == "waiting-on-gate" and run["gate"] == "post_analyze"

    # tick with no decision: nothing happens
    assert daemon_tick(root, cfg) == []

    # tick 2: approval arrives -> resumes, pauses at gate 2
    submit_decision(root, cfg, "post_analyze", problem, "approve")
    queue_responses(queue, happy_path_responses(note)[3:5])
    actions = daemon_tick(root, cfg)
    assert any(a.startswith("resumed:") for a in actions)
    run = active_run(root, cfg)
    assert run["status"] == "waiting-on-gate" and run["gate"] == "post_audit"

    # tick 3: final approval -> done, ticket moves to in-progress
    submit_decision(root, cfg, "post_audit", problem, "approve")
    actions = daemon_tick(root, cfg)
    assert any(a.startswith("resumed:") for a in actions)
    assert active_run(root, cfg) is None
    assert load_runs(root, cfg)[0]["status"] == "done"
    ticket = load_tickets(root, cfg)[0]
    assert ticket["status"] == "in-progress"
    # the note must carry the spec wikilink — it's what makes this ticket
    # an act candidate for the daemon's fan-out
    body = Path(ticket["path"]).read_text()
    assert "-spec]]" in body


def test_daemon_scheduled_scan(tmp_repo: Path):
    cfg = load_config(tmp_repo)
    actions = daemon_tick(tmp_repo, cfg)  # no meta -> scan is due
    assert "scanned" in actions
    assert (tmp_repo / "docs" / "scan.json").exists()
    # immediately after, the scan is fresh -> no rescan
    assert "scanned" not in daemon_tick(tmp_repo, cfg)


# --- server ---------------------------------------------------------------------

@pytest.fixture
def hub_server(tmp_repo):
    from http.server import ThreadingHTTPServer
    cfg = load_config(tmp_repo)
    token = get_token(tmp_repo, cfg)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0),
                                make_handler(tmp_repo, cfg, token))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    yield tmp_repo, cfg, token, base
    httpd.shutdown()


def _get(url: str, token: str | None = None) -> tuple[int, dict | str]:
    req = urllib.request.Request(url)
    if token:
        req.add_header("X-Radar-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            ctype = resp.headers.get("Content-Type", "")
            return resp.status, json.loads(body) if "json" in ctype else body
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def _post(url: str, token: str, data: dict) -> tuple[int, dict]:
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json",
                                          "X-Radar-Token": token},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def test_server_requires_token(hub_server):
    root, cfg, token, base = hub_server
    assert _get(f"{base}/api/state")[0] == 401
    assert _get(f"{base}/api/state", token)[0] == 200
    assert _get(f"{base}/?token={token}")[0] == 200  # query token works too


def test_server_state_payload(hub_server):
    root, cfg, token, base = hub_server
    from repo_scan.radar.gates import write_pending
    _approved_ticket(root)
    write_pending(root, cfg, "post_analyze",
                  {"problem": PROBLEM, "summary": "review me",
                   "detail": {"confidence": "high", "findings": ["f1"]}})
    code, state = _get(f"{base}/api/state", token)
    assert code == 200
    assert state["repo"]["name"] == root.name
    assert state["gates"][0]["gate"] == "post_analyze"
    assert state["gates"][0]["detail"]["confidence"] == "high"
    assert state["tickets"][0]["id"] == "tkt-0001"


def test_server_gate_decision_roundtrip(hub_server):
    root, cfg, token, base = hub_server
    code, resp = _post(f"{base}/api/gate", token,
                       {"gate": "post_analyze", "problem": PROBLEM,
                        "decision": "approve", "comment": "ship it"})
    assert code == 200 and resp["ok"]
    d = peek_decision(root, cfg, "post_analyze", PROBLEM)
    assert d["decision"] == "approve" and d["source"] == "dashboard"

    code, resp = _post(f"{base}/api/gate", token,
                       {"gate": "post_analyze", "problem": PROBLEM,
                        "decision": "maybe"})
    assert code == 400


def test_server_ticket_action(hub_server):
    root, cfg, token, base = hub_server
    ticket = {"id": "tkt-0002", "title": "T", "priority": "low",
              "fingerprint": "x:2", "why": "w", "criteria": ["c"]}
    write_ticket(root, DEFAULT_CONFIG, ticket)
    code, resp = _post(f"{base}/api/ticket", token,
                       {"id": "tkt-0002", "action": "approve"})
    assert code == 200 and resp["ok"]
    assert load_tickets(root, cfg)[0]["status"] == "approved"
    assert _post(f"{base}/api/ticket", token,
                 {"id": "tkt-0002", "action": "explode"})[0] == 400


def test_server_doc_endpoint_is_sandboxed(hub_server):
    root, cfg, token, base = hub_server
    (root / "docs" / "specs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "specs" / "x-spec.md").write_text("# Spec\nhello")
    (root / "secret.md").write_text("nope")

    code, doc = _get(f"{base}/api/doc?path=specs/x-spec.md", token)
    assert code == 200 and "hello" in doc["text"]
    assert _get(f"{base}/api/doc?path=../secret.md", token)[0] == 404
    assert _get(f"{base}/api/doc?path=/etc/passwd", token)[0] == 404


def test_dashboard_html_served(hub_server):
    root, cfg, token, base = hub_server
    code, html = _get(f"{base}/?token={token}")
    assert code == 200
    assert "repo-scan hub" in html and "/api/state" in html


# --- local (machine-private) config overrides ------------------------------------

def test_local_config_merges_after_shared(tmp_repo: Path):
    (tmp_repo / ".repo-scan.json").write_text(
        json.dumps({"radar_enabled": True, "serve_port": 9000}))
    (tmp_repo / ".repo-scan.local.json").write_text(
        json.dumps({"ntfy_topic": "secret-topic", "serve_port": 9100}))
    cfg = load_config(tmp_repo)
    assert cfg["radar_enabled"] is True
    assert cfg["ntfy_topic"] == "secret-topic"
    assert cfg["serve_port"] == 9100  # local wins over shared


# --- notify ----------------------------------------------------------------------

def test_notify_disabled_without_topic():
    from repo_scan.hub.notify import notify
    assert notify({}, "t", "m") is False


def test_notify_posts_to_ntfy(monkeypatch):
    from repo_scan.hub import notify as notify_mod
    sent = {}

    class FakeResp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_open(req, timeout=0):
        sent["url"] = req.full_url
        sent["body"] = json.loads(req.data.decode())
        return FakeResp()

    monkeypatch.setattr(notify_mod.urllib.request, "urlopen", fake_open)
    ok = notify_mod.notify({"ntfy_topic": "my-secret-topic"},
                           "RADAR: gate", "review", priority="high",
                           tags=["raised_hand"], click="http://x/")
    assert ok is True
    assert sent["url"] == "https://ntfy.sh"
    assert sent["body"]["topic"] == "my-secret-topic"
    assert sent["body"]["priority"] == 4
    assert sent["body"]["click"] == "http://x/"
