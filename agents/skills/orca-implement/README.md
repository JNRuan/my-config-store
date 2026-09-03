# `orca-implement`

`orca-implement` is a skill for **Claude Code and Codex** that orchestrates implementation work through [Orca's CLI](https://github.com/stablyai/orca).

It takes a GitHub issue, Linear issue, specification, or prompt through planning, implementation, verification, review, optional adversarial QA, and an open pull request.

This repository contains the skill. [Orca](https://github.com/stablyai/orca) is the external orchestration runtime and CLI it uses.

## Invoke the skill

Invoke the skill with:

```text
/orca-implement {TASK-REF | prompt | resume <RUN | RUNDIR>}
```

Examples:

```text
/orca-implement #123
/orca-implement ABC-123
/orca-implement .orchestrator/specs/SPEC-APP-AUTH/001-authentication.md
/orca-implement Add CSV export to the reports page
/orca-implement resume 20260720-0003-spec-0-5-0
```

A general request to implement, fix, or build something does **not** trigger the skill. Use `/orca-implement` when you want this full Orca-backed pipeline. `resume` hands an existing run to a fresh coordinator session, which reads the manifest and every run artifact before it acts.

## What it does

[`references/routing.md`](./references/routing.md) is the only source for model and effort assignments. This README describes roles and phases without repeating them.

1. **Intake**: loads the Orca guides and reads the task source.
2. **Setup**: pins the base, creates the run and integration worktree, and initialises the manifest.
3. **Scout**: sends routed read-only workers to inspect the affected code and project practices.
4. **Understanding check**: presents the task contract and all known questions through the mapped human review interface.
5. **Plan**: drafts, fact-checks, and critiques the implementation plan, then fact-checks the revised plan.
6. **Plan gate**: repeats human review until the plan has no unresolved comments.
7. **Build**: registers the build tasks and their dependencies, then dispatches workers as dependencies merge.
8. **Verify and integrate**: checks, fixes, and merges each task before releasing its dependants.
9. **Whole-run verification**: runs the project checks, sends a routed read-only worker to verify every acceptance criterion, turns unmet criteria into fix tasks, and records any remaining gaps.
10. **Review**: runs the routed code and security review lenses up to the approved cap. Later rounds confirm the previous round's fixes and report only new findings.
11. **Final adversarial QA**: runs once when the routing policy requires it, then verifies accepted fixes.
12. **PR**: commits the evidence, pushes only the run branch, and opens a PR.

There are four human touchpoints: invocation, the understanding check, the plan gate, and review of the resulting PR. After plan approval the coordinator runs autonomously. An unresolved blocker aborts the run rather than opening a new decision mid-build.

## Requirements

Run `/orca-implement` inside Orca.

The environment must provide:

- every worker and coordinator skill mapped in [`references/skill-map.md`](./references/skill-map.md);
- the worker runtimes, sandbox profiles, and launch commands required by [`references/routing.md`](./references/routing.md);
- GitHub tooling for GitHub intake and PR creation;
- a working Linear connection for Linear intake.

Install Orca from its [official repository](https://github.com/stablyai/orca). The upstream project documents desktop downloads and package-manager installation, including:

```bash
brew install --cask stablyai/orca/orca
```

## Orca CLI contract

At intake, the coordinator loads the version-matched `orchestration` and `orca-cli` guides from the installed Orca binary. Those guides are the source for command names, flags, response fields, and recovery actions.

This README does not duplicate CLI syntax. See [`references/orca-mechanics.md`](./references/orca-mechanics.md) for the pipeline's ownership, dispatch, collection, and cleanup rules.

## Run artifacts

Each run keeps its artifacts inside the integration worktree at:

```text
<WT-PATH>/.agents/orca/orchestration/<RUN>/
```

The coordinator commits the run folder to the run branch as each artifact appears and at every phase boundary. Worker reports and the coordinator's working files go under `scratch/`.

The artifact set is closed. A run writes these and nothing else:

- `run-state.json`, the run manifest for state transitions and recovery
- `plan/`, the approved brief and the specification of record
- `tasks/`, worker agent tasks and reports
- `review/`, the review of record for every round run, and the QA review when QA runs
- `summary.md`, the run narrative: what happened, acceptance evidence, incidents, lessons for later runs, and what remains
- `screenshots/`, browser-verification evidence when applicable
- `scratch/`, scout, fact-check, planner, critic, acceptance-check, review-lens, and QA reports

Browser verification stores screenshots when applicable. Its report stays in coordinator context. The brief records the request and distils it into requirements. The plan turns the approved brief into acceptance criteria and tasks.

The integration worktree and run branch survive until the PR merges. The coordinator removes task and QA worktrees using only the ids recorded in the manifest.

## References

- [`SKILL.md`](./SKILL.md), the complete pipeline and safety rules
- [`references/routing.md`](./references/routing.md), model routing, complexity tiers, and worker boot recipes
- [`references/skill-map.md`](./references/skill-map.md), the skill each role invokes
- [`references/templates/`](./references/templates/), the brief, plan, agent-task, and summary formats
- [`references/context/`](./references/context/), role contexts and dispatch templates loaded by phase
- [`references/run-state.md`](./references/run-state.md), the manifest schema and lifecycle states
- [`references/orca-mechanics.md`](./references/orca-mechanics.md), shared Orca dispatch, collection, recovery, and resource rules
- [Orca on GitHub](https://github.com/stablyai/orca), the external CLI and runtime
