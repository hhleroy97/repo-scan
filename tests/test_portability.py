"""Regressions found by running repo-scan on a real external TS repo."""

import shutil
import subprocess
from pathlib import Path

import pytest

import repo_scan
from repo_scan.config import DEFAULT_CONFIG
from repo_scan.graphs import get_ts_dep_edges
from repo_scan.languages import get_line_counts


def test_lockfiles_excluded_from_line_counts(tmp_repo: Path):
    (tmp_repo / "package-lock.json").write_text(
        "{\n" + "\n".join(f'"dep{i}": "1.0.{i}",' for i in range(1000)) + "\n}"
    )
    counts = get_line_counts(tmp_repo, DEFAULT_CONFIG)
    assert "package-lock.json" not in counts
    assert "main.py" in counts


@pytest.mark.skipif(shutil.which("madge") is None, reason="madge not installed")
def test_ts_edges_are_repo_relative_and_find_tsx_imports(tmp_path: Path):
    """madge needs --extensions for .tsx, and its src-relative paths must be
    re-anchored to the repo root so they match ranking keys."""
    repo = tmp_path / "tsrepo"
    src = repo / "src"
    src.mkdir(parents=True)
    (src / "util.tsx").write_text("export const x = 1;\n")
    (src / "App.tsx").write_text("import { x } from './util';\nexport default x;\n")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    edges, reason = get_ts_dep_edges(repo, [src / "App.tsx", src / "util.tsx"])
    assert reason == ""
    assert ("src/App.tsx", "src/util.tsx") in edges
