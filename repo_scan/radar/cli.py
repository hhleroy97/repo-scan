"""radar CLI — argparse façade for research-to-implementation loop commands.

Gate flag vocabulary (--approve, --gates) is sourced from ``gates``; this module
must not duplicate gate names or mode literals.

Vault: docs/tickets/tkt-0015, docs/tickets/tkt-0031
Spec:  docs/specs/2026-06-10-hidden-seam-repo-scan-radar-cli-py-repo-spec
"""

import argparse
import sys
from pathlib import Path

from ..config import VERSION, load_config
from ..utils import ensure_dirs, err, git_root, header, info, ok, step
from .fetchers import FetchError, fetch
from .gates import ACT_GATE_NAMES, LOOP_GATE_NAMES, gate_cli_parent
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
            source = summarize_source(source, text, cfg, root=root)
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

    p_loop = sub.add_parser(
        "loop",
        help="Full R-A-D-A-R pipeline for a problem",
        parents=[gate_cli_parent(
            approve_help=f"Pre-approve a gate ({', '.join(LOOP_GATE_NAMES)}); repeatable",
            include_gates=True,
        )],
    )
    p_loop.add_argument("problem", help="Natural-language problem description")
    p_loop.add_argument("--max-sources", type=int, default=3)

    p_full = sub.add_parser(
        "full",
        help="Metric-triggered loop over RADAR candidates",
        parents=[gate_cli_parent(approve_help=None, include_gates=True)],
    )

    p_act = sub.add_parser(
        "act",
        help="Implement an approved spec (tests as hard gate)",
        parents=[gate_cli_parent(
            approve_help=f"Pre-approve a gate ({', '.join(ACT_GATE_NAMES)}); repeatable",
            include_gates=False,
        )],
    )
    p_act.add_argument("--ticket", default=None, metavar="TKT-ID",
                       help="Target ticket (default: highest-priority in-progress with approved spec)")
    p_act.add_argument("--worktree", action="store_true",
                       help="Implement in an isolated worktree (parallel-safe)")

    p_top = sub.add_parser("top", help="Terminal dashboard: runs, gates, tickets, LLM usage")
    p_top.add_argument("--poll", type=float, default=3.0, help="Refresh seconds (default 3)")

    p_daemon = sub.add_parser("daemon", help="Resident runner: scans, loops, gate resume")
    p_daemon.add_argument("--poll", type=int, default=None, metavar="SECONDS")

    p_serve = sub.add_parser("serve", help="Mobile dashboard + daemon (default port 8800)")
    p_serve.add_argument("--host", default=None)
    p_serve.add_argument("--port", type=int, default=None)
    p_serve.add_argument("--no-daemon", action="store_true",
                         help="Serve the dashboard without the background runner")

    p_audit = sub.add_parser("audit-provenance",
                             help="Vault provenance coverage audit with regression check")
    p_audit.add_argument("--fix", action="store_true",
                         help="Auto-link orphan analyses from source linked_files")
    p_audit.add_argument("--fail-on-regression", action="store_true",
                         help="Exit 1 if coverage dropped vs last scan.json")

    p_lint = sub.add_parser("lint-links",
                            help="Check linked_files frontmatter in vault docs")

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

    if args.command == "act":
        from .act import cmd_act
        sys.exit(cmd_act(root, cfg, ticket_id=args.ticket, approve=args.approve,
                         worktree=args.worktree))

    if args.command == "top":
        from ..hub.tui import run_tui
        sys.exit(run_tui(root, cfg, poll_seconds=args.poll))

    if args.command == "daemon":
        from ..hub.daemon import cmd_daemon
        sys.exit(cmd_daemon(root, cfg, poll_seconds=args.poll))

    if args.command == "serve":
        from ..hub.server import cmd_serve
        sys.exit(cmd_serve(root, cfg, host=args.host, port=args.port,
                           with_daemon=not args.no_daemon))

    if args.command == "audit-provenance":
        from ..provenance_audit import audit
        sys.exit(audit(root, cfg, fix=args.fix,
                       fail_on_regression=args.fail_on_regression))

    if args.command == "lint-links":
        from ..provenance_lint import main as lint_main
        sys.exit(lint_main())


if __name__ == "__main__":
    main()
