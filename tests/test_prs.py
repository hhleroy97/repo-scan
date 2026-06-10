"""PR visibility + merge from the hub, with a fake gh CLI on PATH."""

import json
import os
from pathlib import Path

import pytest

from repo_scan.config import load_config
from repo_scan.hub import prs
from repo_scan.hub.prs import (checks_state, list_open_prs, merge_pr,
                               update_pr_branch)

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
    prs.invalidate_cache()
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


def test_merge_pr_failure_propagates_message(tmp_repo, tmp_path, monkeypatch):
    bindir = tmp_path / "bin2"
    bindir.mkdir()
    gh = bindir / "gh"
    gh.write_text("#!/bin/sh\necho 'GraphQL: not mergeable' >&2\nexit 1\n")
    gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    prs.invalidate_cache()
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
    prs.invalidate_cache()
    done, msg = update_pr_branch(tmp_repo, 5)
    assert done and "checks re-running" in msg
    argv = argv_file.read_text()
    assert "pulls/5/update-branch" in argv


def test_no_gh_degrades_quietly(tmp_repo, monkeypatch, tmp_path):
    empty = tmp_path / "empty-path"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    prs.invalidate_cache()
    assert list_open_prs(tmp_repo) == []
    done, msg = merge_pr(tmp_repo, load_config(tmp_repo), 1)
    assert not done and "gh CLI" in msg


def test_build_state_includes_prs(tmp_repo, fake_gh):
    from repo_scan.hub.server import build_state
    state = build_state(tmp_repo, load_config(tmp_repo))
    assert len(state["prs"]) == 3
    assert state["prs"][0]["checks"] in ("passing", "failing", "pending", "none")
