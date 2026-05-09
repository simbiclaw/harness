# your-product

A web product built end-to-end by Claude Code. This README is for the human steerer.

## What's here

This is a freshly-scaffolded repo. There is no application code yet — only the **harness** that lets Claude Code build the application without you writing code.

  CLAUDE.md                          Entry point. Auto-loaded by Claude Code.
  docs/                              System of record. Plans, conventions, etc.
    PLANS.md                         The ExecPlan rubric.
    conventions/                     The five harnesses (documentation tier).
    plans/active/                    ExecPlans currently in flight.
    plans/completed/                 Done ExecPlans (kept for audit).
    plans/archived/                  Cancelled/superseded ExecPlans.
    experiments/                     Empirical evidence for Decision Logs.
    postmortems/                     Incident write-ups.
  .claude/                           Agent runtime.
    hooks/                           PreToolUse/PostToolUse/commit-msg hooks.
    skills/                          Subagents (dep-vetter, verifier, gc, doc-gardener).
    tests/                           (Reserved; structural tests live in tests/structural/)
    decisions/                       Dep-vet records.
    sensitive-paths.txt              Paths the PreToolUse hook protects.
  tests/structural/                  Python structural tests (run in CI).
  src/                               Application code. Layered: types → ui.
  .github/workflows/harness.yml      CI: structural, TypeScript, depcruise, secrets.
  .dependency-cruiser.cjs            Layered-architecture rules for the import graph.
  Dockerfile, docker-compose.yml     Self-hosted deploy skeleton.

## First-run checklist

1. **Install Node 20+ and pnpm 9+.** `pnpm --version` should print `9.x`. Use `corepack enable` if you don't have pnpm yet.

2. **Install Python 3.12+ and pytest.** `pip install pytest pre-commit`. The structural tests and the commit-msg hook are Python.

3. **Initialize git.** `git init && git add -A && git commit -m "harness(bootstrap): initial scaffold"` — this first commit is exempt from the commit-msg hook because the hook is not installed yet.

4. **Install pre-commit hooks.** `pre-commit install --install-hooks`. From this point on, every commit goes through gitleaks and the commit-msg format check.

5. **Activate Claude Code hooks.** Copy `.claude/hooks/settings.json` into your Claude Code global settings, or symlink it from the project. (See Claude Code docs for the exact mechanism.) This is a Tier C step that the bootstrap ExecPlan walks you through.

6. **Run the bootstrap ExecPlan.** Open Claude Code in this directory and say:

  Read CLAUDE.md, then read docs/plans/active/0001-bootstrap-validation.md, then begin.

   The plan walks you through validation, dep-vetting the seed devDependencies, the first commit, and self-archives when done.

## After bootstrap

Every subsequent piece of work starts with you opening an ExecPlan in `docs/plans/active/` and handing it to Claude Code. The harness enforces the rest.

When you spot a recurring problem, **don't add to CLAUDE.md.** Promote the rule one step left:

  documentation → structural test (in `tests/structural/`)
  documentation → hook (in `.claude/hooks/`)
  documentation → CI gate (in `.github/workflows/harness.yml`)

See the **promotion rule** in CLAUDE.md.

## What you should read

In order, if you've never touched this scaffold before:

1. `CLAUDE.md` — the table of contents.
2. `docs/PLANS.md` — what an ExecPlan looks like.
3. The five files in `docs/conventions/` — the harnesses themselves.
4. `BUILD-NOTES.md` — every decision the scaffold made on your behalf at bootstrap, so you can audit and override.

## License

Add one. Then dep-vet it.
