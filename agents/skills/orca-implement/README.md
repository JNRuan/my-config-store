# `orca-implement`

`orca-implement` is a skill for **Claude Code and Codex** that orchestrates implementation work through [Orca's CLI](https://github.com/stablyai/orca).

It turns a GitHub issue, Linear issue, markdown doc or spec, or ad-hoc prompt into a controlled implementation run. The coordinator plans the work, dispatches workers into isolated Orca worktrees, verifies and integrates their changes, runs cross-model review and adversarial QA, and opens a pull request when the run succeeds.

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

1. **Intake**: resolves a GitHub issue, Linear issue, markdown doc or spec, or ad-hoc prompt into requirements.
2. **Preflight**: confirms Orca is ready, the coordinator is in an Orca-managed terminal, the repository is registered, the base is clean, and worker skills are resolvable.
3. **Scout**: investigates project mechanics, affected code, dependencies, and test coverage.
4. **Plan**: writes the plan, runs a native fact check over its concrete claims, then sends it to both Claude and Codex plan critics. Blocking and risky findings are resolved, with one optional re-critique round.
5. **Plan gate**: presents the plan, both critic verdicts, and open assumptions to the human, using `crit` when available.
6. **Build**: creates an owned task DAG and dispatches workers in parallel Orca worktrees where dependencies allow. Worker routing follows the complexity rubric in [`references/routing.md`](./references/routing.md).
7. **Verify and integrate**: checks worker commits and reports, runs the required checks, merges valid task branches, and turns failures into worker fix cycles.
8. **Whole-run verification**: runs the full project checks and headless browser verification for UI changes. Verification failures must be fixed or explicitly recorded as not verified before review.
9. **Review**: runs Claude and Codex code reviews plus adversarial QA in round 1. If round 1 produces fix-now findings, it runs a second reviewer round after the fix wave. QA does not rerun in round 2; round-2 fix-now findings get one final fix wave and no third review.
10. **Ship**: applies the final fix wave when needed, commits the run artifacts, pushes only the run branch, and opens a PR. Failed or blocked runs use the abort routine instead.

There are three human touchpoints: the initial invocation, approval of the plan, and review of the resulting PR. Critical questions can still pause a run.

## Requirements

The coordinator must run inside an Orca-managed terminal. Before dispatching workers, the skill expects:

- Orca installed and its CLI available as `orca`.
- Orca's runtime to report ready from `orca status --json`.
- `ORCA_TERMINAL_HANDLE` to be set by the current Orca terminal.
- The repository to be registered with Orca and the base ref to be clean.
- `code-review-local` available in both the Claude and Codex skill directories visible to Orca terminals.
- `adversarial-review` available in the Codex skill directory visible to Orca terminals.
- `agent-browser` available to the coordinator's runtime for browser verification.
- Claude Code and Codex available to boot the routed worker terminals.
- GitHub tooling available for GitHub intake or PR creation, and a working Linear connection for Linear intake.

Install Orca from its [official repository](https://github.com/stablyai/orca). The upstream project documents desktop downloads and package-manager installation, including:

```bash
brew install --cask stablyai/orca/orca
```

## Orca CLI operations

The skill uses Orca's CLI to own runtime state, worktrees, terminals, and agent coordination. Representative operations include:

```bash
orca status --json
orca repo list --json
orca linear issue <ref> --full --json
orca worktree create ... --json
orca terminal create ... --json
orca orchestration task-create ... --json
orca orchestration dispatch ... --json
orca orchestration check --wait --types worker_done,escalation ... --json
orca orchestration task-update ... --json
orca worktree rm ... --json
```

These are representative operations, not a standalone command sequence. The skill records the handles, task IDs, worktree IDs and paths, branches, dispatch IDs, and reports it owns. Because Orca state is runtime-global, it never acts on unrecorded tasks, terminals, or worktrees.

## Run artifacts

Each run keeps its audit trail inside the integration worktree at:

```text
<WT-PATH>/.agents/orca/orchestration/<run-id>-<slug>/
```

The run folder is committed to the run branch as artifacts land, including at phase boundaries. It must not be committed while a worker is active in the integration worktree.

Artifacts include:

- `run-state.json`, the run manifest for state transitions and recovery
- `plan.md`, the plan and specification of record
- `tasks/`, worker assignments and reports
- `review/`, cross-model review, QA, and synthesis reports, including round 2 when applicable
- `summary.md`, acceptance evidence, decisions, incidents, and final status
- `screenshots/`, browser-verification evidence when applicable

The integration worktree and run branch survive until the PR merges. Task and disposable QA worktrees are removed using only the IDs recorded in the run manifest.

## References

- [`SKILL.md`](./SKILL.md), the complete pipeline and safety rules
- [`references/routing.md`](./references/routing.md), model routing, complexity tiers, and worker boot recipes
- [`references/plan-template.md`](./references/plan-template.md), the plan format
- [`references/assignment-context.md`](./references/assignment-context.md), the worker assignment format
- [Orca on GitHub](https://github.com/stablyai/orca), the external CLI and runtime
