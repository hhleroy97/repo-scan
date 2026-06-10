"""Vault provenance scoring — evidence, linked, cited signals (fresh is vanity).

See docs/planning/phase-5-week5 for provenance contract.
See docs/changelog/2026-06-11-vault-provenance for implementation notes.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from .citations import citation_index
from .radar.sources import parse_frontmatter

_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
_ALL_SIGNALS = ("evidence", "linked", "cited", "fresh")
_SCORE_SIGNALS = ("evidence", "linked", "cited")  # fresh is vanity — displayed but not scored
_VAULT_KINDS = frozenset({"ticket", "spec", "analysis", "source"})
_FRESH_GRACE_DAYS = 14


def _read_scan(root: Path, cfg: dict) -> dict:
    path = root / cfg["docs_dir"] / "scan.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _parse_linked_files(fm: dict) -> list[str]:
    raw = str(fm.get("linked_files", "") or "")
    if not raw:
        return []
    if raw.startswith("["):
        parts = [p.strip().strip("[]\"'") for p in raw[1:-1].split(",")]
    else:
        parts = [p.strip().strip("[]\"'\"") for p in raw.split(",")]
    return [p for p in parts if p]


def _wikilink_stems(text: str) -> list[str]:
    return [m.strip() for m in _WIKILINK_RE.findall(text)]


def _has_evidence(kind: str, text: str, fm: dict) -> bool:
    if kind == "ticket":
        return "## Evidence" in text or bool(_wikilink_stems(text))
    if kind == "spec":
        if fm.get("analysis"):
            return True
        return any(
            s.endswith("-spec") is False and (
                "analysis" in s or "source" in s or s.endswith("-spec")
            )
            for s in _wikilink_stems(text)
        )
    if kind == "analysis":
        return any("source" in s for s in _wikilink_stems(text))
    if kind == "source":
        return bool(_parse_linked_files(fm)) or len(text) > 200
    return False


def _has_linked(kind: str, fm: dict, scan_files: dict, text: str) -> bool:
    paths = _parse_linked_files(fm)
    if paths:
        return any(p in scan_files for p in paths)
    if kind in ("ticket", "analysis", "spec"):
        for stem in _wikilink_stems(text):
            if stem.endswith(".py") and stem in scan_files:
                return True
            if "/" in stem and stem in scan_files:
                return True
    return False


def _linked_paths(fm: dict, text: str) -> list[str]:
    paths = list(_parse_linked_files(fm))
    for stem in _wikilink_stems(text):
        if stem.endswith(".py") or ("/" in stem and not stem.startswith("research/")):
            paths.append(stem)
    return paths


def _is_cited(kind: str, key: str, cite_idx: dict) -> bool:
    return bool(cite_idx.get((kind, key)))


def _doc_age_days(path: Path) -> float:
    try:
        return max(0.0, (time.time() - path.stat().st_mtime) / 86400)
    except OSError:
        return 0.0


def _is_fresh(doc_path: Path, linked: list[str], age_days: dict, grace: int) -> bool | None:
    """None when freshness cannot be judged (no linked code paths)."""
    resolved = [p for p in linked if p in age_days]
    if not resolved:
        return None
    doc_age = _doc_age_days(doc_path)
    return doc_age <= max(age_days[p] for p in resolved) + grace


def score_node(node: dict, root: Path, cfg: dict, scan: dict,
               cite_idx: dict | None = None) -> dict:
    """Score one vault node 0–3 on evidence/linked/cited (fresh is vanity)."""
    kind = node.get("kind", "")
    key = node.get("id", "").split(":", 1)[-1] if ":" in node.get("id", "") else node.get("label", "")
    if kind not in _VAULT_KINDS:
        return {"signals": [], "score": 0, "missing": list(_ALL_SIGNALS), "stale_days": None}

    doc_rel = node.get("doc")
    if not doc_rel:
        return {"signals": [], "score": 0, "missing": list(_ALL_SIGNALS), "stale_days": None}

    doc_path = root / cfg["docs_dir"] / doc_rel
    if not doc_path.exists():
        return {"signals": [], "score": 0, "missing": list(_ALL_SIGNALS), "stale_days": None}

    text = doc_path.read_text(encoding="utf-8", errors="ignore")
    fm = parse_frontmatter(text)
    scan_files = scan.get("files") or {}
    age_days = (scan.get("behavior") or {}).get("age_days") or {}
    grace = int(cfg.get("provenance_fresh_grace_days", _FRESH_GRACE_DAYS))

    signals: list[str] = []
    if _has_evidence(kind, text, fm):
        signals.append("evidence")
    if _has_linked(kind, fm, scan_files, text):
        signals.append("linked")
    if _is_cited(kind, key, cite_idx or {}):
        signals.append("cited")

    linked = _linked_paths(fm, text)
    fresh = _is_fresh(doc_path, linked, age_days, grace)
    stale_days = None
    if fresh is True:
        signals.append("fresh")
    elif fresh is False:
        resolved = [p for p in linked if p in age_days]
        if resolved:
            stale_days = int(_doc_age_days(doc_path) - min(age_days[p] for p in resolved))

    missing = [s for s in _ALL_SIGNALS if s not in signals]
    return {
        "signals": signals,
        "score": sum(1 for s in signals if s in _SCORE_SIGNALS),
        "missing": missing,
        "stale_days": stale_days,
    }


def _iter_vault_nodes(root: Path, cfg: dict) -> list[dict]:
    docs = root / cfg["docs_dir"]
    nodes: list[dict] = []
    for pattern, kind in (
        ("tickets/tkt-*.md", "ticket"),
        ("specs/*.md", "spec"),
        ("research/analysis/*.md", "analysis"),
        ("research/sources/*.md", "source"),
    ):
        folder, glob = pattern.split("/", 1)
        base = docs / folder
        if not base.is_dir():
            continue
        for path in sorted(base.glob(glob)):
            fm = parse_frontmatter(path.read_text(encoding="utf-8", errors="ignore"))
            key = path.stem
            rel = str(path.relative_to(docs))
            nodes.append({
                "id": f"{kind}:{key}",
                "kind": kind,
                "label": str(fm.get("title") or key)[:48],
                "doc": rel,
            })
    return nodes


def _cited_targets(cite_idx: dict) -> set[str]:
    out: set[str] = set()
    for (kind, key), files in cite_idx.items():
        if files:
            out.add(f"{kind}:{key}")
    return out


def _tracked_code_paths(root: Path, cfg: dict, scan: dict,
                        citations: list[dict]) -> set[str]:
    """Code paths referenced by vault linked_files or that cite vault docs."""
    tracked: set[str] = set()
    scan_files = set((scan.get("files") or {}).keys())
    docs = root / cfg["docs_dir"]
    for sub in ("specs", "research/sources"):
        base = docs / sub
        if not base.is_dir():
            continue
        for path in base.glob("*.md"):
            fm = parse_frontmatter(path.read_text(encoding="utf-8", errors="ignore"))
            for p in _parse_linked_files(fm):
                if p in scan_files:
                    tracked.add(p)
    for row in citations:
        if row.get("file"):
            tracked.add(row["file"])
    return tracked


def thin_citations(citations: list[dict], threshold: int = 1) -> list[dict]:
    """Code files with exactly `threshold` or fewer citation links — fragile connections."""
    by_file: dict[str, int] = {}
    for row in citations:
        f = row.get("file", "")
        if f:
            by_file[f] = by_file.get(f, 0) + 1
    return sorted(
        [{"file": f, "count": c} for f, c in by_file.items() if c <= threshold],
        key=lambda r: r["count"],
    )[:15]


def vault_coverage(root: Path, cfg: dict, scan: dict | None = None,
                   citations: list[dict] | None = None) -> dict:
    """Summarize vault provenance health for scan.json and the hub."""
    if scan is None:
        scan = _read_scan(root, cfg)
    if citations is None:
        citations = scan.get("citations") or []
    cite_idx = citation_index(citations)

    scored: list[dict] = []
    histogram = {str(i): 0 for i in range(len(_SCORE_SIGNALS) + 1)}
    orphans_by_kind: dict[str, int] = {}
    stale_docs = 0
    max_score = len(_SCORE_SIGNALS)

    for node in _iter_vault_nodes(root, cfg):
        result = score_node(node, root, cfg, scan, cite_idx)
        entry = {**node, **result}
        scored.append(entry)
        histogram[str(result["score"])] = histogram.get(str(result["score"]), 0) + 1
        if result["score"] < max_score:
            orphans_by_kind[node["kind"]] = orphans_by_kind.get(node["kind"], 0) + 1
        if result.get("stale_days") is not None and result["stale_days"] > 0:
            stale_docs += 1

    healthy = sum(1 for s in scored if s["score"] == max_score)
    total = len(scored)
    coverage_pct = round(healthy / total, 4) if total else 1.0

    scan_files = set((scan.get("files") or {}).keys())
    ranking = scan.get("ranking") or []
    ranked_code = {
        r["file"] for r in ranking
        if not r["file"].startswith(cfg["docs_dir"] + "/")
    }
    tracked = _tracked_code_paths(root, cfg, scan, citations)
    untracked = sorted(
        f for f in ranked_code
        if f in scan_files and f not in tracked
        and not f.startswith("tests/") and "/tests/" not in f
    )

    return {
        "docs": total,
        "healthy": healthy,
        "coverage_pct": coverage_pct,
        "score_histogram": histogram,
        "orphans_by_kind": orphans_by_kind,
        "orphans": [
            {"id": s["id"], "kind": s["kind"], "score": s["score"], "missing": s["missing"]}
            for s in scored if s["score"] < max_score
        ],
        "untracked_code_count": len(untracked),
        "untracked_code": untracked[:30],
        "stale_docs_count": stale_docs,
        "scored_by_kind": {
            kind: sum(1 for s in scored if s["kind"] == kind)
            for kind in sorted({s["kind"] for s in scored})
        },
        "knowledge_debt": round(
            (1 - coverage_pct) * 40
            + min(stale_docs / max(total, 1), 1) * 30
            + min(len(untracked) / max(len(scan_files), 1), 1) * 30,
            1,
        ),
        "thin_citations": thin_citations(citations),
    }


def autolink_orphan_analyses(root: Path, cfg: dict) -> list[str]:
    """Propagate linked_files from sources to analyses that reference them.

    Analyses list their sources in frontmatter ``sources: [...]``.  If a
    referenced source has ``linked_files``, those paths are propagated to the
    analysis (transitive linking).  Only adds ``linked_files`` — never removes
    existing entries.

    Returns list of analysis filenames that were updated.
    """
    docs = root / cfg["docs_dir"]
    source_dir = docs / "research" / "sources"
    analysis_dir = docs / "research" / "analysis"
    if not source_dir.is_dir() or not analysis_dir.is_dir():
        return []

    source_links: dict[str, list[str]] = {}
    for sp in source_dir.glob("*.md"):
        fm = parse_frontmatter(sp.read_text(encoding="utf-8", errors="ignore"))
        lf = _parse_linked_files(fm)
        if lf:
            source_links[sp.stem] = lf

    updated: list[str] = []
    for ap in sorted(analysis_dir.glob("*-analysis.md")):
        text = ap.read_text(encoding="utf-8", errors="ignore")
        fm = parse_frontmatter(text)
        existing_lf = set(_parse_linked_files(fm))

        raw_sources = fm.get("sources", "")
        if isinstance(raw_sources, str):
            src_ids = [s.strip().strip('"\'') for s in raw_sources.strip("[]").split(",") if s.strip()]
        elif isinstance(raw_sources, list):
            src_ids = [str(s).strip().strip('"\'') for s in raw_sources]
        else:
            src_ids = []

        propagated: set[str] = set()
        for sid in src_ids:
            for lf in source_links.get(sid, []):
                if lf not in existing_lf:
                    propagated.add(lf)

        if not propagated:
            continue

        merged = sorted(existing_lf | propagated)
        lf_value = "[" + ", ".join(f'"{f}"' for f in merged) + "]"

        if "linked_files:" in text:
            import re as _re
            text = _re.sub(
                r"linked_files:\s*\[[^\]]*\]",
                f"linked_files: {lf_value}",
                text,
                count=1,
            )
        else:
            lines = text.splitlines(keepends=True)
            in_fm = False
            for i, line in enumerate(lines):
                if line.strip() == "---":
                    if not in_fm:
                        in_fm = True
                    else:
                        lines.insert(i, f"linked_files: {lf_value}\n")
                        break
            text = "".join(lines)

        ap.write_text(text, encoding="utf-8")
        updated.append(ap.name)
    return updated


def vault_health_payload(root: Path, cfg: dict, scan_files: dict,
                         citations: list[dict], behavior: dict | None,
                         ranking: list | None = None) -> dict:
    """Compact vault_health block for scan.json."""
    scan_stub = {
        "files": scan_files,
        "ranking": ranking or [],
        "behavior": behavior or {},
        "citations": citations,
    }
    cov = vault_coverage(root, cfg, scan_stub, citations)
    return {
        "coverage_pct": cov["coverage_pct"],
        "score_histogram": cov["score_histogram"],
        "orphans_by_kind": cov["orphans_by_kind"],
        "untracked_code_count": cov["untracked_code_count"],
        "stale_docs_count": cov["stale_docs_count"],
        "healthy": cov["healthy"],
        "docs": cov["docs"],
        "knowledge_debt": cov["knowledge_debt"],
        "thin_citations": cov["thin_citations"],
    }
