# Brief template

Write `<RUNDIR>/plan/brief.md` in exactly this shape. The brief is the task contract the human approves before planning starts.

```markdown
---
run: {RUN}
source: {gh-123 | lin-abc-123 | path@<BASE_SHA> | "ad-hoc"}
created: {ISO 8601 UTC}
modified: {ISO 8601 UTC}
---

# Brief: {title}

## Request

For an issue or a file, cite it and quote only the text that carries a requirement or constraint.

For an ad-hoc prompt, record the prompt verbatim except for secrets and private data.
Replace those values with `[REDACTED]` before writing the brief.

## Goal

What this run builds and what it changes for the people in the Problem section. Be concise.

## Problem

What is wrong or missing today, and for whom. Use the source's terms, not the repository's. Be concise.

## Requirements

What the change must do. Number each one `R-1`, `R-2`, and so on. Write each so the plan can turn it into acceptance criteria without reopening the source.

## Scope

- **In**: what this run builds.
- **Out**: work this run deliberately excludes.

## Constraints

Limits the implementation must obey: security, data handling, architecture, compatibility, process. Number each one `C-1`, `C-2`, and so on. Record every human-owned decision here once the human makes it.

## Repository findings

Scout findings that change the approach: current behaviour, affected code, existing coverage, tooling. Cite all claims with `path:line`.

## Assumptions

Details the source leaves open that a sane default settles. Number each one `A-1`, `A-2`, and so on, and give the default and its reasoning. A human-owned decision is never an assumption. It goes in Questions.

## Questions

Every ambiguity, missing acceptance criterion, and conflict between the source and the repository that no default settles. Number each one `Q-1`, `Q-2`, and so on. Order them by impact: scope first, then security and data handling, then user-facing behaviour, then technical detail.

Write each question as a full question ending in `?`, then one sentence on what the answer decides. Give one to three suggested answers and mark the recommended one:

**Q-1**: Does the export include archived reports?
Decides whether R-2 covers the `archived_reports` table.
- A (recommended): No. The reports page already hides archived rows, and the source does not mention them.
- B: Yes, behind the existing "include archived" filter.
```

