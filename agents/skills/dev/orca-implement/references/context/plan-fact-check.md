# Plan fact-check context

## Load when

Read this file in Phase 3 before each plan fact-check, including changed claims after critique or
human feedback.

## Required values

Resolve:

- `<RUNDIR>`;
- `<PLAN_PATH>` from manifest `artifacts.plan`;
- `<CHECK>`: a unique label, such as `initial`, `r1-final`, or `r2-before`;
- `<SCOPE>`: empty for the initial check. For later checks, name the changed sections and the
  previous snapshot, such as `<RUNDIR>/scratch/plan-pre-critique-r1.html`. Resolve any asset paths
  from the canonical plan, not the scratch snapshot.

The task is `plan-fact-check-<CHECK>` and the report is `<RUNDIR>/scratch/fact-check-<CHECK>.md`.

## Dispatch template

```text
Read <PLAN_PATH> and verify every checkable claim against the repository: file paths, path:line
citations, commands, symbols, contracts, and claimed mitigation mechanisms. Verify that the coverage
mapping lists every requirement, criterion, and task, and that each referenced ID exists.
Include current-state claims made in diagrams. Report contradictions between diagrams and the
plan's written approach or contracts. Treat clearly labelled proposed behaviour as a design,
not a claim about existing repository behaviour.
<SCOPE>
Report mismatches only. Do not assess reasoning, decomposition, scope, or run complexity. HTML
layout does not change the claims to check. Write the full report to
<RUNDIR>/scratch/fact-check-<CHECK>.md. That is the only file you may write. Then report completion.
```
