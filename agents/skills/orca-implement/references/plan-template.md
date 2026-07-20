# Plan template

Write `<RUNDIR>/plan/plan.md` in exactly this shape. The plan is the run's spec of record: workers and reviewers never need the original ticket.

```markdown
---
run: {RUN}                 # the run name; matches <RUNDIR>
source: {ref | "ad-hoc"}   # gh-123, lin-abc-123, a file path, or ad-hoc
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

What needs to be built and why, briefly.

## Review Policy

- **Plan-review cap used**: {1 | 2 | 3, snapshotted before critique}
- **Run-complexity rationale**: {aggregate risk, blast radius, coupling, failure impact, and observability evidence from the reviewed plan}
- **Code-review cap**: {pending before critique | 1 | 2 | 3 after critique}
- **Adversarial QA**: {pending before critique | skip for low/medium | run after all code review for high/xhigh}

Fill the plan-review fields before critique from `references/routing.md`.
After critique, replace every pending downstream field from canonical
`run_complexity`. Keep all recorded values synchronized with `run-state.json`.

## Requirements & Acceptance Criteria

Distilled from the task source at intake, or drafted from the prompt, citing
the source: `path@<BASE_SHA>` for a repo document, URL or ref for an issue.
Quote only the lines that carry a requirement or constraint; never paste the
source in whole. State each requirement fully enough to build and verify
against without opening the source. Each criterion gets an ID (`AC-1`, `AC-2`,
...) so tasks, verification, and the PR can reference it. Every criterion must
be covered by at least one task.

## Out of Scope

What this run deliberately does not touch.

## Assumptions

- **Validated**: confirmed during scouting, with `path:line` evidence.
- **Open**: unconfirmed; flagged to the critics and the human at the plan
  gate, and assigned to the task that must verify them before implementing.

## Contracts

Interfaces shared across tasks, pinned before dispatch: signatures, schemas,
routes, types. Parallel tasks build against these as written; a contract
change goes through the coordinator (re-pin), never through a worker.

## Tasks

Each task's complexity is `low` | `medium` | `high` | `xhigh`, classified with
the task rubric in `references/routing.md`. It routes that task's builder and is
independent of `plan_review_tier` and `run_complexity`.

| seq | slug | deps | complexity | builder | covers |
|-----|------|------|------------|---------|--------|
| 01  | ...  | —    | medium     | codex sol · high | AC-1 |
| 02  | ...  | 01   | high       | codex sol · xhigh | AC-2 |
| 03  | ...  | 02   | xhigh      | claude fable · high | AC-3 |

### {seq}-{slug}

- **What**: the deliverable that results in commits (the what, not the how —
  the builder decides implementation).
- **Why**: what purpose it serves.
- **Deps / Inputs**: dependency tasks and what from their output feeds in.
- **Contracts**: which pinned contracts this task obeys or produces.
- **Constraints & Context**: patterns to follow, invariants to preserve,
  background the builder must know.
- **Relevant existing code**: files the builder should read first, and why.
- **Verification requirements**: behaviors and scenarios, not test code:
  1. Existing coverage to run (must stay green)
  2. Tests to add or update
  3. Edge cases that must be covered
  4. Manual/visual checks (if applicable)
- **Covers**: acceptance criteria this task satisfies.

## Orchestration

Coordinator's execution guide; workers see only their assignment context.

### Waves

What runs in parallel and what serializes, derived from the deps column.

### Sync Points

Where one task's output feeds a later task's context package: what gets
relayed, and why it is a sync point.

### Integration Verification

Cross-task boundaries to verify after each merge, guided by the scouted
blast radius — not just each task's own tests.

### Post-Merge Validation

Exact commands to run once everything is merged (full suite, E2E scenarios,
build verification).

## Project Tooling

Install / Build / Test / Lint / Typecheck / Format check / Format write
commands and the repo's commit-message convention, verbatim — passed
unchanged into every assignment file ("none" where a tool doesn't exist).
Format is two entries: the check form (safe to run during verification) and
the write form (mutates code).
```
