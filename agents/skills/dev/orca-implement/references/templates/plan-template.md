# Plan template

Write `<RUNDIR>/plan/plan.html`. This Markdown template describes required content, not a fixed
HTML layout. The plan is the run's spec of record. Workers and reviewers never need the original
ticket. Choose the layout, typography, diagrams, and disclosure that suit the task.

Use semantic HTML, readable contrast, and stable anchors for sections, tasks, decisions, and
requirement IDs. Keep substantive content readable without scripts. Link to the approved brief.
Keep supporting assets under `<RUNDIR>/plan/assets/` and use relative links. Approval receipts
belong in the manifest, as `references/run-state.md` defines them.

## Metadata and overview

Identify the title, run, source, base ref, pinned base SHA, run branch, plan-review tier, run
complexity, creation time, and modification time. Explain what to build and why, and the decisions
the human is being asked to approve.

## Design basis, explanation, and visuals

Build from the approved brief and supplied specifications and designs. Identify their source and
status. When they are complete, concentrate on implementation mapping, integration, verification,
and genuine unresolved details. Reuse settled choices and adequate visuals. Create further design
work only to resolve a gap or explain something the supplied material leaves unclear. Seek human
approval before materially departing from a supplied design.

Explain how the approach works and why it meets the requirements. Use diagrams where they help
assess the design. Compare existing and proposed component boundaries, data flows, sequences,
or state transitions when the difference matters. Use paired views or one annotated view, with
clear labels and consistent names. Include task dependencies only when a diagram clarifies the
execution order. Choose only the views the change needs.

Show current and proposed interface or type shapes when their change matters. Include design
screenshots or mockups where they help assess the implementation. Label supplied, observed,
and proposed material with its provenance. A mockup is not runtime verification.

For each significant risk, give a concrete failure scenario, mitigation, and observable check.
State what evidence would invalidate the approach. Verify repository-dependent mitigations with
`path:line` evidence rather than treating their existence as an assumption.

## Review policy

Record the run-complexity rationale using aggregate risk, blast radius, coupling, failure impact,
and observability evidence. Record the code-review cap, adversarial-QA policy, critic rounds and
outcome, and any missing lenses. Use the policy in `references/routing.md`.

Leave run complexity and downstream policy fields `pending` before critique. After critique, set
them from the reviewed plan and keep them synchronised with `run-state.json`.

## Requirements, acceptance criteria, and scope

Carry requirements, criteria, scope exclusions, and constraints from the approved brief, preserving
their meaning and `R-n`, `AC-n`, and `C-n` IDs and sources. Make them self-contained for workers.
Every constraint has a verification method.

Add a criterion only when the design needs one the brief does not state, such as an integration
boundary. Continue the numbering and mark it as a plan-derived criterion with its rationale. Each
criterion states observable behaviour, has a covering task, and has a verification method. Changes
to the approved task contract require renewed brief approval.

## Assumptions

Preserve `A-n` IDs. For validated assumptions, cite confirming evidence. For open assumptions, name
the task that must verify them before relying on them, the check, and the consequence if false.
Settle human-owned decisions before approval rather than leaving them as open assumptions.

## Contracts

Pin interfaces shared across tasks: signatures, schemas, routes, and types. Parallel tasks build
against these as written. Only the coordinator changes a contract through the plan revision and
approval process.

## Project rules

List each governing rule file and what it requires of this change. For a deviation, cite the rule,
explain the conflict and chosen approach, and identify the simpler alternative rejected. For an
existing contradiction, cite both the rule and conflicting code, and state which the plan follows.
Use `none` where applicable. A source requirement forbidden by a rule is a question for the brief.

## Decisions

Give significant design decisions stable `PD-n` IDs. Record the choice, source, evidence, rationale,
consequences, and status. Distinguish supplied decisions, human answers, repository observations,
and agent recommendations. For a genuine open choice, explain the rejected alternative and why.
Do not invent alternatives to reopen a settled design or fill this section.

Keep critic findings here under stable `PF-n` IDs, with source, evidence, disposition, resolution,
and affected decisions. Reuse IDs across rounds, including when a fix fails or a finding returns.

When a decision changes, preserve its identity and resolution, or link it to the superseding
decision. Link findings that caused the change. Manifest `D-n` records remain human questions,
not a duplicate design ledger. Write `none` when there is no significant design decision.

## Tasks

Use the smallest workable task set. List each task's sequence, slug, dependencies, complexity,
routed builder, and covered `AC-n` IDs. Classify complexity with `references/routing.md`.
Task complexity is independent of plan-review tier and run complexity.

For each task, provide:

- What: the required result and boundaries. Prescribe details when correctness depends on them.
  Builders make local choices within approved contracts and constraints.
- Why: the purpose, including relevant `PD-n` decisions and supplied-design constraints.
- Dependencies and inputs: what each completed dependency produces for this task.
- Contracts: pinned interfaces this task obeys or produces.
- Constraints and context: patterns, invariants, and background the builder needs.
- Relevant existing code: files to read first and why, with `path:line` evidence.
- Verification requirements: existing coverage to run, tests to add or update, edge cases, and
  manual or visual checks. Describe behaviour rather than test code. Use `{test-skill}` to decide
  which tests are useful.
- Covers: the acceptance criteria this task satisfies.

## Coverage

Map every `R-n` to its `AC-n` IDs and covering tasks. Every criterion has a task. An empty mapping
is a plan defect. Include subsequent human steering in the source-to-requirement mapping.

## Orchestration

The coordinator owns orchestration. Workers read the full plan for context and build only their
assigned tasks. Describe parallel and sequential waves from dependencies, sync points and what
must be relayed, integration checks after each merge, and post-merge validation.

Cover cross-task boundaries and affected areas found during scouting, not only task-local tests.
Give exact commands for final project checks, full suites, builds, and end-to-end scenarios.

## Project tooling

Record exact commands for Install, Build, Test, Lint, Typecheck, Format check, Format write, and
Dev server with its port, using `none` where applicable. Record the repository's commit style
and what the `orca.yaml` setup hook does. Keep Format check and Format write separate: verification
runs the check form, while the write form changes files. Workers copy commands without reinterpretation.
