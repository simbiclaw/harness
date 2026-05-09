# Ask-Before-Assuming Threshold

Three tiers govern when Claude Code proceeds vs. escalates.

## Tier A — Proceed silently

Examples: naming a new internal helper function, choosing between two equivalent style options where one is already used elsewhere, fixing a typo, adding a unit test for an existing function, adding a TypeScript type to an untyped function.

Action: log a Decision Log entry. Do not interrupt the human.

## Tier B — Proceed and flag

Examples: adding a new file under `src/`, importing a peer package of one already in use (`zod` if `zod-to-json-schema` is in use), choosing between two viable implementations of a documented feature, refactoring a function used in fewer than 5 places.

Action: Decision Log entry with rationale. Mention in the next milestone commit message body so the human sees it on review.

## Tier C — Stop and ask

Examples: new top-level dependency from a new vendor; any change to schemas, migrations, auth, payments, billing, or user data; any user-facing change not already specified in the ExecPlan; deletion of more than 100 lines of existing code; choice of a third-party SaaS provider; introduction of a new runtime, language, or framework; any change to `Dockerfile`, `docker-compose.yml`, or deploy configuration.

Action: stop. Add an "Awaiting Steering" section to the ExecPlan describing the decision needed and the options. Do not proceed on related milestones until the human resolves it.

## When unsure of the tier

Default to Tier C. The cost of pausing for human input is minutes; the cost of an unflagged Tier-C decision in production is hours to days.

## Sensitive paths (Tier C automatic)

Configurable in `.claude/sensitive-paths.txt`. Default contents:

  src/auth/**
  src/payments/**
  src/billing/**
  src/schemas/**
  src/migrations/**
  migrations/**
  .env*
  .github/workflows/**
  Dockerfile
  docker-compose*.yml
  CLAUDE.md
  docs/PLANS.md
  docs/conventions/**

Last reviewed: 2026-05-02
