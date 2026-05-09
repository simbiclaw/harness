---
name: dep-vetter
description: Vet a candidate npm package against the four-check policy (age, weekly downloads, recent commits, license). Triggered by the PreToolUse hook when a package install is detected, or invoked manually before adding a new dependency. Writes the result to .claude/decisions/dep-vet-<pkg>.md.
---

# Dep-Vetter Skill

## When to use this skill

Before adding any direct dependency to `package.json`, or when the PreToolUse hook blocks a package install with a "no dep-vet record" message.

## Inputs

- Package name (string, e.g. `zod` or `@types/node`)

## Process

1. Fetch package metadata from the npm registry:

  https://registry.npmjs.org/<encoded-pkg>

  For scoped packages, encode the slash: `@types/node` -> `@types%2Fnode`.

2. Fetch download stats:

  https://api.npmjs.org/downloads/point/last-week/<encoded-pkg>

3. From the metadata, extract `repository.url`. If the URL is GitHub, fetch the most recent commit timestamp from:

  https://api.github.com/repos/<owner>/<repo>/commits?per_page=1

  If the repository is on a non-GitHub host (GitLab, Bitbucket, Codeberg), use the equivalent API; if no API is accessible, mark this check as INCONCLUSIVE and require human override.

4. Check the `license` field in the metadata against the allowed list:

  MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, MPL-2.0

  SPDX expressions like `(MIT OR Apache-2.0)` are accepted if all listed licenses are in the allowed list. `UNLICENSED` is a hard reject.

## Decision rules

- Age: more than 30 days since first publish (use `time.created` in metadata).
- Downloads: more than 1000 per week.
- Activity: most recent commit within 90 days.
- License: in the allowed list.

ALL must pass. Any single failure = REJECT.

## Output

Write `.claude/decisions/dep-vet-<sanitized-pkg>.md` with this structure (where `<sanitized-pkg>` replaces `/` with `-`, so `@types/node` becomes `@types-node`):

  # Dep-vet: <pkg>

  Decision: APPROVED | REJECTED
  Date: <YYYY-MM-DD>

  ## Metadata
  Ecosystem: npm
  First published: <date>
  Latest version: <version>
  License: <SPDX ID or expression>
  Source: <repository URL>

  ## Checks
  Age:        <PASS|FAIL> (<N> days since first publish)
  Downloads:  <PASS|FAIL> (<N>/week)
  Activity:   <PASS|FAIL|INCONCLUSIVE> (last commit <N> days ago)
  License:    <PASS|FAIL> (<SPDX ID>)

  ## Rationale
  <one paragraph: why this dependency is needed for the work; what
   alternatives were considered; why this one wins>

  ## Source
  https://www.npmjs.com/package/<pkg>

## On REJECT

Do NOT proceed with the install. Open a section in the active ExecPlan explaining the rejection and proposing alternatives. Wait for human steering. Override only via commit message containing `[dep-override-approved-by-human]`.

## On INCONCLUSIVE

Same as REJECT: do not proceed. The human can override after manual review.

Last reviewed: 2026-05-02
