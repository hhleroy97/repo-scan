"""Scan-over-scan deltas — the "verify" half of the reflexion loop.

Each scan compares itself against the previous docs/scan.json before
overwriting it, surfaces the delta in index.md, and appends a row to
reports/trend.md. This is what lets a RADAR intervention be judged by
whether the metrics actually moved afterwards.
"""

import json
import re
from pathlib import Path

from .utils import now_iso, write_doc

TREND_MAX_ROWS = 60


def summarize_metrics(line_counts: dict, complexity: list, cfg: dict) -> dict:
    """Compact health snapshot used for scan-over-scan comparison."""
    cc_by_file: dict[str, int] = {}
    for item in complexity:
        cc_by_file[item["file"]] = cc_by_file.get(item["file"], 0) + item["complexity"]
    return {
        "files": len(line_counts),
        "lines": sum(s["lines"] for s in line_counts.values()),
        "hotspot_functions": len(complexity),
        "critical_files": sum(1 for s in line_counts.values() if s["lines"] >= cfg["line_crit"]),
        "cc_by_file": cc_by_file,
    }


def load_previous_summary(root: Path, cfg: dict) -> dict | None:
    """Summary of the last scan, read from scan.json before it is overwritten."""
    path = root / cfg["docs_dir"] / "scan.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        summary = summarize_metrics(data["files"], data["complexity"], cfg)
        summary["generated_at"] = data.get("generated_at", "?")
        return summary
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def compute_delta(prev: dict | None, curr: dict) -> dict | None:
    if prev is None:
        return None
    movers = []
    for f in set(prev["cc_by_file"]) | set(curr["cc_by_file"]):
        diff = curr["cc_by_file"].get(f, 0) - prev["cc_by_file"].get(f, 0)
        if diff:
            movers.append((f, diff))
    movers.sort(key=lambda x: abs(x[1]), reverse=True)
    return {
        "since": prev.get("generated_at", "?"),
        "lines": curr["lines"] - prev["lines"],
        "files": curr["files"] - prev["files"],
        "hotspot_functions": curr["hotspot_functions"] - prev["hotspot_functions"],
        "critical_files": curr["critical_files"] - prev["critical_files"],
        "cc_movers": movers[:5],
    }


def _signed(n: int) -> str:
    return f"+{n}" if n > 0 else str(n)


def trend_callout(delta: dict | None) -> list[str]:
    """Index.md trend block. Empty when there is no previous scan or no change."""
    if delta is None:
        return []
    changed = any(delta[k] for k in ("lines", "files", "hotspot_functions", "critical_files")) \
        or delta["cc_movers"]
    if not changed:
        return ["> [!tip] No metric changes since last scan", ""]
    worse = delta["hotspot_functions"] > 0 or delta["critical_files"] > 0
    kind = "warning" if worse else "note"
    body = [
        f"lines {_signed(delta['lines'])}, files {_signed(delta['files'])}, "
        f"hotspot functions {_signed(delta['hotspot_functions'])}, "
        f"critical files {_signed(delta['critical_files'])}",
    ]
    for f, diff in delta["cc_movers"][:3]:
        body.append(f"- `{f}` complexity {_signed(diff)}")
    return [f"> [!{kind}] Since last scan ({delta['since']})"] + \
        [f"> {line}" for line in body] + [""]


def append_trend_log(root: Path, cfg: dict, curr: dict, delta: dict | None):
    """Append one row per scan to reports/trend.md (capped, oldest dropped)."""
    path = root / cfg["docs_dir"] / "reports" / "trend.md"
    rows: list[str] = []
    if path.exists():
        rows = [l for l in path.read_text(encoding="utf-8").splitlines()
                if re.match(r"^\| \d{4}-", l)]

    d_lines = _signed(delta["lines"]) if delta else "—"
    d_hot = _signed(delta["hotspot_functions"]) if delta else "—"
    rows.append(f"| {now_iso()} | {curr['files']} | {curr['lines']} | "
                f"{curr['hotspot_functions']} | {curr['critical_files']} | "
                f"{d_lines} | {d_hot} |")
    rows = rows[-TREND_MAX_ROWS:]

    content = "\n".join([
        "# Scan trend",
        "",
        "One row per scan — the long-term memory that makes interventions",
        "measurable. Newest at the bottom.",
        "",
        "| When | Files | Lines | Hotspot fns | Critical | Δ lines | Δ hotspots |",
        "|------|-------|-------|-------------|----------|---------|------------|",
        *rows,
        "",
    ])
    write_doc(path, content, root)
