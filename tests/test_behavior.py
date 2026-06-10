"""Behavioral analysis: change coupling, ownership/bus-factor, code age."""

import subprocess
from pathlib import Path

import pytest

import repo_scan
from repo_scan.behavior import analyze_history, hidden_seams
from repo_scan.config import DEFAULT_CONFIG


def _commit(repo: Path, files: dict[str, str], author: str, msg: str = "c"):
    for name, content in files.items():
        (repo / name).write_text(content)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", f"user.name={author}", "-c", f"user.email={author}@t.com",
         "commit", "-qm", msg],
        cwd=repo, check=True, capture_output=True)


@pytest.fixture
def behavior_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "brepo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    # a.py and b.py always change together (5 shared commits) by alice;
    # c.py changes alone, by bob
    for i in range(5):
        _commit(repo, {"a.py": f"x = {i}\n", "b.py": f"y = {i}\n"}, "alice", f"pair {i}")
    _commit(repo, {"c.py": "z = 1\n"}, "bob", "solo")
    return repo


def test_change_coupling_detected(behavior_repo: Path):
    tracked = {"a.py", "b.py", "c.py"}
    result = analyze_history(behavior_repo, DEFAULT_CONFIG, tracked)
    pairs = {(c["a"], c["b"]): c for c in result["coupling"]}
    assert ("a.py", "b.py") in pairs
    pair = pairs[("a.py", "b.py")]
    assert pair["shared"] == 5
    assert pair["degree"] == 100
    assert not any("c.py" in (c["a"], c["b"]) for c in result["coupling"])


def test_ownership_and_age(behavior_repo: Path):
    result = analyze_history(behavior_repo, DEFAULT_CONFIG, {"a.py", "c.py"})
    own = {o["file"]: o for o in result["ownership"]}
    assert own["a.py"]["top_share"] == 1.0
    assert own["a.py"]["authors"] == 1
    assert own["a.py"]["commits"] == 5
    assert own["c.py"]["top_author"] == "bob@t.com"
    assert result["age_days"]["a.py"] == 0  # just committed


def test_untracked_files_ignored(behavior_repo: Path):
    result = analyze_history(behavior_repo, DEFAULT_CONFIG, {"a.py"})
    assert result["coupling"] == []  # b.py not tracked, so no pair
    assert {o["file"] for o in result["ownership"]} == {"a.py"}


def test_mass_changesets_excluded(tmp_path: Path):
    repo = tmp_path / "mass"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    files = {f"f{i}.py": "x = 1\n" for i in range(40)}
    for n in range(5):
        _commit(repo, {k: f"x = {n}\n" for k in files}, "alice", f"mass {n}")
    cfg = dict(DEFAULT_CONFIG, coupling_max_changeset=30)
    result = analyze_history(repo, cfg, set(files))
    assert result["coupling"] == []  # 40-file commits say nothing about coupling


def test_hidden_seams_excludes_imported_pairs():
    coupling = [
        {"a": "repo_scan/scanner.py", "b": "repo_scan/writers.py", "shared": 5, "degree": 80},
        {"a": "repo_scan/radar/cli.py", "b": "repo_scan/radar/gates.py", "shared": 4, "degree": 80},
        {"a": "src/api.ts", "b": "src/billing.ts", "shared": 6, "degree": 90},
    ]
    edges = [
        ("repo_scan.scanner", "repo_scan.writers"),
        ("repo_scan.radar.cli", "repo_scan.radar.gates"),
    ]
    seams = hidden_seams(coupling, edges)
    assert len(seams) == 1
    assert seams[0]["a"] == "src/api.ts"


def test_scan_writes_coupling_report_and_knowledge_map(behavior_repo: Path):
    repo_scan.scan(behavior_repo, quiet=True)
    coupling = (behavior_repo / "docs" / "reports" / "coupling.md").read_text()
    assert "a.py" in coupling and "b.py" in coupling
    assert "hidden seam" in coupling
    health = (behavior_repo / "docs" / "reports" / "health.md").read_text()
    assert "## Knowledge map (bus factor)" in health
    assert "silo" in health  # alice owns a.py/b.py with 5 commits each
