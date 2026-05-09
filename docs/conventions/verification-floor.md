# Verification Floor

No milestone is done until proof of behavior exists.

## Acceptance Test required per milestone

Every milestone in every ExecPlan has an `Acceptance Test:` line naming a specific runnable test that validates the milestone's externally observable property. The test is written first or in the same commit as the implementation. Untested milestones cannot have their checkbox flipped.

The test ID format is `path/to/test/file.test.ts > test description` (Vitest convention) or `path:line` for non-test verifications such as scripts.

## Externally observable property

Acceptance Tests must exercise something visible from outside the component-under-test:

- HTTP request → response (against the real Express handler, not a mocked controller)
- Database row written / read (against a real Postgres or SQLite, in a test container)
- File produced with expected contents
- UI element rendered (Playwright snapshot, accessibility tree, or rendered HTML assertion)
- Subprocess invocation with verified stdout / exit code

Not acceptable as the sole acceptance criterion:

- "Function returns the expected dict" alone
- "Mock was called with these arguments"
- "No exception was thrown"

## External integrations require recorded transcripts

For any test that crosses into a third-party API or service, record the HTTP exchange (`nock` for Node, `msw` for browser, or an equivalent) and commit the recording. Live-network tests do not count.

## Flakes are bugs, not nuisances

A flaky test does not pass for milestone purposes. The fix is a follow-up ExecPlan to stabilize it. Retrying CI does not flip the milestone checkbox.

## The Verifier subagent

When a Progress checkbox flips from `[ ]` to `[x]`, the Verifier subagent re-runs the named Acceptance Test in a clean checkout. On pass: writes "verified at SHA <sha>" to the Decision Log. On fail: reverts the checkbox flip and adds an entry to Surprises & Discoveries.

## What "clean checkout" means

The Verifier runs:

  git worktree add /tmp/verify-<sha> <sha>
  cd /tmp/verify-<sha>
  pnpm install --frozen-lockfile
  pnpm test --run -- <test-id>

It does not reuse the working tree's `node_modules`. It does not skip type checking. A clean run is the only run that counts.

Last reviewed: 2026-05-02
