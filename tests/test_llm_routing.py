"""Model routing, JSON envelope parsing, and the usage ledger."""

import json
import sys
from pathlib import Path

from repo_scan.config import DEFAULT_CONFIG
from repo_scan.radar.llm import (_parse_envelope, complete, load_usage,
                                 role_model)

CURSOR_ENVELOPE = json.dumps({
    "type": "result", "result": "the answer", "duration_ms": 6063,
    "usage": {"inputTokens": 33115, "outputTokens": 27,
              "cacheReadTokens": 5354, "cacheWriteTokens": 0},
})

CLAUDE_ENVELOPE = json.dumps({
    "result": "the answer", "total_cost_usd": 0.0123,
    "usage": {"input_tokens": 900, "output_tokens": 40,
              "cache_read_input_tokens": 100},
})


def test_parse_cursor_envelope():
    text, usage = _parse_envelope(CURSOR_ENVELOPE)
    assert text == "the answer"
    assert usage == {"input_tokens": 33115, "output_tokens": 27,
                     "cache_read_tokens": 5354, "duration_ms": 6063,
                     "estimated": False}


def test_parse_claude_envelope():
    text, usage = _parse_envelope(CLAUDE_ENVELOPE)
    assert text == "the answer"
    assert usage["input_tokens"] == 900
    assert usage["cache_read_tokens"] == 100
    assert usage["cost_usd"] == 0.0123


def test_parse_plain_text_and_bare_json():
    assert _parse_envelope("just prose") == ("just prose", None)
    # JSON that isn't an envelope (e.g. a fake-LLM analysis blob) passes through
    blob = '{"findings": ["a"], "recommendation": "r"}'
    assert _parse_envelope(blob) == (blob, None)


def test_role_model():
    cfg = {"llm_roles": {"act": "composer-2.5"}}
    assert role_model(cfg, "act") == "composer-2.5"
    assert role_model(cfg, "audit") is None
    assert role_model(cfg, None) is None
    assert role_model({}, "act") is None


def _argv_dumping_backend(tmp_path: Path) -> tuple[str, Path]:
    """Backend that records its argv and replies with a cursor-style envelope."""
    argv_file = tmp_path / "argv.json"
    script = tmp_path / "backend.py"
    script.write_text(f"""\
import json, sys
json.dump(sys.argv[1:], open({str(argv_file)!r}, "w"))
print(json.dumps({{"result": "done", "duration_ms": 5,
                  "usage": {{"inputTokens": 10, "outputTokens": 2}}}}))
""")
    return f"{sys.executable} {script}", argv_file


def test_complete_routes_model_and_records_real_usage(tmp_repo: Path, tmp_path: Path):
    backend, argv_file = _argv_dumping_backend(tmp_path)
    cfg = dict(DEFAULT_CONFIG)
    cfg["llm_cli"] = [backend]
    cfg["llm_roles"] = {"act": "composer-2.5"}

    out = complete("do the thing", cfg, role="act", root=tmp_repo)
    assert out == "done"
    argv = json.loads(argv_file.read_text())
    assert argv[-3:] == ["--model", "composer-2.5", "do the thing"]

    events = load_usage(tmp_repo, cfg)
    assert len(events) == 1
    e = events[0]
    assert e["role"] == "act" and e["model"] == "composer-2.5"
    assert e["input_tokens"] == 10 and e["estimated"] is False


def test_complete_no_model_flag_without_role_config(tmp_repo: Path, tmp_path: Path):
    backend, argv_file = _argv_dumping_backend(tmp_path)
    cfg = dict(DEFAULT_CONFIG)
    cfg["llm_cli"] = [backend]

    complete("hello", cfg, role="audit", root=tmp_repo)
    argv = json.loads(argv_file.read_text())
    assert "--model" not in argv
    assert load_usage(tmp_repo, cfg)[0]["model"] == "default"


def test_plain_text_backend_estimates_usage(tmp_repo: Path, tmp_path: Path):
    script = tmp_path / "plain.py"
    script.write_text('print("a plain answer with some words in it")')
    cfg = dict(DEFAULT_CONFIG)
    cfg["llm_cli"] = [f"{sys.executable} {script}"]

    out = complete("x" * 400, cfg, role="research", root=tmp_repo)
    assert "plain answer" in out
    e = load_usage(tmp_repo, cfg)[0]
    assert e["estimated"] is True
    assert e["input_tokens"] == 100  # len(prompt) // 4
    assert e["output_tokens"] > 0


def test_usage_ledger_appends(tmp_repo: Path, tmp_path: Path):
    backend, _ = _argv_dumping_backend(tmp_path)
    cfg = dict(DEFAULT_CONFIG)
    cfg["llm_cli"] = [backend]
    for _ in range(3):
        complete("go", cfg, role="draft", root=tmp_repo)
    assert len(load_usage(tmp_repo, cfg)) == 3
