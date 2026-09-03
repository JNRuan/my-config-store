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

For an ad-hoc prompt, record the prompt verbatim.

## Problem

What is wrong or missing today, and for whom. Use the source's terms, not the repository's.

## Requirements

What the change must do. Number each one `R-1`, `R-2`, and so on. Write each so the plan can turn it into acceptance criteria without reopening the source.

## Scope

- **In**: what this run builds.
- **Out**: work this run deliberately excludes.

## Constraints

Limits the implementation must obey: security, data handling, architecture, compatibility, process. Record every human-owned decision here once the human makes it.

## Repository findings

Scout findings that change the approach: current behaviour, affected code, existing coverage, tooling. Cite all claims with `path:line`.

## Questions

Every ambiguity, missing acceptance criterion, and conflict between the source and the repository. Number each one `Q-1`, `Q-2`, and so on. Give your recommended answer where you have one.
```

