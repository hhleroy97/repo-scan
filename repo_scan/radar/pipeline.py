"""The full RADAR pipeline: Research → Analyze → Gate 1 → Draft → Audit → Gate 2 → Record."""

import json
from pathlib import Path

from ..utils import ensure_dirs, err, header, info, now_date, now_iso, ok, step, warn, write_doc
from .gates import gate
from .llm import LLMError, complete, complete_json
from .research import repo_context_snippet, run_research, write_run_log
from .sources import frontmatter, slugify

ANALYZE_PROMPT = """You are the analysis stage of a research loop for a software project.

Repo context:
{repo_context}

Problem: {problem}

Ingested research (summaries):
{research}

Synthesize the research against the problem. Respond with ONLY a JSON object:
{{
  "findings": ["finding 1", "finding 2", "..."],
  "recommendation": "2-3 sentence recommended approach",
  "confidence": "low|medium|high",
  "risks": ["risk 1", "..."]
}}"""

DRAFT_PROMPT = """You are drafting an implementation spec for a software project.

Problem: {problem}

Analysis findings:
{findings}

Recommendation: {recommendation}

Write a concise implementation spec in markdown (no JSON). Sections:
## Goal, ## Approach, ## Changes (bulleted, by file/module), ## Risks, ## Out of scope.
Keep it under 80 lines. Do not include a top-level title heading."""

AUDIT_PROMPT = """You are auditing an implementation spec before it reaches a human reviewer.

Problem: {problem}

Spec:
---
{spec}
---

Check for: internal contradictions, unjustified claims not supported by the
findings, missing risks, and scope creep. Respond with ONLY a JSON object:
{{
  "verdict": "pass" or "revise",
  "issues": ["specific issue 1", "..."],
  "notes": "one sentence overall assessment"
}}"""

REVISE_PROMPT = """Revise this implementation spec to address the audit issues. Keep the same
section structure and stay under 80 lines. Output only the revised markdown.

Spec:
---
{spec}
---

Audit issues:
{issues}"""


def _research_digest(root: Path, cfg: dict, ingested: list[dict], max_chars: int = 6000) -> str:
    """Concatenate summaries of the sources this run ingested."""
    sources_dir = root / cfg["docs_dir"] / "research" / "sources"
    chunks = []
    for item in ingested:
        path = sources_dir / f"{item['id']}.md"
        if path.exists():
            chunks.append(f"### {item['title']}\n{path.read_text(encoding='utf-8', errors='ignore')[:1500]}")
    return "\n\n".join(chunks)[:max_chars] or "(no sources ingested)"


def run_analyze(root: Path, cfg: dict, problem: str, ingested: list[dict]) -> dict:
    analysis = complete_json(ANALYZE_PROMPT.format(
        repo_context=repo_context_snippet(root, cfg),
        problem=problem,
        research=_research_digest(root, cfg, ingested),
    ), cfg)
    analysis.setdefault("findings", [])
    analysis.setdefault("recommendation", "")
    analysis.setdefault("confidence", "low")
    analysis.setdefault("risks", [])
    return analysis


def write_analysis(root: Path, cfg: dict, problem: str, analysis: dict,
                   ingested: list[dict] | None = None,
                   run_log_path: Path | None = None) -> Path:
    """Analysis note. Wikilinks its evidence (sources + run log) so each loop
    forms a connected provenance cluster in Obsidian's graph view. The
    `-analysis` filename suffix keeps bare wikilinks unambiguous vs the spec
    and run log, which share the same date-slug."""
    out_dir = root / cfg["docs_dir"] / "research" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{now_date()}-{slugify(problem, 40)}-analysis.md"
    ingested = ingested or []
    lines = [
        frontmatter({
            "type": "analysis",
            "problem": problem,
            "confidence": analysis["confidence"],
            "sources": [item["id"] for item in ingested],
            "generated_at": now_iso(),
        }),
        "",
        f"# Analysis — {problem}",
        f"_Generated {now_iso()} — confidence: {analysis['confidence']}_",
        "",
        "## Findings",
        "",
    ]
    lines += [f"- {f}" for f in analysis["findings"]] or ["_none_"]
    lines += ["", "## Recommendation", "", analysis["recommendation"] or "_none_", ""]
    if analysis["risks"]:
        lines += ["## Risks", ""] + [f"- {r}" for r in analysis["risks"]] + [""]
    lines += ["## Evidence", ""]
    for item in ingested:
        lines.append(f"- [[{item['id']}\\|{item['title']}]]")
    if not ingested:
        lines.append("_no sources ingested_")
    if run_log_path is not None:
        lines.append(f"- research run: [[{run_log_path.stem}]]")
    lines.append("")
    write_doc(path, "\n".join(lines), root)
    return path


def run_draft(root: Path, cfg: dict, problem: str, analysis: dict) -> str:
    return complete(DRAFT_PROMPT.format(
        problem=problem,
        findings="\n".join(f"- {f}" for f in analysis["findings"]),
        recommendation=analysis["recommendation"],
    ), cfg)


def run_audit(cfg: dict, problem: str, spec_text: str) -> dict:
    audit = complete_json(AUDIT_PROMPT.format(problem=problem, spec=spec_text[:12000]), cfg)
    audit.setdefault("verdict", "revise")
    audit.setdefault("issues", [])
    audit.setdefault("notes", "")
    return audit


def write_spec(root: Path, cfg: dict, problem: str, spec_text: str,
               audit: dict, status: str, analysis_path: Path | None = None) -> Path:
    specs = root / cfg["docs_dir"] / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    path = specs / f"{now_date()}-{slugify(problem, 40)}-spec.md"
    lines = [
        frontmatter({
            "type": "spec",
            "problem": problem,
            "status": status,
            "audit_verdict": audit["verdict"],
            "analysis": f"[[{analysis_path.stem}]]" if analysis_path else "",
            "drafted_at": now_iso(),
        }),
        "",
        f"# Spec — {problem}",
        f"_Drafted {now_iso()} by radar — **status: {status}**_",
        "",
        spec_text.strip(),
        "",
        "## Audit",
        "",
    ]
    kind = "success" if audit["verdict"] == "pass" else "warning"
    lines += [
        f"> [!{kind}] Audit verdict: {audit['verdict']}",
        f"> {audit['notes'] or '—'}",
    ]
    for issue in audit["issues"]:
        lines.append(f"> - {issue}")
    lines.append("")
    if analysis_path is not None:
        lines += ["## Provenance", "", f"- analysis: [[{analysis_path.stem}]]", ""]
    write_doc(path, "\n".join(lines), root)
    return path


def record_loop(root: Path, cfg: dict, problem: str, result: dict):
    """Append the run to docs/changelog/{date}-loop.md (RADAR_CONTEXT format)."""
    changelog = root / cfg["docs_dir"] / "changelog"
    changelog.mkdir(parents=True, exist_ok=True)
    path = changelog / f"{now_date()}-loop.md"
    if not path.exists():
        path.write_text(f"# RADAR loop runs — {now_date()}\n", encoding="utf-8")
    outcome = result["outcome"]
    kind = "success" if outcome == "approved" else ("warning" if outcome == "stopped" else "danger")
    entry = [
        "",
        f"## {now_iso()} — {problem}",
        "",
        f"> [!{kind}] outcome: **{outcome}**",
        f"> - sources ingested: {result.get('sources', 0)}",
        f"> - confidence: {result.get('confidence', '?')}",
        f"> - spec: {result.get('spec', '—')}",
        f"> - gates: {result.get('gates', '—')}",
        "",
    ]
    with path.open("a", encoding="utf-8") as f:
        f.write("\n".join(entry))
    ok(f"recorded to {path.relative_to(root)}")


def cmd_loop(root: Path, cfg: dict, problem: str, approve: list[str] | None = None,
             gates_override: str | None = None, max_sources: int = 3) -> int:
    header(f"radar loop")
    info(problem)
    ensure_dirs(root, cfg)

    if gates_override:
        cfg = {**cfg, "gates": {"post_analyze": gates_override, "post_audit": gates_override}}
    approved = set(approve or [])
    gates_log: list[str] = []
    result = {"outcome": "stopped", "sources": 0, "confidence": "?", "spec": "—"}

    try:
        # 1 — Research
        step("[1/7] Research")
        research = run_research(root, cfg, problem, max_sources)
        run_log_path = write_run_log(root, cfg, research)
        result["sources"] = len(research["ingested"])
        ok(f"{result['sources']} source(s) ingested")

        # 2 — Analyze
        step("[2/7] Analyze")
        analysis = run_analyze(root, cfg, problem, research["ingested"])
        analysis_path = write_analysis(root, cfg, problem, analysis,
                                       research["ingested"], run_log_path)
        result["confidence"] = analysis["confidence"]
        ok(f"{len(analysis['findings'])} finding(s), confidence {analysis['confidence']}")

        # 3 — Gate 1
        step("[3/7] Gate 1 (post-analyze)")
        gate1_payload = {"summary": f"{analysis['recommendation']} — [[{analysis_path.stem}]]"}
        if not gate("post_analyze", gate1_payload, cfg, root, approved):
            gates_log.append("post_analyze: stopped")
            result["gates"] = "; ".join(gates_log)
            record_loop(root, cfg, problem, result)
            return 2
        gates_log.append("post_analyze: passed")

        # 4 — Draft
        step("[4/7] Draft")
        spec_text = run_draft(root, cfg, problem, analysis)
        ok(f"spec drafted ({len(spec_text.splitlines())} lines)")

        # 5 — Audit (one revision round if needed)
        step("[5/7] Audit")
        audit = run_audit(cfg, problem, spec_text)
        if audit["verdict"] != "pass" and audit["issues"]:
            info(f"audit requested revision: {len(audit['issues'])} issue(s)")
            spec_text = complete(REVISE_PROMPT.format(
                spec=spec_text, issues="\n".join(f"- {i}" for i in audit["issues"]),
            ), cfg)
            audit = run_audit(cfg, problem, spec_text)
        ok(f"audit verdict: {audit['verdict']}")

        # 6 — Gate 2
        step("[6/7] Gate 2 (post-audit)")
        spec_path = write_spec(root, cfg, problem, spec_text, audit,
                               status="draft", analysis_path=analysis_path)
        result["spec"] = f"[[{spec_path.stem}]]"
        payload = {"summary": f"audit {audit['verdict']}: {audit['notes']} — [[{spec_path.stem}]]"}
        if not gate("post_audit", payload, cfg, root, approved):
            gates_log.append("post_audit: stopped")
            result["gates"] = "; ".join(gates_log)
            record_loop(root, cfg, problem, result)
            return 2
        gates_log.append("post_audit: passed")

        # 7 — Record
        step("[7/7] Record")
        write_spec(root, cfg, problem, spec_text, audit,
                   status="approved", analysis_path=analysis_path)
        result["outcome"] = "approved"
        result["gates"] = "; ".join(gates_log)
        record_loop(root, cfg, problem, result)
        return 0

    except LLMError as e:
        err(f"loop needs an LLM backend: {e}")
        result["outcome"] = f"failed ({e})"
        result["gates"] = "; ".join(gates_log) or "—"
        record_loop(root, cfg, problem, result)
        return 1


def pick_candidate(root: Path, cfg: dict) -> str | None:
    """Top metric-triggered problem from scan.json (churn x complexity)."""
    scan_json = root / cfg["docs_dir"] / "scan.json"
    if not scan_json.exists():
        return None
    try:
        data = json.loads(scan_json.read_text())
    except json.JSONDecodeError:
        return None
    churn = {c["file"]: c["commits"] for c in data.get("churn", [])}
    cc: dict[str, int] = {}
    for item in data.get("complexity", []):
        cc[item["file"]] = cc.get(item["file"], 0) + item["complexity"]
    overlap = [(f, churn[f] * cc[f]) for f in set(churn) & set(cc)]
    if not overlap:
        return None
    target = max(overlap, key=lambda x: x[1])[0]
    return (f"`{target}` is both high-churn ({churn[target]} commits) and high-complexity "
            f"(CC {cc[target]}). Research current best practices and propose how to simplify "
            f"or restructure it.")


def cmd_full(root: Path, cfg: dict, approve: list[str] | None = None,
             gates_override: str | None = None) -> int:
    header("radar full")
    if not cfg.get("radar_enabled"):
        warn('radar full requires "radar_enabled": true in .repo-scan.json')
        return 1

    # the approved-ticket queue is the work source of record; raw metric
    # candidates are the fallback when nothing has been approved yet
    from ..tickets import append_ticket_note, pick_approved_ticket, set_ticket_status
    ticket = pick_approved_ticket(root, cfg)
    if ticket:
        problem = f"{ticket['title']}. {ticket['why']} " \
                  "Research current best practices and draft a spec for this work."
        info(f"working approved ticket {ticket['id']}: {ticket['title'][:80]}")
        rc = cmd_loop(root, cfg, problem, approve=approve, gates_override=gates_override)
        if rc == 0:
            set_ticket_status(root, cfg, ticket["id"], "in-progress")
            spec = _latest_spec(root, cfg)
            note = f"radar spec approved{f': [[{spec}]]' if spec else ''} — status moved to in-progress"
            append_ticket_note(root, cfg, ticket["id"], note)
            ok(f"{ticket['id']} -> in-progress")
        return rc

    problem = pick_candidate(root, cfg)
    if not problem:
        info("no approved tickets and no metric-triggered candidates — "
             "run repo-scan, then approve a ticket (`repo-scan tickets`)")
        return 1
    info(f"triggered: {problem[:100]}")
    return cmd_loop(root, cfg, problem, approve=approve, gates_override=gates_override)


def _latest_spec(root: Path, cfg: dict) -> str | None:
    specs = sorted((root / cfg["docs_dir"] / "specs").glob("*.md"),
                   key=lambda p: p.stat().st_mtime)
    return specs[-1].stem if specs else None
