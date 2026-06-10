"""PR visibility + merge from the hub, with a fake gh CLI on PATH."""

import json
import os
from pathlib import Path

import pytest

from repo_scan.config import load_config
from repo_scan.hub import prs
from repo_scan.hub.prs import (_probe_merge_conflicts, checks_state,
                               invalidate_cache, list_open_prs, merge_pr,
                               remediate_pr, update_pr_branch)

PR_LIST = [
    {"number": 7, "title": "radar: implement tkt-0002", "headRefName": "radar/tkt-0002",
     "url": "https://github.com/x/y/pull/7", "mergeable": "MERGEABLE", "isDraft": False,
     "statusCheckRollup": [{"conclusion": "FAILURE"}]},
    {"number": 9, "title": "radar: implement tkt-0004", "headRefName": "radar/tkt-0004",
     "url": "https://github.com/x/y/pull/9", "mergeable": "MERGEABLE", "isDraft": False,
     "statusCheckRollup": [{"conclusion": "SUCCESS"}, {"state": "SUCCESS"}]},
    {"number": 3, "title": "human PR", "headRefName": "fix/typo",
     "url": "https://github.com/x/y/pull/3", "mergeable": "CONFLICTING", "isDraft": False,
     "statusCheckRollup": []},
]


@pytest.fixture
def fake_gh(tmp_path: Path, monkeypatch):
    """gh stub: records argv, answers `pr list` with PR_LIST."""
    argv_file = tmp_path / "gh-argv.txt"
    bindir = tmp_path / "bin"
    bindir.mkdir()
    gh = bindir / "gh"
    gh.write_text(f"""#!/bin/sh
echo "$@" >> {argv_file}
case "$2" in
  list) cat {tmp_path / "prlist.json"} ;;
  *) echo done ;;
esac
""")
    gh.chmod(0o755)
    (tmp_path / "prlist.json").write_text(json.dumps(PR_LIST))
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    invalidate_cache()
    return argv_file


def test_checks_state_collapse():
    assert checks_state([]) == "none"
    assert checks_state([{"conclusion": "SUCCESS"}, {"state": "SUCCESS"}]) == "passing"
    assert checks_state([{"conclusion": "SUCCESS"}, {"conclusion": "FAILURE"}]) == "failing"
    assert checks_state([{"status": "IN_PROGRESS"}]) == "pending"
    assert checks_state([{"conclusion": "SKIPPED"}, {"conclusion": "NEUTRAL"}]) == "passing"


def test_list_open_prs_maps_tickets_and_checks(tmp_repo, fake_gh):
    out = list_open_prs(tmp_repo)
    assert [p["number"] for p in out] == [9, 7, 3]  # newest first
    by_num = {p["number"]: p for p in out}
    assert by_num[7]["ticket"] == "tkt-0002" and by_num[7]["checks"] == "failing"
    assert by_num[9]["ticket"] == "tkt-0004" and by_num[9]["checks"] == "passing"
    assert by_num[3]["ticket"] is None and by_num[3]["mergeable"] == "CONFLICTING"


def test_list_open_prs_caches(tmp_repo, fake_gh):
    list_open_prs(tmp_repo)
    list_open_prs(tmp_repo)
    calls = fake_gh.read_text().strip().splitlines()
    assert len(calls) == 1  # second hit served from cache
    list_open_prs(tmp_repo, fresh=True)
    assert len(fake_gh.read_text().strip().splitlines()) == 2


def test_merge_pr_squash_deletes_and_notes_ticket(tmp_repo, fake_gh):
    from repo_scan.tickets import load_tickets, write_ticket
    cfg = load_config(tmp_repo)
    write_ticket(tmp_repo, cfg, {"id": "tkt-0002", "title": "T", "why": "w",
                                 "fingerprint": "refactor:x", "criteria": [],
                                 "status": "in-progress"})
    list_open_prs(tmp_repo)  # warm cache: maps #7 -> tkt-0002

    done, msg = merge_pr(tmp_repo, cfg, 7)
    assert done and "#7" in msg
    argv = fake_gh.read_text()
    assert "pr merge 7 --squash --delete-branch" in argv

    t = next(t for t in load_tickets(tmp_repo, cfg) if t["id"] == "tkt-0002")
    assert t["status"] == "done"
    assert "PR #7 merged" in Path(t["path"]).read_text()
    from repo_scan.hub.state import load_events
    assert any("PR #7 merged" in e["text"] for e in load_events(tmp_repo, cfg))


def test_merge_pr_syncs_local_checkout(tmp_repo, tmp_path, fake_gh):
    """After a GitHub-side merge, the hub's checkout fast-forwards so later
    scans/acts run against the merged code."""
    import subprocess

    def run(args, cwd):
        return subprocess.run(args, cwd=cwd, check=True, capture_output=True)

    remote = tmp_path / "origin.git"
    run(["git", "clone", "--bare", "-q", str(tmp_repo), str(remote)], tmp_path)
    run(["git", "remote", "add", "origin", str(remote)], tmp_repo)

    # someone (GitHub's squash-merge) advances origin/main past local
    clone = tmp_path / "clone"
    run(["git", "clone", "-q", str(remote), str(clone)], tmp_path)
    run(["git", "config", "user.email", "t@t.com"], clone)
    run(["git", "config", "user.name", "T"], clone)
    (clone / "merged.py").write_text("MERGED = True\n")
    run(["git", "add", "."], clone)
    run(["git", "commit", "-qm", "squash-merge of PR"], clone)
    run(["git", "push", "-q", "origin", "main"], clone)
    assert not (tmp_repo / "merged.py").exists()

    cfg = load_config(tmp_repo)
    done, msg = merge_pr(tmp_repo, cfg, 9)
    assert done and "synced with origin" in msg
    assert (tmp_repo / "merged.py").exists()  # local main fast-forwarded


def test_merge_pr_sync_never_destroys_local_work(tmp_repo, fake_gh):
    """No origin configured: merge still succeeds, sync degrades to a note."""
    cfg = load_config(tmp_repo)
    done, msg = merge_pr(tmp_repo, cfg, 9)
    assert done and ("fetch failed" in msg or "sync skipped" in msg)


def test_merge_pr_failure_propagates_message(tmp_repo, tmp_path, monkeypatch):
    bindir = tmp_path / "bin2"
    bindir.mkdir()
    gh = bindir / "gh"
    gh.write_text("#!/bin/sh\necho 'GraphQL: not mergeable' >&2\nexit 1\n")
    gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    invalidate_cache()
    done, msg = merge_pr(tmp_repo, load_config(tmp_repo), 7)
    assert not done and "not mergeable" in msg


def test_update_pr_branch(tmp_repo, fake_gh):
    done, msg = update_pr_branch(tmp_repo, 7)
    assert done and "checks re-running" in msg
    assert "pr update-branch 7" in fake_gh.read_text()


def test_update_pr_branch_falls_back_to_rest_on_old_gh(tmp_repo, tmp_path, monkeypatch):
    """gh < 2.56 lacks `pr update-branch`; the REST endpoint does the same."""
    argv_file = tmp_path / "old-gh-argv.txt"
    bindir = tmp_path / "bin-old"
    bindir.mkdir()
    gh = bindir / "gh"
    gh.write_text(f"""#!/bin/sh
echo "$@" >> {argv_file}
case "$1 $2" in
  "pr update-branch") echo 'unknown command "update-branch" for "gh pr"' >&2; exit 1 ;;
  "api -X") echo '{{"message":"Updating pull request branch."}}' ;;
esac
""")
    gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    invalidate_cache()
    done, msg = update_pr_branch(tmp_repo, 5)
    assert done and "checks re-running" in msg
    argv = argv_file.read_text()
    assert "pulls/5/update-branch" in argv


def test_update_branch_fallback_when_error_on_stdout(tmp_repo, tmp_path, monkeypatch):
    """Ubuntu gh 2.4 prints 'unknown command' on stdout, not stderr."""
    argv_file = tmp_path / "gh24-argv.txt"
    bindir = tmp_path / "bin-gh24"
    bindir.mkdir()
    gh = bindir / "gh"
    gh.write_text(f"""#!/bin/sh
echo "$@" >> {argv_file}
case "$1 $2" in
  "pr update-branch") echo 'unknown command "update-branch" for "gh pr"'; exit 1 ;;
  "api -X") echo '{{"message":"Updating pull request branch."}}' ;;
esac
""")
    gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    invalidate_cache()
    done, msg = update_pr_branch(tmp_repo, 5)
    assert done and "checks re-running" in msg
    assert "pulls/5/update-branch" in argv_file.read_text()


def test_no_gh_degrades_quietly(tmp_repo, monkeypatch, tmp_path):
    empty = tmp_path / "empty-path"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    invalidate_cache()
    assert list_open_prs(tmp_repo) == []
    done, msg = merge_pr(tmp_repo, load_config(tmp_repo), 1)
    assert not done and "gh CLI" in msg


def test_build_state_includes_prs(tmp_repo, fake_gh):
    from repo_scan.hub.server import build_state
    state = build_state(tmp_repo, load_config(tmp_repo))
    assert len(state["prs"]) == 3
    assert state["prs"][0]["checks"] in ("passing", "failing", "pending", "none")


def test_probe_merge_conflicts_detects_files(tmp_repo):
    """Local merge probe finds the file that actually conflicts."""
    import subprocess

    def run(args, cwd=tmp_repo):
        subprocess.run(args, cwd=cwd, check=True, capture_output=True)

    run(["git", "checkout", "-b", "feature/pr-probe"])
    (tmp_repo / "clash.py").write_text("ours = 1\n")
    run(["git", "add", "clash.py"])
    run(["git", "commit", "-qm", "feature side"])
    run(["git", "checkout", "main"])
    (tmp_repo / "clash.py").write_text("theirs = 2\n")
    run(["git", "add", "clash.py"])
    run(["git", "commit", "-qm", "main side"])
    remote = tmp_repo.parent / "origin.git"
    run(["git", "clone", "--bare", "-q", str(tmp_repo), str(remote)],
        cwd=tmp_repo.parent)
    run(["git", "remote", "add", "origin", str(remote)])
    run(["git", "push", "-q", "origin", "main", "feature/pr-probe"])

    probe = _probe_merge_conflicts(tmp_repo, "feature/pr-probe", "main")
    assert "clash.py" in probe["files"]
    assert probe["excerpt"]
    assert not probe["merged_clean"]


def test_remediate_pr_captures_ci_log(tmp_repo, tmp_path, monkeypatch):
    """Failing checks -> update branch + CI log diagnosis persisted on the PR."""
    argv_file = tmp_path / "remediate-gh.txt"
    bindir = tmp_path / "bin-rem"
    bindir.mkdir()
    pr_view = {
        "number": 7, "title": "radar: implement tkt-0002",
        "headRefName": "radar/tkt-0002", "baseRefName": "main",
        "url": "https://github.com/x/y/pull/7", "mergeable": "MERGEABLE",
        "isDraft": False,
        "statusCheckRollup": [{"conclusion": "FAILURE"}],
    }
    run_log = [{"databaseId": 99, "conclusion": "failure", "name": "pytest",
                "workflowName": "CI", "url": "https://github.com/x/y/actions/runs/99"}]
    gh = bindir / "gh"
    gh.write_text(f"""#!/bin/sh
echo "$@" >> {argv_file}
case "$1" in
  pr)
    case "$2" in
      list) cat {tmp_path / "prlist.json"} ;;
      view) echo '{json.dumps(pr_view)}' ;;
      update-branch) echo done ;;
    esac ;;
  run)
    case "$2" in
      list) echo '{json.dumps(run_log)}' ;;
      view) echo "FAILED tests/test_foo.py::test_bar" ;;
    esac ;;
esac
""")
    gh.chmod(0o755)
    (tmp_path / "prlist.json").write_text(json.dumps(PR_LIST))
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    invalidate_cache()

    cfg = load_config(tmp_repo)
    cfg["act_enabled"] = False  # diagnosis only — no background agent
    result = remediate_pr(tmp_repo, cfg, 7)
    assert not result["ok"]  # still failing — not merge-ready
    assert result["diagnosis"]["kind"] == "tests"
    assert result["diagnosis"]["status_note"]
    assert "FAILED" in result["diagnosis"]["log_tail"]
    assert "pr update-branch 7" in argv_file.read_text()

    diag_path = tmp_repo / "docs" / ".radar" / "pr-diagnosis" / "7.json"
    assert diag_path.exists()
    saved = json.loads(diag_path.read_text())
    assert saved["kind"] == "tests"
