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


def summarize_metrics(line_counts: dict, complexity: list, cfg: dict,
                      vault_health: dict | None = None) -> dict:
    """Compact health snapshot used for scan-over-scan comparison."""
    cc_by_file: dict[str, int] = {}
    for item in complexity:
        cc_by_file[item["file"]] = cc_by_file.get(item["file"], 0) + item["complexity"]
    out = {
        "files": len(line_counts),
        "lines": sum(s["lines"] for s in line_counts.values()),
        "hotspot_functions": len(complexity),
        "critical_files": sum(1 for s in line_counts.values() if s["lines"] >= cfg["line_crit"]),
        "cc_by_file": cc_by_file,
    }
    if vault_health:
        out["vault_coverage_pct"] = vault_health.get("coverage_pct", 0.0)
        out["untracked_code_count"] = vault_health.get("untracked_code_count", 0)
    return out


def load_trend_sparkline(root: Path, cfg: dict, limit: int = 12) -> list[dict]:
    """Last N rows from reports/trend.md for dashboard sparklines (newest last)."""
    path = root / cfg["docs_dir"] / "reports" / "trend.md"
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\| \d{4}-", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 8:
            continue
        vault_raw = cells[7]
        vault_pct = None
        if vault_raw and vault_raw != "—":
            m = re.match(r"(\d+)%", vault_raw)
            if m:
                vault_pct = int(m.group(1)) / 100.0
        rows.append({
            "when": cells[0],
            "files": int(cells[1]),
            "lines": int(cells[2]),
            "hotspots": int(cells[3]),
            "vault_pct": vault_pct,
        })
    return rows[-limit:]


def load_previous_summary(root: Path, cfg: dict) -> dict | None:
    """Summary of the last scan, read from scan.json before it is overwritten."""
    path = root / cfg["docs_dir"] / "scan.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        summary = summarize_metrics(
            data["files"], data["complexity"], cfg,
            vault_health=data.get("vault_health"),
        )
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
    delta = {
        "since": prev.get("generated_at", "?"),
        "lines": curr["lines"] - prev["lines"],
        "files": curr["files"] - prev["files"],
        "hotspot_functions": curr["hotspot_functions"] - prev["hotspot_functions"],
        "critical_files": curr["critical_files"] - prev["critical_files"],
        "cc_movers": movers[:5],
    }
    if "vault_coverage_pct" in curr and "vault_coverage_pct" in prev:
        delta["vault_coverage_pct"] = round(
            curr["vault_coverage_pct"] - prev["vault_coverage_pct"], 4)
    if "untracked_code_count" in curr and "untracked_code_count" in prev:
        delta["untracked_code_count"] = (
            curr["untracked_code_count"] - prev["untracked_code_count"])
    return delta


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
    if delta.get("vault_coverage_pct") is not None:
        pct_delta = delta["vault_coverage_pct"]
        if abs(pct_delta) >= 0.05:
            body.append(
                f"- vault coverage {_signed(int(round(pct_delta * 100)))}%")
    if delta.get("untracked_code_count") is not None and delta["untracked_code_count"]:
        body.append(
            f"- untracked ranked code {_signed(delta['untracked_code_count'])}")
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
    vault_pct = curr.get("vault_coverage_pct")
    vault_s = f"{int(round(vault_pct * 100))}%" if vault_pct is not None else "—"
    d_vault = "—"
    if delta and delta.get("vault_coverage_pct") is not None:
        d_vault = _signed(int(round(delta["vault_coverage_pct"] * 100))) + "%"
    rows.append(f"| {now_iso()} | {curr['files']} | {curr['lines']} | "
                f"{curr['hotspot_functions']} | {curr['critical_files']} | "
                f"{d_lines} | {d_hot} | {vault_s} | {d_vault} |")
    rows = rows[-TREND_MAX_ROWS:]

    content = "\n".join([
        "# Scan trend",
        "",
        "One row per scan — the long-term memory that makes interventions",
        "measurable. Newest at the bottom.",
        "",
        "| When | Files | Lines | Hotspot fns | Critical | Δ lines | Δ hotspots | Vault % | Δ vault |",
        "|------|-------|-------|-------------|----------|---------|------------|---------|---------|",
        *rows,
        "",
    ])
    write_doc(path, content, root)
