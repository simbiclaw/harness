"""
Structural test: every direct dependency in package.json has a Decision Log
entry referencing it AND a dep-vet record under .claude/decisions/.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DECISIONS_DIR = REPO_ROOT / ".claude" / "decisions"
PLANS_DIRS = [REPO_ROOT / "docs" / "plans" / d for d in ("active", "completed")]
PACKAGE_JSON = REPO_ROOT / "package.json"


def collected_deps() -> list[str]:
    deps: set[str] = set()
    if PACKAGE_JSON.exists():
        data = json.loads(PACKAGE_JSON.read_text())
        for k in ("dependencies", "devDependencies", "peerDependencies",
                  "optionalDependencies"):
            deps.update((data.get(k) or {}).keys())
    return sorted(deps)


def all_plan_text() -> str:
    chunks = []
    for d in PLANS_DIRS:
        if not d.exists():
            continue
        for p in d.glob("*.md"):
            chunks.append(p.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def vet_filename(dep: str) -> str:
    """Sanitize scoped names: @types/node -> dep-vet-@types-node.md"""
    sanitized = dep.replace("/", "-")
    return f"dep-vet-{sanitized}.md"


def amnesty_packages() -> set[str]:
    """Return packages listed in dep-amnesty baselines as pre-existing."""
    from tests.structural.scope_helpers import _load_scope

    scope = _load_scope()
    if scope.get("mode") != "brownfield":
        return set()

    amnesty_files = [
        f for f in DECISIONS_DIR.glob("dep-baseline-*.md")
        if f.name.startswith("dep-baseline-")
    ]
    packages: set[str] = set()
    for f in amnesty_files:
        text = f.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("- ") and not stripped.startswith("- #"):
                pkg = stripped[2:].split()[0]
                packages.add(pkg)
    return packages


def test_each_dep_has_decision_and_vet():
    failures: list[str] = []
    plan_text = all_plan_text()
    amnesty = amnesty_packages()
    for dep in collected_deps():
        if dep in amnesty:
            continue
        vet = DECISIONS_DIR / vet_filename(dep)
        if not vet.exists():
            failures.append(
                f"dependency '{dep}' has no dep-vet record at "
                f".claude/decisions/{vet_filename(dep)}. Run the dep-vetter "
                f"skill on '{dep}'."
            )
        if dep not in plan_text:
            failures.append(
                f"dependency '{dep}' is not mentioned in any active or "
                f"completed ExecPlan Decision Log. Add a Decision Log entry "
                f"with rationale to the plan that introduced it."
            )
    assert not failures, "\n  ".join([""] + failures)
