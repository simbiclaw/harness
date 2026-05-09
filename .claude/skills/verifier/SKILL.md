---
name: verifier
description: Triggered when an ExecPlan progress checkbox flips from `[ ]` to `[x]`. Re-runs the milestone's named Acceptance Test in a clean checkout via `pnpm test`. On pass, writes a 'verified at SHA' Decision Log entry. On fail, reverts the checkbox flip and adds a Surprises entry.
---

# Verifier Skill

## When to use this skill

Automatically, when the PostToolUse hook detects an Edit/Write to a file under `docs/plans/active/` whose diff includes a checkbox flip from `[ ]` to `[x]`.

## Process

1. Read the milestone-N section of the ExecPlan. Extract the `Acceptance Test:` line. Parse out the test ID — for Vitest, the format is `path/to/file.test.ts > test description`.

2. Create a clean checkout of HEAD in a git worktree:

  git worktree add /tmp/verify-<sha> <sha>

3. In the worktree:

  cd /tmp/verify-<sha>
  pnpm install --frozen-lockfile
  pnpm test --run -- "<test-id>"

4. Capture exit code, stdout, stderr.

5. Remove the worktree:

  cd <repo-root>
  git worktree remove /tmp/verify-<sha>

## On pass

Append to the ExecPlan's Decision Log:

  ### Milestone N verified

  Verified at SHA <sha> on <YYYY-MM-DD HH:MM TZ>.
  Acceptance Test: <test-id>
  Source: docs/plans/active/<plan>.md#milestone-N

## On fail

Revert the checkbox flip via `git checkout <prior-sha> -- docs/plans/active/<plan>.md`. Append to the ExecPlan's Surprises & Discoveries section:

  ### Milestone N verification failed at <date>

  Acceptance Test: <test-id>
  Exit code: <N>
  Output: <first 50 lines of combined stdout+stderr>
  Source: <captured run log path under .claude/verifier-runs/>

  Action: do not flip the checkbox until the cause is understood and fixed. If the test is wrong, fix the test in a separate commit.

## What this skill must NOT do

- Modify any source code beyond reverting the ExecPlan file.
- Run the full test suite (CI does that).
- Cache results between runs (every flip gets fresh verification).
- Skip type-checking or linting steps that are part of the project's `pnpm test` pipeline.

Last reviewed: 2026-05-02
