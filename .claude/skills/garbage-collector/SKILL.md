---
name: garbage-collector
description: Recurring custodial agent. Scans the repo for cruft (unused files, dead exports, stale TODOs, dormant ExecPlans) and opens an ExecPlan per cleanup theme. Does not delete autonomously.
---

# Garbage-Collector Skill

## When to use this skill

Nightly via cron, or on-demand when a human says "clean up". Never as a side-effect of feature work.

## Scans

### Unused files

For each `.ts` / `.tsx` / `.js` / `.jsx` source under `src/`, check whether anything imports it. Use `pnpm dlx ts-prune` or `knip` (when added as a dependency through normal dep-vet) to find dead exports and unreferenced files. Files with no inbound imports and no inclusion in entry-point manifests (anything in `package.json`'s `main`, `bin`, `exports`, or referenced by `vite.config.ts` / `tsconfig.json`'s `include`) are candidates for removal.

### Unused exports

Within each file, identify exported symbols (functions, classes, consts, types) that are not referenced anywhere outside the file. Candidates for internalization or removal.

### Stale TODOs

`grep -rn "TODO\|FIXME\|XXX\|HACK" src/` — any match older than 30 days (per `git blame`) is a candidate for resolution. Resolution = open ExecPlan to fix, or convert to a tracked issue, or remove.

### Dormant active ExecPlans

ExecPlans in `docs/plans/active/` with no Progress checkbox flips in 14 days. Candidates for archival or revival.

### Empty test files

Test files where every test has been skipped (`.skip`) or `describe.skip` wraps everything.

### Stale dep-vet records

`.claude/decisions/dep-vet-*.md` where the package is no longer in `package.json`. Candidates for archival.

## Output

For each cleanup theme with non-empty candidates, open ONE ExecPlan at `docs/plans/active/NNNN-gc-<theme>-<date>.md` following the PLANS.md rubric. List the candidates as Milestones. Do not delete anything.

## What this skill must NOT do

- Delete files
- Remove code
- Modify ExecPlans authored by feature work
- Modify CLAUDE.md, conventions, hooks, or tests
- Run on a clock that overlaps with active feature work (CI signals if a feature ExecPlan is mid-flight; defer if so)

Last reviewed: 2026-05-02
