"""Token-budgeted single-file digest export (repomix/gitingest-style)."""

from pathlib import Path

from .config import VERSION
from .identity import readme_summary
from .utils import git_branch, git_last_commit, git_remote_url, now_iso


def write_digest(root: Path, cfg: dict, line_counts: dict, languages: dict,
                 churn: list, complexity: list, ranking: list, tree: str) -> Path:
    """Single token-budgeted markdown export (repomix/gitingest-style)."""
    docs = root / cfg["docs_dir"]
    docs.mkdir(parents=True, exist_ok=True)
    budget_chars = cfg.get("digest_tokens", 4000) * 4  # ~4 chars per token

    total_lines = sum(s["lines"] for s in line_counts.values())
    lang_summary = ", ".join(f"{k.upper()}: {len(v)}" for k, v in languages.items() if v)
    summary = readme_summary(root)

    sections = [
        f"# {root.name} — repo digest",
        f"_Generated {now_iso()} by repo-scan {VERSION}. Single-file context for LLM use._",
        "",
        f"**Remote:** {git_remote_url(root)}  |  **Branch:** {git_branch(root)}  |  "
        f"**Last commit:** {git_last_commit(root)}",
        f"**Files:** {len(line_counts)}  |  **Lines:** {total_lines:,}  |  **Languages:** {lang_summary}",
    ]
    if summary:
        sections += ["", f"> {summary}"]

    if ranking:
        sections += ["", "## Most important files", ""]
        for r in ranking:
            sections.append(f"- `{r['file']}` (score {r['score']}, pagerank {r.get('pagerank', 0):.4f}, "
                            f"{r['lines']} lines, imported by {r['imported_by']}, {r['commits']} commits)")

    if tree:
        sections += ["", "## Structure", "", "```", tree, "```"]

    hotspots = complexity[:8]
    if hotspots:
        sections += ["", "## Complexity hotspots", ""]
        for h in hotspots:
            sections.append(f"- `{h['file']}::{h['name']}` rank {h['rank']} (CC {h['complexity']})")

    if churn:
        sections += ["", "## Most changed files", ""]
        for c in churn[:8]:
            sections.append(f"- `{c['file']}` ({c['commits']} commits)")

    content = "\n".join(sections) + "\n"
    if len(content) > budget_chars:
        content = content[:budget_chars] + "\n\n_…truncated to digest token budget._\n"

    path = docs / "digest.md"
    path.write_text(content, encoding="utf-8")
    return path
