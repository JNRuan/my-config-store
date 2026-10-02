# Plan fact-check context

## Load when

Read this file in Phase 3 immediately before creating a plan fact-check task.

## Required values

Resolve:

- `<RUNDIR>`;
- `<SUFFIX>`: empty for the check before critique; `-final` for the check after it;
- `<SCOPE>`: empty before critique. After it:

  ```text
  Limit the check to the sections that differ between <RUNDIR>/scratch/plan-pre-critique.md and <RUNDIR>/plan/plan.md.
  ```

The task is `plan-fact-check<SUFFIX>` and the report is `<RUNDIR>/scratch/fact-check<SUFFIX>.md`.

## Dispatch template

```text
Read <RUNDIR>/plan/plan.md and verify every checkable claim against the repository: file paths, path:line evidence, command names, symbols, and interfaces cited in contracts. Verify that every id in the Coverage table exists in the plan and that the table lists every requirement, criterion, and task. <SCOPE> Report mismatches only. Do not assess reasoning, decomposition, scope, or the run-complexity judgement. Write the full report to <RUNDIR>/scratch/fact-check<SUFFIX>.md. That report is the only file you may write. Then report completion.
```
