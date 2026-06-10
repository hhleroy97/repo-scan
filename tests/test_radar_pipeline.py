"""B3: full radar loop with the fake-LLM response queue (offline, deterministic)."""

import json
import sys
from pathlib import Path

import pytest

from repo_scan.config import load_config
from repo_scan.radar.pipeline import cmd_loop

FAKE_LLM = f"{sys.executable} {Path(__file__).parent / 'fake_llm.py'}"


def queue_responses(queue_dir: Path, responses: list[str]):
    queue_dir.mkdir(parents=True, exist_ok=True)
    for i, resp in enumerate(responses):
        (queue_dir / f"{i:02d}.txt").write_text(resp)


@pytest.fixture
def loop_env(tmp_repo, tmp_path, monkeypatch):
    """tmp repo + fake LLM queue + a local note the loop can 'research'."""
    note = tmp_repo / "note.md"
    note.write_text("# Note\nGates should be file-backed.\n")
    queue = tmp_path / "queue"
    monkeypatch.delenv("RADAR_FAKE_RESPONSE", raising=False)
    monkeypatch.setenv("RADAR_FAKE_RESPONSES_DIR", str(queue))
    cfg = load_config(tmp_repo)
    cfg["llm_cli"] = [FAKE_LLM]
    return tmp_repo, cfg, note, queue


def happy_path_responses(note: Path) -> list[str]:
    return [
        # 1 research proposal
        json.dumps({"sources": [{"ref": f"file:{note}", "why": "design note"}],
                    "notes": "use local note"}),
        # 2 summarize source
        json.dumps({"summary": "Note about gates.", "key_claims": ["file-backed gates"],
                    "tags": ["design"], "relevance": "directly relevant"}),
        # 3 analyze
        json.dumps({"findings": ["gates should be file-backed"],
                    "recommendation": "Use pending-state files for gate pauses.",
                    "confidence": "high", "risks": ["stale pending files"]}),
        # 4 draft (markdown, not JSON)
        "## Goal\nFile-backed gates.\n\n## Approach\nWrite pending JSON.\n\n"
        "## Changes\n- gates.py\n\n## Risks\n- none\n\n## Out of scope\n- UI",
        # 5 audit
        json.dumps({"verdict": "pass", "issues": [], "notes": "solid"}),
    ]


def test_loop_happy_path_auto_gates(loop_env):
    root, cfg, note, queue = loop_env
    queue_responses(queue, happy_path_responses(note))

    rc = cmd_loop(root, cfg, "how should gates work?", gates_override="auto")
    assert rc == 0

    docs = root / "docs"
    specs = list((docs / "specs").glob("*.md"))
    assert len(specs) == 1
    spec = specs[0].read_text()
    assert "status: approved" in spec
    assert "File-backed gates" in spec
    assert "[!success] Audit verdict: pass" in spec

    analysis = list((docs / "research" / "analysis").glob("*.md"))
    assert len(analysis) == 1
    analysis_text = analysis[0].read_text()
    assert "confidence: high" in analysis_text

    # provenance cluster: spec -> analysis -> sources/run log; decisions -> artifacts
    analysis_stem = analysis[0].stem
    assert analysis_stem.endswith("-analysis")
    assert f"[[{analysis_stem}]]" in spec
    assert "[[file-note\\|" in analysis_text          # evidence wikilink to source
    run_log = next((docs / "research" / "runs").glob("*.md"))
    assert f"[[{run_log.stem}]]" in analysis_text
    assert run_log.stem != analysis_stem != specs[0].stem  # bare links stay unambiguous
    decisions_text = (docs / "research" / "decisions.md").read_text()
    assert f"[[{analysis_stem}]]" in decisions_text
    assert f"[[{specs[0].stem}]]" in decisions_text

    loop_logs = list((docs / "changelog").glob("*-loop.md"))
    assert len(loop_logs) == 1
    log = loop_logs[0].read_text()
    assert "outcome: **approved**" in log
    assert "post_analyze: passed; post_audit: passed" in log

    decisions = (docs / "research" / "decisions.md").read_text()
    assert decisions.count("| auto |") == 2


def test_loop_pauses_at_gate1_noninteractive(loop_env):
    root, cfg, note, queue = loop_env
    queue_responses(queue, happy_path_responses(note)[:3])  # research, summarize, analyze

    rc = cmd_loop(root, cfg, "how should gates work?")  # prompt mode, no tty
    assert rc == 2

    assert (root / "docs" / "research" / "pending" / "post_analyze.json").exists()
    assert not (root / "docs" / "specs").exists()
    log = next((root / "docs" / "changelog").glob("*-loop.md")).read_text()
    assert "outcome: **stopped**" in log


def test_loop_resumes_with_approve(loop_env):
    root, cfg, note, queue = loop_env
    # pause first
    queue_responses(queue, happy_path_responses(note)[:3])
    assert cmd_loop(root, cfg, "how should gates work?") == 2

    # resume: full queue again, gate1 pre-approved, gate2 auto via config
    queue_responses(queue, happy_path_responses(note))
    cfg["gates"] = {"post_audit": "auto"}
    rc = cmd_loop(root, cfg, "how should gates work?", approve=["post_analyze"])
    assert rc == 0
    assert not (root / "docs" / "research" / "pending" / "post_analyze.json").exists()
    spec = next((root / "docs" / "specs").glob("*.md")).read_text()
    assert "status: approved" in spec


def test_loop_revision_round(loop_env):
    root, cfg, note, queue = loop_env
    responses = happy_path_responses(note)
    responses[4] = json.dumps({"verdict": "revise",
                               "issues": ["missing risk section detail"],
                               "notes": "needs work"})
    responses += [
        "## Goal\nRevised.\n\n## Approach\nBetter.\n\n## Changes\n- gates.py\n\n"
        "## Risks\n- stale files\n\n## Out of scope\n- UI",
        json.dumps({"verdict": "pass", "issues": [], "notes": "fixed"}),
    ]
    queue_responses(queue, responses)

    rc = cmd_loop(root, cfg, "how should gates work?", gates_override="auto")
    assert rc == 0
    spec = next((root / "docs" / "specs").glob("*.md")).read_text()
    assert "Revised." in spec
    assert "[!success] Audit verdict: pass" in spec


def test_loop_fails_cleanly_without_backend(tmp_repo):
    cfg = load_config(tmp_repo)
    cfg["llm_cli"] = ["definitely-not-a-real-cli-xyz"]
    rc = cmd_loop(tmp_repo, cfg, "q", gates_override="auto")
    assert rc == 1
    log = next((tmp_repo / "docs" / "changelog").glob("*-loop.md")).read_text()
    assert "failed" in log
