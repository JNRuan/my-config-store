# `orca-implement`

`orca-implement` is a skill for **Claude Code and Codex** that orchestrates implementation work through [Orca's CLI](https://github.com/stablyai/orca).

It takes a GitHub issue, Linear issue, specification, or prompt through planning, implementation, verification, review, optional adversarial QA, and an open pull request.

This repository contains the skill. [Orca](https://github.com/stablyai/orca) is the external orchestration runtime and CLI it uses.

## Invoke the skill

The skill is explicitly invoked with:

```text
/orca-implement {TASK-REF | prompt}
```

Examples:

```text
/orca-implement #123
/orca-implement ABC-123
/orca-implement .orchestrator/specs/SPEC-APP-AUTH/001-authentication.md
/orca-implement Add CSV export to the reports page
```

The skill is **not** triggered by a general request to implement, fix, or build something. Use `/orca-implement` when you want this full Orca-backed pipeline.

## What it does

[`references/routing.md`](./references/routing.md) is the only source for model and effort assignments. This README describes roles and phases without repeating them.

1. **Intake**: loads the Orca guidance and turns the task source into requirements.
2. **Setup**: pins the base, creates the run and integration worktree, and initialises the manifest.
3. **Scout**: sends routed read-only workers to inspect the affected code and project practices.
4. **Understanding review**: presents the task contract and all known questions through the mapped human review interface.
5. **Plan**: drafts, fact-checks, and critiques the implementation plan.
6. **Plan gate**: repeats human review until the plan has no unresolved comments.
7. **Build**: creates the task DAG and dispatches workers where dependencies allow.
8. **Verify and integrate**: checks, fixes, and merges each task before releasing its dependants.
9. **Whole-run verification**: verifies the integrated result and records any remaining gaps.
10. **Review**: runs the routed code and security review lenses up to the approved cap.
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

Each run keeps its audit trail inside the integration worktree at:

```text
<WT-PATH>/.agents/orca/orchestration/<RUN>/
```

The run folder is committed to the run branch as artifacts land, including at phase boundaries.

The artifact set is closed. A run writes these and nothing else:

- `run-state.json`, the run manifest for state transitions and recovery
- `plan/`, the approved brief, scout and fact-check reports, the planner brief and drafts, the specification of record, and critic reports for every round run
- `tasks/`, worker assignments and reports
- `review/`, cross-model review and synthesis for every round run, plus QA findings and triage when QA runs
- `summary.md`, acceptance evidence, decisions, incidents, and final status
- `screenshots/`, browser-verification evidence when applicable

Browser verification stores screenshots when applicable. Its report stays in coordinator context. The plan cites source material by path or URL and distils it into requirements.

The integration worktree and run branch survive until the PR merges. Task and disposable QA worktrees are removed using only the IDs recorded in the run manifest.

## References

- [`SKILL.md`](./SKILL.md), the complete pipeline and safety rules
- [`references/routing.md`](./references/routing.md), model routing, complexity tiers, and worker boot recipes
- [`references/skill-map.md`](./references/skill-map.md), the skill each role invokes
- [`references/plan-template.md`](./references/plan-template.md), the plan format
- [`references/context/`](./references/context/), role contexts and dispatch templates loaded by phase
- [`references/run-state.md`](./references/run-state.md), the manifest schema and lifecycle states
- [`references/orca-mechanics.md`](./references/orca-mechanics.md), shared Orca dispatch, collection, recovery, and resource rules
- [Orca on GitHub](https://github.com/stablyai/orca), the external CLI and runtime
