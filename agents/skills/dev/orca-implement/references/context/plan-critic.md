# Plan-critic context

## Load when

Read this file in Phase 3 before the plan-critique round.

## Required values

Resolve:

- `<M>`: the stable critic label;
- `<ROUND>`;
- `<RUNDIR>`.

## Dispatch template

```text
Read <RUNDIR>/plan/plan.md. Review it as an adversarial critic, not an approver. Find the strongest concrete issues that could cause implementation, integration, or verification to fail.

Follow the plan's specific risks wherever they lead. Your critique must account for requirement coverage, assumptions, decisions and their rejected alternatives, task boundaries and dependencies, verification adequacy, task sizing, and conflicts with the project rules. Read the rule files named in the plan's Project rules section. An unjustified conflict with a project rule is `BLOCKING`. Pursue any other credible failure mode the plan reveals.

When you need repository evidence, use native subagents for read-only scouting. Do not create Orca tasks, dispatches, or terminals. You own and must clean up any subagents you start.

Do not review implementation detail or style. Do not expand the approved scope.

For each finding, report the plan section, a concrete failure scenario, and severity `BLOCKING`, `RISKY`, or `NOTE`.

A no-finding report is valid only after you have examined the relevant plan and repository evidence and found no credible failure scenario. End with verdict `proceed`, `revise`, or `re-plan`.

Write the full critique to <RUNDIR>/scratch/critique-<M>-r<ROUND>.md. Write no other file. Then report completion.
```
