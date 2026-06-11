"""`radar research` — LLM proposes sources for a question, radar ingests them.

ReAct-shaped: the model reasons over repo context, proposes acquisition

Vault: docs/tickets/tkt-0036
Vault: docs/research/sources/url-aider-chat-docs-repomap
actions (source refs), the tool executes them, and the run is recorded to
docs/research/runs/ so every research session is auditable.
"""

import hashlib
import json
import subprocess
from pathlib import Path

from ..utils import check_scan_schema_version, ensure_dirs, err, header, info, now_date, now_iso, ok, step, write_doc
from .fetchers import FetchError, fetch
from .llm import LLMError, complete_json, summarize_source
from .sources import frontmatter, rebuild_research_index, slugify, write_source

PROPOSE_PROMPT = """You are the research arm of a software project's knowledge loop.

Repo context (from repo-scan):
{repo_context}

Already-ingested sources (do NOT propose these again):
{existing}

Research question: {question}

Propose up to {max_sources} concrete external sources to ingest. Only formats:
- "arxiv:<id>" for papers (e.g. "arxiv:2210.03629")
- "github:<owner>/<repo>" for repositories
- "url:<https://...>" for articles/docs
- "file:<path>" only if the question mentions a local file

Respond with ONLY a JSON object:
{{
  "sources": [
    {{"ref": "github:owner/repo", "why": "one sentence — why this source answers the question"}}
  ],
  "notes": "1-2 sentences on your overall research strategy"
}}"""


_SNAPSHOT_CACHE: dict[str, str] = {}


def _git_head_short(root: Path) -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root,
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else "?"
    except (subprocess.TimeoutExpired, OSError):
        return "?"


def repo_snapshot_digest(root: Path, cfg: dict) -> str:
    """Stable digest from scan timestamp + git HEAD — dedup across parallel loops."""
    scan_json = root / cfg["docs_dir"] / "scan.json"
    generated = "none"
    if scan_json.exists():
        try:
            generated = json.loads(scan_json.read_text()).get("generated_at", "none")
        except json.JSONDecodeError:
            generated = "unreadable"
    raw = f"{generated}:{_git_head_short(root)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def repo_snapshot(root: Path, cfg: dict, max_chars: int | None = None) -> str:
    """Ranked repo map for LLM prompts — scan.json + tickets, not whole files."""
    max_chars = max_chars or int(cfg.get("repo_snapshot_max_chars", 2500))
    digest = repo_snapshot_digest(root, cfg)
    if digest in _SNAPSHOT_CACHE:
        return _SNAPSHOT_CACHE[digest][:max_chars]

    scan_json = root / cfg["docs_dir"] / "scan.json"
    if not scan_json.exists():
        text = repo_context_snippet(root, cfg, max_chars)
        _SNAPSHOT_CACHE[digest] = text
        return text
    try:
        data = json.loads(scan_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        text = repo_context_snippet(root, cfg, max_chars)
        _SNAPSHOT_CACHE[digest] = text
        return text
    if not check_scan_schema_version(data):
        text = repo_context_snippet(root, cfg, max_chars)
        _SNAPSHOT_CACHE[digest] = text
        return text

    repo = data.get("repo", {})
    branch = repo.get("branch") or _git_branch(root)
    generated = data.get("generated_at", "?")
    head = _git_head_short(root)
    lines = [
        f"## Repo snapshot (generated {generated}, {branch}@{head})",
        f"Languages: {data.get('languages', {})}",
        "Hotspots (rank × churn × complexity):",
    ]

    churn_by_file = {c["file"]: c.get("commits", 0) for c in data.get("churn", [])}
    for i, row in enumerate(data.get("ranking", [])[:8], 1):
        f = row["file"]
        churn = churn_by_file.get(f, row.get("commits", 0))
        tested = "yes" if row.get("tested") else "no"
        lines.append(
            f"  - {f} — rank #{i}, {row.get('lines', '?')} lines, "
            f"tests: {tested}, churn {churn}, CC {row.get('complexity', 0)}"
        )

    from ..tickets import OPEN_STATUSES, load_tickets
    open_tickets = [t for t in load_tickets(root, cfg)
                    if t.get("status") in OPEN_STATUSES][:5]
    if open_tickets:
        lines.append("Open tickets:")
        for t in open_tickets:
            title = (t.get("title") or "")[:60]
            lines.append(f"  - {t['id']}: {title} ({t.get('status')})")

    delta_lines = _snapshot_delta_lines(root, cfg)
    if delta_lines:
        lines.append("Metric deltas:")
        lines.extend(delta_lines)

    seam = _top_seam_pair(data)
    if seam:
        lines.append(f"Coupling alert: {seam['a']} ↔ {seam['b']} "
                     f"(degree {seam.get('degree', '?')}, shared {seam.get('shared', '?')})")

    digest_excerpt = _digest_excerpt(root, cfg)
    if digest_excerpt:
        lines.append(f"Digest: {digest_excerpt}")

    text = "\n".join(lines)[:max_chars]
    _SNAPSHOT_CACHE[digest] = text
    return text


def _git_branch(root: Path) -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root,
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else "?"
    except (subprocess.TimeoutExpired, OSError):
        return "?"


def _snapshot_delta_lines(root: Path, cfg: dict) -> list[str]:
    """Last trend row or index callout — top regressions only."""
    trend = root / cfg["docs_dir"] / "reports" / "trend.md"
    if trend.exists():
        rows = [ln for ln in trend.read_text(encoding="utf-8").splitlines()
                if ln.startswith("|") and "---" not in ln and "generated_at" not in ln]
        if rows:
            cells = [c.strip() for c in rows[-1].strip("|").split("|")]
            if len(cells) >= 5:
                return [f"  - since {cells[0]}: lines {cells[1]}, files {cells[2]}, "
                        f"hotspots {cells[3]}, critical {cells[4]}"]
    index = root / cfg["docs_dir"] / "index.md"
    if not index.exists():
        return []
    block = []
    for ln in index.read_text(encoding="utf-8").splitlines():
        if ln.startswith("> "):
            block.append(ln[2:].strip())
        elif block and not ln.strip():
            break
        elif block and ln.startswith(">"):
            block.append(ln.lstrip("> ").strip())
    return [f"  - {ln}" for ln in block[:3]] if block else []


def _top_seam_pair(data: dict) -> dict | None:
    seams = data.get("behavior", {}).get("seams") or data.get("seams") or []
    if seams:
        return max(seams, key=lambda s: s.get("degree", 0))
    coupling = data.get("behavior", {}).get("coupling") or []
    if not coupling:
        return None
    py_edges = {(e.get("a"), e.get("b")) for e in data.get("py_edges", [])}
    ts_edges = {(e.get("a"), e.get("b")) for e in data.get("ts_edges", [])}
    import_edges = py_edges | ts_edges | {(b, a) for a, b in py_edges | ts_edges}
    seam_pairs = []
    for c in coupling:
        a, b = c.get("a"), c.get("b")
        if not a or not b:
            continue
        if (a, b) not in import_edges and (b, a) not in import_edges:
            seam_pairs.append(c)
    if not seam_pairs:
        return max(coupling, key=lambda s: s.get("degree", 0))
    return max(seam_pairs, key=lambda s: s.get("degree", 0))


def _digest_excerpt(root: Path, cfg: dict, limit: int = 800) -> str:
    for rel in ("digest.md", "reports/health.md"):
        path = root / cfg["docs_dir"] / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for ln in text.splitlines():
            stripped = ln.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
                return stripped[:limit]
    return ""


def repo_context_snippet(root: Path, cfg: dict, max_chars: int = 1500) -> str:
    """Compact identity block — delegates to repo_snapshot when scan.json exists."""
    scan_json = root / cfg["docs_dir"] / "scan.json"
    if scan_json.exists():
        return repo_snapshot(root, cfg, max_chars=max_chars)
    return f"(no scan.json — repo '{root.name}', run repo-scan for richer context)"


def existing_source_ids(root: Path, cfg: dict) -> list[str]:
    sources_dir = root / cfg["docs_dir"] / "research" / "sources"
    if not sources_dir.is_dir():
        return []
    return sorted(f.stem for f in sources_dir.glob("*.md"))


def run_research(root: Path, cfg: dict, question: str, max_sources: int = 3) -> dict:
    """Core research routine. Returns a result dict (also used by the B3 loop)."""
    from ..hub.telemetry import set_llm_context, timed_block
    set_llm_context(question, "research")
    proposal = complete_json(PROPOSE_PROMPT.format(
        repo_context=repo_snapshot(root, cfg),
        existing="\n".join(existing_source_ids(root, cfg)) or "(none)",
        question=question,
        max_sources=max_sources,
    ), cfg, role="research", root=root, problem=question, stage_id="research")

    proposed = proposal.get("sources", [])[:max_sources]
    ingested, failed = [], []
    with timed_block(root, cfg, question, "research_fetch", "fetch + summarize sources"):
        for item in proposed:
            ref = str(item.get("ref", ""))
            why = str(item.get("why", ""))
            try:
                source, text = fetch(ref)
            except FetchError as e:
                failed.append({"ref": ref, "error": str(e)})
                continue
            source.relevance = why or source.relevance
            try:
                source = summarize_source(source, text, cfg, root=root)
            except LLMError as e:
                info(f"summarize failed for {ref} ({e}) — keeping fetched summary")
            write_source(root, cfg, source)
            ingested.append({"ref": ref, "id": source.id, "title": source.title, "why": why})

    rebuild_research_index(root, cfg)
    return {
        "question": question,
        "strategy": proposal.get("notes", ""),
        "ingested": ingested,
        "failed": failed,
    }


def write_run_log(root: Path, cfg: dict, result: dict) -> Path:
    runs = root / cfg["docs_dir"] / "research" / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    path = runs / f"{now_date()}-{slugify(result['question'], 40)}.md"

    lines = [
        frontmatter({
            "type": "research-run",
            "question": result["question"],
            "sources": [item["id"] for item in result["ingested"]],
            "run_at": now_iso(),
        }),
        "",
        f"# Research run — {result['question']}",
        f"_Run {now_iso()}_",
        "",
        f"**Strategy:** {result.get('strategy') or '—'}",
        "",
        "## Ingested",
        "",
    ]
    for item in result["ingested"]:
        lines.append(f"- [[sources/{item['id']}\\|{item['title']}]] — {item['why'] or item['ref']}")
    if not result["ingested"]:
        lines.append("_nothing ingested_")
    if result["failed"]:
        lines += ["", "## Failed", ""]
        for item in result["failed"]:
            lines.append(f"- `{item['ref']}` — {item['error']}")
    lines.append("")
    write_doc(path, "\n".join(lines), root)
    return path


def cmd_research(root: Path, cfg: dict, question: str, max_sources: int = 3) -> int:
    header(f"radar research")
    info(question)
    ensure_dirs(root, cfg)

    step("Proposing sources (LLM)")
    try:
        result = run_research(root, cfg, question, max_sources)
    except LLMError as e:
        err(f"research needs an LLM backend: {e}")
        return 1
    ok(f"{len(result['ingested'])} ingested, {len(result['failed'])} failed")

    step("Recording run")
    write_run_log(root, cfg, result)
    return 0 if result["ingested"] else 1
