"""Intent intake, executable acceptance criteria, and governance (offline).

Covers the three pillars that turn the maintenance loop into a feature loop:
1. a human idea becomes a first-class ticket (CLI/API), same lifecycle as
   scan-proposed work
2. acceptance criteria ride the problem string into the spec, and the act
   stage refuses feature work that ships without tests
5. budgets cap daily spend, protected paths force human review, and gate
   autonomy is granted per work kind
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from repo_scan.config import DEFAULT_CONFIG, load_config
from repo_scan.hub.daemon import daemon_tick, over_budget
from repo_scan.hub.state import create_run, load_events, save_meta
from repo_scan.radar.act import cmd_act, ticket_kind
from repo_scan.radar.gates import gates_for_kind
from repo_scan.radar.llm import record_usage
from repo_scan.radar.pipeline import ticket_problem
from repo_scan.tickets import (append_ticket_note, load_tickets, new_ticket,
                               set_ticket_status, tickets_main, write_ticket)


def _git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return r.stdout.strip()


def _stub_agent(tmp_path: Path, script: str) -> str:
    path = tmp_path / "agent.py"
    path.write_text(script)
    return f"{sys.executable} {path}"


# writes impl.py but never any test file
NO_TESTS_AGENT = """\
from pathlib import Path
Path("impl.py").write_text("VALUE = 42\\n")
print("implemented, no tests")
"""

# first call: impl only; second call (the acceptance round): the test file
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


# ---------------------------------------------------------------- 1: intake

def test_new_ticket_creates_feature_with_criteria(tmp_repo):
    cfg = load_config(tmp_repo)
    t = new_ticket(tmp_repo, cfg, "Add CSV export", why="users asked",
                   priority="high", criteria=["exports all rows", "handles utf-8"])
    assert t["id"] == "tkt-0001"
    assert t["fingerprint"] == "feature:add-csv-export"
    body = Path(t["path"]).read_text()
    assert 'origin: "human"' in body and 'source: "intent"' in body
    assert "- [ ] exports all rows" in body and "- [ ] handles utf-8" in body
    # board includes it
    assert "Add CSV export" in (tmp_repo / "docs" / "tickets" / "board.md").read_text()


def test_new_ticket_dedups_on_resubmit(tmp_repo):
    cfg = load_config(tmp_repo)
    first = new_ticket(tmp_repo, cfg, "Add CSV export")
    again = new_ticket(tmp_repo, cfg, "Add CSV  Export!")  # same slug
    assert again["id"] == first["id"]
    assert len(load_tickets(tmp_repo, cfg)) == 1


def test_new_ticket_rejects_empty_title(tmp_repo):
    with pytest.raises(ValueError):
        new_ticket(tmp_repo, load_config(tmp_repo), "   ")


def test_tickets_cli_new(tmp_repo, monkeypatch):
    monkeypatch.chdir(tmp_repo)
    rc = tickets_main(["new", "Dark mode", "--why", "night users",
                       "--criterion", "toggle persists", "--priority", "low",
                       "--approve"])
    assert rc == 0
    t = load_tickets(tmp_repo, load_config(tmp_repo))[0]
    assert t["title"] == "Dark mode" and t["status"] == "approved"
    assert t["priority"] == "low"
    assert "toggle persists" in t["criteria"]


# ------------------------------------------------- 2: acceptance criteria

def test_ticket_problem_carries_criteria(tmp_repo):
    cfg = load_config(tmp_repo)
    t = new_ticket(tmp_repo, cfg, "Add CSV export",
                   criteria=["exports all rows", "handles utf-8"])
    loaded = next(x for x in load_tickets(tmp_repo, cfg) if x["id"] == t["id"])
    problem = ticket_problem(loaded)
    assert "Acceptance criteria: exports all rows; handles utf-8." in problem


def test_ticket_problem_without_criteria_unchanged():
    p = ticket_problem({"title": "T", "why": "w", "criteria": []})
    assert "Acceptance criteria" not in p


@pytest.fixture
def feature_act_repo(tmp_repo: Path):
    """In-progress feature ticket with an approved spec (act candidate)."""
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


def test_act_feature_without_tests_stops(feature_act_repo, tmp_path):
    root, cfg = feature_act_repo
    cfg["llm_cli"] = [_stub_agent(tmp_path, NO_TESTS_AGENT)]
    assert cmd_act(root, cfg) == 2
    act_log = next((root / "docs" / "changelog").glob("*-act.md")).read_text()
    assert "outcome: **no-acceptance-tests**" in act_log
    body = Path(load_tickets(root, cfg)[0]["path"]).read_text()
    assert "no acceptance tests" in body


def test_act_feature_acceptance_round_adds_tests(feature_act_repo, tmp_path):
    root, cfg = feature_act_repo
    cfg["llm_cli"] = [_stub_agent(tmp_path, TESTS_ON_RETRY_AGENT)]
    assert cmd_act(root, cfg) == 0
    committed = _git(root, "show", "--name-only", "HEAD")
    assert "impl.py" in committed and "tests/test_impl.py" in committed


def test_act_non_feature_kind_skips_test_requirement(feature_act_repo, tmp_path):
    root, cfg = feature_act_repo
    # same agent that writes no tests, but ticket kind is refactor
    path = load_tickets(root, cfg)[0]["path"]
    text = Path(path).read_text().replace("feature:add-csv-export",
                                          "refactor:impl.py")
    Path(path).write_text(text)
    subprocess.run(["git", "add", "-A"], cwd=root, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "rekind"], cwd=root, capture_output=True)
    cfg["llm_cli"] = [_stub_agent(tmp_path, NO_TESTS_AGENT)]
    assert cmd_act(root, cfg) == 0


# ---------------------------------------------------------- 5: governance

def test_ticket_kind_from_fingerprint():
    assert ticket_kind({"fingerprint": "feature:x"}) == "feature"
    assert ticket_kind({"fingerprint": "refactor:a.py"}) == "refactor"
    assert ticket_kind({"fingerprint": ""}) == "task"


def test_gates_for_kind_merges_overrides():
    cfg = {"gates": {"pre_implement": "prompt", "post_implement": "prompt"},
           "gates_by_kind": {"refactor": {"pre_implement": "auto"}}}
    out = gates_for_kind(cfg, "refactor")
    assert out["gates"] == {"pre_implement": "auto", "post_implement": "prompt"}
    assert gates_for_kind(cfg, "feature") is cfg  # untouched
    assert cfg["gates"]["pre_implement"] == "prompt"  # original not mutated


def test_protected_paths_force_human_review(feature_act_repo, tmp_path):
    """Auto post gate, but the agent touched a protected path -> pause."""
    root, cfg = feature_act_repo
    cfg["llm_cli"] = [_stub_agent(tmp_path, TESTS_ON_RETRY_AGENT)]
    cfg["protected_paths"] = ["impl.py"]
    assert cmd_act(root, cfg) == 2  # paused at post_implement despite auto
    pending = json.loads(next(
        (root / "docs" / "research" / "pending").glob("post_implement*.json")
    ).read_text())
    assert "PROTECTED" in pending["payload"]["summary"]
    assert "impl.py" in pending["payload"]["detail"]["protected"]


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

    assert daemon_tick(root, cfg) == []  # would have started an act otherwise
    events = load_events(root, cfg, limit=10)
    assert any("budget" in e["text"] for e in events)
    # notification is once per day, not every tick
    assert daemon_tick(root, cfg) == []
    assert sum("budget" in e["text"] for e in load_events(root, cfg, limit=10)) == 1
