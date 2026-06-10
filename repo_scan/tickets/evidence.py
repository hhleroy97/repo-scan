"""Mermaid evidence diagrams for auto-proposed tickets."""

from ..graphs import refactor_ego_mermaid, seam_pair_mermaid


def ticket_evidence_diagrams(fingerprint: str, signals: dict, cfg: dict) -> list[str]:
    """Mermaid blocks and callouts for auto-ticket Evidence sections.

    Maps fingerprint prefix to diagram kind: ``refactor:{file}`` ego subgraph,
    ``seam:{a}+{b}`` pair subgraph, ``size:{file}`` health-report callout only.
    ``stale:`` and ``silo:`` tickets get no body diagrams. Returns empty when
    ``ticket_diagrams_enabled`` is false. Diagrams are frozen at ticket creation.
    """
    if not cfg.get("ticket_diagrams_enabled", True):
        return []
    if ":" not in fingerprint:
        return []
    kind, target = fingerprint.split(":", 1)
    coupling = signals.get("behavior", {}).get("coupling", [])
    ranking = signals.get("ranking", [])
    line_counts = signals.get("line_counts", {})
    py_edges = signals.get("py_edges", [])
    ts_edges = signals.get("ts_edges", [])
    import_edges = py_edges + ts_edges
    max_neighbors = cfg.get("diagram_max_ticket_neighbors", 4)
    lines: list[str] = []

    if kind == "refactor":
        chart = refactor_ego_mermaid(target, coupling, ranking, max_neighbors=max_neighbors)
        if chart:
            lines += ["```mermaid", chart, "```", ""]
    elif kind == "seam" and "+" in target:
        a, b = target.split("+", 1)
        degree = next(
            (c["degree"] for c in coupling if {c["a"], c["b"]} == {a, b}),
            0,
        )
        chart = seam_pair_mermaid(
            a, b, degree, import_edges, line_counts,
            max_import_edges=max_neighbors * 2,
        )
        if chart:
            lines += ["```mermaid", chart, "```", ""]
    elif kind == "size":
        lines += [
            f"> [!note] Oversized file — see [[reports/health#file-sizes]] "
            f"for `{target}` size and thresholds.",
            "",
        ]
    return lines
