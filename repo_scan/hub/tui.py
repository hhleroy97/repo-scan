"""radar top — a curses dashboard over the same state the phone sees.

Stdlib only. Reads build_state() directly (no HTTP hop), writes through the
same decision inbox and ticket APIs as every other surface. Pure helpers
(actionable_items, frame_lines, apply_decision) are separated from the curses
loop so the rendering logic is testable without a terminal.

Keys: j/k move · a approve · r reject · enter detail · g refresh · q quit
"""

import time
from pathlib import Path

# style tags resolved to curses attributes inside the loop
S_TITLE, S_DIM, S_OK, S_WARN, S_BAD, S_ACCENT, S_SEL, S_TEXT = range(8)


def _tok(n: int) -> str:
    n = int(n or 0)
    if n >= 1_000_000:
        return f"{n / 1e6:.1f}M"
    if n >= 1_000:
        return f"{n / 1e3:.1f}k"
    return str(n)


def actionable_items(state: dict) -> list[dict]:
    """Gates first (most urgent), then tickets a human can move forward."""
    items = []
    for g in state.get("gates", []):
        items.append({"kind": "gate", "gate": g.get("gate"),
                      "problem": g.get("problem", ""),
                      "label": g.get("summary", "")[:120],
                      "detail": g.get("detail", {})})
    for t in state.get("tickets", []):
        if t.get("status") in ("proposed", "approved"):
            items.append({"kind": "ticket", "id": t.get("id"),
                          "status": t.get("status"),
                          "label": f"{t.get('id')} {t.get('title', '')}"[:120]})
    return items


def apply_decision(root: Path, cfg: dict, item: dict, decision: str) -> str:
    """Route a/r onto the selected item. Returns a status message."""
    from ..tickets import set_ticket_status
    from .state import submit_decision
    if item["kind"] == "gate":
        submit_decision(root, cfg, item["gate"], item["problem"], decision,
                        source="tui")
        return (f"{item['gate']}: {decision}d — daemon resumes on next poll"
                if decision == "approve" else f"{item['gate']}: rejected")
    # ticket: approve moves proposed->approved / approved->in-progress
    if decision == "approve":
        new = "approved" if item["status"] == "proposed" else "in-progress"
    else:
        new = "rejected"
    set_ticket_status(root, cfg, item["id"], new)
    return f"{item['id']}: {new}"


def _usage_rows(usage: dict) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    total, today = usage.get("total", {}), usage.get("today", {})
    if not total.get("calls"):
        rows.append((S_DIM, "  no LLM calls recorded yet"))
        return rows
    est = " (some estimated)" if total.get("estimated") else ""
    rows.append((S_TEXT, f"  today     {today.get('calls', 0):>4} calls   "
                         f"{_tok(today.get('input_tokens', 0)):>8} in  "
                         f"{_tok(today.get('output_tokens', 0)):>8} out"))
    rows.append((S_TEXT, f"  all time  {total.get('calls', 0):>4} calls   "
                         f"{_tok(total.get('input_tokens', 0)):>8} in  "
                         f"{_tok(total.get('output_tokens', 0)):>8} out{est}"))
    for model, a in usage.get("by_model", {}).items():
        rows.append((S_DIM, f"    {model[:28]:<28} {a.get('calls', 0):>4} calls   "
                            f"{_tok(a.get('input_tokens', 0)):>8} in  "
                            f"{_tok(a.get('output_tokens', 0)):>8} out"))
    for role, a in usage.get("by_role", {}).items():
        rows.append((S_DIM, f"    {role[:28]:<28} {a.get('calls', 0):>4} calls   "
                            f"{_tok(a.get('input_tokens', 0)):>8} in  "
                            f"{_tok(a.get('output_tokens', 0)):>8} out"))
    if total.get("cost_usd") is not None:
        rows.append((S_DIM, f"    reported cost ${total['cost_usd']}"))
    return rows


def frame_lines(state: dict, sel: int, message: str = "") -> list[tuple[int, str]]:
    """The whole screen as (style, text) rows — pure, testable."""
    rows: list[tuple[int, str]] = []
    repo = state.get("repo", {})
    rows.append((S_TITLE, f" {repo.get('name', '?')} hub · {repo.get('branch', '?')}"
                          f" · v{state.get('version', '?')} · {state.get('now', '')}"))

    sc = state.get("scan", {})
    if sc:
        rows.append((S_DIM, f"  {sc.get('files', 0)} files · "
                            f"{sc.get('lines', 0):,} lines · "
                            f"{sc.get('hotspots', 0)} hotspots · "
                            f"{sc.get('critical', 0)} critical"))

    items = actionable_items(state)
    gates = [i for i in items if i["kind"] == "gate"]
    tickets = [i for i in items if i["kind"] == "ticket"]

    rows.append((S_WARN, f" GATES ({len(gates)})"))
    if not gates:
        rows.append((S_DIM, "  none waiting — all clear"))
    for i, g in enumerate(gates):
        style = S_SEL if i == sel else S_TEXT
        rows.append((style, f"  {'>' if i == sel else ' '} [{g['gate']}] {g['label']}"))

    runs = state.get("runs", [])
    rows.append((S_ACCENT, f" RUNS ({len(runs)})"))
    if not runs:
        rows.append((S_DIM, "  no runs yet"))
    for r in runs[:6]:
        mark = {"done": S_OK, "failed": S_BAD, "stopped": S_BAD,
                "waiting-on-gate": S_WARN}.get(r.get("status"), S_ACCENT)
        gate = f" @ {r['gate']}" if r.get("gate") else ""
        kind = r.get("kind", "loop")
        rows.append((mark, f"  {r.get('status', '?'):<16}{gate:<18} {kind:<5} "
                           f"{str(r.get('problem', ''))[:70]}"))
        if r.get("stage") and r.get("status") in ("running", "queued", "waiting-on-gate"):
            detail = f" — {r['stage_detail']}" if r.get("stage_detail") else ""
            rows.append((S_DIM, f"      > {r['stage']}{detail}"[:110]))

    rows.append((S_ACCENT, f" TICKETS ({len(tickets)} actionable)"))
    if not tickets:
        rows.append((S_DIM, "  nothing actionable"))
    for j, t in enumerate(tickets):
        i = len(gates) + j
        style = S_SEL if i == sel else S_TEXT
        rows.append((style, f"  {'>' if i == sel else ' '} [{t['status']}] {t['label']}"))

    events = state.get("events", [])
    if events:
        rows.append((S_ACCENT, " AGENT FEED"))
        for e in events[:6]:
            when = str(e.get("when", ""))[11:16]
            rows.append((S_DIM, f"  {when}  {e.get('kind', '?'):<6} {e.get('text', '')[:85]}"))

    rows.append((S_ACCENT, " LLM USAGE"))
    rows.extend(_usage_rows(state.get("usage", {})))

    acts = state.get("activity", [])
    if acts:
        rows.append((S_ACCENT, " RECENT DECISIONS"))
        for a in acts[:4]:
            rows.append((S_DIM, f"  {a.get('when', '')[:16]} {a.get('gate', ''):<14} "
                                f"{a.get('decision', ''):<10} {a.get('summary', '')[:60]}"))

    rows.append((S_DIM, ""))
    rows.append((S_TITLE, " j/k move · a approve · r reject · enter detail · g refresh · q quit"))
    if message:
        rows.append((S_OK, f" {message}"))
    return rows


def detail_lines(item: dict) -> list[str]:
    """Popup body for the selected gate."""
    d = item.get("detail", {})
    out = [f"[{item.get('gate', item.get('id', '?'))}]", item.get("label", ""), ""]
    if d.get("confidence"):
        out.append(f"confidence: {d['confidence']}")
    if d.get("audit_verdict"):
        out.append(f"audit: {d['audit_verdict']}")
    for key in ("findings", "issues", "risks"):
        vals = d.get(key) or []
        if vals:
            out.append("")
            out.append(f"{key.upper()}:")
            out.extend(f"  - {str(v)[:200]}" for v in vals)
    if d.get("doc"):
        out += ["", f"full document: {d['doc']}"]
    return out


def run_tui(root: Path, cfg: dict, poll_seconds: float = 3.0) -> int:
    import curses
    from .server import build_state

    def main(scr):
        curses.curs_set(0)
        curses.use_default_colors()
        curses.start_color()
        pairs = {S_TITLE: (curses.COLOR_CYAN, curses.A_BOLD),
                 S_DIM: (curses.COLOR_WHITE, curses.A_DIM),
                 S_OK: (curses.COLOR_GREEN, 0),
                 S_WARN: (curses.COLOR_YELLOW, curses.A_BOLD),
                 S_BAD: (curses.COLOR_RED, 0),
                 S_ACCENT: (curses.COLOR_BLUE, curses.A_BOLD),
                 S_SEL: (curses.COLOR_BLACK, 0),
                 S_TEXT: (-1, 0)}
        attr = {}
        for i, (tag, (color, extra)) in enumerate(pairs.items(), start=1):
            bg = curses.COLOR_CYAN if tag == S_SEL else -1
            curses.init_pair(i, color, bg)
            attr[tag] = curses.color_pair(i) | extra

        scr.timeout(int(poll_seconds * 1000))
        state = build_state(root, cfg)
        sel, message, popup = 0, "", None
        last_poll = time.time()

        while True:
            items = actionable_items(state)
            sel = max(0, min(sel, len(items) - 1)) if items else 0
            scr.erase()
            h, w = scr.getmaxyx()
            if popup is not None:
                for y, line in enumerate(popup[:h - 1]):
                    scr.addnstr(y, 0, line, w - 1)
                scr.addnstr(h - 1, 0, " any key to close ", w - 1,
                            attr[S_TITLE])
            else:
                for y, (tag, text) in enumerate(frame_lines(state, sel, message)[:h]):
                    try:
                        scr.addnstr(y, 0, text, w - 1, attr.get(tag, 0))
                    except curses.error:
                        pass
            scr.refresh()

            ch = scr.getch()
            if popup is not None and ch != -1:
                popup = None
                continue
            if ch in (ord("q"), 27):
                return 0
            if ch in (ord("j"), curses.KEY_DOWN):
                sel += 1
            elif ch in (ord("k"), curses.KEY_UP):
                sel -= 1
            elif ch == ord("g"):
                state, message = build_state(root, cfg), "refreshed"
            elif ch in (ord("a"), ord("r")) and items:
                decision = "approve" if ch == ord("a") else "reject"
                message = apply_decision(root, cfg, items[sel], decision)
                state = build_state(root, cfg)
            elif ch in (10, 13, curses.KEY_ENTER) and items:
                popup = detail_lines(items[sel])
            elif ch == -1 and time.time() - last_poll >= poll_seconds:
                state, last_poll = build_state(root, cfg), time.time()

    import curses
    return curses.wrapper(main)
