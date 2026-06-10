"""Regressions found by running repo-scan on a real external TS repo."""

import shutil
import subprocess
from pathlib import Path

import pytest

import repo_scan
from repo_scan.complexity import _ccn_rank, _min_ccn, get_complexity, get_lizard_complexity
from repo_scan.config import DEFAULT_CONFIG
from repo_scan.graphs import get_ts_dep_edges
import repo_scan.languages as languages
from repo_scan.languages import get_line_counts


def test_lockfiles_excluded_from_line_counts(tmp_repo: Path, monkeypatch):
    (tmp_repo / "package-lock.json").write_text(
        "{\n" + "\n".join(f'"dep{i}": "1.0.{i}",' for i in range(1000)) + "\n}"
    )
    monkeypatch.setattr(languages, "tool_available", lambda name: False)
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


def test_ccn_rank_mapping():
    assert _ccn_rank(1) == "A"
    assert _ccn_rank(11) == "C"
    assert _ccn_rank(42) == "F"
    assert _min_ccn("C") == 11
    assert _min_ccn("A") == 1


COMPLEX_TS = "export function branchy(n: number) {\n" + "".join(
    f"  if (n === {i}) return {i};\n" for i in range(15)
) + "  return -1;\n}\n"


@pytest.mark.skipif(shutil.which("lizard") is None, reason="lizard not installed")
def test_lizard_covers_typescript(tmp_repo: Path):
    (tmp_repo / "branchy.ts").write_text(COMPLEX_TS)
    rows = get_lizard_complexity(tmp_repo, DEFAULT_CONFIG)
    match = [r for r in rows if r["file"] == "branchy.ts"]
    assert match and match[0]["complexity"] >= 11
    assert match[0]["rank"] in "CDEF"

    # merged path: python rows via radon (if present) + ts rows via lizard
    merged = get_complexity(tmp_repo, [tmp_repo / "main.py"], DEFAULT_CONFIG)
    assert any(r["file"] == "branchy.ts" for r in merged)


@pytest.mark.skipif(shutil.which("lizard") is None, reason="lizard not installed")
def test_lizard_skips_excluded_dirs(tmp_repo: Path):
    vendored = tmp_repo / "node_modules" / "pkg"
    vendored.mkdir(parents=True)
    (vendored / "dep.ts").write_text(COMPLEX_TS)
    rows = get_lizard_complexity(tmp_repo, DEFAULT_CONFIG)
    assert not any("node_modules" in r["file"] for r in rows)
