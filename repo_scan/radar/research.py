"""`radar research` — LLM proposes sources for a question, radar ingests them.

ReAct-shaped: the model reasons over repo context, proposes acquisition
actions (source refs), the tool executes them, and the run is recorded to
docs/research/runs/ so every research session is auditable.
"""

import json
from pathlib import Path

from ..utils import ensure_dirs, err, header, info, now_date, now_iso, ok, step, write_doc
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


def repo_context_snippet(root: Path, cfg: dict, max_chars: int = 1500) -> str:
    """Compact identity block from scan.json (run repo-scan first for best results)."""
    scan_json = root / cfg["docs_dir"] / "scan.json"
    if not scan_json.exists():
        return f"(no scan.json — repo '{root.name}', run repo-scan for richer context)"
    try:
        data = json.loads(scan_json.read_text())
    except json.JSONDecodeError:
        return f"(unreadable scan.json — repo '{root.name}')"
    repo = data.get("repo", {})
    top = [r["file"] for r in data.get("ranking", [])[:5]]
    snippet = (
        f"name: {repo.get('name')}\n"
        f"remote: {repo.get('remote')}\n"
        f"languages: {data.get('languages')}\n"
        f"entry_points: {repo.get('entry_points')}\n"
        f"most_important_files: {top}"
    )
    return snippet[:max_chars]


def existing_source_ids(root: Path, cfg: dict) -> list[str]:
    sources_dir = root / cfg["docs_dir"] / "research" / "sources"
    if not sources_dir.is_dir():
        return []
    return sorted(f.stem for f in sources_dir.glob("*.md"))


def run_research(root: Path, cfg: dict, question: str, max_sources: int = 3) -> dict:
    """Core research routine. Returns a result dict (also used by the B3 loop)."""
    proposal = complete_json(PROPOSE_PROMPT.format(
        repo_context=repo_context_snippet(root, cfg),
        existing="\n".join(existing_source_ids(root, cfg)) or "(none)",
        question=question,
        max_sources=max_sources,
    ), cfg)

    proposed = proposal.get("sources", [])[:max_sources]
    ingested, failed = [], []
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
            source = summarize_source(source, text, cfg)
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
