"""B3: full radar loop with the fake-LLM response queue (offline, deterministic).

Private ``assert_*`` helpers keep the happy-path integration test readable (Assertion
Roulette fix) without splitting the artifact graph into micro-tests.
"""

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


def assert_approved_spec(docs: Path) -> Path:
    """Single spec file with approved status, goal text, and audit pass banner."""
    specs = list((docs / "specs").glob("*.md"))
    assert len(specs) == 1
    spec = specs[0].read_text()
    assert "status: approved" in spec
    assert "File-backed gates" in spec
    assert "[!success] Audit verdict: pass" in spec
    return specs[0]


def assert_analysis_confidence(docs: Path) -> Path:
    """Single analysis file reporting high confidence."""
    analysis = list((docs / "research" / "analysis").glob("*.md"))
    assert len(analysis) == 1
    assert "confidence: high" in analysis[0].read_text()
    return analysis[0]


def _assert_provenance_analysis_links(
    docs: Path, spec_text: str, analysis_text: str, analysis_stem: str,
) -> None:
    """Wikilinks from spec and analysis to the analysis artifact and run log."""
    assert analysis_stem.endswith("-analysis")
    assert f"[[{analysis_stem}]]" in spec_text
    assert "[[file-note\\|" in analysis_text
    run_log = next((docs / "research" / "runs").glob("*.md"))
    assert f"[[{run_log.stem}]]" in analysis_text


def _assert_provenance_decision_links(
    docs: Path, spec_stem: str, analysis_stem: str, run_log_stem: str,
) -> None:
    """Decisions table wikilinks and bare-link stem disambiguation."""
    assert run_log_stem != analysis_stem != spec_stem
    decisions_text = (docs / "research" / "decisions.md").read_text()
    assert f"[[{analysis_stem}]]" in decisions_text
    assert f"[[{spec_stem}]]" in decisions_text


def assert_provenance_cluster(docs: Path, spec_stem: str, analysis_stem: str) -> None:
    """Wikilinks among spec, analysis, run log, and decisions; evidence to source."""
    spec_text = (docs / "specs" / f"{spec_stem}.md").read_text()
    analysis_text = (docs / "research" / "analysis" / f"{analysis_stem}.md").read_text()
    _assert_provenance_analysis_links(docs, spec_text, analysis_text, analysis_stem)
    run_log_stem = next((docs / "research" / "runs").glob("*.md")).stem
    _assert_provenance_decision_links(docs, spec_stem, analysis_stem, run_log_stem)


def assert_loop_changelog(docs: Path) -> None:
    """Single loop changelog with approved outcome and gate pass lines."""
    loop_logs = list((docs / "changelog").glob("*-loop.md"))
    assert len(loop_logs) == 1
    log = loop_logs[0].read_text()
    assert "outcome: **approved**" in log
    assert "post_analyze: passed; post_audit: passed" in log


def assert_decisions_auto_rows(docs: Path, count: int = 2) -> None:
    """Decisions table contains the expected number of auto gate rows."""
    decisions = (docs / "research" / "decisions.md").read_text()
    assert decisions.count("| auto |") == count


def test_loop_happy_path_auto_gates(loop_env):
    root, cfg, note, queue = loop_env
    queue_responses(queue, happy_path_responses(note))

    rc = cmd_loop(root, cfg, "how should gates work?", gates_override="auto")
    assert rc == 0

    docs = root / "docs"
    spec_path = assert_approved_spec(docs)
    analysis_path = assert_analysis_confidence(docs)
    assert_provenance_cluster(docs, spec_path.stem, analysis_path.stem)
    assert_loop_changelog(docs)
    assert_decisions_auto_rows(docs)


def test_loop_pauses_at_gate1_noninteractive(loop_env):
    root, cfg, note, queue = loop_env
    queue_responses(queue, happy_path_responses(note)[:3])  # research, summarize, analyze

    rc = cmd_loop(root, cfg, "how should gates work?")  # prompt mode, no tty
    assert rc == 2

    assert list((root / "docs" / "research" / "pending").glob("post_analyze*.json"))
    assert not (root / "docs" / "specs").exists()
    log = next((root / "docs" / "changelog").glob("*-loop.md")).read_text()
    assert "outcome: **stopped**" in log


def test_loop_resumes_with_approve(loop_env):
    root, cfg, note, queue = loop_env
    # pause first
    queue_responses(queue, happy_path_responses(note)[:3])
    assert cmd_loop(root, cfg, "how should gates work?") == 2

    # resume: research/analyze come from the checkpoint, so only draft+audit
    # responses are needed; gate1 pre-approved, gate2 auto via config
    queue_responses(queue, happy_path_responses(note)[3:5])
    cfg["gates"] = {"post_audit": "auto"}
    rc = cmd_loop(root, cfg, "how should gates work?", approve=["post_analyze"])
    assert rc == 0
    assert not sorted(queue.glob("*.txt"))
    assert not list((root / "docs" / "research" / "pending").glob("post_analyze*.json"))
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


def test_spec_for_problem_matches_slug_not_mtime(tmp_repo):
    """Parallel loops finish out of order — spec resolution must key off the
    problem slug, never "newest spec file"."""
    import time

    from repo_scan.radar.pipeline import spec_for_problem
    from repo_scan.radar.sources import slugify

    cfg = load_config(tmp_repo)
    specs = tmp_repo / "docs" / "specs"
    specs.mkdir(parents=True)
    a, b = "improve the widget", "fix the gadget"
    a_stem = f"2026-06-10-{slugify(a, 40)}-spec"
    (specs / f"{a_stem}.md").write_text("a")
    time.sleep(0.05)
    (specs / f"2026-06-10-{slugify(b, 40)}-spec.md").write_text("b")  # newer

    assert spec_for_problem(tmp_repo, cfg, a) == a_stem
    assert spec_for_problem(tmp_repo, cfg, "unrelated problem") is None


def test_loop_fails_cleanly_without_backend(tmp_repo):
    cfg = load_config(tmp_repo)
    cfg["llm_cli"] = ["definitely-not-a-real-cli-xyz"]
    rc = cmd_loop(tmp_repo, cfg, "q", gates_override="auto")
    assert rc == 1
    log = next((tmp_repo / "docs" / "changelog").glob("*-loop.md")).read_text()
    assert "failed" in log
