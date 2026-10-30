"""
Structural test: recent commits follow the trailer format.

Walks `git log --since=30.days.ago` and asserts every commit message:
  - has a Plan: trailer pointing to a real ExecPlan path
  - has a Decision: trailer
  - has a non-trivial subject (verb-noun, 12-72 chars)

Skips merge commits and the root commit (bootstrap scaffold).
In brownfield mode, skips non-Claude-authored commits.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

TRAILER_PLAN = re.compile(
    r"^Plan:\s*(docs/plans/\S+\.md)(#\S+)?", re.MULTILINE
)
TRAILER_DECISION = re.compile(r"^Decision:\s*\S.*$", re.MULTILINE)
SUBJECT_RE = re.compile(
    r"^[a-z]+(\([\w\-]+\))?:\s+(.{12,72})$"
)
USELESS_SUBJECTS = re.compile(
    r"^(update files|fix issues|various changes|wip|misc|stuff|tweaks?|"
    r"updates?|changes|things)\.?$",
    re.IGNORECASE,
)


def _root_commit_sha() -> str | None:
    """Return the SHA of the root commit (no parents), or None."""
    try:
        out = subprocess.check_output(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            cwd=REPO_ROOT, text=True,
        )
    except subprocess.CalledProcessError:
        return None
    return out.strip()[:40] if out.strip() else None


def _oldest_plan_timestamp() -> int | None:
    """Return the Unix mtime of the oldest active ExecPlan, or None."""
    plans_dir = REPO_ROOT / "docs" / "plans" / "active"
    if not plans_dir.exists():
        return None
    stamps = []
    for p in plans_dir.glob("*.md"):
        if p.name == ".gitkeep":
            continue
        stamps.append(p.stat().st_mtime)
    return int(min(stamps)) if stamps else None


def git_log() -> list[tuple[str, str, int, str]]:
    """Return (sha, author, timestamp, message) for recent non-merge commits."""
    try:
        out = subprocess.check_output(
            ["git", "log", "--since=30.days.ago", "--no-merges",
             "--pretty=format:%H%x00%an%x00%at%x00%B%x1e"],
            cwd=REPO_ROOT, text=True,
        )
    except subprocess.CalledProcessError:
        return []
    out = out.rstrip("\x1e")
    if not out:
        return []
    entries = []
    for chunk in out.split("\x1e"):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        sha, rest = chunk.split("\x00", 1)
        author, rest = rest.split("\x00", 1)
        ts_str, msg = rest.split("\x00", 1)
        entries.append((sha, author, int(ts_str), msg))
    return entries


def _is_claude_author(author: str) -> bool:
    """Return True if the author is a Claude agent."""
    return "Claude" in author or "claude" in author.lower()


def _scope_requires_all_commits() -> bool:
    """In greenfield mode, all commits need trailers. In brownfield, only Claude-authored."""
    from tests.structural.scope_helpers import _load_scope
    scope = _load_scope()
    return scope.get("mode") != "brownfield"


def test_commits_follow_format():
    failures: list[str] = []
    require_all = _scope_requires_all_commits()
    root_sha = _root_commit_sha()
    plan_ts = _oldest_plan_timestamp()

    for sha, author, ts, msg in git_log():
        sha_short = sha[:8]

        # Skip the root commit — it lays down the scaffold before any
        # ExecPlan existed and cannot retroactively reference one.
        if root_sha and sha.startswith(root_sha):
            continue

        # Skip commits made before the first ExecPlan existed.
        # The bootstrap scaffold commit predates the plan system.
        if plan_ts and ts < plan_ts:
            continue

        # In brownfield mode, skip commits not authored by Claude agents.
        if not require_all and not _is_claude_author(author):
            continue

        lines = msg.splitlines()
        subject = lines[0] if lines else ""
        m = SUBJECT_RE.match(subject)
        if not m:
            failures.append(
                f"{sha_short}: subject does not match "
                f"'<type>(<scope>): <verb-noun>': {subject!r}"
            )
            continue
        if USELESS_SUBJECTS.match(m.group(2).strip()):
            failures.append(
                f"{sha_short}: subject is too vague: {subject!r}"
            )

        plan_match = TRAILER_PLAN.search(msg)
        if not plan_match:
            failures.append(f"{sha_short}: missing 'Plan:' trailer.")
        else:
            plan_path = REPO_ROOT / plan_match.group(1)
            if not plan_path.exists():
                stem = Path(plan_match.group(1)).name
                alt_dirs = [REPO_ROOT / "docs" / "plans" / d
                            for d in ("active", "completed", "archived")]
                if not any((d / stem).exists() for d in alt_dirs):
                    failures.append(
                        f"{sha_short}: Plan trailer references missing "
                        f"file '{plan_match.group(1)}'."
                    )
        if not TRAILER_DECISION.search(msg):
            failures.append(f"{sha_short}: missing 'Decision:' trailer.")

    assert not failures, "\n  ".join([""] + failures)
