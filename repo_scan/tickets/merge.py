"""Post-merge rescan and ticket fingerprint verification."""

import json
from pathlib import Path

from ..utils import check_scan_schema_version
from .generation import fingerprint_still_triggers, is_metric_fingerprint
from .io import load_tickets
from .workflow import append_ticket_note, set_ticket_status


def record_merge_verification(root: Path, cfg: dict, ticket_id: str,
                              pr_number: int) -> None:
    """Rescan after merge and note whether the ticket's metric fingerprint cleared."""
    from ..scanner import scan
    from ..trends import trend_callout, summarize_metrics, load_previous_summary, compute_delta

    prev = load_previous_summary(root, cfg)
    scan(root, quiet=True)
    ticket = next((t for t in load_tickets(root, cfg) if t["id"] == ticket_id), None)
    if not ticket:
        return
    fp = str(ticket.get("fingerprint", ""))
    delta_note = ""
    scan_json = root / cfg["docs_dir"] / "scan.json"
    if scan_json.exists():
        try:
            data = json.loads(scan_json.read_text(encoding="utf-8"))
            if not check_scan_schema_version(data):
                data = {}
            curr = summarize_metrics(data.get("files", {}), data.get("complexity", []), cfg)
            delta = compute_delta(prev, curr)
            callout = trend_callout(delta)
            if callout:
                delta_note = " ".join(ln.lstrip("> ") for ln in callout if ln.startswith("> "))
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    if not is_metric_fingerprint(fp):
        append_ticket_note(root, cfg, ticket_id,
                           f"PR #{pr_number} merged — intent ticket marked done"
                           + (f" ({delta_note})" if delta_note else ""))
        set_ticket_status(root, cfg, ticket_id, "done")
        return

    if fingerprint_still_triggers(root, cfg, fp):
        append_ticket_note(root, cfg, ticket_id,
                           f"PR #{pr_number} merged — rescan: metric still active"
                           + (f" ({delta_note})" if delta_note else ""))
    else:
        append_ticket_note(root, cfg, ticket_id,
                           f"PR #{pr_number} merged — rescan: metric fingerprint cleared"
                           + (f" ({delta_note})" if delta_note else ""))
        set_ticket_status(root, cfg, ticket_id, "done")
