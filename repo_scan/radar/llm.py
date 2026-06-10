"""LLM completion via local agent CLIs — no API keys, no SDK dependency.

The backend shells out to whatever agent CLI is on PATH (cursor-agent, claude,
or anything configured under `"llm_cli"` in .repo-scan.json). Tests point
`llm_cli` at a fake script, so the whole loop is testable offline.
"""

import json
import re
import shlex
import shutil
import subprocess

from .sources import Source

LLM_TIMEOUT = 420

# Each candidate is a command template; the prompt is appended as the final arg.
# cursor-agent needs -f in non-interactive mode, else it exits asking for
# directory trust (or hangs waiting for the trust prompt if stdin is open).
DEFAULT_LLM_CLIS = [
    "cursor-agent -p --output-format text -f",
    "claude -p",
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


def complete(prompt: str, cfg: dict, timeout: int | None = None) -> str:
    # agent CLIs have highly variable latency (cold starts, thinking time);
    # default is generous and overridable per repo via "llm_timeout"
    if timeout is None:
        timeout = int(cfg.get("llm_timeout", LLM_TIMEOUT))
    cmd = available_backend(cfg)
    if not cmd:
        tried = ", ".join(c[0] for c in _candidates(cfg))
        raise LLMError(f"no LLM CLI found on PATH (tried: {tried})")
    try:
        result = subprocess.run(
            cmd + [prompt], capture_output=True, text=True, timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        raise LLMError(f"{cmd[0]} timed out after {timeout}s")
    if result.returncode != 0:
        raise LLMError(f"{cmd[0]} exited {result.returncode}: {result.stderr.strip()[:200]}")
    out = (result.stdout or "").strip()
    if not out:
        raise LLMError(f"{cmd[0]} returned empty output")
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


def complete_json(prompt: str, cfg: dict, timeout: int | None = None) -> dict:
    return extract_json(complete(prompt, cfg, timeout))


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


def summarize_source(source: Source, text: str, cfg: dict) -> Source:
    prompt = SUMMARIZE_PROMPT.format(
        title=source.title, type=source.type, content=text[:12000],
    )
    data = complete_json(prompt, cfg)
    source.summary = data.get("summary") or source.summary
    source.key_claims = [str(c) for c in data.get("key_claims", [])][:8]
    new_tags = [str(t) for t in data.get("tags", [])]
    source.tags = sorted(set(source.tags) | set(new_tags))
    source.relevance = data.get("relevance") or source.relevance
    return source
