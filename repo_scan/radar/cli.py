"""radar CLI — research-to-implementation loop on the repo-scan docs/ base."""

import argparse
import sys
from pathlib import Path

from ..config import VERSION, load_config
from ..utils import ensure_dirs, err, git_root, header, info, ok, step
from .fetchers import FetchError, fetch
from .sources import rebuild_research_index, write_source


def _resolve_root(path_str: str) -> Path:
    root = Path(path_str).resolve()
    if not root.exists():
        err(f"Path not found: {root}")
        sys.exit(1)
    return git_root(root) or root


def cmd_ingest(root: Path, cfg: dict, ref: str, summarize: bool) -> int:
    header(f"radar ingest  {ref}")
    ensure_dirs(root, cfg)

    step("Fetching")
    try:
        source, text = fetch(ref)
    except FetchError as e:
        err(str(e))
        return 1
    ok(f"{source.type}: {source.title[:70]}")

    if summarize:
        from .llm import LLMError, summarize_source
        step("Summarizing (LLM)")
        try:
            source = summarize_source(source, text, cfg)
            ok(f"summary + {len(source.key_claims)} key claim(s)")
        except LLMError as e:
            info(f"LLM unavailable ({e}) — keeping fetched summary")

    step("Writing")
    write_source(root, cfg, source)
    rebuild_research_index(root, cfg)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="radar — research loop for repo-scan knowledge bases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"radar {VERSION}")
    parser.add_argument("--repo", default=".", help="Target repo root (default: cwd's git root)")
    sub = parser.add_subparsers(dest="command")

    p_ingest = sub.add_parser("ingest", help="Ingest one source into docs/research/sources/")
    p_ingest.add_argument("ref", help="arxiv:ID | github:owner/repo | url:https://... | file:./path")
    p_ingest.add_argument("--no-llm", action="store_true", help="Skip LLM summarization")

    p_research = sub.add_parser("research", help="Find and ingest sources for a question")
    p_research.add_argument("question", help="Natural-language research question")
    p_research.add_argument("--max-sources", type=int, default=3)

    p_loop = sub.add_parser("loop", help="Full R-A-D-A-R pipeline for a problem")
    p_loop.add_argument("problem", help="Natural-language problem description")
    p_loop.add_argument("--approve", action="append", default=[], metavar="GATE",
                        help="Pre-approve a gate (post_analyze, post_audit); repeatable")
    p_loop.add_argument("--gates", choices=["prompt", "auto", "deny"],
                        help="Override all gate modes for this run")
    p_loop.add_argument("--max-sources", type=int, default=3)

    p_full = sub.add_parser("full", help="Metric-triggered loop over RADAR candidates")
    p_full.add_argument("--approve", action="append", default=[], metavar="GATE")
    p_full.add_argument("--gates", choices=["prompt", "auto", "deny"])

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    root = _resolve_root(args.repo)
    cfg = load_config(root)

    if args.command == "ingest":
        sys.exit(cmd_ingest(root, cfg, args.ref, summarize=not args.no_llm))

    if args.command == "research":
        from .research import cmd_research
        sys.exit(cmd_research(root, cfg, args.question, args.max_sources))

    if args.command == "loop":
        from .pipeline import cmd_loop
        sys.exit(cmd_loop(root, cfg, args.problem, approve=args.approve,
                          gates_override=args.gates, max_sources=args.max_sources))

    if args.command == "full":
        from .pipeline import cmd_full
        sys.exit(cmd_full(root, cfg, approve=args.approve, gates_override=args.gates))


if __name__ == "__main__":
    main()
