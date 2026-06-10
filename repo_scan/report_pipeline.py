"""Scan-to-docs write pipeline — explicit orchestration→writers contract.

``ReportPayload`` carries precomputed scan outputs; ``write_scan_reports`` is
the sole orchestration-layer entry that sequences ``writers.write_*`` calls
and appends the trend log.
"""

from dataclasses import dataclass
from pathlib import Path

from .trends import append_trend_log
from .writers import (
    write_call_report,
    write_coupling_report,
    write_dep_report,
    write_health_report,
    write_index,
    write_scan_json,
)


@dataclass
class ReportPayload:
    """Fields assembled after scan metrics and before doc writes."""

    line_counts: dict
    languages: dict
    churn: list
    complexity: list
    ranking: list
    tree: str
    behavior: dict
    seams: list
    ts_mermaid: str | None
    py_mermaid: str | None
    ts_reason: str
    c_mermaid: str | None
    py_edges: list
    ts_edges: list
    curr_summary: dict
    delta: dict | None

    @property
    def coupling(self) -> list:
        return self.behavior["coupling"]


def write_scan_reports(root: Path, cfg: dict, payload: ReportPayload) -> None:
    """Write health, coupling, dependency, call, index, scan.json, then trend log."""
    write_health_report(
        root, cfg, payload.line_counts, payload.churn, payload.complexity,
        behavior=payload.behavior,
    )
    write_coupling_report(
        root, cfg, payload.coupling, payload.seams,
        py_edges=payload.py_edges, ts_edges=payload.ts_edges,
        line_counts=payload.line_counts,
    )
    write_dep_report(root, cfg, payload.ts_mermaid, payload.py_mermaid, payload.ts_reason)
    write_call_report(root, cfg, payload.c_mermaid)
    write_index(
        root, cfg, payload.line_counts, payload.languages, payload.ranking,
        payload.tree, delta=payload.delta,
    )
    write_scan_json(
        root, cfg, payload.line_counts, payload.languages, payload.churn,
        payload.complexity, payload.ranking, payload.py_edges, payload.ts_edges,
        behavior=payload.behavior,
    )
    append_trend_log(root, cfg, payload.curr_summary, payload.delta)
