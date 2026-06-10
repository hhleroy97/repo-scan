"""Pipeline stage timing and token burn telemetry.

Append-only ``stages.jsonl`` records per-stage wall clock and token totals.
``progress()`` is the primary hook; ``timed_block()`` covers non-LLM work.
"""

from __future__ import annotations

import json
import re
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

_STAGES_LOCK = threading.Lock()
_open: dict[str, dict] = {}
_ctx = threading.local()


def normalize_stage_id(stage: str) -> str:
    """``[2/7] Analyze`` → ``analyze``; ``[3/7] Gate 1 (post-analyze)`` → ``gate_1``."""
    s = stage.strip()
    if "]" in s:
        s = s.split("]", 1)[1].strip()
    s = re.sub(r"\s*\(.*", "", s)
    s = s.lower().replace(" ", "_")
    s = re.sub(r"[^\w_-]", "", s)
    return (s[:48] or "stage")


def set_llm_context(problem: str | None = None, stage_id: str | None = None) -> None:
    _ctx.problem = problem
    _ctx.stage_id = stage_id


def get_llm_context() -> tuple[str | None, str | None]:
    return getattr(_ctx, "problem", None), getattr(_ctx, "stage_id", None)


def _problem_key(problem: str) -> str:
    from .state import problem_key
    return problem_key(problem)


def _stages_path(root: Path, cfg: dict) -> Path:
    from .state import state_dir
    return state_dir(root, cfg) / "stages.jsonl"


def _usage_count(root: Path, cfg: dict) -> int:
    from ..radar.llm import load_usage
    return len(load_usage(root, cfg))


def _sum_usage_since(root: Path, cfg: dict, since_count: int,
                     problem: str | None = None, stage_id: str | None = None) -> tuple[int, int]:
    from ..radar.llm import load_usage
    rows = load_usage(root, cfg)[since_count:]
    if problem:
        rows = [r for r in rows if r.get("problem") in (problem, None)]
    if stage_id:
        matched = [r for r in rows if r.get("stage_id") == stage_id]
        if matched:
            rows = matched
    tin = sum(int(r.get("input_tokens", 0)) for r in rows)
    tout = sum(int(r.get("output_tokens", 0)) for r in rows)
    return tin, tout


def record_stage_done(root: Path, cfg: dict, problem: str, stage_id: str, label: str,
                      duration_ms: int, tokens_in: int = 0, tokens_out: int = 0,
                      **extra) -> dict:
    """Append one completed stage row and emit a feed event."""
    event = {
        "ts": int(time.time()),
        "problem": problem[:200],
        "stage_id": stage_id,
        "label": label[:120],
        "duration_ms": max(0, int(duration_ms)),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        **extra,
    }
    path = _stages_path(root, cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _STAGES_LOCK:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, separators=(",", ":")) + "\n")
    try:
        from .state import append_event
        tok = tokens_in + tokens_out
        burn = ""
        if duration_ms > 0 and tok:
            burn = f" · {tok * 60000 // duration_ms:,} tok/min"
        append_event(
            root, cfg, "stage_done",
            f"{label} · {duration_ms // 1000}s · {tok:,} tok{burn}",
            problem=problem[:120], stage_id=stage_id, duration_ms=duration_ms,
            tokens_in=tokens_in, tokens_out=tokens_out,
        )
    except OSError:
        pass
    return event


def flush_open_stage(root: Path, cfg: dict, problem: str) -> dict | None:
    """Close the in-flight stage for *problem*, if any."""
    key = _problem_key(problem)
    with _STAGES_LOCK:
        open_stage = _open.pop(key, None)
    if not open_stage:
        return None
    elapsed_ms = int((time.monotonic() - open_stage["started_mono"]) * 1000)
    tin, tout = _sum_usage_since(
        root, cfg, open_stage["usage_count"],
        problem=problem, stage_id=open_stage["stage_id"],
    )
    return record_stage_done(
        root, cfg, problem,
        open_stage["stage_id"], open_stage["label"],
        elapsed_ms, tin, tout,
    )


def flush_problem(root: Path, cfg: dict, problem: str) -> dict | None:
    """Alias for flushing the last open stage at run end."""
    return flush_open_stage(root, cfg, problem)


def transition_stage(root: Path, cfg: dict, problem: str, stage: str, detail: str = "") -> None:
    """End the prior stage (if any) and open a new one."""
    flush_open_stage(root, cfg, problem)
    stage_id = normalize_stage_id(stage)
    label = f"{stage} — {detail}" if detail else stage
    key = _problem_key(problem)
    with _STAGES_LOCK:
        _open[key] = {
            "stage_id": stage_id,
            "label": label,
            "started_mono": time.monotonic(),
            "started_ts": int(time.time()),
            "usage_count": _usage_count(root, cfg),
        }
    set_llm_context(problem, stage_id)


@contextmanager
def timed_block(root: Path, cfg: dict, problem: str, stage_id: str, label: str):
    """Time a block that does not go through ``progress()``."""
    started = time.monotonic()
    usage_count = _usage_count(root, cfg)
    set_llm_context(problem, stage_id)
    try:
        yield
    finally:
        elapsed_ms = int((time.monotonic() - started) * 1000)
        tin, tout = _sum_usage_since(root, cfg, usage_count, problem=problem, stage_id=stage_id)
        record_stage_done(root, cfg, problem, stage_id, label, elapsed_ms, tin, tout)


def _parse_iso(ts: str) -> float | None:
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        if " UTC" in ts:
            ts = ts.replace(" UTC", "+00:00")
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (ValueError, TypeError):
        return None


def record_gate_wait(root: Path, cfg: dict, problem: str, gate_name: str) -> dict | None:
    """Record human wait time from pending gate file ``written_at``."""
    from ..radar.gates import pending_path
    path = pending_path(root, cfg, gate_name, problem)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    written = _parse_iso(str(data.get("written_at", "")))
    if written is None:
        return None
    duration_ms = int(max(0, (time.time() - written) * 1000))
    return record_stage_done(
        root, cfg, problem, f"gate_wait_{gate_name}",
        f"Gate wait ({gate_name})", duration_ms, 0, 0, gate=gate_name,
    )


def load_stages(root: Path, cfg: dict, limit: int = 500) -> list[dict]:
    path = _stages_path(root, cfg)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def stages_for_problem(root: Path, cfg: dict, problem: str) -> list[dict]:
    return [s for s in load_stages(root, cfg) if s.get("problem") == problem]


def stage_summary_for_problem(root: Path, cfg: dict, problem: str) -> dict:
    """Aggregate stage rows for one problem (latest run wins per stage_id)."""
    stages = stages_for_problem(root, cfg, problem)
    if not stages:
        return {"problem": problem, "stages": [], "total_ms": 0, "total_tokens": 0,
                "burn_per_min": 0}
    by_id: dict[str, dict] = {}
    for s in stages:
        by_id[s.get("stage_id", "?")] = s
    ordered = list(by_id.values())
    total_ms = sum(int(s.get("duration_ms", 0)) for s in ordered)
    total_tokens = sum(int(s.get("tokens_in", 0)) + int(s.get("tokens_out", 0)) for s in ordered)
    burn = int(total_tokens * 60000 / total_ms) if total_ms > 0 else 0
    return {
        "problem": problem,
        "stages": ordered,
        "total_ms": total_ms,
        "total_tokens": total_tokens,
        "burn_per_min": burn,
    }


def stage_summary_recent(root: Path, cfg: dict, hours: int = 24) -> list[dict]:
    """Latest stage rows across all problems in the last *hours*."""
    cutoff = int(time.time()) - hours * 3600
    return [s for s in load_stages(root, cfg) if s.get("ts", 0) >= cutoff][-40:]


# Canonical loop/act order for chart labels (unknown stages sort last).
_STAGE_ORDER = (
    "research", "research_fetch", "analyze", "gate_1", "draft", "audit", "gate_2",
    "record", "gate_pre-implement", "branch", "implement", "test",
    "gate_post-implement",
)


def _stages_in_window(root: Path, cfg: dict, hours: int = 24) -> list[dict]:
    cutoff = int(time.time()) - hours * 3600
    return [s for s in load_stages(root, cfg) if s.get("ts", 0) >= cutoff]


def _problem_stage_totals(events: list[dict]) -> dict[str, dict]:
    """Sum stage rows within one run (problem)."""
    by_id: dict[str, dict] = {}
    for s in events:
        sid = str(s.get("stage_id") or "unknown")
        if sid in ("unknown", "None", "?"):
            continue
        row = by_id.setdefault(sid, {"stage_id": sid, "duration_ms": 0, "tokens": 0, "count": 0})
        row["duration_ms"] += int(s.get("duration_ms", 0))
        row["tokens"] += int(s.get("tokens_in", 0)) + int(s.get("tokens_out", 0))
        row["count"] += 1
    return by_id


def _finalize_chart_rows(rows: list[dict], *, run_count: int | None = None) -> list[dict]:
    """Attach pct shares, duration_s, and sort by burn."""
    rows = [r for r in rows if r.get("duration_ms") or r.get("tokens")]
    total_ms = sum(int(r.get("duration_ms", 0)) for r in rows) or 1
    total_tokens = sum(int(r.get("tokens", 0)) for r in rows) or 1
    order = {sid: i for i, sid in enumerate(_STAGE_ORDER)}

    def _sort_key(r: dict) -> tuple:
        return (-(r["duration_ms"] + r["tokens"]), order.get(r["stage_id"], 99))

    for r in rows:
        r["pct_time"] = round(100 * r["duration_ms"] / total_ms, 1)
        r["pct_tokens"] = round(100 * r["tokens"] / total_tokens, 1)
        r["duration_s"] = round(r["duration_ms"] / 1000)
        if run_count is not None:
            r["run_count"] = run_count
    rows.sort(key=_sort_key)
    return rows


def _group_stages_by_problem(stages: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for s in stages:
        problem = str(s.get("problem") or "").strip() or "unknown"
        grouped.setdefault(problem, []).append(s)
    return grouped


def _run_meta(root: Path, cfg: dict) -> dict[str, dict]:
    from .state import load_runs, problem_key
    meta: dict[str, dict] = {}
    for run in load_runs(root, cfg):
        rid = run.get("id") or problem_key(str(run.get("problem", "")))
        meta[rid] = {
            "ticket": run.get("ticket"),
            "kind": run.get("kind"),
            "status": run.get("status"),
            "problem": run.get("problem", ""),
        }
    return meta


def _run_label(problem: str, meta: dict | None) -> str:
    if meta and meta.get("ticket"):
        return f"{meta['ticket']} — {problem[:50]}"
    return problem[:72] or "(unknown run)"


def stage_burn_chart(root: Path, cfg: dict, hours: int = 24) -> list[dict]:
    """Per-stage totals for Activity chart — time and token share of pipeline burn."""
    by_id: dict[str, dict] = {}
    for s in _stages_in_window(root, cfg, hours):
        sid = str(s.get("stage_id") or "unknown")
        row = by_id.setdefault(sid, {
            "stage_id": sid,
            "duration_ms": 0,
            "tokens": 0,
            "count": 0,
        })
        row["duration_ms"] += int(s.get("duration_ms", 0))
        row["tokens"] += int(s.get("tokens_in", 0)) + int(s.get("tokens_out", 0))
        row["count"] += 1

    burn = burn_summary(root, cfg).get("by_stage", {})
    for sid, agg in burn.items():
        if sid in ("unknown", "None", "?"):
            continue
        row = by_id.setdefault(sid, {
            "stage_id": sid,
            "duration_ms": 0,
            "tokens": 0,
            "count": 0,
        })
        if not row["tokens"]:
            row["tokens"] = int(agg.get("tokens", 0))
        if not row["duration_ms"]:
            row["duration_ms"] = int(agg.get("duration_ms", 0))

    return _finalize_chart_rows(list(by_id.values()))


def stage_burn_average(root: Path, cfg: dict, hours: int = 24) -> list[dict]:
    """Per-stage mean duration/tokens across distinct runs (problems)."""
    grouped = _group_stages_by_problem(_stages_in_window(root, cfg, hours))
    if not grouped:
        return []
    run_count = len(grouped)
    sums: dict[str, dict] = {}
    for events in grouped.values():
        for sid, row in _problem_stage_totals(events).items():
            acc = sums.setdefault(sid, {"stage_id": sid, "duration_ms": 0, "tokens": 0, "count": 0})
            acc["duration_ms"] += row["duration_ms"]
            acc["tokens"] += row["tokens"]
            acc["count"] += row["count"]
    avg_rows = []
    for sid, acc in sums.items():
        avg_rows.append({
            "stage_id": sid,
            "duration_ms": int(acc["duration_ms"] / run_count),
            "tokens": int(acc["tokens"] / run_count),
            "count": acc["count"],
        })
    return _finalize_chart_rows(avg_rows, run_count=run_count)


def stage_burn_by_run(root: Path, cfg: dict, hours: int = 24) -> list[dict]:
    """Per-run stage burn — one chart payload per problem."""
    from .state import problem_key
    stages = _stages_in_window(root, cfg, hours)
    grouped = _group_stages_by_problem(stages)
    meta_by_id = _run_meta(root, cfg)
    runs = []
    for problem, events in grouped.items():
        rid = problem_key(problem)
        meta = meta_by_id.get(rid, {})
        chart = _finalize_chart_rows(list(_problem_stage_totals(events).values()))
        total_ms = sum(r["duration_ms"] for r in chart)
        total_tokens = sum(r["tokens"] for r in chart)
        runs.append({
            "id": rid,
            "problem": problem,
            "label": _run_label(problem, meta),
            "ticket": meta.get("ticket"),
            "kind": meta.get("kind") or "run",
            "status": meta.get("status"),
            "total_ms": total_ms,
            "total_tokens": total_tokens,
            "chart": chart,
        })
    runs.sort(key=lambda r: -(r["total_ms"] + r["total_tokens"]))
    return runs


def stage_burn_views(root: Path, cfg: dict, hours: int = 24) -> dict:
    """Bundle total, per-run average, and selectable per-run charts."""
    runs = stage_burn_by_run(root, cfg, hours)
    return {
        "hours": hours,
        "run_count": len(runs),
        "total": stage_burn_chart(root, cfg, hours),
        "average": stage_burn_average(root, cfg, hours),
        "runs": runs,
    }


def _fmt_duration(ms: int) -> str:
    if ms < 1000:
        return f"{ms}ms"
    secs = ms // 1000
    if secs < 60:
        return f"{secs}s"
    mins, secs = divmod(secs, 60)
    if mins < 60:
        return f"{mins}m {secs}s" if secs else f"{mins}m"
    hrs, mins = divmod(mins, 60)
    return f"{hrs}h {mins}m"


def _fmt_tok(n: int) -> str:
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def format_timing_changelog(summary: dict) -> list[str]:
    """Markdown callout lines for ``record_loop`` / ``record_act``."""
    if not summary.get("stages"):
        return []
    parts = []
    for s in summary["stages"]:
        sid = s.get("stage_id", "?")
        dur = _fmt_duration(int(s.get("duration_ms", 0)))
        tok = int(s.get("tokens_in", 0)) + int(s.get("tokens_out", 0))
        part = f"{sid} {dur}"
        if tok:
            part += f" ({_fmt_tok(tok)} tok)"
        parts.append(part)
    lines = [f"> **Timing:** {' · '.join(parts)}"]
    if summary.get("total_ms"):
        lines.append(
            f"> **Total:** {_fmt_duration(summary['total_ms'])}"
            f" · {summary.get('total_tokens', 0):,} tok"
        )
    if summary.get("burn_per_min"):
        lines.append(f"> **Burn rate:** {summary['burn_per_min']:,} tok/min")
    return lines


def burn_summary(root: Path, cfg: dict) -> dict:
    """Token burn rates from usage ledger (by role, stage, today)."""
    from ..radar.llm import load_usage, usage_summary
    events = load_usage(root, cfg)
    base = usage_summary(root, cfg)

    def _burn_agg(rows: list[dict]) -> dict:
        if not rows:
            return {"calls": 0, "tokens": 0, "duration_ms": 0, "tokens_per_min": 0}
        tokens = sum(int(r.get("input_tokens", 0)) + int(r.get("output_tokens", 0)) for r in rows)
        dur = sum(int(r.get("duration_ms", 0)) for r in rows)
        tpm = int(tokens * 60000 / dur) if dur > 0 else 0
        return {"calls": len(rows), "tokens": tokens, "duration_ms": dur, "tokens_per_min": tpm}

    by_stage: dict[str, list[dict]] = {}
    for e in events:
        by_stage.setdefault(str(e.get("stage_id", "unknown")), []).append(e)

    today_rows = [e for e in events if e.get("ts", 0) >= int(time.mktime(time.localtime()[:3] + (0, 0, 0, 0, 0, -1)))]
    today_agg = _burn_agg(today_rows)
    budget = int(cfg.get("budget_daily_tokens", 0) or 0)
    return {
        "today": today_agg,
        "by_stage": {k: _burn_agg(v) for k, v in sorted(by_stage.items())},
        "by_role": base.get("by_role", {}),
        "budget_daily_tokens": budget,
        "budget_headroom": max(0, budget - today_agg["tokens"]) if budget else None,
    }
