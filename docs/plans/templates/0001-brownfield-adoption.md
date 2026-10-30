# 0001-brownfield-adoption

## Purpose

Adopt the harness engineering scaffold (CLAUDE.md, conventions, hooks, structural tests, dep-cruiser rules, CI workflow) into an existing (brownfield) codebase with pre-existing application code, legacy commits, and dependencies. This plan bootstraps the harness through inventory, scoping, baselining, and a beachhead smoke test — without a flag-day rewrite or retrofitting years of git history.

This is the brownfield equivalent of the greenfield `0001-bootstrap-validation.md`. Where the greenfield bootstrap validates an empty scaffold, this plan discovers the existing repo's shape, declares the beachhead, and sets up scoped enforcement.

## Big Picture

Six milestones move the repo from "no harness" to "harness active in the beachhead":

1. Inventory the existing codebase and reverse-engineer the real layer graph.
2. Install the document tier (CLAUDE.md, conventions) edited for brownfield truth.
3. Choose a beachhead and populate `.claude/harness-scope.json`.
4. Generate baseline violation snapshots with ratchet targets.
5. Record dep amnesty for pre-existing packages; activate hooks.
6. Execute one feature ExecPlan inside the beachhead, end-to-end.

In scope: the six milestones above, producing a repo where new work in the beachhead is fully harness-governed.

Deliberately out of scope: bringing legacy regions into compliance (that's follow-up ExecPlans, one per region). Rewriting the layer model for a non-TypeScript stack (that's a separate plan — adapt the dep-cruiser equivalent for your stack first). Retrofitting `Plan:`/`Decision:` trailers onto existing git history (that is explicitly not a goal).

## Milestones

### M1: Repo inventory and layer reverse-engineering

Produce a reverse-edition `BUILD-NOTES.md` documenting:
- What stack the repo actually uses (language, package manager, build tool, test runner).
- What the real layering looks like — run your stack's equivalent of `depcruise --output-type dot | dot -Tsvg` and describe the actual import graph.
- What layers exist, where the cycles are, what the natural boundaries are.
- Which decisions the existing codebase has already made on your behalf (so the harness's documentation tier reflects reality, not scaffold defaults).

Acceptance Test: `BUILD-NOTES.md` exists, contains the five sections listed above, and accurately describes the current repo's stack and architecture. Run `tests/structural/test_plan_templates_valid.py::test_brownfield_template_follows_rubric` (this validates the plan structure; the content is validated by human review of BUILD-NOTES.md).

Notes: this is the most important milestone. If the inventory is wrong, every subsequent milestone builds on a false premise. Be honest about cycles and architectural issues — the baseline in M4 exists precisely to acknowledge them without blocking progress.

### M2: Document tier in place

Copy or adapt from the harness scaffold:
- `CLAUDE.md` — edit the "What this repository is" section to truthfully describe the existing application + partial harness adoption + named harness-managed regions.
- `docs/PLANS.md` — copy verbatim (governs new ExecPlans only).
- `docs/conventions/ask-threshold.md` — copy verbatim.
- `docs/conventions/verification-floor.md` — copy verbatim.
- `docs/conventions/deps-and-secrets.md` — copy verbatim (dep-amnesty in M5 handles pre-existing deps).
- `docs/conventions/commit-hygiene.md` — copy verbatim (commit scoping in M4 handles legacy commits).
- `docs/conventions/i-dont-know-protocol.md` — copy verbatim.
- `docs/conventions/brownfield-adoption.md` — copy verbatim (reference document).

Legacy quirks discovered in M1 go in `docs/conventions/legacy-<area>.md`, not in CLAUDE.md.

Acceptance Test: all eight files listed above exist in `docs/`. `tests/structural/test_no_forbidden_phrases.py` passes (checks all plan files for forbidden phrases). `tests/structural/test_harness_scope.py::test_claude_md_acknowledges_both_modes` passes.

### M3: Beachhead selection and scope configuration

Choose one bounded area as the beachhead — a new feature module, a bounded-context extraction, or the next rewrite target. Populate `.claude/harness-scope.json`:

```json
{
  "version": 1,
  "mode": "brownfield",
  "managed_paths": ["<beachhead-glob>"],
  "legacy_paths": ["<legacy-glob-1>", "<legacy-glob-2>"],
  "baselines": {}
}
```

Add `.claude/baselines/` directory (committed). Update `.claude/sensitive-paths.txt` to include `.claude/harness-scope.json` and `.claude/baselines/**`.

Acceptance Test: `tests/structural/test_harness_scope.py::test_scope_file_exists_and_valid` passes. `managed_paths` is non-empty. Each glob in `managed_paths` matches at least one existing file in the repo (verify manually or with `ls <beachhead-glob>`).

Notes: the beachhead should be small enough that its violations can be brought to zero in under 30 days. A single new feature module is ideal. Don't make the beachhead too large — you can expand it later via ExecPlan.

### M4: Baseline generation and ratchet targets

For each structural test that would fail on legacy code, generate a baseline:

1. Run `tests/structural/test_layering.py` against legacy paths — capture the violation set.
2. Save to `.claude/baselines/test_layering.json` as a sorted JSON array.
3. Repeat for any other structural tests that produce legacy failures.
4. Record each baseline in this plan's Decision Log with an explicit ratchet target.

The baselines are committed. The structural tests now pass (known violations filtered, new violations caught).

Acceptance Test: `tests/structural/test_layering.py` passes (even though legacy violations exist — they're baselined). `tests/structural/test_harness_scope.py::test_baseline_check_filters_known_violations` passes.

### M5: Dep amnesty and hook activation

Generate `.claude/decisions/dep-baseline-YYYY-MM-DD.md` listing every direct dependency with the annotation "pre-existing, not vetted at adoption." Install pre-commit hooks (`pre-commit install --install-hooks`). Activate Claude Code hooks per the greenfield bootstrap M5 procedure.

Acceptance Test: `tests/structural/test_dep_decisions.py` passes (amnesty packages are skipped). `tests/structural/test_harness_scope.py::test_dep_amnesty_file_valid` passes (amnesty file lists only packages from package.json). Pre-commit hook rejects a deliberately bad commit message.

### M6: First feature ExecPlan in the beachhead

Write and execute one feature ExecPlan entirely inside the beachhead, following the full harness: plan written first, TDD, Acceptance Test per milestone, commit trailers, Decision Log with shaped rationales. This is the smoke test that proves the harness is operational in the beachhead.

Acceptance Test: the feature ExecPlan's milestones all have flipped checkboxes with passing Acceptance Tests. The Verifier subagent confirms each flip. CI is green on all commits. The plan moves to `docs/plans/completed/`.

Notes: pick the smallest meaningful feature — a single endpoint, a single UI component, a single config migration. The goal is end-to-end harness validation, not feature scope.

## Progress

- [ ] M1: Repo inventory and layer reverse-engineering  (created <date>)
- [ ] M2: Document tier in place  (created <date>)
- [ ] M3: Beachhead selection and scope configuration  (created <date>)
- [ ] M4: Baseline generation and ratchet targets  (created <date>)
- [ ] M5: Dep amnesty and hook activation  (created <date>)
- [ ] M6: First feature ExecPlan in the beachhead  (created <date>)

## Decision Log

### Decision: Brownfield bootstrap follows the same PLANS.md rubric as feature ExecPlans

Rationale: the brownfield adoption is itself feature-scale work — multiple commits, multiple logical steps, Tier C paths touched. It deserves the same structure (Purpose, Big Picture, Milestones, Progress, Decision Log, Surprises, Awaiting Steering, Outcomes) rather than a separate format.

Source: docs/PLANS.md:15-18 (what an ExecPlan is).

### Decision: Managed and legacy regions declared via path globs, not per-file markers

Rationale: per-file markers (e.g., `// @harness-managed` comments) would require editing legacy files to opt out, defeating the "no flag-day rewrite" goal. Path globs in a single config file achieve the same scoping without touching legacy code. The tradeoff is granularity — you can't mark individual files within a directory as managed — but the beachhead pattern expects whole directories to be managed, so this is not a practical limitation.

Confidence: low.
Revisit: by milestone-6. If the glob-based approach proves too coarse in practice, per-file markers can be layered on top without removing the glob system.

### Decision: Baseline files use sorted JSON arrays of violation fingerprints

Rationale: JSON is trivially diffable in git, sortable for determinism, and parseable by both Python structural tests and the dep-cruiser baseline script without additional dependencies. The fingerprint format (`file:line: violation description`) is human-readable and stable across runs of the same tool.

Source: .claude/scripts/depcruiser-baseline-diff.py (the reference baseline-diff implementation).

### Decision: Dep-amnesty file format is markdown, not JSON

Rationale: the amnesty file is read by both the PreToolUse hook (Python) and the dep-decisions structural test (Python), but it's also the human-readable record of why each pre-existing dependency exists. Markdown with a simple list format (`- <package> — pre-existing, not vetted at adoption`) is more accessible than JSON for audit and review. The parsing is a trivial line-by-line scan.

Source: .claude/hooks/pre_tool_use.py (Guard 2 amnesty logic).

## Surprises & Discoveries

*(Empty until execution begins.)*

## Awaiting Steering

### Decision required: beachhead selection

The beachhead (<beachhead-glob> in M3) must be chosen by the human steerer. Options:
- A new feature module not yet started (cleanest — no legacy violations to baseline).
- A bounded-context extraction from existing code (more work up front, but proves the harness works on real code).
- The next rewrite target (highest impact, most complex).

Deadline: before M3 execution. If no decision by <date + 7 days>, default to the smallest new-feature option.

## Outcomes & Retrospective

*(Written at M6. Empty until then.)*
