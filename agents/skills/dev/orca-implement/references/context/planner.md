# Planner context

## Load when

Read this file in Phase 3 before composing the planner brief or dispatching planners. Keep it loaded
until you write the final plan.

## Required values

Resolve `<P>` as the stable planner label, `<RUNDIR>`, and `<BRIEF_PATH>` and `<PLAN_PATH>` from
manifest `artifacts` paths.

## Prepare the planner brief

Write `<RUNDIR>/scratch/planner-brief.md` as a self-contained packet with:

- the approved brief's content, path, and revision, including supplied design sources and constraints;
- confirmed scout evidence and open assumptions;
- project tooling verbatim and project-rule paths, with an instruction to read every rule file;
- the selected plan-review tier, with downstream policy fields left `pending`;
- task-complexity and builder-routing guidance from `references/routing.md`;
- the content guidance from `references/templates/plan-template.md`;
- any existing `PD-n` decisions and `PF-n` findings with their dispositions when revising a plan.

Planners cannot read coordinator skill files. Include every instruction they need in the packet.
Both planners, when routed, read the same packet and independently assess feasibility and coverage.
A full supplied specification and design shifts the work to implementation mapping and genuine gaps.
Reuse adequate designs and visuals. Create new design work only when needed to resolve a gap or
explain unclear behaviour. Flag material departures from supplied designs for human approval.

## Dispatch template

```text
Read <RUNDIR>/scratch/planner-brief.md. Independently write a complete implementation plan to
<RUNDIR>/scratch/draft-<P>.html using the content guidance in that file. Choose an HTML layout that
suits the task, with stable anchors. Reuse supplied designs and explain only genuine gaps. Keep any
new diagrams inline and link existing assets so your draft remains the only file you write.
Do not read any other draft-*.html file. Then report completion.
```

## Assess drafts and write the final plan

Assess each draft for fidelity to the approved brief and supplied design, requirement coverage,
feasibility, assumptions and their failure consequences, task boundaries and dependencies,
verification, task sizing, and project rules. Select the strongest base and use stronger parts of
another draft where useful. Correct unsupported claims and write one coherent `<PLAN_PATH>`.
Preserve stable anchors and IDs rather than concatenating drafts.

Cover every requirement of `references/templates/plan-template.md`. Leave run complexity and
policy fields pending until critique. Choose the smallest workable task set. The coordinator owns
final asset placement under `plan/assets/` and relative links from the canonical plan.
