"""Shared ticket constants and path helpers (leaf module — no upward imports)."""

from pathlib import Path

_SCAN_PROPOSAL_KEYS = (
    "line_counts", "ranking", "churn", "complexity", "tested", "behavior", "seams",
)

METRIC_FINGERPRINT_PREFIXES = ("refactor:", "seam:", "size:", "stale:", "silo:")

STATUSES = ["proposed", "approved", "in-progress", "done", "rejected"]
BOARD_COLUMNS = [("Proposed", "proposed"), ("Approved", "approved"),
                 ("In progress", "in-progress"), ("Done", "done"),
                 ("Rejected", "rejected")]

OPEN_STATUSES = {"proposed", "approved", "in-progress"}

PLACEHOLDER_CRITERIA = frozenset({
    "define done",
    "define acceptance criteria before approving",
})


def tickets_dir(root: Path, cfg: dict) -> Path:
    return root / cfg["docs_dir"] / "tickets"
