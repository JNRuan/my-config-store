# Brief template

Write `<RUNDIR>/brief.md` in exactly this shape. The brief is the contract the human approves before any proof starts. Its Lean statements are the frozen claims.

```markdown
---
run: {RUNDIR basename}
target: {path | symbol | PR #N | "branch diff vs <BASE>" | "scan"}
base: {BASE_SHA}
created: {ISO 8601 UTC}
modified: {ISO 8601 UTC}
---

# Lean brief: {topic}

## Request

Record the human's invocation verbatim, except for secrets and private data. Replace those values with `[REDACTED]`. For a spec, ticket, or file the human named, cite it and quote only the text that states a property or constraint.

## Targets

One row per candidate from triage, ranked:

| Target | Route | Reason |
| --- | --- | --- |
| `path:line` `name` | Lean / property test only / none | one line |

The human removes a row to drop a target.

## Claims

Number each claim `P-1`, `P-2`, and so on. For each:

**P-1**: {the claim in one plain-English sentence}
- Target: `path:line` `name`
- Lean: `theorem {name} {binders} : {statement}`
- Preconditions: {each hypothesis in plain English, or "none"}
- Source: {where the property comes from: `path:line`, spec quote, or "proposed by the agent"}

Write the Lean statement verbatim from the model file. Proofs stay out of the brief.

## Model notes

Every place the model differs from the source: types (`Nat` for a count that cannot go negative), bounds, simplifications, and code the model leaves out. Cite the source with `path:line`. The link test covers each difference or the note says why it cannot.

## Scope

- **In**: the targets, the files this run creates or changes, and the link tests it adds.
- **Out**: what this run leaves unmodelled or unproved.

## Repository findings

Scout findings that shape the claims: callers and what they rely on, existing tests, the test runner and property-testing library. Cite all claims with `path:line`.

## Assumptions

Details that no source states and a sane default settles. Number each one `A-1`, `A-2`, and so on, and give the default and its reasoning. A human-owned decision is never an assumption. It goes in Questions.

## Questions

Every ambiguity about what a function must do, every conflict between a source and the code, and every missing tool or package. Number each one `Q-1`, `Q-2`, and so on. Order them by impact: which targets and claims first, then preconditions, then tooling.

Write each question as a full question ending in `?`, then one sentence on what the answer decides. Give one to three suggested answers and mark the recommended one:

**Q-1**: May `splitEvenly` receive `n = 0`?
Decides whether P-1 needs the precondition `n > 0`.
- A (recommended): No. Every caller passes the participant count, which `apps/web/src/split/form.ts:42` validates as at least 1.
- B: Yes. The claim must then cover an empty result.
```
