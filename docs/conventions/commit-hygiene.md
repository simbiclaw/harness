# Commit Hygiene

The git log is the second narrative thread alongside ExecPlan Progress sections. The two must agree.

## Message format

  <type>(<scope>): <subject>

  Plan: docs/plans/active/NNNN-<slug>.md#milestone-N
  Decision: <one-line rationale, or "implementation only">

Where:

- `<type>` is one of: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `harness`.
- `<scope>` is a short module or area name (`auth`, `billing`, `ci`, `harness`).
- `<subject>` is an imperative-mood verb phrase, 12–72 characters.

The `harness` type is reserved for changes inside `.claude/`, `docs/conventions/`, `docs/PLANS.md`, or CI configuration.

## One commit per milestone-checkbox flip

Every flip of a Progress checkbox from `[ ]` to `[x]` is its own commit. The commit message names the milestone in the Plan trailer. Implementation work toward a milestone may span multiple commits; only the final commit (the one that flips the checkbox) needs to claim completion.

## Never amend pushed commits

`git commit --amend` is permitted only for the most recent local commit that has not been pushed. Once pushed, fixes go in new commits.

## Force-push requires explicit unlock

The pre-push hook blocks `--force` and `--force-with-lease` unless the env var `CLAUDE_FORCE_PUSH_OK=1` is set. This var is never set in normal agent operation.

## What "useful commit message" means

Subject must contain a verb and a noun. "update files", "fix issues", "various changes", "wip", "misc", "stuff", "tweaks" are rejected by the structural test even if they pass the regex hook.

## Plan trailer survives plan archival

When an ExecPlan is moved from `docs/plans/active/` to `docs/plans/completed/`, the `Plan:` trailer in old commits still references the `active/` path. The structural test that validates trailers looks in `active/`, `completed/`, and `archived/`. Do not retroactively rewrite commit messages to update paths; the trailer is a historical record of where the plan lived at commit time.

Last reviewed: 2026-05-02
