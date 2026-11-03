# Summary template

Write `<RUNDIR>/summary.md` in exactly this shape. The summary is the run narrative. It tells what
happened. The manifest, plan, reviews, and reports hold the detail, so point to them rather than
repeat them. Start it in Phase 0 and add to it as the run proceeds. Complete it after the PR opens
and teardown finishes, or when the run aborts.

```markdown
---
run: {RUN}
source: {gh-123 | lin-abc-123 | path@<BASE_SHA> | "ad-hoc"}
started: {ISO 8601 UTC}
finished: {ISO 8601 UTC, or pending}
---

# Summary: {title}

## Outcome

Before the PR opens: publication pending and what the branch contains.

For an open PR: one paragraph, written for the person who asked for the work, naming the PR and what
it delivers. For a draft PR, say first why it is a draft. Summarise; do not list every change.
Detail belongs in the PR description. Link to `review.html` when available for approved versus
delivered design, before/after evidence, and review coverage.

For a failed or blocked run: one paragraph giving the status, what the run attempted, and what
failed, then a list of every preserved branch.

## Decisions

Decisions the coordinator made that no other artifact records, each with its reason. Human answers
are in the brief, `PD-n` decisions and contracts in the plan, and stable `PF-n` or `F-n` finding
resolutions in the plan or technical reviews. Link existing records rather than duplicating them.

- {decision}: {reason}

## Acceptance criteria and constraints

One row per criterion and constraint in the plan. Result is `verified`, `not met`, or
`not verified`. Evidence is a command and its result, a test name, a screenshot path, or
`path:line`, with the checked code revision and scope. Distinguish executed checks from static
inspection. Link `verification.evidence` entries and preserve earlier results' actual revisions.
For `not verified`, give the reason instead.

| AC   | Result   | Evidence               |
|------|----------|------------------------|
| AC-1 | {result} | {evidence, or reason}  |
| C-1  | {result} | {evidence, or reason}  |

## Incidents

Each incident in order: what happened, what the coordinator did, and its effect on the run. Include
every resumption and its reconciliations.

## Lessons

Friction or incidents that a change to this skill, its routing, or its templates would prevent, each
with the evidence.

## Remaining

Every unverified or unfixed item and its reason, linked by stable finding ID where applicable.
Distinguish deferred work, accepted risk, and workarounds from verified fixes. Write `none` when
nothing remains.
```
