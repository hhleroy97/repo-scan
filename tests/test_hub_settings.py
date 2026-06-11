"""Hub settings contract: explicit config↔daemon seam via hub.settings."""

import ast
import json
import subprocess
from pathlib import Path

from repo_scan.behavior import analyze_history
from repo_scan.config import DEFAULT_CONFIG, load_config
from repo_scan.hub.settings import HUB_DEFAULTS

_PKG = "repo_scan"
_CONFIG = f"{_PKG}/config.py"
_DAEMON = f"{_PKG}/hub/daemon.py"
_SETTINGS = f"{_PKG}/hub/settings.py"

_HUB_CFG_GET_DEFAULTS = {
    "serve_port": {8800},
    "daemon_poll_seconds": {20},
    "daemon_scan_hours": {6},
    "vault_autocommit": {True},
    "max_parallel_acts": {2},
    "max_parallel_loops": {2},
}


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


def test_config_defines_hub_settings():
    """config.py defines HUB_CONFIG_KEYS and HUB_DEFAULTS (core layer)."""
    config_path = Path(__file__).resolve().parents[1] / "repo_scan" / "config.py"
    source = config_path.read_text()
    assert "HUB_CONFIG_KEYS" in source
    assert "HUB_DEFAULTS" in source
    tree = ast.parse(source)
    import_froms = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "hub.settings" not in import_froms, "config must not import hub (layer violation)"


def test_daemon_imports_hub_settings():
    """daemon.py imports hub.settings and does not inline hub-key magic defaults."""
    daemon_path = Path(__file__).resolve().parents[1] / "repo_scan" / "hub" / "daemon.py"
    source = daemon_path.read_text()
    tree = ast.parse(source)
    import_froms = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "settings" in import_froms

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "get"):
            continue
        if not (isinstance(func.value, ast.Name) and func.value.id == "cfg"):
            continue
        if len(node.args) < 2 or not isinstance(node.args[0], ast.Constant):
            continue
        key = node.args[0].value
        if key not in _HUB_CFG_GET_DEFAULTS:
            continue
        default = node.args[1]
        if isinstance(default, ast.Constant) and default.value in _HUB_CFG_GET_DEFAULTS[key]:
            raise AssertionError(
                f"daemon.py still hardcodes cfg.get({key!r}, {default.value!r}); use cfg_hub"
            )


def test_load_config_applies_hub_defaults(tmp_path: Path):
    """Empty repo load_config includes every HUB_DEFAULTS key; overrides win."""
    cfg = load_config(tmp_path)
    for key, value in HUB_DEFAULTS.items():
        assert cfg[key] == value

    (tmp_path / ".repo-scan.json").write_text(json.dumps({"serve_port": 9999}))
    cfg = load_config(tmp_path)
    assert cfg["serve_port"] == 9999
    assert cfg["daemon_poll_seconds"] == HUB_DEFAULTS["daemon_poll_seconds"]


def test_hub_config_keys_accepted_in_repo_scan_json(tmp_path: Path):
    """Hub-only keys (e.g. serve_host) validate even when not in DEFAULT_CONFIG."""
    (tmp_path / ".repo-scan.json").write_text(json.dumps({"serve_host": "myhost"}))
    cfg = load_config(tmp_path)
    assert cfg["serve_host"] == "myhost"


def test_config_daemon_degree_below_threshold(tmp_path: Path):
    """After decoupling history, config↔daemon coupling drops below 50%."""
    repo = tmp_path / "coupling-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)

    for i in range(7):
        _commit(
            repo,
            {_CONFIG: f"# pair {i}\n", _DAEMON: f"# pair {i}\n"},
            f"pair {i}",
        )
    for i in range(6):
        _commit(repo, {_CONFIG: f"# config solo {i}\n"}, f"config {i}")
    for i in range(5):
        _commit(repo, {_DAEMON: f"# daemon solo {i}\n"}, f"daemon {i}")
    _commit(
        repo,
        {_CONFIG: "# refactor\n", _DAEMON: "# refactor\n"},
        "refactor co-touch",
    )
    for i in range(6):
        _commit(repo, {_CONFIG: f"# decouple {i}\n"}, f"decouple {i}")

    tracked = {_CONFIG, _DAEMON, _SETTINGS}
    result = analyze_history(repo, DEFAULT_CONFIG, tracked)
    pair_keys = {frozenset((c["a"], c["b"])) for c in result["coupling"]}
    seam_pair = frozenset((_CONFIG, _DAEMON))
    assert seam_pair not in pair_keys
