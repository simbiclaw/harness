#!/usr/bin/env bash
# Simulate a brownfield repo with legacy code, pre-existing layer violations,
# and a harness beachhead. Validates that the scoped harness:
#   1. Passes when legacy violations are baselined.
#   2. Fails when new violations appear in the beachhead (managed path).
#   3. Fails when new violations appear in legacy code (not in baseline).
#
# Exit 0 on success (all assertions match expected outcomes).
# Exit 1 on failure (something didn't work as expected).
set -euo pipefail

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

HARNESS="$(cd "$(dirname "$0")" && pwd)/../.."
SIM="$TMPDIR/brownfield-repo"

# -- Phase 1: set up the simulated brownfield repo ----------------------------
echo "--- Phase 1: Scaffolding brownfield repo ---"

mkdir -p "$SIM/src/service/orders"
mkdir -p "$SIM/src/config"
mkdir -p "$SIM/src/types"
mkdir -p "$SIM/src/repo"
mkdir -p "$SIM/src/runtime"
mkdir -p "$SIM/src/ui"
mkdir -p "$SIM/.claude/baselines"
mkdir -p "$SIM/.claude/decisions"
mkdir -p "$SIM/tests/structural"
mkdir -p "$SIM/docs/conventions"
mkdir -p "$SIM/docs/plans/active"
mkdir -p "$SIM/docs/plans/templates"

# Copy harness files needed for structural tests
cp "$HARNESS/tests/structural/test_layering.py" "$SIM/tests/structural/"
cp "$HARNESS/tests/structural/scope_helpers.py" "$SIM/tests/structural/"
cp "$HARNESS/tests/structural/__init__.py" "$SIM/tests/structural/"
cp "$HARNESS/docs/PLANS.md" "$SIM/docs/"

# Write a minimal scope test for the simulation (avoids recursion from
# copying the full test_harness_scope.py which includes
# test_brownfield_simulation).
cat > "$SIM/tests/structural/test_sim_scope.py" << 'PYTEST'
"""Minimal scope tests for the brownfield simulation."""
from __future__ import annotations
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def test_scope_file_valid_in_simulation():
    scope_file = REPO_ROOT / ".claude" / "harness-scope.json"
    assert scope_file.exists()
    scope = json.loads(scope_file.read_text())
    assert scope["mode"] == "brownfield"
    assert len(scope["managed_paths"]) > 0

def test_managed_path_matching():
    from tests.structural.scope_helpers import is_managed_path, is_legacy_path
    scope = json.loads((REPO_ROOT / ".claude" / "harness-scope.json").read_text())
    assert is_managed_path("src/service/orders/create.ts", scope) is True
    assert is_managed_path("src/legacy/old.ts", scope) is False
    assert is_legacy_path("src/config/legacy-config.ts", scope) is True

def test_baseline_filters_known_violations():
    from tests.structural.scope_helpers import check_baseline
    scope = json.loads((REPO_ROOT / ".claude" / "harness-scope.json").read_text())
    # Use a real fingerprint that exists in the baseline
    current = {
        "src/service/legacy-handler.ts:1: layer 'service' imports from higher layer 'ui' (../ui/button). Imports must flow downward toward 'types'. Move the imported symbol to a layer <= service, or invert the dependency."
    }
    new, kept = check_baseline("test_layering", current, scope)
    assert new == set(), f"Expected no new violations, got: {new}"
    assert len(kept) == 1
PYTEST

cat > "$SIM/package.json" << 'JSON'
{"name":"brownfield-sim","private":true,"devDependencies":{}}
JSON

# Brownfield scope: beachhead = src/service/orders/, legacy = known violators
cat > "$SIM/.claude/harness-scope.json" << 'JSON'
{
  "version": 1,
  "mode": "brownfield",
  "managed_paths": ["src/service/orders/**"],
  "legacy_paths": ["src/service/legacy*.ts", "src/config/legacy*.ts"],
  "baselines": {
    "test_layering": ".claude/baselines/test_layering.json"
  }
}
JSON

# -- Phase 2: create layer stubs and legacy violations ------------------------
echo "--- Phase 2: Creating layer stubs and legacy violations ---"

# Lowest-layer stubs
cat > "$SIM/src/types/models.ts" << 'TS'
export type User = { id: string };
TS

cat > "$SIM/src/config/env.ts" << 'TS'
export const env = { port: 3000 };
TS

cat > "$SIM/src/repo/db.ts" << 'TS'
import { env } from "../config/env";
export function connect() { return env.port; }
TS

cat > "$SIM/src/runtime/server.ts" << 'TS'
import { connect } from "../repo/db";
export function startServer() { connect(); return "started"; }
TS

cat > "$SIM/src/ui/button.ts" << 'TS'
export const Button = { label: "click" };
TS

# Legacy violation: service layer importing from ui (higher layer)
cat > "$SIM/src/service/legacy-handler.ts" << 'TS'
import { Button } from "../ui/button";
export function legacyHandler() { return Button.label; }
TS

# Legacy violation: config layer importing from runtime (higher layer)
cat > "$SIM/src/config/legacy-config.ts" << 'TS'
import { startServer } from "../runtime/server";
export const legacySetting = startServer();
TS

# Clean managed file in beachhead — only imports from lower layers
cat > "$SIM/src/service/orders/create.ts" << 'TS'
import type { User } from "../../types/models";
import { env } from "../../config/env";
import { connect } from "../../repo/db";
export function createOrder(user: User) {
  connect();
  return { orderId: "123", userId: user.id, port: env.port };
}
TS

# -- Phase 3: create baseline of known legacy violations ----------------------
echo "--- Phase 3: Creating baseline ---"

cat > "$SIM/.claude/baselines/test_layering.json" << 'JSON'
[
  "src/config/legacy-config.ts:1: layer 'config' imports from higher layer 'runtime' (../runtime/server). Imports must flow downward toward 'types'. Move the imported symbol to a layer <= config, or invert the dependency.",
  "src/service/legacy-handler.ts:1: layer 'service' imports from higher layer 'ui' (../ui/button). Imports must flow downward toward 'types'. Move the imported symbol to a layer <= service, or invert the dependency."
]
JSON

# -- Phase 4: verify structural tests pass with baseline ----------------------
echo "--- Phase 4: Running structural tests (should pass) ---"

cd "$SIM"
if python3 -m pytest tests/structural/test_layering.py -v 2>&1; then
    echo "Phase 4 PASSED: test_layering passes with baseline."
else
    echo "FAIL: Phase 4 — test_layering should pass with baseline."
    exit 1
fi

# -- Phase 5: new violation in beachhead (managed path, should fail) ----------
echo "--- Phase 5: New violation in beachhead (should fail) ---"

# Add a bad import to the managed beachhead file
cat > "$SIM/src/service/orders/create.ts" << 'TS'
import type { User } from "../../types/models";
import { env } from "../../config/env";
import { connect } from "../../repo/db";
import { Button } from "../../ui/button";
export function createOrder(user: User) {
  connect();
  return { orderId: "123", userId: user.id, port: env.port, label: Button.label };
}
TS

if python3 -m pytest tests/structural/test_layering.py -v 2>&1; then
    echo "FAIL: Phase 5 — test_layering should FAIL when beachhead has new violation."
    exit 1
else
    echo "Phase 5 PASSED: new beachhead violation correctly caught."
fi

# Restore clean beachhead file
cat > "$SIM/src/service/orders/create.ts" << 'TS'
import type { User } from "../../types/models";
import { env } from "../../config/env";
import { connect } from "../../repo/db";
export function createOrder(user: User) {
  connect();
  return { orderId: "123", userId: user.id, port: env.port };
}
TS

# -- Phase 6: new legacy violation (not in baseline, should fail) -------------
echo "--- Phase 6: New legacy violation not in baseline (should fail) ---"

# Add a new violation to an existing legacy file
cat >> "$SIM/src/service/legacy-handler.ts" << 'TS'

import { startServer } from "../runtime/server";
export function badLegacy() { return startServer(); }
TS

if python3 -m pytest tests/structural/test_layering.py -v 2>&1; then
    echo "FAIL: Phase 6 — test_layering should FAIL when legacy has new unbaselined violation."
    exit 1
else
    echo "Phase 6 PASSED: new unbaselined legacy violation correctly caught."
fi

# -- Phase 7: verify scope helpers work in this brownfield setup --------------
echo "--- Phase 7: Running scope helper tests ---"

if python3 -m pytest tests/structural/test_sim_scope.py -v 2>&1; then
    echo "Phase 7 PASSED: scope tests pass in brownfield simulation."
else
    echo "FAIL: Phase 7 — scope tests should pass in brownfield simulation."
    exit 1
fi

echo "Phase 7 PASSED: scope tests pass."
echo ""
echo "===================================="
echo "ALL PHASES PASSED"
echo "===================================="
exit 0
