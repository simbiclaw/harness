# 0001-bootstrap-validation

## Purpose

The harness scaffolding (CLAUDE.md, docs/PLANS.md, conventions, hooks, structural tests, skill definitions, CI workflow, TypeScript stack) was laid down before this plan exists. This plan's job is to validate that everything is wired correctly, complete the operational steps that require runtime actions (`pnpm install`, hook activation, dep-vetting the seed devDependencies, first commit), and confirm the harness is live before any feature work begins.

This is unusual: most ExecPlans build something new. This one verifies that the bootstrap delivery is internally consistent.

## Big Picture

Six things must be true before this plan can self-archive:

1. The Node.js / pnpm toolchain is installed and the lockfile generates without errors.
2. All five seed devDependencies have dep-vet records under `.claude/decisions/`.
3. The structural tests run and pass against the bootstrap repo.
4. The pre-commit hook is installed and rejects malformed commits.
5. The Claude Code hooks are activated in the local settings.
6. The first real commit (this plan plus the dep-vet records) lands in `main` with a properly-formatted message that the structural test accepts.

In scope: the validation steps above and the dep-vet records for the five seed devDependencies (`@types/node`, `dependency-cruiser`, `eslint`, `typescript`, `vitest`).

Out of scope: any application code in `src/`, choice of HTTP framework, choice of database, frontend framework selection. Each of these is a Tier C decision that gets its own ExecPlan.

## Milestones

### M1: Validate the toolchain

Run `pnpm install` (without `--frozen-lockfile` since the lockfile does not yet exist). Confirm `node_modules/` populates without errors and `pnpm-lock.yaml` is generated. Run `pnpm typecheck` against the empty layer stubs — it should pass with no errors. Run `pnpm lint` — should pass with no errors. Run `pnpm depcruise` — should pass because the layer stubs have no inter-layer imports.

Acceptance Test: `tests/structural/test_layering.py::test_layer_imports_flow_upward` — passes when `src/` exists with the bootstrap stubs and no violations are present. Run via `pytest tests/structural/test_layering.py -v`.

Notes: if `pnpm install` fails with a missing-lockfile or version-pin error, that's a real bootstrap bug — log in Surprises and fix the package.json pin, do not loosen it.

### M2: Dep-vet the seed devDependencies

The five packages in `package.json` `devDependencies` were chosen at scaffold time without going through the dep-vetter (because the dep-vetter itself depends on `package.json` existing). Retroactively run the dep-vetter skill on each: `@types/node`, `dependency-cruiser`, `eslint`, `typescript`, `vitest`. Each produces a record at `.claude/decisions/dep-vet-<sanitized>.md`.

Acceptance Test: `tests/structural/test_dep_decisions.py::test_each_dep_has_decision_and_vet` — passes when every entry in `package.json` has both a `dep-vet-*.md` file and a mention in this ExecPlan's Decision Log below.

Notes: each dep-vet record is its own commit. The skill's `Source:` field provides the citation that satisfies the Decision Log evidence test.

### M3: Verify all structural tests pass

Run the full structural test suite: `pytest tests/structural/ -v`. All five tests should pass on the bootstrap repo, because each is designed to short-circuit cleanly when its target inputs are absent or trivial.

Acceptance Test: pytest exits 0 with five passing tests. Captured output goes to `.claude/verifier-runs/m3-structural-suite.log`.

### M4: Install pre-commit and verify it rejects bad commits

Install the pre-commit toolchain: `pip install pre-commit && pre-commit install --install-hooks`. Verify the commit-msg hook is registered: `pre-commit run --hook-stage commit-msg --commit-msg-filename /tmp/test-msg.txt` against a deliberately-bad message ("test"). The hook should reject with a non-zero exit code and the template printed to stderr.

Acceptance Test: `tests/structural/test_pre_commit_installed.py::test_hook_rejects_bad_message` — invokes the hook script directly with a synthetic bad message and asserts non-zero exit. (This test file is created in this milestone.)

### M5: Activate Claude Code hooks

Hook activation is a Tier C step: it changes the runtime behavior of the session itself. Add an "Awaiting Steering" entry below requesting the human to confirm hook activation. The human's resolution unlocks M6.

The activation step itself: copy `.claude/hooks/settings.json` into the user's Claude Code settings, or symlink it. Verify by attempting an Edit on `package.json` (a sensitive path) and confirming the PreToolUse hook blocks with the expected message.

Acceptance Test: human verification that an Edit attempt on `package.json` is blocked with the correct reason text. Recorded in this plan's Decision Log under "Decision: hook activation verified".

### M6: First-commit smoke test

Make a commit that lands the dep-vet records from M2. Use a properly-formatted commit message:

  harness(deps): add dep-vet records for seed devDependencies

  Plan: docs/plans/active/0001-bootstrap-validation.md#milestone-2
  Decision: implementation only

Push the commit. CI fires. All four CI jobs (`structural`, `typescript`, `dependency-graph`, `secrets`) should pass on first run.

Acceptance Test: `tests/structural/test_commit_messages.py::test_commits_follow_format` — passes when the recent git history contains only well-formed commits referencing real ExecPlans. CI green status on the first commit.

### M7: Self-archive

Move this ExecPlan from `docs/plans/active/0001-bootstrap-validation.md` to `docs/plans/completed/0001-bootstrap-validation.md`. Write the final entry in Outcomes & Retrospective below.

Acceptance Test: `tests/structural/test_bootstrap_complete.py::test_bootstrap_archived` — asserts the bootstrap plan is no longer in `active/` and is in `completed/`. (This test file is created in this milestone.)

Notes: do this in two commits — first writes Outcomes & Retrospective, second moves the file. The `Plan:` trailer in the move-commit references the path *as it was* (`docs/plans/active/...`); the structural test for commit messages handles this by also checking `completed/` and `archived/`.

## Progress

- [ ] M1: Validate the toolchain  (created 2026-05-02)
- [ ] M2: Dep-vet the seed devDependencies  (created 2026-05-02)
- [ ] M3: Verify all structural tests pass  (created 2026-05-02)
- [ ] M4: Install pre-commit and verify it rejects bad commits  (created 2026-05-02)
- [ ] M5: Activate Claude Code hooks  (created 2026-05-02)
- [ ] M6: First-commit smoke test  (created 2026-05-02)
- [ ] M7: Self-archive  (created 2026-05-02)

## Decision Log

### Decision: TypeScript on Node 20 with pnpm 9

Rationale: chosen by the human steerer at scaffold time. Node 20 is an active LTS line; pnpm 9 is the current stable major. Strictest available TypeScript settings (`strict`, `noUncheckedIndexedAccess`, `verbatimModuleSyntax`) are enabled to maximize the type-checker's catch rate during agent work.

Source: package.json:8-11 (engines block); tsconfig.json:5-9 (strict settings).

### Decision: Layered architecture enforced by dependency-cruiser AND a Python regex test

Rationale: dependency-cruiser provides full graph analysis (cycles, orphans, transitive); the Python test in `tests/structural/test_layering.py` provides a fast-feedback regex pass usable inside the structural test suite without requiring Node to be installed. Two layers of enforcement are intentional, not redundant: agents and CI may catch failures at different stages.

Source: .dependency-cruiser.cjs:11-90 (layered rules); tests/structural/test_layering.py:25-40 (LAYER_RANK and import regex).

### Decision: Harness scripts in Python, application in TypeScript

Rationale: Python is the lingua franca for tooling scripts and ships on every dev machine. Decoupling the harness from the application's runtime means the structural tests run even if `node_modules` is broken or the TypeScript build is failing.

Source: docs/conventions/deps-and-secrets.md:12-19 (dep-vetter design rationale).

### Decision: Self-hosted deploy via Docker; cloud target deferred

Rationale: human steerer specified self-hosted at scaffold time. A skeleton `Dockerfile` + `docker-compose.yml` are provided as starting points. The actual deploy environment (bare metal, NAS, VPS, k3s, etc.) is a Tier C decision that gets its own ExecPlan once application requirements are clearer.

Source: Dockerfile:1-26; docker-compose.yml:1-15.

### Decision: pnpm install seed devDependencies pre-vet

Rationale: bootstrapping the dep-vetter requires `package.json` and a working pnpm; vetting devDependencies after installation is logically inverted but operationally necessary. M2 retroactively runs the dep-vetter on the five seed packages so the structural test passes from M3 onward.

Confidence: low.
Revisit: by milestone-3.

### Dep-vet records (added during M2)

Each entry below is created when M2 produces the corresponding `.claude/decisions/dep-vet-<pkg>.md` file.

#### Decision: adopt @types/node@20.11.30

Rationale: required for any Node.js code to type-check. Pinned to a specific version to keep the type definitions stable until the human chooses a Node minor-version upgrade ExecPlan.

Source: .claude/decisions/dep-vet-@types-node.md

#### Decision: adopt dependency-cruiser@16.3.3

Rationale: enforces the layered architecture in CI. Chosen over alternatives like `madge` because it supports configurable rules, severity levels, and TypeScript path-alias resolution out of the box.

Source: .claude/decisions/dep-vet-dependency-cruiser.md

#### Decision: adopt eslint@8.57.0

Rationale: linter required for code style and basic correctness checks. ESLint 8.x is pinned because the 9.x flat-config migration is still in flux and would add bootstrap risk.

Source: .claude/decisions/dep-vet-eslint.md

#### Decision: adopt typescript@5.4.5

Rationale: required compiler for the `.ts` source. Pinned to 5.4.x so behavior of strict-mode checks is reproducible.

Source: .claude/decisions/dep-vet-typescript.md

#### Decision: adopt vitest@1.5.2

Rationale: test runner. Chosen over Jest for native ESM support, faster start, and tighter Vite ecosystem integration. Recorded HTTP transcripts (per verification-floor.md) will use `nock` or `msw` once an HTTP framework is selected.

Source: .claude/decisions/dep-vet-vitest.md

## Surprises & Discoveries

*(Empty until execution begins.)*

## Awaiting Steering

*(Empty. Will be populated at M5 to request hook activation confirmation.)*

## Outcomes & Retrospective

*(Written at M7. Empty until then.)*
