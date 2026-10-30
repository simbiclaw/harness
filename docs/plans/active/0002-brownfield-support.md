# 0002-brownfield-support

## Purpose

The harness scaffold (CLAUDE.md, conventions, hooks, structural tests, dep-cruiser rules) assumes a greenfield repo — empty `src/`, no prior git history, no pre-existing dependencies. This plan adapts the enforcement tier so the same scaffold works in a brownfield repo with existing application code, legacy commits, and pre-existing dependencies, without a flag-day rewrite. The mechanism is scoped enforcement: a single config file (`harness-scope.json`) defines which paths are harness-managed, and every structural test, hook, and CI rule reads it. Legacy regions are governed by baselines with explicit ratchet targets.

This is not a brownfield adoption guide. It is the engineering work to make the harness itself support both modes.

## Big Picture

Four things change:

1. **A new scope file** (`.claude/harness-scope.json`) that every enforcement mechanism reads. It declares: which paths are harness-managed ("the beachhead"), which paths are legacy, and where baseline violation snapshots live.
2. **Structural tests gain a scope gate.** `test_layering.py`, `test_dep_decisions.py`, `test_commit_messages.py`, `test_no_forbidden_phrases.py`, and `test_decision_log_evidence.py` each gain a mode — greenfield (current behavior, repo-wide) vs. brownfield (scoped to harness-managed paths, baselined elsewhere).
3. **The dep-cruiser config and sensitive-paths hook** gain the same scope awareness. dep-cruiser rules are split into harness-managed (error) and legacy (warn or info). The PreToolUse hook's dep-vet guard gains an amnesty path for pre-existing packages.
4. **CLAUDE.md and BUILD-NOTES.md** gain a brownfield variant so the "What this repository is" section is truthful rather than aspirational.

In scope: the scope file schema, the structural test adaptations, the dep-cruiser config split, the PreToolUse amnesty path, the CLAUDE.md template update, and a brownfield bootstrap ExecPlan template.

Deliberately out of scope: rewriting any skill (dep-vetter, verifier, garbage-collector, doc-gardener — these are entropy managers that work identically in brownfield repos). Changing the PLANS.md rubric (it governs ExecPlans, not application code). Adding language-specific layer definitions beyond the current TypeScript/Node layering (that's a follow-up ExecPlan per stack).

## Milestones

### M1: Define the harness-scope.json schema and create the default (greenfield)

Create `.claude/harness-scope.json` with a schema that encodes: mode (`greenfield` or `brownfield`), harness-managed path globs, legacy path globs, baseline file locations, and ratchet deadlines. The default is greenfield — all paths are managed, no baselines needed. The file is itself listed in `sensitive-paths.txt` so agents cannot silently change the scope.

Acceptance Test: `tests/structural/test_harness_scope.py::test_scope_file_exists_and_valid` — asserts `.claude/harness-scope.json` exists, parses as JSON, and contains the required keys with valid values. Run via `pytest tests/structural/test_harness_scope.py -v`.

Notes: the schema must be forward-compatible so new enforcement mechanisms can add keys without breaking existing scope files. Use a `version: 1` field. The scope file is the single source of truth; no enforcement mechanism hardcodes path globs.

### M2: Adapt structural tests to read harness-scope.json

Each of the five structural tests gains a mode switch:

- **Greenfield mode** (`mode: "greenfield"`): current behavior, unchanged. All paths enforced.
- **Brownfield mode** (`mode: "brownfield"`): enforcement applies only to files matching `managed_paths` globs. Files matching `legacy_paths` are skipped. If a `baselines` entry exists for a test, violations in legacy paths are checked against the baseline snapshot — existing violations pass, new violations fail.

The adaptation is additive: each test reads the scope file once at import time, gates its assertions behind `is_managed_path()` checks, and optionally diffs against a committed baseline JSON file.

Acceptance Test: `tests/structural/test_layering.py::test_layer_imports_flow_upward` — passes in greenfield mode (default scope file). A companion test `tests/structural/test_harness_scope.py::test_brownfield_mode_skips_legacy_paths` creates a temporary legacy file with a deliberate layer violation and asserts no failure.

Notes: the baseline diff logic is a single shared helper in `tests/structural/scope_helpers.py`. Each test's baseline (if any) lives at `.claude/baselines/<test-name>.json` and is a set of violation fingerprints (file:line:rule). The baseline may only shrink; the structural test fails if a baseline grows.

### M3: Split dep-cruiser rules by scope

The `.dependency-cruiser.cjs` gains a `brownfield` mode section. In greenfield mode, all rules apply at `severity: "error"` repo-wide (current behavior). In brownfield mode:

- Harness-managed paths get the full layer rules at `error`.
- Legacy paths get the same rules at `warn` (visibility without blocking CI).
- A `no-new-legacy-violations` rule runs at `error` against legacy paths, diffed against a committed baseline (same pattern as M2's structural tests).

The dep-cruiser config reads `harness-scope.json` via a small JS helper at the top of the config file.

Acceptance Test: `tests/structural/test_harness_scope.py::test_depcruiser_config_matches_scope` — parses `.dependency-cruiser.cjs`, extracts the path globs from its `forbidden` rules, and asserts they match `harness-scope.json`'s `managed_paths`. In CI: the `dependency-graph` job runs `pnpm depcruise` and exits 0 in both modes.

Notes: dependency-cruiser 16.x does not natively support baseline files, so the baseline diff runs as a separate step in CI (a small Python script that compares depcruiser's JSON output against `.claude/baselines/depcruiser.json`).

### M4: Add dep-amnesty path to PreToolUse hook

The PreToolUse hook's package-manager guard (Guard 2) gains an amnesty path:

- If `harness-scope.json` mode is `brownfield` and a `.claude/decisions/dep-baseline-<date>.md` file exists, packages listed in that file as "pre-existing, not vetted at adoption" are allowed without a dep-vet record.
- Upgrades to pre-existing packages (same package name, different version) require a lighter vet record: CVE diff check and breaking-changes diff only, not the full four-check vet.
- New packages (not in the amnesty list) require the full dep-vet as before.

The amnesty file is generated once at adoption time and is itself listed in `sensitive-paths.txt`.

Acceptance Test: `tests/structural/test_harness_scope.py::test_dep_amnesty_file_valid` — asserts the amnesty file (if present) lists only packages that exist in `package.json` and has the required date and rationale fields. A second test asserts that packages in the amnesty file are skipped by `test_dep_decisions.py` in brownfield mode.

### M5: Update CLAUDE.md and BUILD-NOTES.md for dual-mode

CLAUDE.md's "What this repository is" section currently asserts "There is no human-written application code in `src/`." Replace with a conditional: when `harness-scope.json` mode is `brownfield`, the section reads from a brownfield variant that describes existing application code + partial harness adoption + named harness-managed regions.

Add a new convention file: `docs/conventions/brownfield-adoption.md` documenting the beachhead + baseline + ratchet pattern, the three-tier adoption model (docs tier verbatim, enforcement tier scoped, src tier with managed vs. legacy regions), and the anti-patterns (no flag-day rewrites, no disabled hooks without ratchet targets, no legacy quirks in CLAUDE.md).

Acceptance Test: `tests/structural/test_no_forbidden_phrases.py` run against `docs/conventions/brownfield-adoption.md` — passes. `tests/structural/test_harness_scope.py::test_claude_md_matches_mode` — asserts CLAUDE.md's "What this repository is" section references brownfield when mode is brownfield, greenfield when greenfield.

### M6: Create the brownfield bootstrap ExecPlan template

Create `docs/plans/templates/0001-brownfield-adoption.md` — a template ExecPlan following the PLANS.md rubric with pre-filled milestones:

- M1: Repo inventory + layer reverse-engineering → `BUILD-NOTES.md` reverse-edition.
- M2: Document tier in place, CLAUDE.md edited for brownfield.
- M3: Beachhead chosen, `harness-scope.json` populated, hooks/CI scoped.
- M4: Baseline files generated; ratchet targets recorded in Decision Log.
- M5: Dep amnesty decision recorded; PreToolUse hook live.
- M6: First feature ExecPlan inside the beachhead, end-to-end.

Each milestone has an Acceptance Test line and Notes block. The template is explicitly a template — it contains placeholder paths (`<beachhead-glob>`, `<legacy-glob>`) that the adopter replaces. The structural tests treat `docs/plans/templates/` as exempt from enforcement.

Acceptance Test: `tests/structural/test_plan_templates_valid.py::test_brownfield_template_follows_rubric` — asserts the template has all eight required sections, at least one milestone with an Acceptance Test line, and no forbidden phrases in any Decision Log entry.

### M7: Validate end-to-end with a simulated brownfield repo

Create a script at `tests/fixtures/simulate-brownfield.sh` that:

1. Copies the harness scaffold into a temp directory.
2. Creates a simulated legacy `src/` with deliberate layer violations, legacy commits without trailers, and pre-existing dependencies.
3. Sets `harness-scope.json` to brownfield mode with `src/new-feature/` as the beachhead.
4. Runs the full structural test suite and asserts all pass (legacy violations baselined, beachhead enforced).
5. Runs `pnpm depcruise` and asserts exit 0 (legacy warnings, no new errors).
6. Creates a new file in the beachhead with a layer violation and asserts the structural test fails.
7. Creates a new legacy file with a *new* layer violation (not in baseline) and asserts the baseline-diff test fails.

Acceptance Test: the script itself. `tests/structural/test_harness_scope.py::test_brownfield_simulation` — runs `tests/fixtures/simulate-brownfield.sh` and asserts exit 0.

Notes: this is the most important milestone. If the simulation doesn't pass, the brownfield support doesn't work. The simulation is intentionally small (~50 lines of legacy TS, 3 legacy commits, 2 pre-existing deps) so it runs in under 10 seconds.

## Progress

- [x] M1: Define the harness-scope.json schema and create the default (greenfield)  (done 2026-05-30)
- [x] M2: Adapt structural tests to read harness-scope.json  (done 2026-05-30)
- [x] M3: Split dep-cruiser rules by scope  (done 2026-05-30)
- [x] M4: Add dep-amnesty path to PreToolUse hook  (done 2026-05-30)
- [x] M5: Update CLAUDE.md and BUILD-NOTES.md for dual-mode  (done 2026-05-30)
- [x] M6: Create the brownfield bootstrap ExecPlan template  (done 2026-05-30)
- [x] M7: Validate end-to-end with a simulated brownfield repo  (done 2026-05-30)

## Decision Log

### Decision: Single scope file rather than per-mechanism config

Rationale: if every structural test, hook, and CI rule had its own scope configuration, brownfield adopters would need to edit 5+ files to set up the beachhead, and keeping them in sync would be a recurring source of drift. A single `harness-scope.json` read by every mechanism means the beachhead is declared once. This does create a coupling point — every mechanism depends on the scope file's schema — but the alternative (N independent configs) has higher operational cost and worse failure modes (partial enforcement).

Source: docs/conventions/brownfield-adoption.md (created in M5).

### Decision: Baseline files are committed JSON, not generated on-the-fly

Rationale: a committed baseline is auditable in git history, diffable in PR review, and can't silently drift. Generating baselines dynamically (e.g., "run depcruiser, save output, diff against it") would mean the baseline changes every time the legacy code changes, defeating the point. Committed baselines make the ratchet explicit: shrinking a baseline is a commit with a Decision Log entry explaining which violations were fixed and how.

Confidence: low.
Revisit: by milestone-7 (validate with simulation — if the baseline-diff UX is too painful in practice, switch to auto-generated with a manual approval gate).

### Decision: Brownfield mode is opt-in via harness-scope.json, not auto-detected

Rationale: auto-detecting brownfield (e.g., "does `src/` have files in it?") would be fragile — a greenfield repo mid-bootstrap has files in `src/` too, and a brownfield repo might have an empty `src/some-module/`. Explicit mode declaration avoids heuristics. The default is `greenfield` so the bootstrap ExecPlan (0001) works unchanged.

Source: harness-scope.json schema (created in M1).

### Decision: dep-cruiser legacy rules at `warn`, not `info`

Rationale: `warn` produces visible output in CI without failing the build. `info` is easy to ignore. The goal in brownfield mode is for legacy violations to be visible enough that teams feel pressure to shrink the baseline, but not so visible that they block unrelated PRs. `warn` hits that balance. Individual teams can override to `error` when their ratchet target is reached.

Source: .dependency-cruiser.cjs (modified in M3).

### Decision: Python scope_helpers.py shared module rather than per-test duplication

Rationale: every structural test needs the same three operations — read scope file, check if path is managed, diff against baseline. A shared helper avoids five copies of the same JSON-load and glob-match logic. The helper is under `tests/structural/` so it's discoverable; it is not under `src/` because harness tooling is Python per the existing harness-scripts-in-Python decision.

Source: tests/structural/scope_helpers.py (created in M2).

## Surprises & Discoveries

*(Empty until execution begins.)*

## Awaiting Steering

*(Empty. The scope file schema choice in M1 may need steering if the human prefers a different config format.)*

## Outcomes & Retrospective

*(Written at M7. Empty until then.)*
