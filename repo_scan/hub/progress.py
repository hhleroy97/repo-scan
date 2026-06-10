"""One progress call, every surface.

progress() is the single way pipeline stages report what they're doing:
it prints to the terminal (same text a CLI user sees), stamps the live
stage onto the run record (web dashboard + radar top render it), and
appends to the shared agent event feed. CLI, web, and TUI can never
drift apart because they all read the same write.
"""

from pathlib import Path

from ..utils import info, step
from .state import append_event, set_run_stage


def progress(root: Path, cfg: dict, problem: str, stage: str,
             detail: str = "", banner: bool = True):
    """Report a stage transition (e.g. "implement", "test: fix round 1/2")."""
    text = f"{stage} — {detail}" if detail else stage
    if banner:
        step(text)
    else:
        info(text)
    set_run_stage(root, cfg, problem, stage, detail)
    append_event(root, cfg, "stage", text, problem=problem[:120])
