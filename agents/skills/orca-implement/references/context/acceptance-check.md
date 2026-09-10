# Acceptance-check context

## Load when

Read this file in Phase 6 after the project checks have run and before creating an acceptance-check task. Reuse it for every later pass.

## Required values

Resolve:

- `<RUNDIR>`;
- `<PASS>`: the number of acceptance checks run so far in this run, plus one;
- `<CRITERIA>`: the criterion ids in scope for this pass;
- `<PREVIOUS_PASS_HEAD>`: the `start_head` of the previous acceptance-check dispatch record, unused in pass 1;
- `<PREVIOUS_REPORT>`: the previous pass's report path, unused in pass 1;
- `<PREVIOUS_CONTEXT>`: empty in pass 1. After pass 1:

  ```text
  <PREVIOUS_REPORT> holds the verdicts for every other criterion. Their evidence is unchanged since that pass. Do not re-verify them.
  ```

The task is `acceptance-check-<PASS>` and the report is `<RUNDIR>/scratch/acceptance-check-<PASS>.md`.

## Scope a pass

Pass 1 covers every criterion. A later pass covers a criterion when:

- a file owned by one of its covering tasks, or a file cited in its previous evidence, appears in `git diff --name-only <PREVIOUS_PASS_HEAD>..HEAD`; or
- a fix task since the previous pass targeted it.

Every other criterion keeps its previous verdict, evidence, and reason. A `not verifiable here` verdict carries forward unless a fix targeted the criterion.

## Context rules

The worker verifies each acceptance criterion against the integrated HEAD in `<WT>`. It reads code, runs the recorded project commands and the tests that cover a criterion, and exercises the behaviour when a command can exercise it. It judges only whether the criterion is met.

## Dispatch template

```text
Read <RUNDIR>/plan/plan.md. Verify these acceptance criteria against the integrated HEAD in this worktree: <CRITERIA>.
<PREVIOUS_CONTEXT>

Read the code, run the recorded project commands and the tests that cover the criterion, and exercise the behaviour when a command can exercise it. Leave implementation files unchanged.

Report each criterion by id as one of:

- verified, with the command output or path:line evidence;
- not met, with what is missing;
- not verifiable here, with the reason.

Judge only whether each criterion is met. Do not assess code quality, design, or scope. Write the full report to <RUNDIR>/scratch/acceptance-check-<PASS>.md. That report is the only file you may write. Then report completion.
```
