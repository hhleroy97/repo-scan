"""Guard: every repo_scan/tickets/*.py module stays within the line budget."""

from pathlib import Path

import pytest

_TICKETS_PKG = Path(__file__).resolve().parent.parent / "repo_scan" / "tickets"
_LINE_CAP = 300


def _ticket_modules():
    return sorted(_TICKETS_PKG.glob("*.py"))


@pytest.mark.parametrize("module_path", _ticket_modules(), ids=lambda p: p.name)
def test_tickets_module_line_cap(module_path: Path):
    line_count = len(module_path.read_text(encoding="utf-8").splitlines())
    assert line_count <= _LINE_CAP, (
        f"{module_path.relative_to(_TICKETS_PKG.parent.parent)} has {line_count} lines "
        f"(cap {_LINE_CAP})"
    )
