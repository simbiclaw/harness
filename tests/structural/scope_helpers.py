"""
Shared helpers for structural tests that adapt behaviour based on
harness-scope.json.

All enforcement mechanisms import these helpers so the beachhead is declared
once (in harness-scope.json) and consumed everywhere, rather than each test
maintaining its own path lists.
"""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCOPE_FILE = REPO_ROOT / ".claude" / "harness-scope.json"


def _load_scope() -> dict:
    """Read and parse harness-scope.json. Returns greenfield default if missing."""
    if not SCOPE_FILE.exists():
        return {
            "version": 1,
            "mode": "greenfield",
            "managed_paths": ["src/**"],
            "legacy_paths": [],
            "baselines": {},
        }
    return json.loads(SCOPE_FILE.read_text(encoding="utf-8"))


def is_managed_path(path: str | Path, scope: dict | None = None) -> bool:
    """Return True if `path` matches any managed_path glob.

    In greenfield mode, this is effectively all src/** paths.
    In brownfield mode, only paths matching managed_paths globs are managed.
    """
    if scope is None:
        scope = _load_scope()

    path_str = str(path)
    for pat in scope.get("managed_paths", ["src/**"]):
        if fnmatch.fnmatch(path_str, pat):
            return True
    return False


def is_legacy_path(path: str | Path, scope: dict | None = None) -> bool:
    """Return True if `path` matches any legacy_path glob."""
    if scope is None:
        scope = _load_scope()

    path_str = str(path)
    for pat in scope.get("legacy_paths", []):
        if fnmatch.fnmatch(path_str, pat):
            return True
    return False


def check_baseline(
    test_name: str, current_violations: set[str], scope: dict | None = None
) -> tuple[set[str], set[str]]:
    """Diff current violations against the committed baseline.

    Returns (new_violations, kept_violations).  new_violations are violations
    not in the baseline — these fail the test.  kept_violations are the
    intersection — known pre-existing issues, allowed for now.

    If no baseline file is configured for `test_name`, all current violations
    are treated as new.
    """
    if scope is None:
        scope = _load_scope()

    baselines = scope.get("baselines", {})
    baseline_path_str = baselines.get(test_name)

    if baseline_path_str is None:
        return (current_violations, set())

    baseline_file = Path(baseline_path_str)
    if not baseline_file.exists():
        return (current_violations, set())

    try:
        known_list = json.loads(baseline_file.read_text(encoding="utf-8"))
        known = set(known_list)
    except (json.JSONDecodeError, ValueError):
        return (current_violations, set())

    new = current_violations - known
    kept = current_violations & known
    return (new, kept)
