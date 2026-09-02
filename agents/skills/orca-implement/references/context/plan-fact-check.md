# Plan fact-check context

## Load when

Read this file in Phase 3 immediately before creating the plan fact-check task.

## Required values

Resolve `<RUNDIR>`.

## Context rules

Verify only checkable repository claims. Do not assess planning judgement, decomposition, scope, or complexity.

## Dispatch template

```text
Read <RUNDIR>/plan/plan.md and verify every checkable claim against the repository: file paths, path:line evidence, command names, symbols, and interfaces cited in contracts. Report mismatches only. Do not assess reasoning, decomposition, scope, or the run-complexity judgement. Write the full report to <RUNDIR>/plan/fact-check.md. That report is the only file you may write. Then report completion.
```
