# Planner context

## Load when

Read this file in Phase 3 before composing the planner brief or dispatching planners. Keep it loaded until you write the final plan.

## Required values

Resolve:

- `<P>`: the stable planner label;
- `<RUNDIR>`.

## Prepare the planner brief

Write the planner brief to `<RUNDIR>/scratch/planner-brief.md`. It stands alone and contains:

- the approved `plan/brief.md`;
- confirmed scout evidence;
- open assumptions;
- project tooling verbatim;
- the project-rules paths from scouting, with the instruction to read every file before drafting;
- the selected `plan_review_tier`, with downstream policy fields left `pending`;
- the task-complexity rubric and builder routing rows from `references/routing.md`;
- the required structure from `references/templates/plan-template.md`.

Planners cannot read the coordinator's skill files. Include every instruction they need in the planner brief. Every planner reads the same file.

## Dispatch template

```text
Read <RUNDIR>/scratch/planner-brief.md. Independently write a complete implementation plan to <RUNDIR>/scratch/draft-<P>.md following the plan structure given in that file. Do not read any other draft-*.md file. Your draft is the only file you may write. Then report completion.
```

## Assess drafts

Assess each complete draft against:

- task boundaries;
- requirement coverage;
- correctness;
- verification;
- task sizing;
- any other risk raised by the requirements or scout evidence.

Select the strongest draft as the base. Correct claims that conflict with the approved brief or repository evidence. Use stronger parts from another draft where they improve the plan.

Write `<RUNDIR>/plan/plan.md` as one coherent document that follows `references/templates/plan-template.md`. Do not concatenate drafts.

## Required final-plan content

The final plan follows `references/templates/plan-template.md` exactly, with `run_complexity` and the downstream policy fields `pending` until critique, and the smallest workable task set.
