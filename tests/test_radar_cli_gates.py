"""Explicit cli→gates dependency and shared argparse vocabulary."""

import ast
from pathlib import Path

from repo_scan.config import DEFAULT_CONFIG
from repo_scan.graphs import get_python_dep_edges
from repo_scan.radar.gates import (
    ACT_GATE_NAMES,
    GATE_MODES,
    LOOP_GATE_NAMES,
    gate_cli_parent,
)


def test_cli_imports_gates_resolves_dep_edge(tmp_path: Path):
    """``cli.py`` imports ``gates`` so the dep graph shows the seam explicitly."""
    radar = tmp_path / "repo_scan" / "radar"
    radar.mkdir(parents=True)
    (radar / "__init__.py").write_text("")
    (radar / "gates.py").write_text('"""gates."""\nGATE_MODES = ("prompt", "auto", "deny")\n')
    (radar / "cli.py").write_text(
        '"""cli."""\nfrom .gates import GATE_MODES, gate_cli_parent\n'
    )
    py_files = list(radar.glob("*.py"))
    edges = get_python_dep_edges(tmp_path, py_files, DEFAULT_CONFIG)
    assert ("repo_scan.radar.cli", "repo_scan.radar.gates") in edges


def test_cli_module_imports_gates():
    cli_path = Path(__file__).resolve().parents[1] / "repo_scan" / "radar" / "cli.py"
    tree = ast.parse(cli_path.read_text())
    imports = {
        (node.module, alias.name)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "gates"
        for alias in node.names
    }
    assert ("gates", "gate_cli_parent") in imports
    assert ("gates", "LOOP_GATE_NAMES") in imports
    assert ("gates", "ACT_GATE_NAMES") in imports


def test_gate_cli_parent_choices_match_gate_modes():
    loop_parent = gate_cli_parent(
        approve_help=f"Pre-approve a gate ({', '.join(LOOP_GATE_NAMES)}); repeatable",
        include_gates=True,
    )
    act_parent = gate_cli_parent(
        approve_help=f"Pre-approve a gate ({', '.join(ACT_GATE_NAMES)}); repeatable",
        include_gates=False,
    )
    full_parent = gate_cli_parent(approve_help=None, include_gates=True)

    loop_gates = next(a for a in loop_parent._actions if a.dest == "gates")  # noqa: SLF001
    full_gates = next(a for a in full_parent._actions if a.dest == "gates")  # noqa: SLF001
    assert loop_gates.choices == list(GATE_MODES)
    assert full_gates.choices == list(GATE_MODES)

    loop_approve = next(a for a in loop_parent._actions if a.dest == "approve")  # noqa: SLF001
    act_approve = next(a for a in act_parent._actions if a.dest == "approve")  # noqa: SLF001
    assert all(name in loop_approve.help for name in LOOP_GATE_NAMES)
    assert all(name in act_approve.help for name in ACT_GATE_NAMES)
    assert not any(a.dest == "gates" for a in act_parent._actions)  # noqa: SLF001

    assert len({id(loop_parent), id(act_parent), id(full_parent)}) == 3
