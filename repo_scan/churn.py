"""Git churn analysis."""

from pathlib import Path

from .utils import run


def get_git_churn(root: Path, cfg: dict) -> list[dict]:
    out, _, code = run(["git", "log", "--name-only", "--pretty=format:", "--no-merges"], cwd=root)
    if code != 0:
        return []
    churn: dict[str, int] = {}
    for line in out.splitlines():
        line = line.strip()
        if line:
            churn[line] = churn.get(line, 0) + 1
    sorted_churn = sorted(churn.items(), key=lambda x: x[1], reverse=True)
    return [{"file": f, "commits": c} for f, c in sorted_churn[:cfg["churn_top_n"]]]
