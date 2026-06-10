"""Obsidian Kanban board generation from ticket lists."""

from pathlib import Path

from ..utils import write_doc
from .constants import BOARD_COLUMNS, tickets_dir


def write_board(root: Path, cfg: dict, tickets: list[dict],
                resolved_ids: set | None = None):
    """Obsidian Kanban-plugin board — review tickets by dragging cards."""
    resolved_ids = resolved_ids or set()
    lines = ["---", "", "kanban-plugin: board", "", "---", ""]
    for column, status in BOARD_COLUMNS:
        lines.append(f"## {column}")
        lines.append("")
        for t in tickets:
            if t.get("status") == status:
                done = "x" if status in ("done", "rejected") else " "
                note = " — **metrics resolved, ready to close**" if t["id"] in resolved_ids else ""
                lines.append(f"- [{done}] [[{t['id']}|{t['title']}]]{note}")
        lines.append("")
    lines += ["%% kanban:settings", "```", '{"kanban-plugin":"board"}', "```", "%%", ""]
    path = tickets_dir(root, cfg) / "board.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    write_doc(path, "\n".join(lines), root)
