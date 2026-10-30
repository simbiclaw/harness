#!/usr/bin/env python3
"""
Compare dep-cruiser JSON output against the committed baseline.

Usage:
  pnpm depcruise --output-type json src/ | python3 .claude/scripts/depcruiser-baseline-diff.py

Exit 0: no new legacy-violation fingerprints detected.
Exit 1: new violations found (not in baseline) — CI fails.
Exit 2: dep-cruiser output could not be parsed.

The baseline file lives at .claude/baselines/depcruiser.json and is a
sorted JSON array of violation fingerprint strings:

  ["src/legacy/handler.ts:5: import from higher layer 'ui'", ...]

In greenfield mode this script is a no-op (exit 0, prints a skip message).
In brownfield mode with no baseline file, all legacy violations are flagged
as new — this is the bootstrap moment before the first baseline is committed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCOPE_FILE = REPO_ROOT / ".claude" / "harness-scope.json"
BASELINE_FILE = REPO_ROOT / ".claude" / "baselines" / "depcruiser.json"


def load_scope() -> dict:
    if not SCOPE_FILE.exists():
        return {"version": 1, "mode": "greenfield",
                "managed_paths": ["src/**"], "legacy_paths": [],
                "baselines": {}}
    return json.loads(SCOPE_FILE.read_text(encoding="utf-8"))


def load_baseline() -> set[str]:
    if not BASELINE_FILE.exists():
        return set()
    try:
        data = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
        return set(data)
    except (json.JSONDecodeError, ValueError):
        print(f"Warning: baseline file {BASELINE_FILE} is not valid JSON.",
              file=sys.stderr)
        return set()


def extract_violations(depcruise_output: dict) -> set[str]:
    """Extract violation fingerprints from dep-cruiser JSON output."""
    fingerprints: set[str] = set()
    violations = depcruise_output.get("summary", {}).get("violations", [])
    if not violations:
        violations = depcruise_output.get("modules", [])
        # Fall back to iterating modules for their rule violations
        for mod in violations:
            for rule in mod.get("rules", []):
                for viol in rule.get("violations", []):
                    fname = f"{mod.get('source', '')}: {rule.get('name', '')}: {viol.get('to', '')}"
                    fingerprints.add(fname)
        return fingerprints

    for v in violations:
        fprint = (
            f"{v.get('from', 'unknown')}:{v.get('rule', {}).get('name', 'unknown')}: "
            f"{v.get('to', 'unknown')}"
        )
        fingerprints.add(fprint)
    return fingerprints


def main() -> int:
    scope = load_scope()
    if scope.get("mode") != "brownfield":
        print("depcruiser-baseline-diff: greenfield mode — skipping baseline check.")
        return 0

    try:
        depcruise_output = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing dep-cruiser output: {e}", file=sys.stderr)
        return 2

    current = extract_violations(depcruise_output)
    baseline = load_baseline()

    if not baseline:
        if current:
            print(f"depcruiser-baseline-diff: {len(current)} violation(s) found, "
                  f"no baseline committed yet. Run 'pnpm depcruise --output-type json | "
                  f"python3 .claude/scripts/depcruiser-baseline-diff.py --create-baseline' "
                  f"to generate the initial baseline.")
            return 1
        print("depcruiser-baseline-diff: no violations, no baseline needed.")
        return 0

    new = current - baseline
    resolved = baseline - current

    if resolved:
        print(f"depcruiser-baseline-diff: {len(resolved)} previously-baselined "
              f"violation(s) now resolved. Shrink the baseline by re-running with "
              f"--create-baseline.")

    if new:
        print(f"depcruiser-baseline-diff: {len(new)} NEW violation(s) not in baseline:")
        for v in sorted(new):
            print(f"  {v}")
        print(f"\n{len(baseline & current)} baselined violation(s) remain.")
        return 1

    print(f"depcruiser-baseline-diff: no new violations. "
          f"{len(baseline & current)} baselined violation(s) remain. "
          f"{len(resolved)} resolved since last baseline.")
    return 0


if __name__ == "__main__":
    if "--create-baseline" in sys.argv:
        sys.argv.remove("--create-baseline")
        try:
            depcruise_output = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing dep-cruiser output: {e}", file=sys.stderr)
            sys.exit(2)
        violations = sorted(extract_violations(depcruise_output))
        BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_FILE.write_text(json.dumps(violations, indent=2) + "\n")
        print(f"Baseline written: {len(violations)} violation(s) recorded at "
              f"{BASELINE_FILE.relative_to(REPO_ROOT)}")
        sys.exit(0)

    sys.exit(main())
