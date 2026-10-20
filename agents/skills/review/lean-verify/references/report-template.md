# Report template

Write `<RUNDIR>/report.md` in exactly this shape. Report what the checks showed, with their output
as evidence.

```markdown
---
run: {RUNDIR basename}
brief: brief.md
head: {HEAD SHA at report time}
lean: {`lean --version` output}
created: {ISO 8601 UTC}
---

# Lean report: {topic}

## Result

One line per outcome kind with its count: proved, false, stuck, declined. Then one sentence per
**false** claim and per link-test mismatch, since each points at a likely bug.

## Claims

One section per claim, in brief order:

### P-1: {plain-English claim}

- Outcome: proved / false / stuck
- Theorem: `{Full.Lean.Name}` in `lean/Proofs/...:line`
- Evidence:
  - proved: the `lean_verify` output, verbatim;
  - false: the breaking input, the model's output, and the real code's output;
  - stuck: the open goal, verbatim, and the approaches tried.
- Stronger than claimed: for a proved claim, each hypothesis `lean_minimal_hypotheses` found
  unused, and which reading applies: the claim holds without it, or the model ignores a precondition
  the source relies on. Otherwise "none".

## Link tests

| Target | Test file | Inputs run | Seed | Result |
| --- | --- | --- | --- | --- |
| `name` | `path` | {count} | {seed} | pass / mismatch |

Under the table, for each test: the tally of branches the inputs reached, and the change to
`Model.lean` that turned it red.

For each mismatch: the input, both outputs, and which side is wrong with the evidence.

## Declined targets

Each target triage routed to none, with its reason.

## Coverage gaps

What the proofs do not cover: each model note from the brief the link test cannot check, and every
precondition a caller does not enforce, with `path:line`.

## Follow-up targets

Functions this run suggests proving next: lemmas a proof needed, callers that inherit a proved
property, and siblings with the same shape. One line each, with the reason.

## Run notes

What the next run needs to know: environment fixes made or still needed, steps declined or skipped
with the reason, and what a test runner needs to run the link tests, such as `lake` on its PATH.

## Files

Every file this run created or changed. All changes are uncommitted.
```
