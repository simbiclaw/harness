---
name: doc-gardener
description: Recurring custodial agent. Walks docs/conventions/, CLAUDE.md, and docs/PLANS.md for staleness, broken cross-references, and past-deadline Confidence-low entries. Opens an ExecPlan if any check fails.
---

# Doc-Gardener Skill

## When to use this skill

Weekly via cron. Also on-demand when a human says "review the docs".

## Checks

### Cross-reference integrity

For every Markdown file under `docs/` and `CLAUDE.md`, every `path:line` reference, every `docs/...` or `.claude/...` link, and every `https://` URL: verify it resolves. For in-repo paths, check that the file exists. For URLs, do a HEAD request and verify a 2xx or 3xx status (do not chase redirects further than 3 hops).

### Last-reviewed staleness

Every convention doc has a `Last reviewed: YYYY-MM-DD` footer. Anything more than 90 days old is flagged.

### Past-deadline Confidence-low entries

Walk every Decision Log entry with `Confidence: low`. If the corresponding `Revisit:` deadline has passed (date or milestone reached), flag it.

### Citation domain quality

For `Source:` URLs, flag domains that look like aggregators or generic "top 10" articles (medium.com, dev.to, geeksforgeeks.org, freecodecamp.org), unless the citation is itself the original primary source for that topic. This is a soft warning, not a failure.

### Override-token audit

Walk `git log --grep='\[dep-override-approved-by-human\]'` for the last 90 days. Each match is surfaced for review — overrides should be rare and explicable.

## Output

If ANY check fails, open `docs/plans/active/NNNN-doc-garden-<date>.md` listing the failures as Milestones. Each milestone has a clear remediation (update the link, refresh the doc, run the experiment, etc.).

Last reviewed: 2026-05-02
