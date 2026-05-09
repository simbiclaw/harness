#!/usr/bin/env python3
"""commit-msg hook: enforce trailer format from commit-hygiene.md."""
from __future__ import annotations

import re
import sys
from pathlib import Path

TEMPLATE = """
Commit message must follow the format:

  <type>(<scope>): <subject>

  Plan: docs/plans/active/NNNN-<slug>.md#milestone-N
  Decision: <one-line rationale, or "implementation only">

Where <type> is one of: feat fix refactor test docs chore harness
"""

SUBJECT_RE = re.compile(
    r"^(feat|fix|refactor|test|docs|chore|harness)(\([\w\-]+\))?:\s+(.{12,72})$"
)
TRAILER_PLAN = re.compile(r"^Plan:\s*docs/plans/", re.MULTILINE)
TRAILER_DECISION = re.compile(r"^Decision:\s*\S", re.MULTILINE)


def main(argv: list[str]) -> int:
    msg_file = Path(argv[1])
    msg = msg_file.read_text()

    first = msg.splitlines()[0] if msg.splitlines() else ""
    if first.startswith("Merge ") or first.startswith("Revert "):
        return 0

    errs = []
    if not SUBJECT_RE.match(first):
        errs.append(
            "Subject line does not match "
            "'<type>(<scope>): <12-72 char subject>'."
        )
    if not TRAILER_PLAN.search(msg):
        errs.append("Missing 'Plan: docs/plans/...' trailer.")
    if not TRAILER_DECISION.search(msg):
        errs.append("Missing 'Decision: ...' trailer.")

    if errs:
        print("Commit rejected:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        print(TEMPLATE, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
