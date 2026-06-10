"""Tests for auto-populating linked_files from ticket fingerprint."""

from repo_scan.tickets.io import _linked_files_from_fingerprint


def test_refactor_fingerprint():
    result = _linked_files_from_fingerprint("refactor:repo_scan/writers.py")
    assert result == ["repo_scan/writers.py"]


def test_seam_fingerprint():
    result = _linked_files_from_fingerprint("seam:repo_scan/a.py+repo_scan/b.py")
    assert result == ["repo_scan/a.py", "repo_scan/b.py"]


def test_silo_fingerprint():
    result = _linked_files_from_fingerprint("silo:repo_scan/config.py")
    assert result == ["repo_scan/config.py"]


def test_feature_fingerprint_no_paths():
    result = _linked_files_from_fingerprint("feature:add-something-cool")
    assert result == []


def test_empty_fingerprint():
    assert _linked_files_from_fingerprint("") == []
    assert _linked_files_from_fingerprint("nocolon") == []


def test_size_fingerprint():
    result = _linked_files_from_fingerprint("size:repo_scan/hub/ui.py")
    assert result == ["repo_scan/hub/ui.py"]
