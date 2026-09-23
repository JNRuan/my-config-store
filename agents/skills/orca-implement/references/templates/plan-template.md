# Plan template

Write `<RUNDIR>/plan/plan.md` in exactly this shape. The plan is the run's spec of record. Workers and reviewers never need the original ticket.

```markdown
---
run: {RUN}                 # the run name; matches <RUNDIR>
source: {gh-123 | lin-abc-123 | path@<BASE_SHA> | "ad-hoc"}
base: {base ref}           # the PR's target branch
base_sha: {pinned SHA}     # what the run branch was created from; all diffs use this
branch: {captured run branch}   # Orca-derived; captured from the integration worktree
plan_review_tier: {low | medium | high | xhigh}
run_complexity: {pending before critique | low | medium | high | xhigh after critique}
created: {ISO 8601 UTC}    # date -u +%Y-%m-%dT%H:%M:%SZ; update modified on edits
modified: {ISO 8601 UTC}
---

# Plan: {title}

## Overview

What to build and why, briefly.

## Review Policy

- **Run-complexity rationale**: {aggregate risk, blast radius, coupling, failure impact, and observability evidence from the reviewed plan}
- **Code-review cap**: {pending before critique | 1 | 2 | 3 | 5 after critique}
- **Adversarial QA**: {pending before critique | skip for low | run after all code review for medium/high/xhigh}

Leave every downstream field `pending` before critique.
After critique, replace every pending downstream field from
`run_complexity`. Keep all recorded values synchronised with `run-state.json`.

## Requirements & Acceptance Criteria

Take the requirements from the approved brief. Cite each by its `R-n` id, and cite the intake source as the brief does.

Write each requirement so a worker can build and verify it without opening the source.

Give every acceptance criterion an id: `AC-1`, `AC-2`, and so on. Every criterion must:

- state observable behaviour;
- have at least one task that covers it;
- have a verification method.

## Out of Scope

What this run deliberately does not touch.

## Constraints

Take the constraints from the approved brief and cite each by its `C-n` id. Every constraint must have a verification method. Write `none` when the brief has no constraints.

## Assumptions

- **Validated**: state the confirmed assumption and cite `path:line` evidence.
- **Open**: name the task that must verify it before relying on it.

Do not leave a known human-owned decision as an open assumption.

## Contracts

Interfaces shared across tasks, pinned before dispatch: signatures, schemas,
routes, types. Parallel tasks build against these as written. Only the
coordinator changes a contract, by re-pinning it.

## Project rules

The rule files that govern this change.

- **Files**: each rule file the scouts found, with its path and one sentence on what it requires of this task.
- **Deviations**: each rule the plan cannot follow, with its `path:line`, the reason, and the simpler alternative rejected. Write `none` when the plan follows every rule.
- **Contradictions**: each rule the existing code already breaks, with the rule's `path:line`, the code's `path:line`, and which one the plan follows. Write `none` when there are none.

A source requirement that a rule forbids is a scope question for the brief, not a deviation.

## Decisions

Each design choice a competent engineer could have made differently: the decision, the alternative rejected, and why. Write `none` when the plan makes no such choice.

## Tasks

Each task's complexity is `low` | `medium` | `high` | `xhigh`, classified with
the task-complexity rubric in `references/routing.md`. It routes that task's builder and is
independent of `plan_review_tier` and `run_complexity`.

| seq | slug | deps | complexity | builder | covers |
|-----|------|------|------------|---------|--------|
| 01  | ...  | —    | medium     | claude opus · medium | AC-1 |
| 02  | ...  | 01   | high       | claude opus · high | AC-2 |
| 03  | ...  | 02   | xhigh      | claude opus · xhigh | AC-3 |

### {seq}-{slug}

- **What**: the required result and its boundaries. Prescribe an implementation detail only when correctness depends on it. The builder may make local choices within the approved contracts and constraints.
- **Why**: what purpose it serves.
- **Deps / Inputs**: dependency tasks and what their output feeds into this task.
- **Contracts**: which pinned contracts this task obeys or produces.
- **Constraints & Context**: patterns to follow, invariants to preserve,
  background the builder must know.
- **Relevant existing code**: files the builder should read first, and why.
- **Verification requirements**: behaviours and scenarios, not test code:
  1. Existing coverage to run (must still pass)
  2. Tests to add or update
  3. Edge cases to cover
  4. Manual/visual checks (if applicable)
- **Covers**: acceptance criteria this task satisfies.

## Coverage

One row per requirement: its `R-n` id, the `AC-n` ids that express it, and the tasks that cover them. An empty cell is a plan defect.

| R   | AC          | Tasks   |
|-----|-------------|---------|
| R-1 | AC-1, AC-2  | 01, 02  |

## Orchestration

The coordinator owns orchestration. Workers read the full plan for context
and implement only their assigned task.

### Waves

What runs in parallel and what runs in sequence, from the deps column.

### Sync Points

Where one task's output feeds a later task's context package: what to
relay, and why it is a sync point.

### Integration Verification

List the cross-task boundaries to verify after each merge. Use the affected area found during scouting, not only each task's own tests.

### Post-Merge Validation

Exact commands to run after the final merge: full suite, end-to-end
scenarios, build verification.

## Project Tooling

Record these commands verbatim:

- Setup hook: what `orca.yaml` `scripts.setup` does on worktree create, or `none`;
- Install;
- Build;
- Test;
- Lint;
- Typecheck;
- Format check;
- Format write;
- Dev server, with its port.

Write `none` when the repository has no command.

Keep Format check and Format write separate. Verification may run the check form. The write form changes files.

Record the repository's commit-message convention.
```
