#!/usr/bin/env python3
"""
PreToolUse hook for Claude Code.

Multiplexes three guards:
  1. Sensitive-path guard (Harness 1: Tier C escalation).
  2. Package-manager guard (Harness 1 + Harness 3: dep vetting).
  3. Force-push guard (Harness 4: commit hygiene).

Hook contract: read JSON event from stdin, print JSON to stdout.
Exit 0 with {"continue": true} to allow.
Exit 0 with {"continue": false, "reason": "..."} to block.

See: https://docs.claude.com/en/docs/claude-code/hooks
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SENSITIVE_PATHS_FILE = REPO_ROOT / ".claude" / "sensitive-paths.txt"
ACTIVE_PLANS_DIR = REPO_ROOT / "docs" / "plans" / "active"


def load_sensitive_patterns() -> list[str]:
    if not SENSITIVE_PATHS_FILE.exists():
        return []
    return [
        line.strip()
        for line in SENSITIVE_PATHS_FILE.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def path_is_sensitive(path: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(path, f"./{pat}"):
            return True
    return False


def has_resolved_steering_for(path: str) -> bool:
    """Return True if any active ExecPlan has 'Awaiting Steering: resolved'
    referencing this path."""
    if not ACTIVE_PLANS_DIR.exists():
        return False
    for plan in ACTIVE_PLANS_DIR.glob("*.md"):
        text = plan.read_text()
        if "Awaiting Steering: resolved" in text and path in text:
            return True
    return False


# pnpm-aware: pnpm add, pnpm install <pkg>, pnpm i <pkg>, npm install <pkg>,
# npm i <pkg>, yarn add <pkg>. Bare `pnpm install` (no args) is allowed
# because it reinstalls from lockfile and adds nothing new.
PKG_MGR_PATTERNS = [
    re.compile(r"\bpnpm\s+add\s+(?:--save-dev\s+|-D\s+|--save-peer\s+|-P\s+)?([@\w/\-\.]+)"),
    re.compile(r"\bpnpm\s+(?:install|i)\s+(?!--frozen-lockfile|--prod\b)([@\w/\-\.]+)"),
    re.compile(r"\bnpm\s+install\s+(?:--save-dev\s+|--save\s+|-D\s+|-S\s+)?([@\w/\-\.]+)"),
    re.compile(r"\bnpm\s+i\s+(?:--save-dev\s+|--save\s+|-D\s+|-S\s+)?([@\w/\-\.]+)"),
    re.compile(r"\byarn\s+add\s+(?:--dev\s+|-D\s+)?([@\w/\-\.]+)"),
]


def parse_pkg_install(cmd: str) -> str | None:
    """Return package name if cmd is a package install, else None."""
    for pat in PKG_MGR_PATTERNS:
        m = pat.search(cmd)
        if m:
            return m.group(1)
    return None


def has_dep_vet_for(package: str) -> bool:
    # Sanitize scoped packages: @org/pkg -> dep-vet-@org-pkg.md
    sanitized = package.replace("/", "-")
    vet_file = REPO_ROOT / ".claude" / "decisions" / f"dep-vet-{sanitized}.md"
    return vet_file.exists()


def is_force_push(cmd: str) -> bool:
    if "git push" not in cmd:
        return False
    return "--force" in cmd or " -f " in cmd or "--force-with-lease" in cmd


def main() -> int:
    event = json.load(sys.stdin)
    tool = event.get("tool_name", "")
    params = event.get("tool_input", {})

    # Guard 1: sensitive path on Edit/Write/MultiEdit/Create
    if tool in ("Edit", "Write", "MultiEdit", "Create"):
        target = params.get("file_path") or params.get("path") or ""
        if target:
            try:
                rel = str(Path(target).resolve().relative_to(REPO_ROOT))
            except ValueError:
                rel = ""
            patterns = load_sensitive_patterns()
            if rel and path_is_sensitive(rel, patterns):
                if not has_resolved_steering_for(rel):
                    print(json.dumps({
                        "continue": False,
                        "reason": (
                            f"Path '{rel}' matches a sensitive pattern "
                            f"(see .claude/sensitive-paths.txt). This is a "
                            f"Tier C decision per "
                            f"docs/conventions/ask-threshold.md. Stop, open "
                            f"an 'Awaiting Steering' section in the active "
                            f"ExecPlan describing the change you intend, "
                            f"and wait for the human. Once resolved, mark "
                            f"the section 'Awaiting Steering: resolved' and "
                            f"reference the path '{rel}' so this hook will "
                            f"allow the edit."
                        ),
                    }))
                    return 0

    # Guard 2: package install on Bash
    if tool == "Bash":
        cmd = params.get("command", "")
        package = parse_pkg_install(cmd)
        if package and not has_dep_vet_for(package):
            sanitized = package.replace("/", "-")
            print(json.dumps({
                "continue": False,
                "reason": (
                    f"Package '{package}' has no dep-vet record at "
                    f".claude/decisions/dep-vet-{sanitized}.md. Per "
                    f"docs/conventions/deps-and-secrets.md, run the "
                    f"dep-vetter skill on '{package}' first. If approved, "
                    f"the skill writes the dep-vet file and this hook will "
                    f"allow the install."
                ),
            }))
            return 0

        # Guard 3: force-push
        if is_force_push(cmd) and os.environ.get("CLAUDE_FORCE_PUSH_OK") != "1":
            print(json.dumps({
                "continue": False,
                "reason": (
                    "Force-push is blocked. Per "
                    "docs/conventions/commit-hygiene.md, force-pushes "
                    "require an explicit unlock and a Decision Log entry "
                    "explaining why. Do not bypass without human approval."
                ),
            }))
            return 0

    # Default allow.
    print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
