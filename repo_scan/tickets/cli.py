"""``repo-scan tickets`` CLI subcommand."""

from pathlib import Path

from ..utils import ok
from .constants import BOARD_COLUMNS
from .io import load_tickets
from .workflow import new_ticket, set_ticket_status


def tickets_main(argv: list[str]) -> int:
    """`repo-scan tickets [list|approve|start|reject|done] [id]`"""
    import argparse

    from ..config import load_config

    parser = argparse.ArgumentParser(
        prog="repo-scan tickets",
        description="Review scan-generated tickets from the terminal",
    )
    parser.add_argument("action", nargs="?", default="list",
                        choices=["list", "new", "approve", "start", "reject", "done"])
    parser.add_argument("ticket_id", nargs="?",
                        help="ticket id (or the title, for `new`)")
    parser.add_argument("--repo", default=".", help="Repo root (default: cwd)")
    parser.add_argument("--why", default="", help="(new) rationale for the ticket")
    parser.add_argument("--priority", default="medium",
                        choices=["high", "medium", "low"], help="(new) priority")
    parser.add_argument("--criterion", action="append", default=[],
                        metavar="TEXT", help="(new) acceptance criterion; repeatable")
    parser.add_argument("--kind", default="feature",
                        help="(new) ticket kind: feature, refactor, chore... (default feature)")
    parser.add_argument("--approve", action="store_true",
                        help="(new) create directly as approved")
    args = parser.parse_args(argv)

    root = Path(args.repo).resolve()
    cfg = load_config(root)
    status_for = {"approve": "approved", "start": "in-progress",
                  "reject": "rejected", "done": "done"}

    if args.action == "new":
        if not args.ticket_id:
            parser.error("`new` requires a title: repo-scan tickets new \"...\"")
        if args.approve and not args.criterion:
            print("error: --approve requires at least one --criterion")
            return 1
        ticket = new_ticket(root, cfg, args.ticket_id, why=args.why,
                            priority=args.priority, criteria=args.criterion,
                            kind=args.kind,
                            status="approved" if args.approve else "proposed")
        ok(f"{ticket['id']} ({ticket['status']}): {ticket['title']}")
        if not args.criterion:
            print("  tip: acceptance criteria drive the spec and the tests —"
                  " add them with --criterion before approving")
        return 0

    if args.action == "list":
        tickets = load_tickets(root, cfg)
        if not tickets:
            print("no tickets — run repo-scan to propose some")
            return 0
        order = {s: i for i, (_, s) in enumerate(BOARD_COLUMNS)}
        prio = {"high": 0, "medium": 1, "low": 2}
        tickets.sort(key=lambda t: (order.get(t.get("status"), 9),
                                    prio.get(t.get("priority", "medium"), 1), t["id"]))
        for t in tickets:
            title = t["title"] if len(t["title"]) <= 70 else t["title"][:69] + "…"
            print(f"{t['id']:<10} {t.get('status', '?'):<12} "
                  f"{t.get('priority', '?'):<7} {t.get('origin', '?'):<6} {title}")
        return 0

    if not args.ticket_id:
        parser.error(f"'{args.action}' requires a ticket id")
    try:
        ticket = set_ticket_status(root, cfg, args.ticket_id, status_for[args.action])
    except (KeyError, ValueError) as e:
        ok_or_err = str(e).strip("'")
        print(f"error: {ok_or_err}")
        return 1
    ok(f"{ticket['id']} -> {status_for[args.action]}  ({ticket['title']})")
    return 0
