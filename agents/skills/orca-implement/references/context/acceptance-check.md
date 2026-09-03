# Acceptance-check context

## Load when

Read this file in Phase 6 after the project checks have run and before creating an acceptance-check task. Reuse it for every later pass.

## Required values

Resolve:

- `<RUNDIR>`;
- `<PASS>`: the number of acceptance checks run so far in this run, plus one.

The task is `acceptance-check-<PASS>` and the report is `<RUNDIR>/scratch/acceptance-check-<PASS>.md`.

## Context rules

The worker verifies each acceptance criterion against the integrated HEAD in `<WT>`. It reads code, runs the recorded project commands and the tests that cover a criterion, and exercises behaviour where a command can. It judges only whether the criterion is met.

## Dispatch template

```text
Read <RUNDIR>/plan/plan.md. Verify each acceptance criterion in it against the integrated HEAD in this worktree. Read the code, run the recorded project commands and the tests that cover the criterion, and exercise the behaviour where a command can. Leave implementation files unchanged.

Report each criterion by id as one of:

- verified, with the command output or path:line evidence;
- not met, with what is missing;
- not verifiable here, with the reason.

Judge only whether each criterion is met. Do not assess code quality, design, or scope. Write the full report to <RUNDIR>/scratch/acceptance-check-<PASS>.md. That report is the only file you may write. Then report completion.
```
