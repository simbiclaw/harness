# Dependencies and Secrets

Two rules. Both non-negotiable. Both mechanically enforced.

## New dependencies must be vetted

Before any direct dependency is added to `package.json`, the dep-vetter skill checks:

1. Package age: more than 30 days since first publish (configurable).
2. Weekly downloads: more than 1000 (configurable).
3. Recent activity: at least one commit in the source repo within 90 days.
4. License: compatible with project license (default allowed list: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, MPL-2.0).

Any failure rejects the dependency. Override only via a commit message containing the literal token `[dep-override-approved-by-human]`, which the doc-gardener surfaces for audit.

The skill writes a record at `.claude/decisions/dep-vet-<package>.md`. The PreToolUse hook reads this file before allowing `pnpm add`, `pnpm install`, `npm install`, or `yarn add` to run.

## Decision Log entry per dependency

Every direct dependency in `package.json` (both `dependencies` and `devDependencies`) has a Decision Log entry in some ExecPlan naming the package and its rationale. The structural test `tests/structural/test_dep_decisions.py` walks `package.json` and the plan tree; CI fails if any direct dependency lacks an entry.

## Pinning

- `package.json`: caret ranges permitted for application dependencies (`^1.2.3`); exact pins required for build tooling (`vite`, `tsx`, `vitest`, `eslint`, etc.).
- `pnpm-lock.yaml`: always committed. Always.
- Never use `latest`, `*`, or unbounded ranges.

## Secrets

- `.env` is gitignored. Always.
- `.env.example` is committed; contains stub values only.
- Real secrets live in the deploy environment's secret store at runtime.
- The repo has no live secrets, ever.

## Secret detection

- Pre-commit hook runs `gitleaks` against staged changes. Any match blocks the commit.
- CI job runs `gitleaks detect` over the full history on every PR.
- `.gitignore` covers `.env`, `.env.local`, `*.pem`, `*.key`, `id_rsa*`, `**/credentials.json`, `**/service-account*.json`.

If a secret is detected post-commit, the response is rotation-then-history-rewrite, in that order. A new ExecPlan documents the incident in `docs/postmortems/`.

Last reviewed: 2026-05-02
