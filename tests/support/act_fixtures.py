"""Shared act and daemon test scaffolding (repos, stub agents)."""

import subprocess
import sys
from pathlib import Path

import pytest

from repo_scan.config import DEFAULT_CONFIG, load_config
from repo_scan.tickets import append_ticket_note, set_ticket_status, write_ticket


def stub_agent(tmp_path: Path, script: str) -> str:
    """An 'agent CLI' — a python script run as ``script.py <prompt>``."""
    path = tmp_path / "agent.py"
    path.write_text(script)
    return f"{sys.executable} {path}"


IMPLEMENT_AGENT = """\
import sys
from pathlib import Path
Path("impl.py").write_text("VALUE = 42\\n")
print("Implemented the spec: created impl.py with VALUE = 42.")
"""

# appends one line per invocation — lets tests require N agent calls
COUNTING_AGENT = """\
import sys
from pathlib import Path
p = Path("counter.txt")
p.write_text(p.read_text() + "x\\n" if p.exists() else "x\\n")
print("ran")
"""


@pytest.fixture
def act_repo(tmp_repo: Path, tmp_path: Path):
    """tmp repo with an in-progress ticket linked to an approved spec."""
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
    """In-progress ticket with acceptance tests named in the spec."""
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
