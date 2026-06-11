"""Enrich pending gate rows for the mobile dashboard drawer."""

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from ..frontmatter import parse_frontmatter

_TICKET_RE = re.compile(r"tkt-\d{4}")
_WIKILINK_RE = re.compile(r"\[\[([^\]|]+)")


def _read_doc(root: Path, cfg: dict, rel: str) -> str | None:
    docs = (root / cfg["docs_dir"]).resolve()
    target = (docs / rel).resolve()
    if not str(target).startswith(str(docs) + "/") or not target.exists():
        return None
    return target.read_text(encoding="utf-8", errors="ignore")


def _wikilink_doc(root: Path, cfg: dict, link: str) -> str | None:
    m = _WIKILINK_RE.search(link)
    if not m:
        return None
    stem = m.group(1).strip()
    for folder in ("research/analysis", "specs"):
        rel = f"{folder}/{stem}.md"
        if _read_doc(root, cfg, rel):
            return rel
    return None


def _parse_vault_time(value: str) -> datetime | None:
    for fmt in ("%Y-%m-%d %H:%M UTC", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _main_commit_time(root: Path) -> datetime | None:
    for ref in ("main", "origin/main", "master"):
        if subprocess.run(["git", "rev-parse", "--verify", "--quiet", ref],
                          cwd=root, capture_output=True).returncode != 0:
            continue
        r = subprocess.run(["git", "log", "-1", "--format=%cI", ref],
                           cwd=root, capture_output=True, text=True, timeout=10)
        if r.returncode != 0 or not r.stdout.strip():
            continue
        raw = r.stdout.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            continue
    return None


def _ticket_for_gate(problem: str, summary: str, tickets: list[dict]) -> dict | None:
    hay = f"{problem} {summary}"
    m = _TICKET_RE.search(hay)
    if m:
        tid = m.group(0)
        hit = next((t for t in tickets if t.get("id") == tid), None)
        if hit:
            return hit
    return None


def enrich_gate(root: Path, cfg: dict, gate_row: dict,
                tickets: list[dict]) -> dict:
    """Add ``drawer`` fields: excerpt, analysis_doc, criteria, stale_warning."""
    detail = gate_row.get("detail") or {}
    doc_rel = detail.get("doc")
    drawer: dict = {}

    ticket = _ticket_for_gate(gate_row.get("problem", ""),
                              gate_row.get("summary", ""), tickets)
    if ticket:
        drawer["ticket_id"] = ticket["id"]
        drawer["criteria"] = ticket.get("criteria") or []
        drawer["criteria_checked"] = ticket.get("criteria_checked") or []

    if doc_rel:
        text = _read_doc(root, cfg, doc_rel)
        if text:
            body = text
            if text.startswith("---"):
                fm = re.match(r"---\n.*?\n---\n?", text, re.S)
                if fm:
                    body = text[fm.end():]
            drawer["excerpt"] = "\n".join(body.splitlines()[:40])
            meta = parse_frontmatter(text)
            analysis = meta.get("analysis", "")
            if analysis:
                drawer["analysis_doc"] = _wikilink_doc(root, cfg, analysis)
            elif doc_rel.startswith("research/analysis/"):
                drawer["analysis_doc"] = doc_rel

            drafted = meta.get("drafted_at", "")
            if drafted and doc_rel.startswith("specs/"):
                drafted_at = _parse_vault_time(drafted)
                main_at = _main_commit_time(root)
                if drafted_at and main_at and drafted_at < main_at:
                    drawer["stale_warning"] = (
                        f"Spec drafted {drafted} — main moved since "
                        f"({main_at.strftime('%Y-%m-%d %H:%M UTC')})"
                    )

    gate_row["drawer"] = drawer
    return gate_row
