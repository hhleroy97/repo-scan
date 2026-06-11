"""Shared fixtures and helpers for the repo-scan test suite.

Vault: docs/research/sources/url-docs-pytest-org-en-stable-reference-fixtures-html
Vault: docs/research/sources/gh-pytest-dev-pytest
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _git(args: list[str], cwd: Path):
    subprocess.run(["git"] + args, cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """A minimal git repo with one Python file and one commit."""
    repo = tmp_path / "repo"
    repo.mkdir()
    # -b main: CI runners default init.defaultBranch to master, dev boxes to
    # main — tests that assert on the base branch need it deterministic
    _git(["init", "-q", "-b", "main"], repo)
    _git(["config", "user.email", "t@t.com"], repo)
    _git(["config", "user.name", "T"], repo)
    (repo / "main.py").write_text("def hello():\n    pass\n")
    _git(["add", "."], repo)
    _git(["commit", "-qm", "init"], repo)
    return repo


# Previous-scan summary that yields the writers DELTA fixture when compared
# against LINE_COUNTS + COMPLEXITY from test_writers_snapshots.
PREV_SUMMARY_FOR_DELTA = {
    "files": 3,
    "lines": 1060,
    "hotspot_functions": 1,
    "critical_files": 1,
    "cc_by_file": {"src/app.py": 18, "src/util.py": 12},
    "generated_at": "2025-12-31 00:00 UTC",
}


def freeze_writers_metadata(monkeypatch) -> None:
    """Stub volatile git/time helpers (patch module-level imports, not utils alone)."""
    import repo_scan.digest as digest
    import repo_scan.writers as writers
    from repo_scan import trends

    frozen = "2026-01-01 00:00 UTC"
    stubs = {
        "now_iso": lambda: frozen,
        "git_branch": lambda root: "main",
        "git_last_commit": lambda root: "abc1234 fixed commit",
        "git_remote_url": lambda root: "https://example.com/repo.git",
    }
    for name, fn in stubs.items():
        monkeypatch.setattr(writers, name, fn)
        monkeypatch.setattr(digest, name, fn)
    monkeypatch.setattr(trends, "now_iso", stubs["now_iso"])


@pytest.fixture
def tmp_repo_with_imports(tmp_repo: Path) -> Path:
    """tmp_repo plus an intra-repo import chain (app -> helpers)."""
    (tmp_repo / "helpers.py").write_text("def go():\n    pass\n")
    (tmp_repo / "app.py").write_text("import helpers\n\ndef run():\n    helpers.go()\n")
    _git(["add", "."], tmp_repo)
    _git(["commit", "-qm", "add imports"], tmp_repo)
    return tmp_repo
