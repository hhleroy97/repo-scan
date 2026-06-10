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

from repo_scan.hub.state import (active_run, load_checkpoint, submit_decision)
from repo_scan.radar.act import act_problem, cmd_act, find_act_ticket
from repo_scan.tickets import load_tickets

from tests.support.act_fixtures import (COUNTING_AGENT, IMPLEMENT_AGENT, act_repo,
                                        stub_agent)

def _git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return r.stdout.strip()


def test_find_act_ticket(act_repo):
    root, cfg = act_repo
    ticket, stem = find_act_ticket(root, cfg)
    assert ticket["id"] == "tkt-0001"
    assert stem == "2026-01-01-fix-the-thing-spec"


def test_act_happy_path_commits_on_branch(act_repo, tmp_path):
    root, cfg = act_repo
    cfg["llm_cli"] = [stub_agent(tmp_path, IMPLEMENT_AGENT)]
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
    cfg["llm_cli"] = [stub_agent(tmp_path, IMPLEMENT_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    (root / "uncommitted.py").write_text("x = 1\n")
    assert cmd_act(root, cfg) == 1


def test_act_pauses_and_resumes_via_inbox(act_repo, tmp_path):
    root, cfg = act_repo
    cfg["llm_cli"] = [stub_agent(tmp_path, IMPLEMENT_AGENT)]
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
    cfg["llm_cli"] = [stub_agent(tmp_path, IMPLEMENT_AGENT)]
    cfg["gates"] = {"pre_implement": "auto"}  # post_implement stays prompt
    problem = act_problem("tkt-0001", "2026-01-01-fix-the-thing-spec")

    assert cmd_act(root, cfg) == 2  # paused at post_implement
    submit_decision(root, cfg, "post_implement", problem, "reject", comment="not yet")
    assert cmd_act(root, cfg) == 2  # consumed rejection -> stopped
    assert "setup" in _git(root, "log", "-1", "--pretty=%s")  # nothing committed
    act_log = next((root / "docs" / "changelog").glob("*-act.md")).read_text()
    assert "outcome: **rejected**" in act_log


def test_needs_readme_sync():
    from repo_scan.radar.act import _needs_readme_sync
    assert _needs_readme_sync(["repo_scan/radar/cli.py"])
    assert not _needs_readme_sync(["repo_scan/radar/cli.py", "README.md"])
    assert not _needs_readme_sync(["impl.py"])


def test_act_doc_fix_round_when_cli_surface_changes(act_repo, tmp_path, monkeypatch):
    """Doc fix round fires when implement touches cli.py without README."""
    root, cfg = act_repo
    prompts: list[str] = []

    def fake_complete(prompt, *args, **kwargs):
        prompts.append(prompt)
        if len(prompts) == 1:
            (root / "impl.py").write_text("VALUE = 1\n")
        else:
            (root / "README.md").write_text("# Updated README\n")
        return "ok"

    monkeypatch.setattr("repo_scan.radar.act.complete", fake_complete)
    monkeypatch.setattr("repo_scan.radar.act._changed_files",
                        lambda *a, **k: ["repo_scan/radar/cli.py"])
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    cfg["test_cmd"] = f"{sys.executable} -c \"pass\""
    assert cmd_act(root, cfg) == 0
    assert len(prompts) >= 2
    assert "Changed code files:" in prompts[1]
    assert "repo_scan/radar/cli.py" in prompts[1]


def test_act_fix_round_then_pass(act_repo, tmp_path):
    root, cfg = act_repo
    cfg["llm_cli"] = [stub_agent(tmp_path, COUNTING_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    # passes only after the agent has been invoked twice (implement + 1 fix)
    cfg["test_cmd"] = (f"{sys.executable} -c \"from pathlib import Path; "
                       f"import sys; "
                       f"sys.exit(0 if Path('counter.txt').read_text().count('x') >= 2 else 1)\"")
    assert cmd_act(root, cfg) == 0
    assert (root / "counter.txt").read_text().count("x") == 2


def test_act_gives_up_after_fix_rounds(act_repo, tmp_path):
    root, cfg = act_repo
    cfg["llm_cli"] = [stub_agent(tmp_path, COUNTING_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    cfg["act_fix_rounds"] = 1
    cfg["test_cmd"] = f"{sys.executable} -c \"import sys; sys.exit(1)\""  # never passes
    assert cmd_act(root, cfg) == 2
    act_log = next((root / "docs" / "changelog").glob("*-act.md")).read_text()
    assert "outcome: **tests-failed**" in act_log
    body = Path(load_tickets(root, cfg)[0]["path"]).read_text()
    assert "needs a human" in body


def test_act_opens_pr_when_configured(act_repo, tmp_path, monkeypatch):
    """With act_open_pr, a successful act pushes the branch and opens a PR
    via the gh CLI; the URL lands on the ticket and in the act log."""
    import os
    root, cfg = act_repo
    cfg["llm_cli"] = [stub_agent(tmp_path, IMPLEMENT_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    cfg["act_open_pr"] = True

    # local bare remote so the push is real
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote)],
                   cwd=root, capture_output=True)

    # fake gh on PATH that records argv and prints a PR URL
    bindir = tmp_path / "bin"
    bindir.mkdir()
    gh = bindir / "gh"
    gh.write_text("#!/bin/sh\necho \"$@\" > " + str(tmp_path / "gh-args.txt") +
                  "\necho https://github.com/x/y/pull/7\n")
    gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")

    assert cmd_act(root, cfg) == 0
    args = (tmp_path / "gh-args.txt").read_text()
    assert "pr create" in args and "radar/tkt-0001" in args
    # branch made it to the remote
    heads = subprocess.run(["git", "ls-remote", "--heads", str(remote)],
                           capture_output=True, text=True).stdout
    assert "radar/tkt-0001" in heads
    body = Path(load_tickets(root, cfg)[0]["path"]).read_text()
    assert "https://github.com/x/y/pull/7" in body
    act_log = next((root / "docs" / "changelog").glob("*-act.md")).read_text()
    assert "pull/7" in act_log


def test_act_pr_failure_keeps_commit(act_repo, tmp_path):
    """No gh / no remote: the commit and branch survive, outcome unchanged."""
    root, cfg = act_repo
    cfg["llm_cli"] = [stub_agent(tmp_path, IMPLEMENT_AGENT)]
    cfg["gates"] = {"pre_implement": "auto", "post_implement": "auto"}
    cfg["act_open_pr"] = True  # no remote configured -> push fails gracefully
    assert cmd_act(root, cfg) == 0
    assert _git(root, "log", "-1", "--pretty=%s").startswith("radar: implement")

