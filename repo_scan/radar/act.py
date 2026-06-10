"""The Act stage: implement an approved spec, tests as the hard gate.

Flow (each gate is file-backed and phone-answerable like all others):

    pick in-progress ticket with approved spec
      -> Gate pre_implement
      -> branch radar/<ticket-id>, agent CLI implements the spec
      -> run the test suite; on failure, feed output back (bounded fix rounds)
      -> Gate post_implement (diff stat + test verdict)
      -> commit on the branch, log to the vault, note the ticket

Safety properties: never starts on a dirty tree, never touches the original
branch, tests must pass before the post gate, and the human merges. Stages
checkpoint, so daemon resumes skip completed work (including the expensive
agent invocation).
"""

import re
import subprocess
from pathlib import Path

from ..utils import err, header, info, now_date, now_iso, ok, step, warn
from .gates import gate
from .llm import LLMError, complete

ACT_TIMEOUT = 1800  # agent implementation runs are long
SPEC_LINK_RE = re.compile(r"\[\[([^\]\|]+-spec)(?:\|[^\]]*)?\]\]")

ACT_PROMPT = """You are implementing an approved specification in this repository.
Work autonomously: read code as needed, make the changes, keep edits minimal
and consistent with existing conventions. Do NOT commit, push, or create
branches — version control is handled outside this session. Do not modify
files under {docs_dir}/. When done, reply with a one-paragraph summary of
what you changed.

Specification:
---
{spec}
---"""

FIX_PROMPT = """Your implementation of a spec in this repository has failing tests.
Fix the failures. Keep changes minimal. Do NOT commit or create branches.
Reply with a one-paragraph summary of the fix.

Test command: {test_cmd}

Failing output (truncated):
---
{output}
---"""


def _git(root: Path, *args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True,
                          text=True, timeout=timeout)


def _tree_dirty(root: Path, docs_dir: str) -> bool:
    """Dirty check that ignores the vault — scans and ticket notes churn
    docs/ constantly and the agent is forbidden from touching it anyway."""
    out = _git(root, "status", "--porcelain", "--", f":(exclude){docs_dir}").stdout
    return bool(out.strip())


def _current_branch(root: Path) -> str:
    return _git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def default_test_cmd(root: Path) -> str | None:
    if (root / "tests").is_dir() or list(root.glob("test_*.py")):
        return "python3 -m pytest -q"
    if (root / "package.json").exists():
        return "npm test --silent"
    return None


def run_tests(root: Path, cfg: dict) -> tuple[bool, str]:
    cmd = cfg.get("test_cmd") or default_test_cmd(root)
    if not cmd:
        return True, "(no test suite detected — treating as pass)"
    try:
        result = subprocess.run(cmd, shell=True, cwd=root, capture_output=True,
                                text=True, timeout=int(cfg.get("test_timeout", 900)))
    except subprocess.TimeoutExpired:
        return False, f"test command timed out: {cmd}"
    output = (result.stdout + "\n" + result.stderr).strip()
    return result.returncode == 0, output[-4000:]


def find_act_tickets(root: Path, cfg: dict) -> list[tuple[dict, str]]:
    """In-progress tickets with an approved spec and no implementation note
    yet, highest priority first. Returns [(ticket, spec_stem), ...]."""
    from ..tickets import load_tickets
    order = {"high": 0, "medium": 1, "low": 2}
    candidates = []
    for t in load_tickets(root, cfg):
        if t["status"] != "in-progress":
            continue
        body = Path(t["path"]).read_text(encoding="utf-8", errors="ignore")
        if "implemented:" in body:
            continue
        stems = SPEC_LINK_RE.findall(body)
        if not stems:
            continue
        spec_path = root / cfg["docs_dir"] / "specs" / f"{stems[-1]}.md"
        if spec_path.exists() and 'status: "approved"' in spec_path.read_text(encoding="utf-8"):
            candidates.append((order.get(t.get("priority"), 9), t, stems[-1]))
    candidates.sort(key=lambda x: (x[0], x[1]["id"]))
    return [(t, stem) for _, t, stem in candidates]


def find_act_ticket(root: Path, cfg: dict) -> tuple[dict, str] | None:
    found = find_act_tickets(root, cfg)
    return found[0] if found else None


def worktree_path(root: Path, ticket_id: str) -> Path:
    """Isolated checkout per ticket so parallel agents never collide."""
    return Path.home() / ".cache" / "repo-scan" / "worktrees" / f"{root.name}-{ticket_id}"


def act_problem(ticket_id: str, spec_stem: str) -> str:
    """Stable key for checkpoints/decisions across pauses and resumes."""
    return f"Implement approved spec [[{spec_stem}]] for {ticket_id}"


def record_act(root: Path, cfg: dict, ticket_id: str, spec_stem: str, result: dict):
    changelog = root / cfg["docs_dir"] / "changelog"
    changelog.mkdir(parents=True, exist_ok=True)
    path = changelog / f"{now_date()}-act.md"
    if not path.exists():
        path.write_text(f"# RADAR act runs — {now_date()}\n", encoding="utf-8")
    kind = {"committed": "success", "stopped": "warning"}.get(result["outcome"], "danger")
    entry = [
        "",
        f"## {now_iso()} — {ticket_id} · [[{spec_stem}]]",
        "",
        f"> [!{kind}] outcome: **{result['outcome']}**",
        f"> - branch: {result.get('branch', '—')}",
        f"> - commit: {result.get('commit', '—')}",
        f"> - tests: {result.get('tests', '—')}",
        f"> - diff: {result.get('diff_stat', '—')}",
        "",
    ]
    with path.open("a", encoding="utf-8") as f:
        f.write("\n".join(entry))
    ok(f"recorded to {path.relative_to(root)}")


def cmd_act(root: Path, cfg: dict, ticket_id: str | None = None,
            approve: list[str] | None = None, worktree: bool = False) -> int:
    """Returns 0 committed, 1 error, 2 stopped (gate pause/reject or test failure).

    With worktree=True the implementation happens in an isolated checkout
    under ~/.cache/repo-scan/worktrees/, so multiple acts can run in
    parallel without touching this working tree. Vault state (gates,
    checkpoints, tickets, changelog) always lives in `root`.
    """
    from ..hub.state import load_checkpoint, save_checkpoint
    from ..tickets import append_ticket_note, load_tickets
    from .pipeline import _finish_loop, _gate_paused

    header("radar act")
    if not cfg.get("act_enabled"):
        warn('radar act requires "act_enabled": true in .repo-scan.json')
        return 1

    # -- target selection ---------------------------------------------------
    if ticket_id:
        found = None
        for t in load_tickets(root, cfg):
            if t["id"] == ticket_id:
                body = Path(t["path"]).read_text(encoding="utf-8", errors="ignore")
                stems = SPEC_LINK_RE.findall(body)
                if stems:
                    found = (t, stems[-1])
        if not found:
            err(f"{ticket_id}: not found or has no spec wikilink")
            return 1
        ticket, spec_stem = found
    else:
        picked = find_act_ticket(root, cfg)
        if not picked:
            info("nothing to act on — need an in-progress ticket with an approved spec")
            return 1
        ticket, spec_stem = picked

    spec_path = root / cfg["docs_dir"] / "specs" / f"{spec_stem}.md"
    spec_text = spec_path.read_text(encoding="utf-8")
    problem = act_problem(ticket["id"], spec_stem)
    branch = f"radar/{ticket['id']}"
    approved = set(approve or [])
    ckpt = load_checkpoint(root, cfg, problem)
    result = {"outcome": "stopped", "branch": branch}
    info(f"{ticket['id']}: {ticket['title'][:80]}")

    # -- preconditions --------------------------------------------------------
    if not worktree and not ckpt.get("branch"):
        if _tree_dirty(root, cfg["docs_dir"]):
            err("working tree is dirty (outside the vault) — commit or stash before radar act")
            return 1

    # -- Gate: pre_implement ---------------------------------------------------
    from ..hub.progress import progress
    from .gates import gate_mode
    from .llm import role_model
    progress(root, cfg, problem, "[1/5] Gate (pre-implement)",
             "waiting on human" if gate_mode("pre_implement", cfg) == "prompt" else "")
    payload = {
        "problem": problem,
        "summary": f"implement [[{spec_stem}]] on branch {branch} for {ticket['id']}",
        "detail": {"doc": f"specs/{spec_path.name}"},
    }
    if not gate("pre_implement", payload, cfg, root, approved):
        if not _gate_paused(root, cfg, "pre_implement", problem):
            _finish_loop(root, cfg, problem)
            record_act(root, cfg, ticket["id"], spec_stem, result)
        return 2

    try:
        # -- branch / worktree --------------------------------------------------
        progress(root, cfg, problem, "[2/5] Branch",
                 f"isolated worktree on {branch}" if worktree else branch)
        work = root  # where the agent edits, tests run, and the commit lands
        if worktree:
            wt = worktree_path(root, ticket["id"])
            if not (wt / ".git").exists():
                wt.parent.mkdir(parents=True, exist_ok=True)
                branch_exists = _git(root, "rev-parse", "--verify", "--quiet",
                                     branch).returncode == 0
                args = (["worktree", "add", str(wt), branch] if branch_exists
                        else ["worktree", "add", "-b", branch, str(wt)])
                r = _git(root, *args)
                if r.returncode != 0:
                    err(f"cannot create worktree: {r.stderr.strip()[:200]}")
                    return 1
                ok(f"worktree {wt.name} on {branch}")
            else:
                info(f"resuming in worktree {wt.name}")
            work = wt
            if not ckpt.get("branch"):
                ckpt["branch"] = branch
                ckpt["base"] = _current_branch(root)
                ckpt["worktree"] = str(wt)
                save_checkpoint(root, cfg, problem, ckpt)
        elif ckpt.get("branch"):
            if _current_branch(root) != branch:
                _git(root, "checkout", branch)
            info(f"resuming on {branch}")
        else:
            base = _current_branch(root)
            r = _git(root, "checkout", "-b", branch)
            if r.returncode != 0:
                err(f"cannot create {branch}: {r.stderr.strip()[:200]}")
                return 1
            ckpt["branch"] = branch
            ckpt["base"] = base
            save_checkpoint(root, cfg, problem, ckpt)
            ok(f"{base} -> {branch}")

        # -- implement -----------------------------------------------------------
        act_model = role_model(cfg, "act") or "default model"
        progress(root, cfg, problem, "[3/5] Implement",
                 f"{act_model} editing per spec (can take many minutes)")
        if ckpt.get("implemented"):
            info("resumed from checkpoint")
        else:
            summary = complete(
                ACT_PROMPT.format(spec=spec_text[:14000], docs_dir=cfg["docs_dir"]),
                cfg, timeout=int(cfg.get("act_timeout", ACT_TIMEOUT)), cwd=str(work),
                role="act", root=root)
            ckpt["implemented"] = True
            ckpt["agent_summary"] = summary[:1000]
            save_checkpoint(root, cfg, problem, ckpt)
            ok("agent finished")

        # -- test (hard gate, bounded fix rounds) -----------------------------------
        progress(root, cfg, problem, "[4/5] Test",
                 cfg.get("test_cmd") or default_test_cmd(work) or "no suite detected")
        rounds = int(cfg.get("act_fix_rounds", 2))
        passed, output = run_tests(work, cfg)
        attempt = int(ckpt.get("fix_attempts", 0))
        while not passed and attempt < rounds:
            attempt += 1
            progress(root, cfg, problem, "[4/5] Test",
                     f"failing — fix round {attempt}/{rounds} ({act_model})", banner=False)
            complete(FIX_PROMPT.format(
                test_cmd=cfg.get("test_cmd") or default_test_cmd(work),
                output=output), cfg,
                timeout=int(cfg.get("act_timeout", ACT_TIMEOUT)), cwd=str(work),
                role="act_fix", root=root)
            ckpt["fix_attempts"] = attempt
            save_checkpoint(root, cfg, problem, ckpt)
            passed, output = run_tests(work, cfg)
        result["tests"] = "passed" if passed else "failed"
        if not passed:
            err(f"tests still failing after {attempt} fix round(s) — "
                f"branch {branch} left for human review")
            result["outcome"] = "tests-failed"
            _finish_loop(root, cfg, problem)
            record_act(root, cfg, ticket["id"], spec_stem, result)
            where = f" (worktree: {work})" if worktree else ""
            append_ticket_note(root, cfg, ticket["id"],
                               f"act run failed tests on {branch} — needs a human{where}")
            return 2
        ok("tests passing")

        # -- Gate: post_implement -----------------------------------------------------
        progress(root, cfg, problem, "[5/5] Gate (post-implement)",
                 "waiting on human" if gate_mode("post_implement", cfg) == "prompt" else "")
        diff_stat = _git(work, "diff", "--stat", "HEAD", "--",
                         f":(exclude){cfg['docs_dir']}").stdout.strip()
        stat_tail = diff_stat.splitlines()[-1].strip() if diff_stat else "no changes"
        result["diff_stat"] = stat_tail
        payload = {
            "problem": problem,
            "summary": f"tests passed; {stat_tail} on {branch} — commit?",
            "detail": {
                "findings": diff_stat.splitlines()[:12],
                "doc": f"specs/{spec_path.name}",
            },
        }
        if not gate("post_implement", payload, cfg, root, approved):
            if not _gate_paused(root, cfg, "post_implement", problem):
                result["outcome"] = "rejected"
                _finish_loop(root, cfg, problem)
                record_act(root, cfg, ticket["id"], spec_stem, result)
                append_ticket_note(root, cfg, ticket["id"],
                                   f"act run rejected at post_implement — branch {branch} kept")
            return 2

        # vault churn stays out of the implementation commit
        _git(work, "add", "-A", "--", f":(exclude){cfg['docs_dir']}")
        msg = f"radar: implement {ticket['id']} — {ticket['title'][:60]}\n\nSpec: {spec_stem}"
        r = _git(work, "commit", "-m", msg, timeout=120)
        if r.returncode != 0:
            err(f"commit failed: {r.stderr.strip()[:200]}")
            return 1
        commit = _git(work, "rev-parse", "--short", "HEAD").stdout.strip()
        result["outcome"] = "committed"
        result["commit"] = commit
        ok(f"committed {commit} on {branch}")
        if worktree:  # branch keeps the commit; the checkout is disposable
            _git(root, "worktree", "remove", "--force", str(work))

        append_ticket_note(root, cfg, ticket["id"],
                           f"implemented: {commit} on {branch} (spec [[{spec_stem}]]) "
                           f"— review and merge, then rescan to confirm metrics")
        _finish_loop(root, cfg, problem)
        record_act(root, cfg, ticket["id"], spec_stem, result)
        info(f"review: git diff {ckpt.get('base', 'main')}...{branch}")
        return 0

    except LLMError as e:
        err(f"act needs an LLM backend: {e}")
        result["outcome"] = f"failed ({e})"
        record_act(root, cfg, ticket["id"], spec_stem, result)
        return 1
