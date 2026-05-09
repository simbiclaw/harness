#!/usr/bin/env python3
"""
PostToolUse hook. Currently used for one purpose:

When an edit to an ExecPlan in docs/plans/active/ flips a checkbox from
'[ ]' to '[x]', emit a reminder to commit immediately with the milestone
reference.

This is a soft nudge, not a hard block. The structural test on commit
messages provides the hard enforcement.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ACTIVE_PLANS_DIR = REPO_ROOT / "docs" / "plans" / "active"


def main() -> int:
    event = json.load(sys.stdin)
    tool = event.get("tool_name", "")
    if tool not in ("Edit", "MultiEdit", "Write"):
        return 0

    params = event.get("tool_input", {})
    target = params.get("file_path") or params.get("path") or ""
    if not target:
        return 0

    target_path = Path(target).resolve()
    try:
        rel = target_path.relative_to(ACTIVE_PLANS_DIR)
    except ValueError:
        return 0

    new_text = params.get("new_str") or params.get("content") or ""
    if "[x]" not in new_text:
        return 0

    print(json.dumps({
        "message": (
            f"Milestone checkbox flipped in docs/plans/active/{rel}. "
            f"Per docs/conventions/commit-hygiene.md, commit immediately:\n\n"
            f"  <type>(<scope>): <verb-noun subject>\n\n"
            f"  Plan: docs/plans/active/{rel}#milestone-N\n"
            f"  Decision: <one-line>\n"
        )
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
