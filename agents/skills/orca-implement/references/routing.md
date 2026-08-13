# Routing &amp; worker boot

**Concurrency cap**: 5 builders; workers' internal native subagents do not count.

## Coordinator-relative roles

These roles follow the runtime that runs `/orca-implement`.


| Role                 | Claude coordinator   | Codex coordinator       | Effort (Claude / Codex) | Notes                                                                                             |
| -------------------- | -------------------- | ----------------------- | ----------------------- | ------------------------------------------------------------------------------------------------- |
| Coordinator          | the invoking session | the invoking session    | session / session       | never writes implementation code; trivial-fix and trivial-merge-conflict exceptions only          |
| Scouts               | `sonnet` subagent    | `gpt-5.6-luna` subagent | `medium` / `medium`     | read-only; native subagents, not Orca terminals                                                   |
| Plan fact check      | `sonnet` subagent    | `gpt-5.6-luna` subagent | `medium` / `medium`     | read-only; verifies the plan's checkable claims only, no content judgment; native subagent        |
| Browser verification | `sonnet` subagent    | `gpt-5.6-sol` subagent  | `medium` / `medium`     | mapped browser skill (`references/skill-map.md`), headless; native subagent, not an Orca terminal |


## Pinned roles

Identical regardless of coordinator.


| Role                      | Runtime / model                                      | Effort          | Fable unavailable fallback      | Notes                                                                                                                                                       |
| ------------------------- | ---------------------------------------------------- | --------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Plan drafter, `low`/`medium` tier    | Claude `fable`                                       | `high`          | Opus `high`                      | single planner; a complete plan from the brief; writes only its own draft file                                                                              |
| Plan drafters, `high`/`xhigh` tier   | Claude `fable` + Claude `opus` + Codex `gpt-5.6-sol` | `high` all      | continue with surviving drafters | independent complete plans from the brief; each writes only its own draft file                                                                              |
| Plan critic, `low`/`medium` tier     | Codex `gpt-5.6-sol`                                  | `high`          | —                                | one critic each round; critique adversarially; read-only by instruction; round cap from `plan_review_tier`                                                  |
| Plan critics, `high`/`xhigh` tier    | Claude `fable` + Claude `opus` + Codex `gpt-5.6-sol` | `high` all      | continue with surviving critics  | all three each round; critique adversarially; read-only by instruction; round cap from `plan_review_tier`                                                   |
| Builder, `low` complexity | Codex `gpt-5.6-sol`                                  | `medium`        | —                               |                                                                                                                                                             |
| Builder, `medium`         | Codex `gpt-5.6-sol`                                  | `high`          | —                               | default builder                                                                                                                                             |
| Builder, `high`           | Claude `opus`                                        | `high`          | —                               | many-file or mechanically hard, but fully specified by plan + contracts                                                                                     |
| Builder, `xhigh`          | Claude `fable`                                       | `high`          | `gpt-5.6-sol` `xhigh`           | the remaining reasoning is the risk: see the task complexity rubric                                                                                         |
| Code reviewers            | Claude `fable` + Codex `gpt-5.6-sol`                 | `high` / `high` | Opus `high`                     | both each round; round cap from `run_complexity`                                                                                                            |
| Security reviewer         | Codex `gpt-5.6-sol`                                  | `high`          | —                               | one each round, dispatched alongside the code reviewers; runs the mapped security-review skill (`references/skill-map.md`); round cap from `run_complexity` |
| Adversarial QA            | Claude `fable`                                       | `high`          | Codex `gpt-5.6-sol`             | `high`/`xhigh` runs only; runs once after all code-review rounds and fixes; disposable worktree, branch never merged                                        |


If a Fable worker fails to boot or run, use the listed fallback model.

Classify every fix with the task-complexity rubric and route it through the matching builder row, including that row's fallback.

## Review tiers and depth

Review depth comes from two assessments of aggregate risk (blast radius, coupling, novelty, failure impact, and observability), both independent of per-task builder complexity. `plan_review_tier`, classified after the understanding check, sets the plan drafting mode and the plan-critique cap. `run_complexity`, assessed from the reviewed plan after critique, sets code-review depth and QA; it can be higher or lower than `plan_review_tier`.


| Tier     | Typical run shape                                                                                             | Plan rounds when used as `plan_review_tier` | Code-review rounds when used as `run_complexity` | Adversarial QA from `run_complexity` |
| -------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------ | ------------------------------------ |
| `low`    | narrow, localized, established pattern, low-impact failure, strong existing coverage                          | 1                                           | 1                                                | no                                   |
| `medium` | several files or one subsystem, ordinary cross-layer interaction, moderate blast radius                       | 2                                           | 2                                                | no                                   |
| `high`   | broad or highly coupled change, important state or user-flow risk, weak observability, or high failure impact | 3                                           | 3                                                | yes, after code review               |
| `xhigh`  | systemic or novel change with subtle invariants, architectural consequences, or severe failure impact         | 5                                           | 5                                                | yes, after code review               |


This table is the sole tier-to-policy mapping. Auth/authz, payments, destructive data migration, security-critical logic, and concurrency or consistency primitives are never below `high`.

## Task complexity and builder routing

Classify each task after the plan is drafted: task complexity is what remains for the builder once contracts, constraints, and relevant-code pointers are pinned. If planning removed the judgment, the tier drops.


| Tier     | What remains for the builder        | Typical signals                                                                                                                                                                                                                                                                                                                                                                                                  |
| -------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `low`    | Execute a near-dictated diff        | the solution is already clear, with one or two trivial touchpoints: renames, formatting, config/copy changes, plumbing a field through an existing pipeline, a change spelled out that needs no interpretation                                                                                                                                                                                                   |
| `medium` | Local decisions inside one area     | one module or layer, established conventions; more modules only when the changes are simple with a small impact surface: a new endpoint or component following existing shapes, a bugfix needing investigation within one subsystem; changes stay behind existing interfaces; moving a contract other modules depend on means `high` or above                                                                    |
| `high`   | Heavy execution, routine reasoning  | crosses module or layer boundaries with substantial changes on each side, but the plan pins every decision: cross-layer features against pinned contracts, mechanical migrations, specced algorithms with a wide but enumerable blast radius; the hard part is volume, sequencing, and consistency, not invention                                                                                                |
| `xhigh`  | The remaining reasoning is the risk | the plan cannot pin the hard part, because correctness depends on sustained, subtle reasoning during implementation: concurrency and consistency invariants, intricate algorithms or complex state, security-critical logic, contract or schema changes that propagate to consumers, novel abstractions others build on, refactors whose "how" only emerges mid-implementation, ambiguity that survives planning |


Rules:

- The hardest remaining part sets the tier, not its bulk. Signals beat size: a 30-file mechanical rename is `high`; a one-file lock-ordering change can be `xhigh`.
- When adjacent tiers both fit, up through `high`, take the higher; the cost is only effort. Between `high` and `xhigh`, ask whether more planning would make the remaining work routine; if it would, pin what can be pinned and route `high`. Nothing should reach a builder undecided; route `xhigh` when the reasoning itself is the difficulty, or when ambiguity survives planning. Two tests break the tie: would two competent developers produce essentially the same diff (same means `high`), and would a mistake fail loudly in build, tests, or review, or ship silently (silent means `xhigh`)?
- Auth/authz, payments, data migration or deletion, and concurrency primitives: never below `high`; `xhigh` when the approach is not pinned.
- `xhigh` judgment operates within the human-approved plan. Settle a decision the human must own (architectural fork, security decision, destructive data operation) at the understanding check or the plan gate; never delegate it to a builder.
- A task that reads `xhigh` because it mixes concerns is a decomposition smell: split it so the judgment concentrates in one `xhigh` task and the remainder drops to `high` or below.

## Worker boot

Boot workers with `terminal create` and an explicit `--command`, never `worker-start`. Orca command syntax comes from the guides loaded at preflight via the `orchestration` skill.

- Substitute model and effort from the tables. Title each terminal `<role>:<slug>`.
- The outer nono sandbox (aliases `nclaude`/`ncodex`, backed by the `my-claude`/`my-codex` profiles) confines every worker and governs its network access. Codex's own sandbox cannot nest inside nono: every Codex worker passes `--sandbox danger-full-access` in its command, never through machine config.
- Workers in `<WT>` (planners, critics, reviewers) use the aliases. Workers in task or QA worktrees write reports and findings to `<RUNDIR>` in the integration worktree, which the aliases do not grant: boot them with `nono run` and `--allow "<RUNDIR>"`. For Codex, `--add-dir` only tells Codex the directory exists; the nono grant enforces access.

**Claude in `<WT>`** (planner, critic, reviewer):

```bash
nclaude --model <fable|opus> --effort <effort> --permission-mode bypassPermissions
```

**Claude in a task or QA worktree** (builder, fix, QA):

```bash
nono run --profile my-claude --allow-cwd --allow "<RUNDIR>" -- claude --model <fable|opus> --effort <effort> --permission-mode bypassPermissions
```

**Codex in `<WT>`** (planner, critic, reviewer):

```bash
ncodex --model gpt-5.6-sol -c 'model_reasoning_effort="<effort>"' --sandbox danger-full-access --ask-for-approval never
```

**Codex in a task worktree** (builder, fix):

```bash
nono run --profile my-codex --allow-cwd --allow "<RUNDIR>" -- codex --model gpt-5.6-sol -c 'model_reasoning_effort="<effort>"' --sandbox danger-full-access --add-dir "<RUNDIR>" --ask-for-approval never
```

