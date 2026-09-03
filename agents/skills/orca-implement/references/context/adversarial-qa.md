# Adversarial-QA context

## Load when

Read this file in Phase 8 after creating and verifying the disposable QA worktree.

## Required values

Resolve:

- `{adversarial-qa-skill}` from `references/skill-map.md`;
- `<BASE_SHA>`;
- `<QA_HEAD>`;
- `<RUNDIR>`;
- `<REVIEW_PATHS>`: every completed `<RUNDIR>/review/review-r*.md`, one per line.

## Context rules

The worker attacks behaviour beyond the plan's happy path and retests every path that review fixes changed. It stays within the approved scope unless an adjacent failure directly affects the PR result.

## Dispatch template

```text
Run /{adversarial-qa-skill} (it exists; do not check) against the current branch and base commit <BASE_SHA>. Try to break the implementation through code-level and browser-based testing.

Context:
- <RUNDIR>/plan/brief.md is the task contract.
- <RUNDIR>/plan/plan.md is the intended design, not proof that the design is correct.
- <RUNDIR>/summary.md holds the verification results. Treat them as evidence, not proof.
- Review findings and fixes so far, treat as evidence:
<REVIEW_PATHS>

Inspect the repository independently. Exclude .agents/orca/orchestration/ because it contains run bookkeeping, not the implementation. Run browser work headlessly. This worktree is your isolated review worktree at verified post-review HEAD <QA_HEAD>. Do not create another worktree and do not remove this one. Save screenshots under <RUNDIR>/screenshots/.

Do not limit testing to the plan's happy path. Retest paths changed by review fixes and explore adjacent failure paths that affect the PR result. Stay within the approved scope unless an adjacent failure directly affects the PR result.

Write the full report to <RUNDIR>/scratch/qa-findings.md. For each finding, include a reproducible test scenario or screenshot. When no finding holds, still report what you attacked, how you tested it, and that it held.

The report and screenshots under <RUNDIR>/screenshots/ are the only paths you may write outside the QA worktree. Remove throwaway test files. Before removing a failing test, record its exact scenario in the finding. Then report completion.
```
