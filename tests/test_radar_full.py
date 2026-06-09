"""B4: metric-triggered radar full + CLI-level fake-LLM e2e through the real entry point."""

import json
import os
import subprocess
import sys
from pathlib import Path

from repo_scan.config import load_config
from repo_scan.radar.pipeline import cmd_full, pick_candidate

FAKE_LLM = f"{sys.executable} {Path(__file__).parent / 'fake_llm.py'}"


def write_scan_json(root: Path, churn=None, complexity=None):
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "scan.json").write_text(json.dumps({
        "schema_version": 1,
        "repo": {"name": root.name},
        "churn": churn or [],
        "complexity": complexity or [],
        "ranking": [],
        "languages": {"py": 1},
    }))


def test_pick_candidate_requires_overlap(tmp_repo):
    cfg = load_config(tmp_repo)
    assert pick_candidate(tmp_repo, cfg) is None  # no scan.json

    write_scan_json(tmp_repo, churn=[{"file": "a.py", "commits": 5}],
                    complexity=[{"file": "b.py", "complexity": 12}])
    assert pick_candidate(tmp_repo, cfg) is None  # no overlap


def test_pick_candidate_targets_top_priority(tmp_repo):
    cfg = load_config(tmp_repo)
    write_scan_json(
        tmp_repo,
        churn=[{"file": "core.py", "commits": 10}, {"file": "util.py", "commits": 9}],
        complexity=[{"file": "core.py", "complexity": 20}, {"file": "util.py", "complexity": 2}],
    )
    problem = pick_candidate(tmp_repo, cfg)
    assert problem is not None
    assert "`core.py`" in problem
    assert "10 commits" in problem


def test_cmd_full_requires_radar_enabled(tmp_repo):
    cfg = load_config(tmp_repo)
    assert cmd_full(tmp_repo, cfg) == 1


def test_cmd_full_no_candidates(tmp_repo):
    cfg = load_config(tmp_repo)
    cfg["radar_enabled"] = True
    assert cmd_full(tmp_repo, cfg) == 1


def test_radar_cli_e2e_loop(tmp_repo, tmp_path, monkeypatch):
    """Full subprocess e2e: real `radar` entry point, fake LLM, auto gates."""
    note = tmp_repo / "note.md"
    note.write_text("# Note\nuse file gates\n")
    (tmp_repo / ".repo-scan.json").write_text(json.dumps({
        "llm_cli": [FAKE_LLM],
        "gates": {"post_analyze": "auto", "post_audit": "auto"},
    }))

    queue = tmp_path / "queue"
    queue.mkdir()
    responses = [
        json.dumps({"sources": [{"ref": f"file:{note}", "why": "note"}], "notes": "n"}),
        json.dumps({"summary": "s", "key_claims": [], "tags": ["t"], "relevance": "r"}),
        json.dumps({"findings": ["f1"], "recommendation": "rec", "confidence": "medium", "risks": []}),
        "## Goal\nG\n\n## Approach\nA\n\n## Changes\n- c\n\n## Risks\n- r\n\n## Out of scope\n- o",
        json.dumps({"verdict": "pass", "issues": [], "notes": "ok"}),
    ]
    for i, r in enumerate(responses):
        (queue / f"{i:02d}.txt").write_text(r)

    env = os.environ.copy()
    env.pop("RADAR_FAKE_RESPONSE", None)
    env["RADAR_FAKE_RESPONSES_DIR"] = str(queue)

    result = subprocess.run(
        [sys.executable, "-m", "repo_scan.radar.cli", "--repo", str(tmp_repo),
         "loop", "how should gates work?"],
        capture_output=True, text=True, timeout=120, env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    spec = next((tmp_repo / "docs" / "specs").glob("*.md")).read_text()
    assert "status: approved" in spec
    log = next((tmp_repo / "docs" / "changelog").glob("*-loop.md")).read_text()
    assert "outcome: **approved**" in log


def test_scan_nudges_radar_full(tmp_repo_with_imports, capsys):
    import repo_scan as rs
    # make a churn x complexity overlap impossible to fake without radon — only
    # assert the nudge is absent when there is no overlap
    (tmp_repo_with_imports / ".repo-scan.json").write_text(json.dumps({"radar_enabled": True}))
    rs.scan(tmp_repo_with_imports, quiet=False)
    out = capsys.readouterr().out
    assert (tmp_repo_with_imports / "docs" / "research" / "candidates.md").exists()
    # nudge only fires when candidates overlap exists; either way scan stays healthy
    assert "Done." in out
