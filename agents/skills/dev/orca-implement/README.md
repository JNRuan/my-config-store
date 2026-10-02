# `orca-implement`

`orca-implement` is a skill for **Claude Code and Codex** that orchestrates implementation work through [Orca's CLI](https://github.com/stablyai/orca).

It takes a GitHub issue, Linear issue, specification, or prompt through planning, implementation, verification, review, and optional adversarial QA, then opens a pull request.

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
2. **Setup**: settles the role of the current branch, pins the base, adopts the current Orca worktree or creates one, and initialises the manifest.
3. **Scout**: sends routed read-only workers to inspect the affected code and project practices.
4. **Understanding check**: presents the task contract and all known questions through the mapped human review interface.
5. **Plan**: drafts and fact-checks the implementation plan, critiques it once, then fact-checks the revised sections.
6. **Plan gate**: repeats human review until the plan has no unresolved comments.
7. **Build**: registers the build tasks and their dependencies, then dispatches workers as dependencies merge.
8. **Verify and integrate**: checks, fixes, and merges each task before releasing its dependants.
9. **Whole-run verification**: runs the project checks, sends a routed read-only worker to verify every acceptance criterion, turns unmet criteria into fix tasks, and records any remaining gaps. Later passes re-check only the criteria a fix affected.
10. **Review**: runs the routed code and security review lenses, with browser verification in parallel in the first round. A later round runs only after a Critical or High fix, up to the approved cap. It confirms the previous round's fixes and reports only new findings.
11. **Final adversarial QA**: runs once when the routing policy requires it, then verifies accepted fixes.
12. **PR**: pushes only the run branch, opens a PR, then commits the final checkpoint.

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

The run record reaches the branch through checkpoint commits at plan approval, build verification, code-review completion, the PR, and abort. Each checkpoint holds the brief, plan, agent tasks and reports, reviews, summary, and manifest at that HEAD. The run makes no other record commits. Worker reports and the coordinator's working files go under `scratch/`, which never reaches the branch.

The artifact set is closed. A run writes these and nothing else:

- `run-state.json`, the run manifest for state transitions and recovery
- `plan/`, the approved brief and the specification of record
- `tasks/`, worker agent tasks and reports
- `review/`, the review of record for every round run, and the QA review when QA runs
- `summary.md`, the run narrative: what happened, acceptance evidence, incidents, lessons for later runs, and what remains
- `timeline.md`, one event per line, and `run-page.html`, a status page rendered from it and the manifest by `scripts/render-run-page.py` and published for the human when an artifact route is available
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
