"""Scan-driven ticket generation, fingerprint dedup, and auto-close."""

import json
from pathlib import Path

from ..utils import check_scan_schema_version
from .board import write_board
from .constants import METRIC_FINGERPRINT_PREFIXES, OPEN_STATUSES, _SCAN_PROPOSAL_KEYS
from .io import load_tickets, next_ticket_num, write_ticket
from .propose import propose_from_scan
from .workflow import append_ticket_note, set_ticket_status


def generate_tickets(root: Path, cfg: dict, signals: dict) -> tuple[int, list[dict]]:
    """Dedup proposals against every existing fingerprint (any status,
    including rejected) and write the top N new tickets.

    Returns (created_count, metrics_resolved) where metrics_resolved are open
    tickets whose fingerprint no longer triggers — the underlying metric
    cleared, so they're likely ready to close."""
    existing = load_tickets(root, cfg)
    known = {t.get("fingerprint") for t in existing if t.get("fingerprint")}
    scan_kw = {k: signals[k] for k in _SCAN_PROPOSAL_KEYS if k in signals}
    proposals = propose_from_scan(cfg, **scan_kw)
    current_fps = {p["fingerprint"] for p in proposals}
    fresh = [p for p in proposals if p["fingerprint"] not in known]
    cap = cfg.get("tickets_max_new_per_scan", 5)
    num = next_ticket_num(existing)
    created = 0
    for p in fresh[:cap]:
        p["id"] = f"tkt-{num + created:04d}"
        write_ticket(root, cfg, p, signals=signals)
        created += 1

    resolved = [t for t in existing
                if t.get("status") in OPEN_STATUSES
                and t.get("fingerprint") and t["fingerprint"] not in current_fps]
    if created or existing:
        write_board(root, cfg, load_tickets(root, cfg),
                    resolved_ids={t["id"] for t in resolved})
    auto_close_resolved_proposed(root, cfg, resolved)
    return created, resolved


def is_metric_fingerprint(fingerprint: str) -> bool:
    return any(fingerprint.startswith(p) for p in METRIC_FINGERPRINT_PREFIXES)


def auto_close_resolved_proposed(root: Path, cfg: dict,
                                 resolved: list[dict]) -> list[str]:
    """Close proposed tickets whose scan metric fingerprint no longer triggers."""
    closed = []
    for t in resolved:
        if t.get("status") != "proposed":
            continue
        if not is_metric_fingerprint(str(t.get("fingerprint", ""))):
            continue
        set_ticket_status(root, cfg, t["id"], "done")
        append_ticket_note(root, cfg, t["id"],
                           "auto-closed: metric fingerprint cleared on scan")
        closed.append(t["id"])
    if closed:
        write_board(root, cfg, load_tickets(root, cfg))
    return closed


def signals_from_scan_json(data: dict) -> dict:
    """Rebuild proposal inputs from a scan.json payload."""
    behavior = data.get("behavior") or {}
    return {
        "line_counts": data.get("files", {}),
        "ranking": data.get("ranking", []),
        "churn": data.get("churn", []),
        "complexity": data.get("complexity", []),
        "tested": {r["file"] for r in data.get("ranking", []) if r.get("tested")},
        "behavior": behavior,
        "seams": behavior.get("seams") or data.get("seams") or [],
    }


def fingerprint_still_triggers(root: Path, cfg: dict, fingerprint: str) -> bool:
    """True when scan would still propose this metric fingerprint."""
    if not fingerprint or not is_metric_fingerprint(fingerprint):
        return False
    scan_json = root / cfg["docs_dir"] / "scan.json"
    if not scan_json.exists():
        return True
    try:
        data = json.loads(scan_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return True
    if not check_scan_schema_version(data):
        return True
    proposals = propose_from_scan(cfg, **signals_from_scan_json(data))
    return fingerprint in {p["fingerprint"] for p in proposals}
