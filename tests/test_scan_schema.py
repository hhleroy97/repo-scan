"""Validate scan.json against the committed JSON Schema."""

import json
from pathlib import Path

import jsonschema
import pytest

import repo_scan

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "repo_scan" / "schemas" / "scan.schema.json"


@pytest.fixture()
def scan_output(tmp_repo: Path) -> dict:
    repo_scan.scan(tmp_repo, quiet=True)
    scan_json = tmp_repo / "docs" / "scan.json"
    assert scan_json.exists(), "scan.json not written"
    return json.loads(scan_json.read_text(encoding="utf-8"))


def test_schema_version_present(scan_output: dict):
    assert scan_output.get("schema_version") == 1


def test_validates_against_schema(scan_output: dict):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=scan_output, schema=schema)


def test_required_keys_present(scan_output: dict):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    for key in schema.get("required", []):
        assert key in scan_output, f"required key {key!r} missing from scan.json"


def test_check_scan_schema_version_helper():
    from repo_scan.utils import check_scan_schema_version
    assert check_scan_schema_version({"schema_version": 1}) is True
    assert check_scan_schema_version({"schema_version": 99}) is False
    assert check_scan_schema_version({}) is False
