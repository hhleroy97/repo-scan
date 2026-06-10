"""Test-presence mapping: which source files have any test coverage signal.

Heuristic, not instrumentation: a source file counts as "tested" when a
test-looking file references its stem (test_foo.py, foo_test.py, foo.test.tsx,
foo.spec.ts, or anything in a tests//test//__tests__/ directory whose name
contains the stem). High churn x high complexity x *zero tests* is the
strongest refactor trigger the scan can emit.
"""

import re
from pathlib import Path

_TEST_DIR_NAMES = {"tests", "test", "__tests__"}
_TEST_FILE_RE = re.compile(r"(^test_|_test$|\.test$|\.spec$)", re.I)


def _tokens(stem: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", stem.lower()) if t}


def is_test_file(rel_path: str) -> bool:
    p = Path(rel_path)
    if any(part in _TEST_DIR_NAMES for part in p.parts[:-1]):
        return True
    return bool(_TEST_FILE_RE.search(p.name.rsplit(".", 1)[0]))


def find_tested_files(files: list[str]) -> set[str]:
    """Subset of `files` that have a matching test file (test files themselves
    are excluded — they don't need tests)."""
    test_tokens: set[str] = set()
    sources = []
    for rel in files:
        if is_test_file(rel):
            test_tokens |= _tokens(Path(rel).stem)
        else:
            sources.append(rel)

    tested = set()
    for rel in sources:
        stem_tokens = _tokens(Path(rel).stem) - {"index", "main", "init"}
        if not stem_tokens:
            # index.tsx / main.py etc. — match on parent directory name instead
            stem_tokens = _tokens(Path(rel).parent.name)
        if stem_tokens and stem_tokens <= test_tokens:
            tested.add(rel)
    return tested
