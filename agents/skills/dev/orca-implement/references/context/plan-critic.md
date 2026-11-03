# Plan-critic context

## Load when

Read this file in Phase 3 before every plan-critique round.

## Required values

Resolve:

- `<M>`: the stable critic label;
- `<ROUND>`;
- `<RUNDIR>`;
- `<BRIEF_PATH>` and `<PLAN_PATH>` from manifest `artifacts` paths;
- `<PREVIOUS_CRITIQUE>`: prior reports and plan finding resolutions, or `none` in round 1.

## Dispatch template

```text
Read <PLAN_PATH> and the approved brief at <BRIEF_PATH>. Review the plan as an adversarial critic,
not an approver. Previous critique and dispositions: <PREVIOUS_CRITIQUE>. Find the strongest
concrete issues that could cause implementation, integration, or verification to fail.

Follow the plan's specific risks wherever they lead. Your critique must account for requirement
coverage, assumptions, decisions and their rejected alternatives, task boundaries and dependencies,
verification adequacy, task sizing, and conflicts with the project rules. Read the rule files named
in the plan's Project rules section. An unjustified conflict with a project rule is `BLOCKING`.
Check that mitigations exist, assumptions have falsifiable checks and failure consequences, and
supplied designs are followed or departures are explicitly proposed for approval. Assess the whole
current plan, including material feature, approach, and fix changes from the previous round.
Confirm previous findings' resolutions and preserve their IDs when reporting a persistent issue.
Pursue any other credible failure mode the plan reveals.

When you need repository evidence, use native subagents for read-only scouting. Do not create Orca
tasks, dispatches, or terminals. You own and must clean up any subagents you start.

Stay within approved scope and assess the design's feasibility rather than implementation style.
Respect settled supplied designs. Propose alternatives only when a concrete failure or gap warrants
one; do not invent redesign work to fill the review.

For each finding, report an existing `PF-n` ID when applicable, the plan anchor, evidence, a concrete
failure scenario, and severity `BLOCKING`, `RISKY`, or `NOTE`. The coordinator assigns IDs to new
findings. Identify whether your proposed correction materially changes features, approach, or fixes.

A no-finding report is valid only after you have examined the relevant plan and repository evidence
and found no credible failure scenario. End with verdict `proceed`, `revise`, or `re-plan`.

Write the full critique to <RUNDIR>/scratch/critique-<M>-r<ROUND>.md. Write no other file. Then
report completion.
```
