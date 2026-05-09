# BUILD-NOTES

Decisions made during scaffolding without explicit instruction from the human steerer. Each one is reversible; review and override before the bootstrap ExecPlan runs if any feel wrong.

## Confirmed by user

- **Stack**: TypeScript on Node, package manager pnpm.
- **Product type**: Web product with HTTP backend and browser frontend.
- **Deploy target**: Self-hosted. Skeleton `Dockerfile` and `docker-compose.yml` provided; actual host environment deferred to a later ExecPlan.
- **Repo hosting**: GitHub. CI workflow uses `actions/setup-node`, `pnpm/action-setup`, `gitleaks/gitleaks-action`.
- **Operator model**: Solo, written so it scales to a small team without rewriting.
- **Knowledge base location**: `docs/` is the system of record. PLANS.md and all ExecPlans live under `docs/`.

## Decisions I made

### Node version: 20

Active LTS. The `engines` block in `package.json` requires `>=20.0.0`. Override by editing `package.json` and `Dockerfile`'s `NODE_VERSION` arg. **Why this could be wrong**: if you have infrastructure pinned to Node 18 or are eyeing Node 22 for performance reasons, this needs adjustment.

### pnpm version: 9

Current stable major. The `engines` block requires `>=9.0.0`. Override the same way as Node version. **Why this could be wrong**: pnpm 8 has different lockfile format; mixing versions across machines breaks reproducibility.

### TypeScript version: 5.4.5

Pinned exact, not caret-ranged. **Why pinned**: TypeScript minor versions occasionally introduce stricter checks that break agent iteration; pinning lets you upgrade deliberately via ExecPlan. **Why this version**: most recent stable minor at scaffold time. If a newer minor exists when you read this, dep-vet and update.

### Test runner: Vitest

Chosen over Jest because:
- Native ESM support (no `"type": "module"` workarounds).
- Faster start (~3-5x).
- Better TypeScript story without `ts-jest`.
- Tighter integration with Vite if a frontend ExecPlan adopts Vite.

**Why this could be wrong**: if you have strong existing Jest familiarity or specific Jest plugins in mind, switching is a one-ExecPlan refactor and worth doing early.

### Linter: ESLint 8.x (not 9.x)

ESLint 9 introduced flat config as default and broke many plugins. Pinning 8.57.0 keeps the bootstrap stable. The provided `eslint.config.js` is already in flat format, so the migration to 9.x will be smooth when you choose. **Override**: bump in `package.json`, then dep-vet.

### Architecture: layered (`types → config → repo → service → runtime → ui`)

This is the layering OpenAI's harness team converged on. It's enforced two ways:
- `tests/structural/test_layering.py` (regex on imports, fast, runs in pytest)
- `.dependency-cruiser.cjs` (full graph analysis, runs in CI)

**Why this could be wrong for your product**: if you're building something that's primarily a frontend SPA with a thin backend, the layer split feels off — you'll want to either (a) restructure into `domain → application → infrastructure → presentation` (DDD-style) or (b) collapse `runtime` and `ui` since they're effectively one layer for SPAs. Either is an early ExecPlan, not a fight with the bootstrap.

### TypeScript path aliases: `@/types/*` etc.

Added to `tsconfig.json` and `vitest.config.ts`. Lets you write `import { User } from "@/types/models"` instead of `../../types/models`. **Override**: remove the `paths` block in tsconfig and the `alias` block in vitest.config if you prefer relative imports.

### Strict TypeScript settings

All four "extra strict" flags on: `noUncheckedIndexedAccess`, `noImplicitOverride`, `noFallthroughCasesInSwitch`, `verbatimModuleSyntax`. The first one (`noUncheckedIndexedAccess`) is the most opinionated — it makes `arr[i]` typed as `T | undefined` rather than `T`, which catches real bugs but can feel noisy. **Override** by removing from `tsconfig.json` if it generates more noise than signal in your context.

### Dependency-cruiser version: 16.3.3

Pinned. **Override**: bump and dep-vet.

### `.dependency-cruiser.cjs` rules

I included `no-circular` (error), `no-orphans` (warn), and the five layer rules (error). The `no-orphans` rule has exceptions for test files, `.d.ts` files, and `src/runtime/index.ts` / `src/ui/index.ts` (top-of-stack entry points). If you find the orphan warnings noisy on your codebase shape, downgrade to `info` or remove.

### CI workflow has four jobs, no deploy step

`structural`, `typescript`, `dependency-graph`, `secrets`. No build-and-push-image step because no deploy target is chosen yet. **Override**: when you pick a deploy target, an ExecPlan should add the deploy job here.

### Pre-commit hook installs gitleaks v8.18.0

Pinned exact. **Override**: bump in `.pre-commit-config.yaml` if a newer gitleaks ships.

### Sensitive paths

The seeded `.claude/sensitive-paths.txt` includes:
- The auth/payments/billing/schema/migrations folders (standard).
- `.env*`, GitHub workflows, Docker files (deploy/secret-adjacent).
- `CLAUDE.md`, `docs/PLANS.md`, `docs/conventions/**` (the harness itself).
- `package.json`, `pnpm-lock.yaml`, `.dependency-cruiser.cjs`, `tsconfig.json` (toolchain — agents should not silently change these).

**Why include the toolchain files**: a stack change is by definition a Tier C decision; protecting the files prevents drift. **Override**: delete the lines you don't want protected.

### Harness scripts in Python

I kept the harness scripts in Python rather than rewriting them in TypeScript. Reasons:
- Decouples harness from application runtime — structural tests run even if `node_modules` is broken.
- Python is on every dev machine; one fewer dependency.
- The structural tests are mostly regex over markdown and small AST walks; Python's stdlib handles this cleanly.

**Override**: if your team is Python-averse and you'd rather have everything TypeScript, this is a multi-ExecPlan migration. The functional surface is small (~600 lines of Python total); not difficult, just deliberate work.

### Bootstrap ExecPlan is validation-focused, not creation-focused

Because I built the scaffold directly, the bootstrap plan's job is to validate, dep-vet the five seed packages retroactively, install pre-commit, activate hooks, and make the first proper commit. If you'd prefer the bootstrap to *create* the scaffold (so the audit trail is fully in-repo), the alternative is to delete everything I built, hand Claude Code the cookbook from the previous turn, and let it generate the scaffold itself. That's a defensible choice; this scaffold is the faster one.

### Things I did NOT decide

These are deliberately deferred to ExecPlans you'll write after bootstrap:

- HTTP framework (Express, Fastify, Hono, Koa, raw Node http).
- Frontend framework (or no framework — just HTML+vanilla TS).
- Database choice and ORM.
- Auth scheme.
- Logging library.
- Observability stack.
- Frontend build tool (Vite is implicit if you use `vitest`'s aliases, but not committed).
- License (the README literally says "add one").

## When this file becomes stale

After the bootstrap ExecPlan completes, re-read this file once. Anything you didn't override silently becomes the convention. The doc-gardener will not flag this file's age (it's not under `docs/`); move it to `docs/postmortems/2026-05-02-scaffold-decisions.md` if you want it under the gardener's watch.

Last reviewed: 2026-05-02.
