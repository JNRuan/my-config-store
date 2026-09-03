# Summary template

Write `<RUNDIR>/summary.md` in exactly this shape. The summary is the run narrative: it tells what happened. The manifest, plan, reviews, and reports hold the detail, so point to them rather than repeat them. Start it in Phase 0, add to it as the run proceeds, and complete it before the PR opens or the run aborts.

```markdown
---
run: {RUN}
source: {gh-123 | lin-abc-123 | path@<BASE_SHA> | "ad-hoc"}
started: {ISO 8601 UTC}
finished: {ISO 8601 UTC, or pending}
---

# Summary: {title}

## Outcome

For an open PR: the PR URL and what the PR contains.

For a failed or blocked run: the status, what the run attempted, the observed failures, and every preserved branch.

## Decisions

Decisions the coordinator made that no other artifact records, each with its reason. Human answers are in the brief, contracts in the plan, and triage in the reviews.

- {decision}: {reason}

## Acceptance criteria

One row per criterion in the plan. Result is `verified`, `not met`, or `not verified`. Evidence is a command and its result, a test name, a screenshot path, or `path:line`. For `not verified`, give the reason instead.

| AC   | Result   | Evidence               |
|------|----------|------------------------|
| AC-1 | {result} | {evidence, or reason}  |

## Incidents

Each incident in order: what happened, what the coordinator did, and its effect on the run. Include every resumption and its reconciliations.

## Lessons

Friction or incidents that a change to this skill, its routing, or its templates would prevent, each with the evidence.

## Remaining

Every unverified or unfixed item and its reason. Write `none` when nothing remains.
```
