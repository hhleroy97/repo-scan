"""Hub: run state, decision inbox, checkpointed resume, server."""

import json
import threading
import urllib.request
from pathlib import Path

import pytest

from repo_scan.config import DEFAULT_CONFIG, load_config
from repo_scan.hub.server import build_state, make_handler
from repo_scan.hub.state import (active_run, clear_decisions, create_run,
                                 get_token, load_checkpoint, load_runs,
                                 peek_decision, problem_key, save_checkpoint,
                                 submit_decision, update_run)
from repo_scan.radar.gates import gate
from repo_scan.radar.pipeline import cmd_loop
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


def _approved_ticket(root: Path) -> dict:
    ticket = {"id": "tkt-0001", "title": "Fix the thing", "priority": "high",
              "fingerprint": "x:1", "why": "It is broken.", "criteria": ["fixed"]}
    write_ticket(root, DEFAULT_CONFIG, ticket)
    set_ticket_status(root, DEFAULT_CONFIG, "tkt-0001", "approved")
    return ticket


def test_event_feed_append_load_and_cap(tmp_repo: Path):
    from repo_scan.hub.state import EVENTS_KEEP, append_event, load_events
    cfg = DEFAULT_CONFIG
    append_event(tmp_repo, cfg, "stage", "[1/7] Research", problem="p")
    append_event(tmp_repo, cfg, "llm", "act · composer-2.5 · 10→2 tok · 1s")
    events = load_events(tmp_repo, cfg)
    assert [e["kind"] for e in events] == ["stage", "llm"]
    assert events[0]["problem"] == "p"
    # cap: the file is trimmed once it doubles past EVENTS_KEEP
    for i in range(EVENTS_KEEP * 2):
        append_event(tmp_repo, cfg, "stage", f"e{i}")
    raw = (tmp_repo / "docs" / ".radar" / "events.jsonl").read_text().splitlines()
    assert len(raw) <= EVENTS_KEEP + 1


def test_set_run_stage_updates_record_and_noops_without_run(tmp_repo: Path):
    from repo_scan.hub.state import create_run, load_runs, set_run_stage
    cfg = DEFAULT_CONFIG
    set_run_stage(tmp_repo, cfg, "no such run", "[1/7] Research")  # must not raise
    create_run(tmp_repo, cfg, "fix the thing", ticket="tkt-0001", kind="act")
    set_run_stage(tmp_repo, cfg, "fix the thing", "[3/5] Implement", "composer-2.5 editing")
    run = load_runs(tmp_repo, cfg)[0]
    assert run["stage"] == "[3/5] Implement"
    assert run["stage_detail"] == "composer-2.5 editing"


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


def test_server_serves_vendored_mermaid(hub_server):
    root, cfg, token, base = hub_server
    code, _ = _get(f"{base}/static/mermaid.min.js", token)
    assert code == 200


def test_server_state_includes_agentic_loop_mermaid(hub_server):
    root, cfg, token, base = hub_server
    code, state = _get(f"{base}/api/state", token)
    assert code == 200
    mmd = state.get("agentic_loop_mermaid", "")
    assert "graph TD" in mmd
    assert "subgraph radar" in mmd


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


def test_build_state_includes_telemetry(hub_server):
    root, cfg, token, base = hub_server
    from repo_scan.hub.telemetry import record_stage_done
    record_stage_done(root, cfg, PROBLEM, "analyze", "[2/7] Analyze", 500, 100, 50)
    code, state = _get(f"{base}/api/state", token)
    assert code == 200
    assert "telemetry" in state
    assert "burn" in state["telemetry"]
    assert "stages" in state["telemetry"]
    assert any(s.get("stage_id") == "analyze" for s in state["telemetry"]["stages"])
    assert "chart" in state["telemetry"]
    assert state["telemetry"]["chart"][0]["stage_id"] == "analyze"
    views = state["telemetry"]["views"]
    assert "total" in views and "average" in views and "runs" in views


def test_build_state_live_runs(hub_server):
    root, cfg, token, base = hub_server
    create_run(root, cfg, PROBLEM, ticket="tkt-0001")
    update_run(root, cfg, problem_key(PROBLEM), "running",
               stage="[3/7] Draft", stage_detail="composer-2.5 · still working")
    code, state = _get(f"{base}/api/state", token)
    assert code == 200
    assert len(state["live_runs"]) == 1
    live = state["live_runs"][0]
    assert live["status"] == "running"
    assert live["stage"] == "[3/7] Draft"
    assert "still working" in live["stage_detail"]
    assert live["ticket"] == "tkt-0001"


def test_build_state_includes_ticket_card_fields(hub_server):
    root, cfg, token, base = hub_server
    write_ticket(root, DEFAULT_CONFIG, {
        "id": "tkt-0099", "title": "Refactor foo.py (CC 9)",
        "fingerprint": "refactor:foo.py", "priority": "high",
        "why": "`foo.py` is hot.", "criteria": ["tests pass"],
    })
    code, state = _get(f"{base}/api/state", token)
    assert code == 200
    row = next(t for t in state["tickets"] if t["id"] == "tkt-0099")
    assert row["card"]["outcome"] == "Reduce risk in foo.py"
    assert row["criteria_count"] == 1
    assert row["criteria_ready"] is True
    assert row["doc"] == "tickets/tkt-0099.md"


def test_ticket_approve_rejected_without_criteria(hub_server):
    root, cfg, token, base = hub_server
    write_ticket(root, DEFAULT_CONFIG, {
        "id": "tkt-0003", "title": "T", "fingerprint": "x:3",
        "why": "w", "criteria": ["define done"],
    })
    code, resp = _post(f"{base}/api/ticket", token,
                       {"id": "tkt-0003", "action": "approve"})
    assert code == 400
    assert "criteria" in resp["error"].lower()
    bad = next(t for t in load_tickets(root, cfg) if t["id"] == "tkt-0003")
    assert bad["status"] == "proposed"


def _patch(url: str, token: str, data: dict) -> tuple[int, dict]:
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json",
                                          "X-Radar-Token": token},
                                 method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def test_ticket_patch_criteria_enables_approve(hub_server):
    root, cfg, token, base = hub_server
    write_ticket(root, DEFAULT_CONFIG, {
        "id": "tkt-0004", "title": "T", "fingerprint": "x:4",
        "why": "w", "criteria": ["define acceptance criteria before approving"],
    })
    code, resp = _patch(f"{base}/api/ticket", token,
                        {"id": "tkt-0004", "criteria": ["exports csv", "handles utf-8"]})
    assert code == 200 and resp["criteria_ready"] is True
    body = (root / "docs" / "tickets" / "tkt-0004.md").read_text()
    assert "- [ ] exports csv" in body
    code, resp = _post(f"{base}/api/ticket", token,
                       {"id": "tkt-0004", "action": "approve"})
    assert code == 200 and resp["ok"]
    good = next(t for t in load_tickets(root, cfg) if t["id"] == "tkt-0004")
    assert good["status"] == "approved"


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


def test_event_bus_broadcast():
    from repo_scan.hub.events import broadcast, subscribe, unsubscribe
    q = subscribe()
    try:
        broadcast({"type": "refresh"})
        assert q.get(timeout=1)["type"] == "refresh"
    finally:
        unsubscribe(q)


def test_append_event_broadcasts(hub_server):
    from repo_scan.hub.events import subscribe, unsubscribe
    root, cfg, token, base = hub_server
    q = subscribe()
    try:
        from repo_scan.hub.state import append_event
        append_event(root, cfg, "run", "sse test ping")
        msg = q.get(timeout=2)
        assert msg["type"] == "feed"
        assert "sse test" in msg["text"]
    finally:
        unsubscribe(q)


def test_sse_requires_auth(hub_server):
    root, cfg, token, base = hub_server
    assert _get(f"{base}/api/events")[0] == 401


def test_sse_streams_connected(hub_server):
    import urllib.request

    root, cfg, token, base = hub_server
    req = urllib.request.Request(f"{base}/api/events")
    req.add_header("X-Radar-Token", token)
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert "text/event-stream" in resp.headers.get("Content-Type", "")
        chunk = resp.fp.read1(256)  # first frame only — stream stays open
    assert b"data:" in chunk and b"connected" in chunk


def test_dashboard_has_gate_drawer(hub_server):
    root, cfg, token, base = hub_server
    code, html = _get(f"{base}/?token={token}")
    assert code == 200
    for needle in ("toggleGate", "rGateDrawer", "gate-drawer", "gate-glance"):
        assert needle in html, f"missing gate drawer UX: {needle}"


def test_dashboard_has_sse_client(hub_server):
    root, cfg, token, base = hub_server
    code, html = _get(f"{base}/?token={token}")
    assert code == 200
    assert "EventSource" in html and "/api/events" in html
    assert "connectSSE" in html


def test_dashboard_loading_states(hub_server):
    """Slow actions expose busy chrome — not a silent frozen UI."""
    root, cfg, token, base = hub_server
    code, html = _get(f"{base}/?token={token}")
    assert code == 200
    for needle in ("beginPending", "syncBusyChrome", "busy-bar",
                   "status-pill", "card-pending", "pending-spinner"):
        assert needle in html, f"missing loading UX: {needle}"


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
