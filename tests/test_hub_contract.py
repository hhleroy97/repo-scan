"""Hub server↔UI contract: explicit routes, ticket workflow, and state shape."""

import ast
import subprocess
from pathlib import Path

import pytest

from repo_scan.behavior import analyze_history
from repo_scan.config import DEFAULT_CONFIG
from repo_scan.hub import ui
from repo_scan.hub.contract import (
    API_DOC,
    API_EVENTS,
    API_GATE,
    API_PR_PREFIX,
    API_STATE,
    API_TICKET,
    API_TICKET_NEW,
    HUB_STATE_KEYS,
    TICKET_ACTION_STATUSES,
    js_contract_block,
)
from repo_scan.hub.server import build_state
from repo_scan.tickets import STATUSES

_PKG = "repo_scan/hub"
_SERVER = f"{_PKG}/server.py"
_UI = f"{_PKG}/ui/__init__.py"
_CONTRACT = f"{_PKG}/contract.py"


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


def _import_from_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    return {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }


def test_server_imports_contract_for_routes_and_actions():
    """Server routes and ticket actions use contract constants, not inline dupes."""
    mods = _import_from_modules(
        Path(__file__).resolve().parents[1] / "repo_scan" / "hub" / "server.py"
    )
    assert "contract" in mods or f"{_PKG.replace('/', '.')}.contract" in mods

    src = Path(__file__).resolve().parents[1] / "repo_scan" / "hub" / "server.py"
    text = src.read_text()
    for const in (
        "API_STATE", "API_EVENTS", "API_DOC", "API_GATE",
        "API_PR_PREFIX", "API_TICKET", "API_TICKET_NEW",
        "TICKET_ACTION_STATUSES",
    ):
        assert const in text
    for literal in (
        '"/api/state"', '"/api/events"', '"/api/doc"',
        '"/api/gate"', '"/api/ticket"', '"/api/ticket/new"',
    ):
        assert literal not in text


def test_ui_imports_contract_for_dashboard_html():
    """Dashboard HTML injects js_contract_block(); ui does not import server."""
    mods = _import_from_modules(
        Path(__file__).resolve().parents[1] / "repo_scan" / "hub" / "ui" / "__init__.py"
    )
    assert "server" not in mods
    assert js_contract_block() in ui.DASHBOARD_HTML
    assert "OPEN_TICKET_STATUSES" in ui.DASHBOARD_HTML
    assert "API_STATE" in ui.DASHBOARD_HTML


def test_dashboard_js_api_paths_match_contract():
    """Embedded JS uses API_* constants; no bare /api/* literals outside injection."""
    block = js_contract_block()
    assert block in ui.DASHBOARD_HTML
    script_start = ui.DASHBOARD_HTML.index("<script>")
    script_end = ui.DASHBOARD_HTML.index("</script>", script_start)
    script = ui.DASHBOARD_HTML[script_start:script_end]
    after_contract = script.split(block, 1)[1]
    assert "/api/" not in after_contract, "bare /api/ paths must come from contract only"
    for name, path in (
        ("API_STATE", API_STATE),
        ("API_EVENTS", API_EVENTS),
        ("API_DOC", API_DOC),
        ("API_GATE", API_GATE),
        ("API_PR_PREFIX", API_PR_PREFIX),
        ("API_TICKET", API_TICKET),
        ("API_TICKET_NEW", API_TICKET_NEW),
    ):
        assert f"const {name}=" in block
        assert path in block


def test_ticket_action_status_map_matches_server_handler():
    """Every dashboard POST action maps to a tickets.STATUSES member."""
    assert set(TICKET_ACTION_STATUSES.values()).issubset(set(STATUSES))
    assert set(TICKET_ACTION_STATUSES) == {"approve", "reject", "start", "done"}


def test_build_state_keys_match_hub_state_contract(tmp_repo):
    """build_state() top-level keys match HUB_STATE_KEYS contract."""
    state = build_state(tmp_repo, DEFAULT_CONFIG)
    assert set(state.keys()) == HUB_STATE_KEYS


def test_server_ui_degree_below_threshold(tmp_path: Path):
    """After landing + divergent history, server↔ui coupling drops below 50%."""
    repo = tmp_path / "coupling-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)

    for i in range(7):
        _commit(
            repo,
            {_SERVER: f"# pair {i}\n", _UI: f"# pair {i}\n"},
            f"pair {i}",
        )
    _commit(
        repo,
        {
            _SERVER: "# landing\n",
            _UI: "# landing\n",
            _CONTRACT: "# landing\n",
        },
        "landing",
    )
    for i in range(9):
        _commit(
            repo,
            {_SERVER: f"# server+contract {i}\n", _CONTRACT: f"# contract {i}\n"},
            f"server {i}",
        )
    for i in range(9):
        _commit(
            repo,
            {_UI: f"# ui+contract {i}\n", _CONTRACT: f"# contract {i}b\n"},
            f"ui {i}",
        )

    tracked = {_SERVER, _UI, _CONTRACT}
    result = analyze_history(repo, DEFAULT_CONFIG, tracked)
    pair_keys = {frozenset((c["a"], c["b"])) for c in result["coupling"]}
    seam_pair = frozenset((_SERVER, _UI))
    if seam_pair in pair_keys:
        degree = next(
            c["degree"]
            for c in result["coupling"]
            if frozenset((c["a"], c["b"])) == seam_pair
        )
        assert degree < DEFAULT_CONFIG["coupling_min_degree"]
    else:
        assert seam_pair not in pair_keys
