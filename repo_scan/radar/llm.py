"""LLM completion via local agent CLIs — no API keys, no SDK dependency.

The backend shells out to whatever agent CLI is on PATH (cursor-agent, claude,
or anything configured under `"llm_cli"` in .repo-scan.json). Tests point
`llm_cli` at a fake script, so the whole loop is testable offline.

Two cross-cutting concerns live here so every stage gets them for free:

- **model routing** — `"llm_roles": {"act": "composer-2.5", ...}` appends
  `--model <name>` per role, so cheap models do the labor (act) while the
  default does the judgment (analyze, audit)
- **usage ledger** — cursor-agent/claude JSON envelopes carry real token
  counts; every call is appended to docs/.radar/usage.jsonl for the TUI and
  web dashboard (plain-text backends fall back to a chars/4 estimate)
"""

import json
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from .sources import Source

LLM_TIMEOUT = 420

# Each candidate is a command template; the prompt is appended as the final arg.
# cursor-agent needs -f in non-interactive mode, else it exits asking for
# directory trust (or hangs waiting for the trust prompt if stdin is open).
# JSON output gives us the result text plus real token usage in one envelope.
DEFAULT_LLM_CLIS = [
    "cursor-agent -p --output-format json -f",
    "claude -p --output-format json",
]


class LLMError(Exception):
    pass


def _candidates(cfg: dict) -> list[list[str]]:
    raw = cfg.get("llm_cli", DEFAULT_LLM_CLIS)
    if isinstance(raw, str):
        raw = [raw]
    return [shlex.split(c) for c in raw if c]


def available_backend(cfg: dict) -> list[str] | None:
    for cmd in _candidates(cfg):
        if cmd and shutil.which(cmd[0]):
            return cmd
    return None


def role_model(cfg: dict, role: str | None) -> str | None:
    """Model override for a pipeline role ("research", "analyze", "draft",
    "audit", "act", "act_fix"), or None to use the backend's default."""
    if not role:
        return None
    model = cfg.get("llm_roles", {}).get(role)
    return str(model) if model else None


def _parse_envelope(raw: str) -> tuple[str, dict | None]:
    """Unwrap an agent CLI JSON envelope -> (result_text, usage|None).

    cursor-agent: {"result": "...", "usage": {"inputTokens": N, ...}, "duration_ms": N}
    claude:       {"result": "...", "usage": {"input_tokens": N, ...}, "total_cost_usd": F}
    Anything that doesn't parse as such is treated as plain text.
    """
    if not raw.lstrip().startswith("{"):
        return raw, None
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return raw, None
    if not isinstance(obj, dict) or "result" not in obj:
        return raw, None
    u = obj.get("usage") or {}
    usage = {
        "input_tokens": int(u.get("inputTokens", u.get("input_tokens", 0)) or 0),
        "output_tokens": int(u.get("outputTokens", u.get("output_tokens", 0)) or 0),
        "cache_read_tokens": int(u.get("cacheReadTokens", u.get("cache_read_input_tokens", 0)) or 0),
        "duration_ms": int(obj.get("duration_ms", 0) or 0),
        "estimated": False,
    }
    if obj.get("total_cost_usd") is not None:
        usage["cost_usd"] = float(obj["total_cost_usd"])
    return str(obj.get("result") or ""), usage


def record_usage(root: Path | None, cfg: dict, event: dict):
    """Append one call to the file-backed usage ledger (best-effort)."""
    if root is None:
        return
    try:
        from ..hub.state import state_dir
        path = state_dir(root, cfg) / "usage.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, separators=(",", ":")) + "\n")
    except OSError:
        pass


def load_usage(root: Path, cfg: dict, limit: int = 2000) -> list[dict]:
    from ..hub.state import state_dir
    path = state_dir(root, cfg) / "usage.jsonl"
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _agg(events: list[dict]) -> dict:
    out = {
        "calls": len(events),
        "input_tokens": sum(e.get("input_tokens", 0) for e in events),
        "output_tokens": sum(e.get("output_tokens", 0) for e in events),
        "cache_read_tokens": sum(e.get("cache_read_tokens", 0) for e in events),
        "duration_ms": sum(e.get("duration_ms", 0) for e in events),
        "estimated": any(e.get("estimated") for e in events),
    }
    costs = [e["cost_usd"] for e in events if e.get("cost_usd") is not None]
    if costs:
        out["cost_usd"] = round(sum(costs), 4)
    return out


def usage_summary(root: Path, cfg: dict) -> dict:
    """Aggregated view of the usage ledger for dashboards (web + TUI)."""
    events = load_usage(root, cfg)
    midnight = time.mktime(time.localtime()[:3] + (0, 0, 0, 0, 0, -1))
    today = [e for e in events if e.get("ts", 0) >= midnight]

    def group(key: str) -> dict:
        groups: dict[str, list[dict]] = {}
        for e in events:
            groups.setdefault(str(e.get(key, "?")), []).append(e)
        return {k: _agg(v) for k, v in sorted(groups.items())}

    return {
        "total": _agg(events),
        "today": _agg(today),
        "by_role": group("role"),
        "by_model": group("model"),
        "recent": events[-8:][::-1],
    }


def complete(prompt: str, cfg: dict, timeout: int | None = None,
             cwd: str | None = None, role: str | None = None,
             root: Path | None = None) -> str:
    # agent CLIs have highly variable latency (cold starts, thinking time);
    # default is generous and overridable per repo via "llm_timeout".
    # `cwd` matters for act-mode invocations where the agent edits files.
    if timeout is None:
        timeout = int(cfg.get("llm_timeout", LLM_TIMEOUT))
    cmd = available_backend(cfg)
    if not cmd:
        tried = ", ".join(c[0] for c in _candidates(cfg))
        raise LLMError(f"no LLM CLI found on PATH (tried: {tried})")
    model = role_model(cfg, role)
    if model:
        cmd = cmd + ["--model", model]
    started = time.time()
    try:
        result = subprocess.run(
            cmd + [prompt], capture_output=True, text=True, timeout=timeout,
            stdin=subprocess.DEVNULL, cwd=cwd,
        )
    except subprocess.TimeoutExpired:
        raise LLMError(f"{cmd[0]} timed out after {timeout}s")
    if result.returncode != 0:
        raise LLMError(f"{cmd[0]} exited {result.returncode}: {result.stderr.strip()[:200]}")
    raw = (result.stdout or "").strip()
    if not raw:
        raise LLMError(f"{cmd[0]} returned empty output")
    out, usage = _parse_envelope(raw)
    out = out.strip()
    if not out:
        raise LLMError(f"{cmd[0]} envelope had an empty result")
    if usage is None:  # plain-text backend: estimate so the ledger stays useful
        usage = {
            "input_tokens": len(prompt) // 4,
            "output_tokens": len(out) // 4,
            "cache_read_tokens": 0,
            "duration_ms": int((time.time() - started) * 1000),
            "estimated": True,
        }
    record_usage(root, cfg, {
        "ts": int(time.time()),
        "role": role or "general",
        "backend": cmd[0],
        "model": model or "default",
        **usage,
    })
    if root is not None:
        try:
            from ..hub.state import append_event
            secs = usage.get("duration_ms", 0) / 1000
            append_event(root, cfg, "llm",
                         f"{role or 'general'} · {model or 'default'} · "
                         f"{usage.get('input_tokens', 0):,}→{usage.get('output_tokens', 0):,} tok"
                         f" · {secs:.0f}s",
                         role=role or "general", model=model or "default")
        except OSError:
            pass
    return out


def extract_json(text: str) -> dict:
    """Pull the first JSON object out of LLM output (tolerates fences/prose)."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            raise LLMError(f"no JSON object in LLM output: {text[:120]!r}")
        candidate = text[start:end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        raise LLMError(f"LLM output was not valid JSON: {e}") from e


def complete_json(prompt: str, cfg: dict, timeout: int | None = None,
                  role: str | None = None, root: Path | None = None) -> dict:
    return extract_json(complete(prompt, cfg, timeout, role=role, root=root))


SUMMARIZE_PROMPT = """You are indexing a research source for a software project's knowledge base.

Source title: {title}
Source type: {type}

Content:
---
{content}
---

Respond with ONLY a JSON object:
{{
  "summary": "2-4 sentence summary of what this source is and why it matters",
  "key_claims": ["claim 1", "claim 2", "..."],
  "tags": ["lowercase-tag", "..."],
  "relevance": "one sentence on how this could apply to a software project"
}}"""


def summarize_source(source: Source, text: str, cfg: dict,
                     root: Path | None = None) -> Source:
    prompt = SUMMARIZE_PROMPT.format(
        title=source.title, type=source.type, content=text[:12000],
    )
    data = complete_json(prompt, cfg, role="research", root=root)
    source.summary = data.get("summary") or source.summary
    source.key_claims = [str(c) for c in data.get("key_claims", [])][:8]
    new_tags = [str(t) for t in data.get("tags", [])]
    source.tags = sorted(set(source.tags) | set(new_tags))
    source.relevance = data.get("relevance") or source.relevance
    return source
