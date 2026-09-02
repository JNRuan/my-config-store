# Planner context

## Load when

Read this file in Phase 3 before composing the planner brief or dispatching planners. Keep it loaded through draft selection and synthesis.

## Required values

Resolve:

- `<P>`: the stable planner label;
- `<RUNDIR>`.

## Prepare the planner brief

Write one standalone brief to `<RUNDIR>/plan/planner-brief.md` containing:

- the approved `plan/brief.md`;
- confirmed scout evidence;
- open assumptions;
- project tooling verbatim;
- the required structure from `references/plan-template.md`.

Planners cannot read the coordinator's skill files. Include every instruction they need in the brief. Every planner reads the same file.

## Dispatch template

```text
Read <RUNDIR>/plan/planner-brief.md. Independently write a complete implementation plan to <RUNDIR>/plan/draft-<P>.md following the plan structure given in the brief. Do not read any other draft-*.md file. Your draft is the only file you may write. Then report completion.
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

Write `<RUNDIR>/plan/plan.md` as one coherent document that follows `references/plan-template.md`. Do not concatenate drafts.

## Required final-plan content

The final plan must contain:

- frontmatter with pinned `base_sha`, captured `<RUN-BRANCH>`, `plan_review_tier`, and `run_complexity: pending`;
- the plan-review cap selected from `plan_review_tier`;
- pending code-review and QA policy until critique determines `run_complexity`;
- requirements and acceptance criteria with `AC-n` ids;
- at least one task covering every acceptance criterion;
- a task table with explicit dependencies, complexity, and builder routing;
- the smallest viable task set;
- every interface shared across tasks as a pinned contract;
- validated assumptions with evidence;
- open assumptions assigned to the task that must verify them;
- project tooling verbatim, including Build, Format check, and Format write;
- verification requirements for important behaviour and edge cases.
