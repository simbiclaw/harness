# The "I Don't Know" Protocol

When Claude Code makes a decision under uncertainty, it cites evidence or flags the uncertainty explicitly. Generic confidence is a bug.

## Every Decision Log entry has a Rationale

The Rationale must be one of three shapes.

### Cited

  Rationale: <one-sentence explanation>.
  Source: <URL or path:lineRange>

Example:

  Rationale: chose UUID v7 because it preserves time-ordering for database
  index efficiency.
  Source: https://www.rfc-editor.org/rfc/rfc9562.html#name-uuid-version-7

### Empirical

  Rationale: <one-sentence explanation>.
  Experiment: docs/experiments/<NNNN>-<name>/

The experiment directory contains a runnable script and the captured output that demonstrates the property the decision rests on.

Example:

  Rationale: chose Postgres over SQLite because measured concurrent write
  throughput exceeded SQLite's serialized write ceiling.
  Experiment: docs/experiments/0007-write-throughput/

### Marked-as-guess

  Rationale: <one-sentence>. Confidence: low.
  Revisit: by milestone-NNN | by YYYY-MM-DD

Creates a corresponding entry in Surprises & Discoveries with the same Revisit deadline, so the doc-gardener can surface it.

## Forbidden phrases

The following phrases are banned in any Decision Log entry, regardless of context. The structural test enforces this:

- "standard approach"
- "best practice"
- "industry standard"
- "commonly used"
- "widely accepted"
- "the go-to"
- "people generally"
- "everyone knows"

These phrases are tells for unsupported confidence. If you would write one of them, you are guessing — use the Marked-as-guess shape instead.

## Wikipedia is not evidence

Citations must be either:

- Primary sources: the project's own docs, source code, RFCs, standards.
- In-repo experiments: scripts you ran with captured output.

Aggregator articles, blog posts ranking "top 10 X", or Wikipedia survey articles do not count as evidence for an engineering decision. The structural test accepts any URL today, but the doc-gardener flags suspicious citation domains for review.

Last reviewed: 2026-05-02
