"""Pipeline stage timing and token burn telemetry."""

import json
import time
from pathlib import Path

import pytest

from repo_scan.config import load_config
from repo_scan.hub.progress import progress
from repo_scan.hub.state import state_dir
from repo_scan.hub.telemetry import (
    burn_summary,
    flush_open_stage,
    format_timing_changelog,
    load_stages,
    normalize_stage_id,
    record_stage_done,
    stage_burn_average,
    stage_burn_by_run,
    stage_burn_chart,
    stage_burn_views,
    stage_summary_for_problem,
    timed_block,
)
from repo_scan.radar.llm import complete, load_usage, record_usage


PROBLEM = "how should telemetry work?"


@pytest.fixture
def cfg(tmp_repo):
    return load_config(tmp_repo)


def test_normalize_stage_id():
    assert normalize_stage_id("[2/7] Analyze") == "analyze"
    assert normalize_stage_id("[3/7] Gate 1 (post-analyze)") == "gate_1"
    assert normalize_stage_id("[4/5] Test") == "test"


def test_progress_emits_stage_done_on_transition(tmp_repo, cfg):
    progress(tmp_repo, cfg, PROBLEM, "[1/7] Research", "ingesting")
    time.sleep(0.05)
    progress(tmp_repo, cfg, PROBLEM, "[2/7] Analyze", "synthesizing")
    stages = load_stages(tmp_repo, cfg)
    assert len(stages) >= 1
    done = [s for s in stages if s.get("stage_id") == "research"]
    assert done
    assert done[0]["duration_ms"] > 0
    assert done[0]["problem"] == PROBLEM


def test_flush_open_stage_closes_inflight(tmp_repo, cfg):
    progress(tmp_repo, cfg, PROBLEM, "[1/7] Research", "start")
    time.sleep(0.02)
    flushed = flush_open_stage(tmp_repo, cfg, PROBLEM)
    assert flushed is not None
    assert flushed["stage_id"] == "research"


def test_record_stage_done_writes_jsonl(tmp_repo, cfg):
    record_stage_done(tmp_repo, cfg, PROBLEM, "analyze", "[2/7] Analyze", 1200, 500, 100)
    path = state_dir(tmp_repo, cfg) / "stages.jsonl"
    assert path.exists()
    row = json.loads(path.read_text().strip().splitlines()[-1])
    assert row["stage_id"] == "analyze"
    assert row["tokens_in"] == 500


def test_timed_block_context_manager(tmp_repo, cfg):
    with timed_block(tmp_repo, cfg, PROBLEM, "test", "test run"):
        time.sleep(0.02)
    stages = load_stages(tmp_repo, cfg)
    assert any(s.get("stage_id") == "test" for s in stages)


def test_stage_summary_for_problem(tmp_repo, cfg):
    record_stage_done(tmp_repo, cfg, PROBLEM, "research", "research", 1000, 100, 50)
    record_stage_done(tmp_repo, cfg, PROBLEM, "analyze", "analyze", 2000, 200, 80)
    summary = stage_summary_for_problem(tmp_repo, cfg, PROBLEM)
    assert summary["total_ms"] == 3000
    assert summary["total_tokens"] == 430
    assert summary["burn_per_min"] > 0


def test_format_timing_changelog():
    lines = format_timing_changelog({
        "stages": [
            {"stage_id": "research", "duration_ms": 12000, "tokens_in": 1000, "tokens_out": 200},
        ],
        "total_ms": 12000,
        "total_tokens": 1200,
        "burn_per_min": 6000,
    })
    assert any("Timing:" in ln for ln in lines)
    assert any("Burn rate:" in ln for ln in lines)


def test_usage_records_stage_id(tmp_repo, cfg, monkeypatch):
    import sys
    fake = f"{sys.executable} {Path(__file__).parent / 'fake_llm.py'}"
    cfg["llm_cli"] = [fake]
    monkeypatch.setenv("RADAR_FAKE_RESPONSE", "ok")
    from repo_scan.hub.telemetry import set_llm_context
    set_llm_context(PROBLEM, "analyze")
    complete("prompt", cfg, root=tmp_repo, role="analyze", stage_id="analyze", problem=PROBLEM)
    rows = load_usage(tmp_repo, cfg)
    assert rows[-1].get("stage_id") == "analyze"
    assert rows[-1].get("problem") == PROBLEM


def test_stage_burn_chart_aggregates_and_pct(tmp_repo, cfg):
    record_stage_done(tmp_repo, cfg, PROBLEM, "research", "research", 10000, 1000, 200)
    record_stage_done(tmp_repo, cfg, PROBLEM, "analyze", "analyze", 30000, 3000, 800)
    record_stage_done(tmp_repo, cfg, PROBLEM, "analyze", "analyze", 10000, 500, 100)
    chart = stage_burn_chart(tmp_repo, cfg)
    by_id = {r["stage_id"]: r for r in chart}
    assert by_id["analyze"]["duration_ms"] == 40000
    assert by_id["analyze"]["tokens"] == 4400
    assert by_id["analyze"]["pct_time"] > by_id["research"]["pct_time"]
    assert by_id["analyze"]["pct_tokens"] > by_id["research"]["pct_tokens"]


def test_stage_burn_average_per_run(tmp_repo, cfg):
    record_stage_done(tmp_repo, cfg, PROBLEM, "research", "r", 10000, 1000, 0)
    record_stage_done(tmp_repo, cfg, PROBLEM, "analyze", "a", 20000, 2000, 0)
    other = "second problem for average test"
    record_stage_done(tmp_repo, cfg, other, "research", "r", 20000, 2000, 0)
    record_stage_done(tmp_repo, cfg, other, "analyze", "a", 40000, 4000, 0)
    avg = stage_burn_average(tmp_repo, cfg)
    by_id = {r["stage_id"]: r for r in avg}
    assert by_id["research"]["duration_ms"] == 15000
    assert by_id["analyze"]["duration_ms"] == 30000
    assert by_id["research"]["run_count"] == 2


def test_stage_burn_by_run_and_views(tmp_repo, cfg):
    record_stage_done(tmp_repo, cfg, PROBLEM, "draft", "d", 5000, 500, 0)
    views = stage_burn_views(tmp_repo, cfg)
    assert views["run_count"] >= 1
    assert views["total"][0]["stage_id"] == "draft"
    assert views["average"][0]["duration_ms"] == 5000
    runs = stage_burn_by_run(tmp_repo, cfg)
    assert any(r["problem"] == PROBLEM for r in runs)
    assert runs[0]["chart"][0]["tokens"] == 500


def test_burn_summary_tpm(tmp_repo, cfg):
    record_usage(tmp_repo, cfg, {
        "ts": int(time.time()),
        "role": "analyze",
        "stage_id": "analyze",
        "problem": PROBLEM,
        "input_tokens": 1000,
        "output_tokens": 500,
        "duration_ms": 60000,
    })
    burn = burn_summary(tmp_repo, cfg)
    assert burn["today"]["tokens"] >= 1500
    assert burn["by_stage"].get("analyze", {}).get("tokens_per_min") == 1500
