# Brownfield Adoption

How to adopt the harness engineering scaffold in an existing (brownfield) codebase with pre-existing application code, legacy commits, and dependencies. The harness's philosophy (ExecPlans, Decision Logs, structural enforcement, promotion rule, entropy management) is brownfield-ready as written. What needs adapting is the enforcement scope.

## The three-tier adoption model

The harness has three layers and they brownfield-adopt very differently:

### `docs/` — system of record

Pure additive. Copy `CLAUDE.md`, `docs/PLANS.md`, and the five convention files verbatim. The conventions govern *new work* via ExecPlans, so legacy code isn't retroactively in violation. The only file that needs editing is CLAUDE.md's "What this repository is" section — make it truthful about existing code + partial harness adoption + named harness-managed regions.

Legacy quirks go in scoped convention files (`docs/conventions/legacy-<area>.md`), not in CLAUDE.md. CLAUDE.md is a table of contents, not an encyclopedia.

### `.claude/` — enforcement runtime

This tier will fail against legacy code on day one unless scoped. The mechanism is `.claude/harness-scope.json` — a single config file that declares which paths are harness-managed (the "beachhead") and which are legacy. Every structural test, hook, and CI rule reads it.

### `src/` — the application

Cannot be "no human-written code" in a brownfield repo. Use a region model: harness-managed regions vs. legacy regions, declared in `harness-scope.json`'s `managed_paths` and `legacy_paths` globs.

## The beachhead pattern

Pick one bounded area that gets the full harness from day one: a new feature module, a bounded-context extraction, or the next rewrite target. Everything in `.claude/` runs against globs that include only the beachhead initially.

Outside the beachhead, the harness is documentary only. Expansion is itself an ExecPlan:

> Promote `src/payments/**` from legacy to harness-managed, with baseline of N violations and a 30-day ratchet to zero.

## The baseline pattern

For rules that you want repo-wide but can't enforce immediately, use baselines instead of flag-day rewrites:

1. Generate a one-time snapshot of existing violations.
2. New violations fail CI; baselined violations pass.
3. The baseline shrinks monotonically — never grows. Each shrink is a Decision Log entry.

Concretely:

- **Layered-import structural test**: scope to harness-managed regions; baseline violations elsewhere.
- **Commit-trailer structural test**: apply to commits matching specific authors (Claude, co-authored-by Claude Code) or branches (`claude/*`, `feat/*`).
- **Forbidden-phrases structural test**: scope to `docs/plans/**` (new ExecPlans), not legacy docs.

## The ratchet pattern

Every baseline has an explicit ratchet target recorded as a Decision Log entry:

> Baselined 247 layer violations on 2026-05-30; target zero by 2026-08-01.

Without a ratchet target, baselines become permanent amnesty and the rule effectively dies. The structural tests enforce that baselines may only shrink — never grow. A baseline that grows is a test failure.

## Dep-amnesty for pre-existing packages

Generate `.claude/decisions/dep-baseline-YYYY-MM-DD.md` listing every direct dependency marked "pre-existing, not vetted at adoption." The PreToolUse hook's dep-vet guard reads this file:

- **Pre-existing package** (in amnesty list): allowed without full vet.
- **Upgrade to pre-existing package**: lighter vet (CVE diff, breaking-changes diff).
- **New package** (not in amnesty): full four-check vet required.

Secrets rules (gitleaks via pre-commit) apply repo-wide from day one — a leaked secret is a leaked secret regardless of region. No baseline.

## The brownfield bootstrap ExecPlan

Use the template at `docs/plans/templates/0001-brownfield-adoption.md` which covers:

1. Repo inventory + layer reverse-engineering.
2. Document tier in place, CLAUDE.md edited.
3. Beachhead chosen, `harness-scope.json` populated, hooks/CI scoped.
4. Baseline files generated; ratchet targets recorded.
5. Dep amnesty decision recorded; PreToolUse hook live.
6. First feature ExecPlan inside the beachhead, end-to-end.

## What to deliberately not do

- **Don't bring the whole repo into compliance in one PR.** The promotion rule (doc → structural test → hook → CI gate) still applies. Rules earn enforcement gradually.
- **Don't disable hooks "temporarily"** without a written ratchet target. That's how rules die.
- **Don't put legacy quirks in CLAUDE.md.** They go in scoped convention files, referenced only when relevant.
- **Don't count legacy-region violations** toward the promotion rule's "violated twice → promote leftward" trigger. Legacy noise swamps the signal.

## Adapting the layer model

If your brownfield isn't TypeScript/Node with `types → config → repo → service → runtime → ui` layers, swap the engine:

| Stack | Tool |
|-------|------|
| Python | `import-linter` |
| Java/Kotlin | `archunit` |
| Go | `arch-go` |

The *concept* — layered architecture enforced by a structural test — carries. The tool is incidental. Define your actual layers in `harness-scope.json` and write the corresponding dep-cruiser (or equivalent) rules to match.

Last reviewed: 2026-05-30.
