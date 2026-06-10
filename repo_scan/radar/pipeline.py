"""The full RADAR pipeline: Research → Analyze → Gate 1 → Draft → Audit → Gate 2 → Record."""

import json
from pathlib import Path

from ..utils import ensure_dirs, err, header, info, now_date, now_iso, ok, step, warn, write_doc
from .gates import gate, gate_mode
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
## Goal, ## Approach, ## Changes (bulleted, by file/module), ## Tests,
## Documentation (docstrings/README sections that must change with the
implementation), ## Risks, ## Out of scope.
If the problem lists acceptance criteria, the ## Tests section MUST map each
criterion to a concrete automated test (file + test name) — those tests are
the definition of done for the implementation stage.
Keep it under 90 lines. Do not include a top-level title heading."""

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
    ), cfg, role="analyze", root=root)
    analysis.setdefault("findings", [])
    analysis.setdefault("recommendation", "")
    analysis.setdefault("confidence", "low")
    analysis.setdefault("risks", [])
    return analysis


def _analysis_frontmatter(problem: str, analysis: dict, ingested: list[dict]) -> str:
    """YAML frontmatter for an analysis note."""
    return frontmatter({
        "type": "analysis",
        "problem": problem,
        "confidence": analysis["confidence"],
        "sources": [item["id"] for item in ingested],
        "generated_at": now_iso(),
    })


def _analysis_findings_block(analysis: dict) -> list[str]:
    """Findings section; empty list yields the ``_none_`` sentinel."""
    lines = ["## Findings", ""]
    if analysis["findings"]:
        lines += [f"- {f}" for f in analysis["findings"]]
    else:
        lines.append("_none_")
    return lines


def _analysis_risks_block(analysis: dict) -> list[str]:
    """Optional risks section; omitted when there are no risks."""
    if not analysis["risks"]:
        return []
    return ["## Risks", ""] + [f"- {r}" for r in analysis["risks"]] + [""]


def _analysis_evidence_block(ingested: list[dict], run_log_path: Path | None) -> list[str]:
    """Evidence wikilinks to ingested sources and the research run log."""
    lines = ["## Evidence", ""]
    for item in ingested:
        lines.append(f"- [[{item['id']}\\|{item['title']}]]")
    if not ingested:
        lines.append("_no sources ingested_")
    if run_log_path is not None:
        lines.append(f"- research run: [[{run_log_path.stem}]]")
    return lines


def write_analysis(root: Path, cfg: dict, problem: str, analysis: dict,
                   ingested: list[dict] | None = None,
                   run_log_path: Path | None = None) -> Path:
    """Write an analysis note; section builders own markdown shape.

    Wikilinks its evidence (sources + run log) so each loop forms a connected
    provenance cluster in Obsidian's graph view. The ``-analysis`` filename
    suffix keeps bare wikilinks unambiguous vs the spec and run log, which share
    the same date-slug.
    """
    out_dir = root / cfg["docs_dir"] / "research" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{now_date()}-{slugify(problem, 40)}-analysis.md"
    ingested = ingested or []
    lines = [
        _analysis_frontmatter(problem, analysis, ingested),
        "",
        f"# Analysis — {problem}",
        f"_Generated {now_iso()} — confidence: {analysis['confidence']}_",
        "",
    ]
    lines += _analysis_findings_block(analysis)
    lines += ["", "## Recommendation", "", analysis["recommendation"] or "_none_", ""]
    lines += _analysis_risks_block(analysis)
    lines += _analysis_evidence_block(ingested, run_log_path)
    lines.append("")
    write_doc(path, "\n".join(lines), root)
    return path


def run_draft(root: Path, cfg: dict, problem: str, analysis: dict) -> str:
    return complete(DRAFT_PROMPT.format(
        problem=problem,
        findings="\n".join(f"- {f}" for f in analysis["findings"]),
        recommendation=analysis["recommendation"],
    ), cfg, role="draft", root=root)


def run_audit(cfg: dict, problem: str, spec_text: str,
              root: Path | None = None) -> dict:
    audit = complete_json(AUDIT_PROMPT.format(problem=problem, spec=spec_text[:12000]),
                          cfg, role="audit", root=root)
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


def _gate_paused(root: Path, cfg: dict, name: str, problem: str = "") -> bool:
    """After gate() returns False: pending file present = paused, gone = rejected."""
    from .gates import pending_path
    legacy = root / cfg["docs_dir"] / "research" / "pending" / f"{name}.json"
    return pending_path(root, cfg, name, problem).exists() or legacy.exists()


def _finish_loop(root: Path, cfg: dict, problem: str):
    """A loop fully ended (approved or rejected) — drop its resume state."""
    from ..hub.state import clear_checkpoint, clear_decisions
    clear_checkpoint(root, cfg, problem)
    clear_decisions(root, cfg, problem)


class _RadarLoopRunner:
    """Seven-stage RADAR command object; resume via checkpoint guard clauses.

    Holds loop state (checkpoint, gates log, result dict) and runs each stage
    in order. ``cmd_loop`` constructs a runner and maps exceptions to return
    codes; checkpoint key names and gate semantics are unchanged.
    """

    def __init__(self, root: Path, cfg: dict, problem: str,
                 approve: list[str] | None = None,
                 gates_override: str | None = None,
                 max_sources: int = 3):
        from ..hub.state import load_checkpoint
        if gates_override:
            cfg = {**cfg, "gates": {"post_analyze": gates_override, "post_audit": gates_override}}
        self.root = root
        self.cfg = cfg
        self.problem = problem
        self.approved = set(approve or [])
        self.max_sources = max_sources
        self.gates_log: list[str] = []
        self.result = {"outcome": "stopped", "sources": 0, "confidence": "?", "spec": "—"}
        self.ckpt = load_checkpoint(root, cfg, problem)
        self.ingested: list[dict] = []
        self.run_log_path: Path | None = None
        self.analysis: dict = {}
        self.analysis_path: Path | None = None
        self.spec_text: str = ""
        self.audit: dict = {}

    def run(self) -> int:
        from ..hub.progress import progress
        from ..hub.state import save_checkpoint
        self._progress = progress
        self._save_checkpoint = save_checkpoint
        try:
            if (rc := self._stage_research()) is not None:
                return rc
            if (rc := self._stage_analyze()) is not None:
                return rc
            if (rc := self._stage_gate1()) is not None:
                return rc
            if (rc := self._stage_draft()) is not None:
                return rc
            if (rc := self._stage_audit()) is not None:
                return rc
            if (rc := self._stage_gate2()) is not None:
                return rc
            return self._stage_record()
        except LLMError as e:
            err(f"loop needs an LLM backend: {e}")
            self.result["outcome"] = f"failed ({e})"
            self.result["gates"] = "; ".join(self.gates_log) or "—"
            record_loop(self.root, self.cfg, self.problem, self.result)
            return 1

    def _run_or_resume_research(self) -> None:
        if "ingested" in self.ckpt:
            self.ingested = self.ckpt["ingested"]
            self.run_log_path = Path(self.ckpt["run_log"]) if self.ckpt.get("run_log") else None
            info("resumed from checkpoint")
            return
        research = run_research(self.root, self.cfg, self.problem, self.max_sources)
        self.run_log_path = write_run_log(self.root, self.cfg, research)
        self.ingested = research["ingested"]
        self.ckpt["ingested"] = self.ingested
        self.ckpt["run_log"] = str(self.run_log_path)
        self._save_checkpoint(self.root, self.cfg, self.problem, self.ckpt)

    def _stage_research(self) -> int | None:
        self._progress(self.root, self.cfg, self.problem, "[1/7] Research",
                       "proposing + ingesting sources")
        self._run_or_resume_research()
        self.result["sources"] = len(self.ingested)
        ok(f"{self.result['sources']} source(s) ingested")
        return None

    def _run_or_resume_analyze(self) -> None:
        if "analysis" in self.ckpt:
            self.analysis = self.ckpt["analysis"]
            self.analysis_path = Path(self.ckpt["analysis_path"])
            info("resumed from checkpoint")
            return
        self.analysis = run_analyze(self.root, self.cfg, self.problem, self.ingested)
        self.analysis_path = write_analysis(self.root, self.cfg, self.problem, self.analysis,
                                            self.ingested, self.run_log_path)
        self.ckpt["analysis"] = self.analysis
        self.ckpt["analysis_path"] = str(self.analysis_path)
        self._save_checkpoint(self.root, self.cfg, self.problem, self.ckpt)

    def _stage_analyze(self) -> int | None:
        self._progress(self.root, self.cfg, self.problem, "[2/7] Analyze",
                       f"synthesizing {self.result['sources']} source(s) against the repo")
        self._run_or_resume_analyze()
        self.result["confidence"] = self.analysis["confidence"]
        ok(f"{len(self.analysis['findings'])} finding(s), confidence {self.analysis['confidence']}")
        return None

    def _gate1_payload(self) -> dict:
        return {
            "problem": self.problem,
            "summary": (f"{self.analysis['recommendation']} — "
                        f"[[{self.analysis_path.stem}]]"),
            "detail": {
                "confidence": self.analysis["confidence"],
                "findings": self.analysis["findings"][:6],
                "risks": self.analysis["risks"][:4],
                "doc": f"research/analysis/{self.analysis_path.name}",
            },
        }

    def _stop_at_gate(self, name: str) -> int:
        self.gates_log.append(f"{name}: stopped")
        self.result["gates"] = "; ".join(self.gates_log)
        if not _gate_paused(self.root, self.cfg, name, self.problem):
            _finish_loop(self.root, self.cfg, self.problem)
        record_loop(self.root, self.cfg, self.problem, self.result)
        return 2

    def _stage_gate1(self) -> int | None:
        self._progress(self.root, self.cfg, self.problem, "[3/7] Gate 1 (post-analyze)",
                       "waiting on human" if gate_mode("post_analyze", self.cfg) == "prompt" else "")
        if not gate("post_analyze", self._gate1_payload(), self.cfg, self.root, self.approved):
            return self._stop_at_gate("post_analyze")
        self.gates_log.append("post_analyze: passed")
        return None

    def _run_or_resume_draft(self) -> None:
        if "spec_text" in self.ckpt:
            self.spec_text = self.ckpt["spec_text"]
            info("resumed from checkpoint")
            return
        self.spec_text = run_draft(self.root, self.cfg, self.problem, self.analysis)
        ok(f"spec drafted ({len(self.spec_text.splitlines())} lines)")

    def _stage_draft(self) -> int | None:
        self._progress(self.root, self.cfg, self.problem, "[4/7] Draft",
                       "writing the implementation spec")
        self._run_or_resume_draft()
        return None

    def _audit_with_revision(self) -> dict:
        audit = run_audit(self.cfg, self.problem, self.spec_text, root=self.root)
        if audit["verdict"] == "pass" or not audit["issues"]:
            return audit
        self._progress(self.root, self.cfg, self.problem, "[5/7] Audit",
                       f"revising: {len(audit['issues'])} issue(s)", banner=False)
        self.spec_text = complete(REVISE_PROMPT.format(
            spec=self.spec_text,
            issues="\n".join(f"- {i}" for i in audit["issues"]),
        ), self.cfg, role="draft", root=self.root)
        return run_audit(self.cfg, self.problem, self.spec_text, root=self.root)

    def _run_or_resume_audit(self) -> None:
        if "audit" in self.ckpt:
            self.audit = self.ckpt["audit"]
            self.spec_text = self.ckpt["spec_text"]
            info("resumed from checkpoint")
            return
        self.audit = self._audit_with_revision()
        self.ckpt["spec_text"] = self.spec_text
        self.ckpt["audit"] = self.audit
        self._save_checkpoint(self.root, self.cfg, self.problem, self.ckpt)

    def _stage_audit(self) -> int | None:
        self._progress(self.root, self.cfg, self.problem, "[5/7] Audit",
                       "adversarial review of the spec")
        self._run_or_resume_audit()
        ok(f"audit verdict: {self.audit['verdict']}")
        return None

    def _gate2_payload(self, spec_path: Path) -> dict:
        return {
            "problem": self.problem,
            "summary": (f"audit {self.audit['verdict']}: {self.audit['notes']} — "
                        f"[[{spec_path.stem}]]"),
            "detail": {
                "audit_verdict": self.audit["verdict"],
                "issues": self.audit["issues"][:8],
                "doc": f"specs/{spec_path.name}",
            },
        }

    def _stage_gate2(self) -> int | None:
        self._progress(self.root, self.cfg, self.problem, "[6/7] Gate 2 (post-audit)",
                       "waiting on human" if gate_mode("post_audit", self.cfg) == "prompt" else "")
        spec_path = write_spec(self.root, self.cfg, self.problem, self.spec_text, self.audit,
                               status="draft", analysis_path=self.analysis_path)
        self.result["spec"] = f"[[{spec_path.stem}]]"
        if not gate("post_audit", self._gate2_payload(spec_path), self.cfg, self.root,
                    self.approved):
            return self._stop_at_gate("post_audit")
        self.gates_log.append("post_audit: passed")
        return None

    def _stage_record(self) -> int:
        self._progress(self.root, self.cfg, self.problem, "[7/7] Record", "spec approved")
        write_spec(self.root, self.cfg, self.problem, self.spec_text, self.audit,
                   status="approved", analysis_path=self.analysis_path)
        self.result["outcome"] = "approved"
        self.result["gates"] = "; ".join(self.gates_log)
        _finish_loop(self.root, self.cfg, self.problem)
        record_loop(self.root, self.cfg, self.problem, self.result)
        return 0


def cmd_loop(root: Path, cfg: dict, problem: str, approve: list[str] | None = None,
             gates_override: str | None = None, max_sources: int = 3) -> int:
    """Returns 0 done, 1 error, 2 stopped (paused at a gate or rejected).

    Stage orchestration lives on ``_RadarLoopRunner``; checkpoint keys and
    return codes are unchanged.
    """
    header(f"radar loop")
    info(problem)
    ensure_dirs(root, cfg)
    return _RadarLoopRunner(root, cfg, problem, approve, gates_override, max_sources).run()


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


def ticket_problem(ticket: dict) -> str:
    """Canonical problem string for a ticket — must be stable, it keys
    checkpoints and gate decisions across pauses/resumes.

    Acceptance criteria ride along: they are the contract the spec's
    Tests/Documentation sections and the act stage must satisfy."""
    criteria = ticket.get("criteria") or []
    crit = (" Acceptance criteria: " + "; ".join(c.strip() for c in criteria) + ".") \
        if criteria else ""
    return (f"{ticket['title']}. {ticket['why']}{crit} "
            "Research current best practices and draft a spec for this work.")


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
        problem = ticket_problem(ticket)
        info(f"working approved ticket {ticket['id']}: {ticket['title'][:80]}")
        rc = cmd_loop(root, cfg, problem, approve=approve, gates_override=gates_override)
        if rc == 0:
            set_ticket_status(root, cfg, ticket["id"], "in-progress")
            spec = spec_for_problem(root, cfg, problem) or _latest_spec(root, cfg)
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


def spec_for_problem(root: Path, cfg: dict, problem: str) -> str | None:
    """The spec stem THIS problem produced (deterministic slug match).

    Concurrent loops make "latest spec" a race — loop A finishing must never
    link loop B's spec onto its ticket."""
    slug = slugify(problem, 40)
    specs = sorted((root / cfg["docs_dir"] / "specs").glob(f"*-{slug}-spec.md"),
                   key=lambda p: p.stat().st_mtime)
    return specs[-1].stem if specs else None
