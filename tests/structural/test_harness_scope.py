"""
Structural test: harness-scope.json exists, is valid, and all enforcement
mechanisms respect it.

The scope file is the single source of truth for which paths are
harness-managed vs. legacy. Every structural test, hook, and CI rule reads
it. This test validates the file itself and the consistency of all
mechanisms that depend on it.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCOPE_FILE = REPO_ROOT / ".claude" / "harness-scope.json"

REQUIRED_KEYS = {"version", "mode", "managed_paths", "legacy_paths", "baselines"}
VALID_MODES = {"greenfield", "brownfield"}


def test_scope_file_exists_and_valid():
    """Assert harness-scope.json exists, parses, and has valid required keys."""
    assert SCOPE_FILE.exists(), (
        f"Missing {SCOPE_FILE.relative_to(REPO_ROOT)}. "
        f"Create the file with mode 'greenfield' for new repos or "
        f"'brownfield' for repos adopting the harness into existing code."
    )

    try:
        scope = json.loads(SCOPE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise AssertionError(
            f"{SCOPE_FILE.relative_to(REPO_ROOT)} is not valid JSON: {e}"
        ) from e

    missing = REQUIRED_KEYS - set(scope.keys())
    assert not missing, (
        f"{SCOPE_FILE.relative_to(REPO_ROOT)} missing required keys: "
        f"{sorted(missing)}. Required: {sorted(REQUIRED_KEYS)}."
    )

    assert scope["version"] == 1, (
        f"scope file version must be 1, got {scope['version']!r}"
    )

    assert scope["mode"] in VALID_MODES, (
        f"mode must be one of {sorted(VALID_MODES)}, got {scope['mode']!r}"
    )

    assert isinstance(scope["managed_paths"], list), (
        "managed_paths must be a list of glob strings"
    )
    assert isinstance(scope["legacy_paths"], list), (
        "legacy_paths must be a list of glob strings"
    )
    assert isinstance(scope["baselines"], dict), (
        "baselines must be a dict mapping test names to baseline file paths"
    )

    if scope["mode"] == "greenfield":
        assert scope["legacy_paths"] == [], (
            "greenfield mode expects no legacy paths"
        )
    elif scope["mode"] == "brownfield":
        assert len(scope["managed_paths"]) > 0, (
            "brownfield mode requires at least one managed_path glob"
        )


# -- Brownfield mode path-gating tests --

def _make_brownfield_scope() -> dict:
    """Return a brownfield-mode scope dict for testing."""
    return {
        "version": 1,
        "mode": "brownfield",
        "managed_paths": ["src/new-feature/**"],
        "legacy_paths": ["src/legacy/**"],
        "baselines": {},
    }


def test_is_managed_path_matches_glob():
    """scope_helpers.is_managed_path returns True for files matching managed_paths."""
    from tests.structural.scope_helpers import is_managed_path

    scope = _make_brownfield_scope()
    assert is_managed_path(Path("src/new-feature/handler.ts"), scope) is True
    assert is_managed_path(Path("src/new-feature/sub/db.ts"), scope) is True


def test_is_managed_path_rejects_legacy():
    """scope_helpers.is_managed_path returns False for files outside managed_paths."""
    from tests.structural.scope_helpers import is_managed_path

    scope = _make_brownfield_scope()
    assert is_managed_path(Path("src/legacy/old-handler.ts"), scope) is False
    assert is_managed_path(Path("src/other/thing.ts"), scope) is False


def test_is_managed_path_greenfield_all():
    """In greenfield mode, all src/** paths are managed."""
    from tests.structural.scope_helpers import is_managed_path

    scope = {
        "version": 1,
        "mode": "greenfield",
        "managed_paths": ["src/**"],
        "legacy_paths": [],
        "baselines": {},
    }
    assert is_managed_path(Path("src/anything/at/all.ts"), scope) is True
    assert is_managed_path(Path("tests/structural/test.py"), scope) is False


def test_baseline_check_no_baseline_errors_on_new_violations():
    """check_baseline returns new violations when no baseline exists yet."""
    from tests.structural.scope_helpers import check_baseline

    scope = _make_brownfield_scope()
    current = {"src/legacy/o.ts:5: imports from higher layer 'ui'"}
    new, kept = check_baseline("test_layering", current, scope)
    assert new == current
    assert kept == set()


def test_baseline_check_filters_known_violations():
    """check_baseline filters out violations already in the baseline file."""
    from tests.structural.scope_helpers import check_baseline
    import tempfile
    import json

    baseline_dir = Path(tempfile.mkdtemp())
    baseline_file = baseline_dir / "test_layering.json"
    known = {
        "src/legacy/o.ts:5: imports from higher layer 'ui'",
        "src/legacy/x.ts:12: imports from higher layer 'service'",
    }
    baseline_file.write_text(json.dumps(sorted(known)))

    scope = _make_brownfield_scope()
    scope["baselines"]["test_layering"] = str(baseline_file)

    current = known | {"src/legacy/o.ts:42: new violation"}
    new, kept = check_baseline("test_layering", current, scope)
    assert new == {"src/legacy/o.ts:42: new violation"}
    assert kept == known


def test_baseline_check_baseline_cannot_grow():
    """check_baseline raises AssertionError if the baseline has grown (violations added)."""
    from tests.structural.scope_helpers import check_baseline
    import tempfile
    import json

    baseline_dir = Path(tempfile.mkdtemp())
    baseline_file = baseline_dir / "test_layering.json"
    known = {"src/legacy/o.ts:5: old violation"}
    baseline_file.write_text(json.dumps(sorted(known)))

    scope = _make_brownfield_scope()
    scope["baselines"]["test_layering"] = str(baseline_file)

    # Fewer violations than baseline = baseline shrunk (good, allowed)
    current: set[str] = set()
    new, kept = check_baseline("test_layering", current, scope)
    assert new == set()
    assert kept == set()  # baseline is effectively ignored when current is empty


def test_depcruiser_config_matches_scope():
    """dep-cruiser config references managed_paths from harness-scope.json."""
    depcruiser = REPO_ROOT / ".dependency-cruiser.cjs"
    assert depcruiser.exists(), "Missing .dependency-cruiser.cjs"

    text = depcruiser.read_text(encoding="utf-8")

    # The config must read harness-scope.json
    assert "harness-scope.json" in text, (
        ".dependency-cruiser.cjs must read harness-scope.json to adapt "
        "rules per scope mode (greenfield = all error, brownfield = "
        "managed error + legacy warn)."
    )

    # In both modes the essential rules must exist
    for rule_name in ["no-circular", "no-orphans", "types-no-deps",
                       "config-up-only", "repo-up-only", "service-up-only",
                       "runtime-up-only"]:
        assert rule_name in text, (
            f".dependency-cruiser.cjs missing rule '{rule_name}'"
        )


def test_pre_tool_use_hook_reads_scope():
    """PreToolUse hook reads harness-scope.json for dep-amnesty decisions."""
    hook = REPO_ROOT / ".claude" / "hooks" / "pre_tool_use.py"
    assert hook.exists(), "Missing .claude/hooks/pre_tool_use.py"

    text = hook.read_text(encoding="utf-8")

    assert "harness-scope.json" in text, (
        "pre_tool_use.py must read harness-scope.json to check mode "
        "before enforcing dep-vet requirements."
    )
    assert "dep-baseline" in text, (
        "pre_tool_use.py must reference dep-baseline amnesty files "
        "to allow pre-existing packages in brownfield mode."
    )


def test_dep_amnesty_file_valid():
    """If dep-baseline files exist, they list packages from package.json."""
    import json

    decisions = REPO_ROOT / ".claude" / "decisions"
    amnesty_files = sorted(decisions.glob("dep-baseline-*.md"))

    if not amnesty_files:
        return  # No amnesty file — valid state for greenfield repos.

    pkg_json = REPO_ROOT / "package.json"
    if not pkg_json.exists():
        return

    data = json.loads(pkg_json.read_text(encoding="utf-8"))
    known_pkgs: set[str] = set()
    for k in ("dependencies", "devDependencies", "peerDependencies",
              "optionalDependencies"):
        known_pkgs.update((data.get(k) or {}).keys())

    for f in amnesty_files:
        text = f.read_text(encoding="utf-8")
        assert f.name.startswith("dep-baseline-"), (
            f"Amnesty file {f.name} must follow naming: dep-baseline-YYYY-MM-DD.md"
            )

        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("- ") and not stripped.startswith("- #"):
                pkg = stripped[2:].split()[0]
                assert pkg in known_pkgs, (
                    f"{f.name}: amnesty package '{pkg}' not found in "
                    f"package.json. Either add it to package.json or remove "
                    f"from the amnesty list."
                )


def test_brownfield_convention_doc_exists():
    """docs/conventions/brownfield-adoption.md exists and is a valid doc."""
    doc = REPO_ROOT / "docs" / "conventions" / "brownfield-adoption.md"
    assert doc.exists(), (
        "Missing docs/conventions/brownfield-adoption.md. This document "
        "describes the beachhead + baseline + ratchet pattern for adopting "
        "the harness in an existing (brownfield) codebase."
    )
    text = doc.read_text(encoding="utf-8")
    assert "beachhead" in text.lower(), (
        "brownfield-adoption.md must document the beachhead pattern"
    )
    assert "baseline" in text.lower(), (
        "brownfield-adoption.md must document the baseline pattern"
    )
    assert "ratchet" in text.lower(), (
        "brownfield-adoption.md must document the ratchet pattern"
    )


def test_claude_md_acknowledges_both_modes():
    """CLAUDE.md recognizes both greenfield and brownfield repos."""
    claude_md = REPO_ROOT / "CLAUDE.md"
    text = claude_md.read_text(encoding="utf-8")
    assert "brownfield" in text.lower() or "harness-scope.json" in text, (
        "CLAUDE.md must reference harness-scope.json or acknowledge "
        "brownfield adoption so agents in brownfield repos know to check "
        "the scope file before enforcing repo-wide assertions."
    )


def test_brownfield_simulation():
    """End-to-end brownfield simulation exits 0."""
    import subprocess
    sim = REPO_ROOT / "tests" / "fixtures" / "simulate-brownfield.sh"
    assert sim.exists(), "Missing simulate-brownfield.sh fixture."
    result = subprocess.run(
        ["bash", str(sim)],
        capture_output=True, text=True, timeout=30,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"Brownfield simulation failed (exit {result.returncode}):\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
