# PLANS.md — the ExecPlan rubric

This file defines the shape every ExecPlan in this repository takes. It is read once when an ExecPlan is being created or substantially edited, then released from session context. Reading this file is mandatory before authoring or modifying any plan; it is not required for routine implementation work that does not touch a plan.

## What an ExecPlan is

A living document that captures one unit of feature-scale work. It is written *before* the work begins, edited continuously *during* the work, and archived *after* the work ships. It is the single source of truth for: why this work, what it produces, what was decided along the way, what surprised us, and how it ended up.

ExecPlans are not specs handed down from above. The agent assigned to execute the plan is also responsible for keeping it current. State that lives only in the chat transcript or only in the git log is state that the next session — fresh agent, fresh context — cannot recover. The plan is what survives.

## File location and lifecycle

A new ExecPlan lives at `docs/plans/active/NNNN-<slug>.md`, where `NNNN` is the next free four-digit number. When the work ships, the file moves to `docs/plans/completed/`. If the work is cancelled or absorbed into another plan, it moves to `docs/plans/archived/` with a final entry in Outcomes & Retrospective explaining why.

A plan should be created when work is at least feature-sized: more than one commit, more than one logical step, or any work touching a Tier C path (see `conventions/ask-threshold.md`). One-line typo fixes do not need a plan. A new endpoint, a schema change, a refactor across files, anything user-visible: yes.

## Required sections, in order

The sections below appear in every ExecPlan. Empty sections are kept (with a single italic note explaining the absence) rather than omitted, so the structure is immediately recognizable to a fresh reader.

### 1. Purpose

One paragraph. Prose. What user-visible problem does this work solve, and why now? If you cannot write this paragraph without referring to internal architecture, the plan is too low-level — split it.

### 2. Big Picture

The architectural view. What components are touched. What is in scope. What is *deliberately* out of scope (this matters more than what is in). If the work has natural extensions you are choosing not to do, name them here so the next reader does not redo the analysis.

### 3. Milestones

A numbered list. Each milestone is a coherent shippable unit of progress, typically one to five commits. Each milestone has:

- A one-sentence description in imperative mood ("Add the `/orders` endpoint").
- An `Acceptance Test:` line naming a runnable test (path:test_name) that, when it passes, proves the milestone is done. The test exists by the time the milestone's checkbox flips. Untested milestones do not flip.
- An optional `Notes:` block for implementation hints, gotchas, or dependencies on other milestones.

Milestones are sized so that the agent can complete one without exhausting its context. If a milestone is too big, split it.

### 4. Progress

Checklist. The *only* mandatory-bullet section. Each item is a milestone from section 3, with a checkbox and a timestamp:

```
- [ ] M1: Add the /orders endpoint  (created 2026-05-02)
- [x] M2: Add order schema validation  (done 2026-05-03 14:30 PT)
- [ ] M3: Add idempotency keys  (in progress, started 2026-05-03 15:00 PT)
```

Each flip of `[ ]` to `[x]` is its own commit (see `commit-hygiene.md`). The PostToolUse hook will remind you. The Verifier subagent re-runs the Acceptance Test before the flip is considered final.

### 5. Decision Log

Every consequential decision made during execution gets an entry. "Consequential" means: another reasonable agent could have made a different call, *and* the call affects something downstream. Choosing variable names is not consequential. Choosing UUID v4 vs v7 is consequential.

Entries are H3-headed (`### Decision: <one-line>`) and contain a Rationale shaped according to `conventions/i-dont-know-protocol.md`:

- `Source: <URL or path:line>` — cited
- `Experiment: docs/experiments/<name>/` — empirical
- `Confidence: low` + `Revisit: <milestone or date>` — explicit guess

Forbidden phrases ("standard approach", "best practice", etc.) are enforced by structural test. See the protocol doc.

### 6. Surprises & Discoveries

Anything the plan did not predict. New constraints surfaced during work. Bugs in dependencies. Misunderstandings about the API. Things the next reader picking up this plan should know that they would not derive from the code.

This section is also where the Verifier subagent records milestone-flip failures. If a milestone's Acceptance Test failed on flip, the failure shows up here, not in Progress.

### 7. Awaiting Steering

Empty by default. Populated when the plan hits a Tier C decision and pauses for the human. Each entry names the question, the options under consideration, and the deadline by which a non-decision will be treated as one of the options. When the human resolves it, the entry is updated to start with `Awaiting Steering: resolved` (the PreToolUse hook keys on this string).

### 8. Outcomes & Retrospective

Written at completion or cancellation. What shipped vs. what was planned. What took longer than expected and why. What you would do differently. One paragraph minimum; no upper limit. The garbage-collector and doc-gardener skills periodically read these to learn patterns; treat the section as feedback into the harness, not as ceremony.

## Style rules

- **Prose over lists** outside Progress and Milestones. Bullets fragment thought; prose forces you to articulate the *why*. The exceptions are the two sections where structure matters more than reasoning.
- **One fenced markdown block max** per file. ExecPlans are read inside other tools that may not handle nested fences gracefully.
- **Self-contained**. Every term of art used in the plan is defined either in the plan itself or in a linked file. Assume the next reader is a fresh agent or a fresh human with no chat-transcript memory.
- **Edited during execution**, not just at start and end. The Decision Log and Surprises sections grow as work proceeds. A plan that has not been touched in days is suspicious; the doc-gardener will flag it.
- **Filename includes a slug**, not just a number. `0023-add-orders-endpoint.md`, not `0023.md`. The slug is searchable in commit messages and reduces cross-reference errors.

## What an ExecPlan is not

- Not a specification of system architecture. Architectural rules live in `docs/conventions/` and in structural tests under `.claude/tests/`. A plan inherits them; it does not redefine them.
- Not a substitute for code review. The plan tracks decisions and progress; it does not prove the implementation is correct. The Acceptance Tests do that.
- Not a status report for the human. The human reads commit messages and Progress checkboxes for status. The plan's audience is the *next agent that picks it up*, which may be a fresh session of yourself.
- Not write-once. If the plan turns out to be wrong about scope or approach, edit it. Mark the change in Decision Log with rationale. Do not invent a new plan to escape an old one's commitments.

## How a session uses an ExecPlan

A typical session loop:

1. Read the most recent active plan end-to-end. Read Surprises & Discoveries first; it tells you what you do not yet know.
2. Identify the next unflipped milestone. Read its Acceptance Test. If the test does not exist, create it first, in its own commit.
3. Implement against the test. Commit when the test passes. Flip the checkbox in a separate commit.
4. The Verifier runs. On pass, the flip stands. On fail, the flip reverts and an entry appears in Surprises.
5. If you make a consequential decision en route, add it to Decision Log with a properly-shaped Rationale.
6. If you hit a Tier C question, stop, add to Awaiting Steering, and end the session.

## When this rubric is wrong

The PLANS.md rubric itself is documentation. If you find that the structure here gets in the way more than it helps — for example, the Awaiting Steering section adds friction for plans that never hit Tier C — flag it as a Surprise in the affected ExecPlan and propose a rubric change. The doc-gardener will surface the proposal. The rubric is itself subject to the promotion rule: if a structural part of it is consistently violated or ignored, that is a signal the rubric is failing.

Last reviewed: 2026-05-02.
