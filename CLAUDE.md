# CLAUDE.md

Auto-loaded at the start of every Claude Code session in this repo. Intentionally short. Long instruction files crowd out task context and rot faster than they're maintained. This is a table of contents, not an encyclopedia.

## What this repository is

A web product — Node.js HTTP backend, browser frontend — built end-to-end by Claude Code. A human steers; agents execute. Engineering work happens through ExecPlans under `docs/plans/`, structural tests under `tests/structural/`, hooks under `.claude/hooks/`, and skills under `.claude/skills/`. Collectively: the **harness**.

**Greenfield mode** (default): `src/` is created by feature ExecPlans, never by hand. There is no human-written application code in `src/`.

**Brownfield mode**: the repo has existing application code. Enforcement is scoped to harness-managed regions declared in `.claude/harness-scope.json`. See `docs/conventions/brownfield-adoption.md` for the beachhead + baseline + ratchet pattern. Check the scope file before assuming any rule is repo-wide.

## The split

- `docs/` — the system of record. Plans, decisions, conventions, postmortems, experiments. Read as knowledge.
- `.claude/` — the agent runtime. Hooks that fire on tool use, structural tests that run in CI, skills that subagents invoke. Code that runs.
- `src/` — the application itself. Created by feature ExecPlans, never by hand.

## Read these before non-trivial work

- `docs/PLANS.md` — the rubric every ExecPlan follows. Read once per session if you'll create or modify a plan.
- `docs/conventions/ask-threshold.md` — when to proceed silently vs. flag vs. stop and ask.
- `docs/conventions/verification-floor.md` — what "done" means for a milestone.
- `docs/conventions/deps-and-secrets.md` — how new dependencies and secrets are handled.
- `docs/conventions/commit-hygiene.md` — commit message format.
- `docs/conventions/i-dont-know-protocol.md` — how to handle uncertainty in Decision Logs.
- `docs/conventions/brownfield-adoption.md` — how to adopt the harness in an existing codebase (beachhead, baselines, ratchets).

## First action on every session

Read the most recent file in `docs/plans/active/` end-to-end. That is the work in flight. If there is more than one active plan, ask the human which to pick up. Do not start in the middle of a plan you have not read.

## The five harnesses

1. **Ask before assuming** — three explicit tiers; default to the most cautious. See `ask-threshold.md`.
2. **Verification floor** — every milestone has a runnable Acceptance Test exercising an externally observable property. See `verification-floor.md`.
3. **Deps and secrets** — new dependencies are vetted by the dep-vetter skill; secrets never enter the repo. See `deps-and-secrets.md`.
4. **Commit hygiene** — every commit references its ExecPlan and milestone with a Decision trailer. See `commit-hygiene.md`.
5. **"I don't know" protocol** — Decision Log entries cite evidence, run experiments, or flag uncertainty. Forbidden phrases are enforced by structural test. See `i-dont-know-protocol.md`.

## The promotion rule

Every rule starts as documentation in `docs/conventions/`. When the same rule is violated twice, the documentation has failed. Open an ExecPlan to promote it leftward:

- documentation → structural test (in `.claude/tests/`)
- documentation → hook (in `.claude/hooks/`)
- documentation → CI gate (in `.github/workflows/harness.yml`)

Do not "try harder to remember." Move the rule into code.

## Skills

- `.claude/skills/dep-vetter/` — vet a new dependency against the four-check policy.
- `.claude/skills/verifier/` — re-run a milestone's Acceptance Test on a checkbox flip.
- `.claude/skills/garbage-collector/` — recurring scan for cruft (nightly).
- `.claude/skills/doc-gardener/` — recurring scan for stale docs and broken cross-refs (weekly).

## What hooks block

- Edits to paths in `.claude/sensitive-paths.txt` without a resolved "Awaiting Steering" entry in the active ExecPlan.
- Package installs (`pnpm add`, `npm install`) without a dep-vet record at `.claude/decisions/dep-vet-<pkg>.md`.
- `git push --force` unless `CLAUDE_FORCE_PUSH_OK=1` is set (never set in normal operation).
- Commits whose message lacks `Plan:` and `Decision:` trailers.

## What structural tests fail

- Imports in `src/` pointing downward in the layer graph (`types → config → repo → service → runtime → ui`).
- ExecPlan Decision Log entries without a recognized rationale shape (Source / Experiment / Confidence: low).
- ExecPlan Decision Log entries containing forbidden phrases ("standard approach", "best practice", etc.).
- Recent commits without `Plan:` / `Decision:` trailers, or with vague subjects.
- Direct dependencies in `package.json` without a Decision Log entry and dep-vet record.

When a hook or structural test fails, the error message names the file, line, and required fix. Do what it says.

## Last reviewed

2026-05-02. The doc-gardener will surface this if it goes >90 days without review.
