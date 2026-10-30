"""
Structural test: src/ layered architecture for TypeScript.

Layer order: types -> config -> repo -> service -> runtime -> ui.
Imports may flow only upward in the layer graph.

This test does NOT execute application code; it parses imports with regex.
For deeper graph analysis (cycles, dead code), see the dependency-cruiser
step in .github/workflows/harness.yml.
"""
from __future__ import annotations

import re
from pathlib import Path

LAYERS = ["types", "config", "repo", "service", "runtime", "ui"]
LAYER_RANK = {name: i for i, name in enumerate(LAYERS)}

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = REPO_ROOT / "src"

# Match TypeScript / ES6 imports. Covers:
#   import x from "..."
#   import { x } from "..."
#   import * as x from "..."
#   import "..."
#   export ... from "..."
#   const x = require("...")  (CommonJS, just in case)
IMPORT_RE = re.compile(
    r"""(?:
        ^\s*import\s+(?:[^'"\n]+?\s+from\s+)?['"]([^'"\n]+)['"]
      | ^\s*export\s+(?:[^'"\n]+?\s+from\s+)?['"]([^'"\n]+)['"]
      | \brequire\s*\(\s*['"]([^'"\n]+)['"]
    )""",
    re.VERBOSE | re.MULTILINE,
)

# Treat src/<layer>/... and tilde aliases (~/<layer>/...) as layer references.
LAYER_PATH_RE = re.compile(
    r"^(?:[~@]/)?(?:src/|\.\./|\./)*(types|config|repo|service|runtime|ui)(?:/|$)"
)


def file_layer(path: Path) -> str | None:
    try:
        rel = path.relative_to(SRC)
    except ValueError:
        return None
    parts = rel.parts
    if parts and parts[0] in LAYER_RANK:
        return parts[0]
    return None


def imports_in(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    out = []
    for m in IMPORT_RE.finditer(text):
        spec = m.group(1) or m.group(2) or m.group(3)
        if not spec:
            continue
        # Compute approximate line number
        line = text.count("\n", 0, m.start()) + 1
        out.append((line, spec))
    return out


def resolve_layer(import_spec: str, source_file: Path) -> str | None:
    """Map an import string to a layer name, or None if it's external."""
    # External package (no dot, no slash leading)
    if not import_spec.startswith((".", "/", "~", "@/", "src/")):
        return None
    # Relative imports: resolve against source file's directory
    if import_spec.startswith("."):
        target = (source_file.parent / import_spec).resolve()
        try:
            rel = target.relative_to(SRC)
            parts = rel.parts
            if parts and parts[0] in LAYER_RANK:
                return parts[0]
        except ValueError:
            return None
        return None
    # src/, ~/, @/ aliases
    m = LAYER_PATH_RE.match(import_spec)
    if m:
        return m.group(1)
    return None


def test_layer_imports_flow_upward():
    if not SRC.exists():
        return  # Bootstrap: src/ may not exist yet.

    from tests.structural.scope_helpers import (
        is_managed_path, is_legacy_path, check_baseline, _load_scope,
    )

    scope = _load_scope()
    mode = scope.get("mode", "greenfield")

    managed_violations: list[str] = []
    legacy_violations: list[str] = []
    extensions = (".ts", ".tsx", ".js", ".jsx", ".mts", ".cts")

    for src_file in SRC.rglob("*"):
        if src_file.suffix not in extensions or not src_file.is_file():
            continue
        src_layer = file_layer(src_file)
        if src_layer is None:
            continue

        rel = str(src_file.relative_to(REPO_ROOT))

        # In brownfield mode, partition files into managed and legacy.
        # Managed: all violations are errors (beachhead must be clean).
        # Legacy: violations checked against baseline (only new ones fail).
        # Greenfield: all paths are managed implicitly.
        if mode == "brownfield":
            if not is_managed_path(rel) and not is_legacy_path(rel):
                continue
            target_list = (
                managed_violations if is_managed_path(rel) else legacy_violations
            )
        else:
            # Greenfield: every file is managed.
            target_list = managed_violations

        for lineno, spec in imports_in(src_file):
            tgt_layer = resolve_layer(spec, src_file)
            if tgt_layer is None:
                continue
            if LAYER_RANK[tgt_layer] > LAYER_RANK[src_layer]:
                target_list.append(
                    f"{rel}:{lineno}: "
                    f"layer '{src_layer}' imports from higher layer "
                    f"'{tgt_layer}' ({spec}). Imports must flow downward "
                    f"toward '{LAYERS[0]}'. Move the imported symbol to "
                    f"a layer <= {src_layer}, or invert the dependency."
                )

    failures: list[str] = []

    # Managed violations always fail — the beachhead must be clean.
    if managed_violations:
        failures.append(
            "Managed-path layer violations:\n  "
            + "\n  ".join(sorted(managed_violations))
        )

    # Legacy violations are filtered through the baseline.
    if legacy_violations:
        new, kept = check_baseline(
            "test_layering", set(legacy_violations), scope
        )
        if new:
            failures.append(
                "New legacy layer violations (not in baseline):\n  "
                + "\n  ".join(sorted(new))
                + f"\n\n{len(kept)} baselined violation(s) remain."
            )

    assert not failures, "\n\n".join(failures)
