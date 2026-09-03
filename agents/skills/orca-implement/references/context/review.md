# Review context

## Load when

Read this file at the start of Phase 7. Reuse it for every code-review round.

## Required values

Resolve:

- `{code-review-skill}` and `{security-review-skill}` from `references/skill-map.md`;
- `<BASE_SHA>`;
- `<RUNDIR>`;
- `<ROUND>`;
- `<CODE_REVIEWER>`: the stable code-reviewer label;
- `<SECURITY_REVIEWER>`: the stable security-reviewer label;
- `<PREVIOUS_HEAD>`: the previous round's recorded HEAD;
- `<ROUND_CONTEXT>`: empty in round 1. After round 1:

  ```text
  The previous round's review of record, with its triage and fix commits, is <PREVIOUS_REVIEW>. First confirm that every finding it records as fixed is fixed at this HEAD, and report each that is not. Then review the whole branch and report only findings that review did not triage. The commits since the previous round are <PREVIOUS_HEAD>..HEAD.
  ```

## Context rules

Every reviewer in a round receives the same context block. The block names the run files and how to weigh them. Reviewers inspect the repository and diff for themselves.

## Code-review dispatch template

```text
Run /{code-review-skill} (it exists; do not check) and follow its instructions. Review the current branch against base commit <BASE_SHA>.

Context:
- <RUNDIR>/plan/brief.md is the task contract: approved requirements, scope, exclusions, and human decisions.
- <RUNDIR>/plan/plan.md is the intended design, not proof that the design is correct.
- <RUNDIR>/summary.md and test results are evidence, not proof.
<ROUND_CONTEXT>

Inspect the repository and diff independently. Report implementation defects, and plan defects when they affect the PR result. Do not expand the task because an unrelated improvement is possible.

Exclude .agents/orca/orchestration/ because it contains run bookkeeping, not the implementation. Write the full report to <RUNDIR>/scratch/<CODE_REVIEWER>-review-r<ROUND>.md. That report is the only file you may write. Do not edit code. Then report completion.
```

## Security-review dispatch template

```text
Run /{security-review-skill} (it exists; do not check) and follow its instructions. Review the current branch against base commit <BASE_SHA>.

Context:
- <RUNDIR>/plan/brief.md is the task contract: approved requirements, scope, exclusions, and human decisions.
- <RUNDIR>/plan/plan.md is the intended design, not proof that the design is correct.
- <RUNDIR>/summary.md and test results are evidence, not proof.
<ROUND_CONTEXT>

Inspect the repository and diff independently. Report implementation defects, and plan defects when they affect the PR result. Do not expand the task because an unrelated improvement is possible.

Exclude .agents/orca/orchestration/ because it contains run bookkeeping, not the implementation. Write the full report to <RUNDIR>/scratch/security-<SECURITY_REVIEWER>-review-r<ROUND>.md. That report is the only file you may write. Do not edit code. Then report completion.
```
