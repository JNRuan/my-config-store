# Plan-critic context

## Load when

Read this file in Phase 3 before the first plan-critique round. Reuse it for later rounds.

## Required values

Resolve:

- `<M>`: the stable critic label;
- `<ROUND>`;
- `<RUNDIR>`.

## Context rules

The critic challenges the plan rather than approving it. It may use runtime-native subagents for read-only repository scouting. It must not create Orca tasks, dispatches, or terminals and must clean up its native subagents.

## Dispatch template

```text
Read <RUNDIR>/plan/plan.md. Review it as an adversarial critic, not an approver. Find the strongest concrete issues that could cause implementation, integration, or verification to fail.

Follow the plan's specific risks wherever they lead. Your critique must account for requirement coverage, assumptions, task boundaries and dependencies, verification adequacy, and task sizing. Pursue any other credible failure mode the plan reveals.

When you need repository evidence, use your runtime's native subagents for read-only scouting. Do not create Orca tasks, dispatches, or terminals. You own and must clean up any subagents you start.

Do not review implementation detail or style. Do not expand the approved scope.

For each finding, report the plan section, a concrete failure scenario, and severity `BLOCKING`, `RISKY`, or `NOTE`.

A no-finding report is valid only after you have examined the relevant plan and repository evidence and found no credible failure scenario. End with verdict `proceed`, `revise`, or `re-plan`.

Write the full critique to <RUNDIR>/plan/critique-<M>-r<ROUND>.md. Write no other file. Then report completion.
```
