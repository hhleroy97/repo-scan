"""Hub act_run contract: explicit daemon↔act orchestration seam via hub.act_run."""

import ast
import subprocess
from pathlib import Path

import pytest

from repo_scan.behavior import analyze_history
from repo_scan.config import DEFAULT_CONFIG, load_config
from repo_scan.hub import act_run
from repo_scan.hub.act_run import ACT_RC_PAUSED, ACT_RC_SUCCESS, run_act
from repo_scan.hub.state import create_run, load_runs

_PKG = "repo_scan"
_DAEMON = f"{_PKG}/hub/daemon.py"
_ACT_RUN = f"{_PKG}/hub/act_run.py"
_TEST_ACT = "tests/test_act.py"


def _commit(repo: Path, files: dict[str, str], msg: str = "c"):
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t.com", "commit", "-qm", msg],
        cwd=repo, check=True, capture_output=True,
    )


def _import_froms(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    return {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }


def test_daemon_imports_act_run():
    """daemon.py imports hub.act_run; _run_act delegates to run_act."""
    root = Path(__file__).resolve().parents[1]
    daemon_path = root / "repo_scan" / "hub" / "daemon.py"
    source = daemon_path.read_text()
    assert "act_run" in _import_froms(daemon_path)
    tree = ast.parse(source)
    run_act_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_act"
    ]
    assert run_act_calls, "_run_act should delegate to run_act"


def test_act_run_module_contract():
    """act_run.py exports RC constants and run_act; no import from daemon."""
    root = Path(__file__).resolve().parents[1]
    act_run_path = root / "repo_scan" / "hub" / "act_run.py"
    source = act_run_path.read_text()
    tree = ast.parse(source)
    import_froms = _import_froms(act_run_path)
    assert "daemon" not in import_froms
    assert hasattr(act_run, "run_act")
    assert ACT_RC_SUCCESS == 0
    assert ACT_RC_PAUSED == 2
    assert "def run_act" in source


def test_act_run_rc_constants():
    """ACT_RC_SUCCESS/ACT_RC_PAUSED match cmd_act return codes used in act tests."""
    assert ACT_RC_SUCCESS == 0
    assert ACT_RC_PAUSED == 2


def test_act_run_outcome_mapping(tmp_repo: Path, monkeypatch):
    """RC 0 → done; RC 2 + gate → waiting-on-gate; RC 2 alone → stopped; other → failed."""
    cfg = load_config(tmp_repo)
    problem = "implement the thing"
    run = create_run(tmp_repo, cfg, problem, ticket="tkt-0001", kind="act")
    vault_calls: list[str] = []

    def fake_commit_vault(root, cfg, message):
        vault_calls.append(message)
        return False

    def fake_dashboard_url(cfg):
        return "http://localhost:8800/"

    def fake_pending_gate(root, cfg, prob):
        return "post_implement" if prob == problem else None

    def stub_cmd_act(root, cfg, *, ticket_id=None, worktree=False):
        return stub_cmd_act.rc

    stub_cmd_act.rc = ACT_RC_SUCCESS
    monkeypatch.setattr("repo_scan.radar.act.cmd_act", stub_cmd_act)

    run_act(
        tmp_repo,
        cfg,
        run,
        pending_gate_for=fake_pending_gate,
        dashboard_url=fake_dashboard_url,
        commit_vault=fake_commit_vault,
    )
    assert load_runs(tmp_repo, cfg)[0]["status"] == "done"
    assert vault_calls

    run = create_run(tmp_repo, cfg, problem, ticket="tkt-0002", kind="act")
    stub_cmd_act.rc = ACT_RC_PAUSED
    run_act(
        tmp_repo,
        cfg,
        run,
        pending_gate_for=fake_pending_gate,
        dashboard_url=fake_dashboard_url,
        commit_vault=fake_commit_vault,
    )
    assert load_runs(tmp_repo, cfg)[-1]["status"] == "waiting-on-gate"
    assert load_runs(tmp_repo, cfg)[-1]["gate"] == "post_implement"

    run = create_run(tmp_repo, cfg, problem, ticket="tkt-0003", kind="act")
    run_act(
        tmp_repo,
        cfg,
        run,
        pending_gate_for=lambda *a, **k: None,
        dashboard_url=fake_dashboard_url,
        commit_vault=fake_commit_vault,
    )
    assert load_runs(tmp_repo, cfg)[-1]["status"] == "stopped"

    run = create_run(tmp_repo, cfg, problem, ticket="tkt-0004", kind="act")
    stub_cmd_act.rc = 1
    run_act(
        tmp_repo,
        cfg,
        run,
        pending_gate_for=fake_pending_gate,
        dashboard_url=fake_dashboard_url,
        commit_vault=fake_commit_vault,
    )
    assert load_runs(tmp_repo, cfg)[-1]["status"] == "failed"


def test_daemon_test_act_degree_below_threshold(tmp_path: Path):
    """After decoupling history, daemon↔test_act coupling drops below 50%."""
    repo = tmp_path / "coupling-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)

    for i in range(7):
        _commit(
            repo,
            {_DAEMON: f"# pair {i}\n", _TEST_ACT: f"# pair {i}\n"},
            f"pair {i}",
        )
    for i in range(6):
        _commit(repo, {_TEST_ACT: f"# test solo {i}\n"}, f"test {i}")
    for i in range(5):
        _commit(repo, {_DAEMON: f"# daemon solo {i}\n"}, f"daemon {i}")
    _commit(
        repo,
        {_DAEMON: "# refactor\n", _TEST_ACT: "# refactor\n"},
        "refactor co-touch",
    )
    for i in range(6):
        _commit(repo, {_TEST_ACT: f"# decouple {i}\n"}, f"decouple {i}")

    tracked = {_DAEMON, _TEST_ACT, _ACT_RUN}
    result = analyze_history(repo, DEFAULT_CONFIG, tracked)
    pair_keys = {frozenset((c["a"], c["b"])) for c in result["coupling"]}
    seam_pair = frozenset((_DAEMON, _TEST_ACT))
    assert seam_pair not in pair_keys
