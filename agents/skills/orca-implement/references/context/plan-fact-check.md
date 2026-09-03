# Plan fact-check context

## Load when

Read this file in Phase 3 immediately before creating a plan fact-check task.

## Required values

Resolve:

- `<RUNDIR>`;
- `<SUFFIX>`: empty for the check before critique; `-final` for the check after it.

The task is `plan-fact-check<SUFFIX>` and the report is `<RUNDIR>/scratch/fact-check<SUFFIX>.md`.

## Context rules

Verify only checkable repository claims. Do not assess planning judgement, decomposition, scope, or complexity.

## Dispatch template

```text
Read <RUNDIR>/plan/plan.md and verify every checkable claim against the repository: file paths, path:line evidence, command names, symbols, and interfaces cited in contracts. Report mismatches only. Do not assess reasoning, decomposition, scope, or the run-complexity judgement. Write the full report to <RUNDIR>/scratch/fact-check<SUFFIX>.md. That report is the only file you may write. Then report completion.
```
