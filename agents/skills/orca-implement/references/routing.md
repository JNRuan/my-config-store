# Routing and worker boot

**Concurrency cap**: 5 builders. Workers' native subagents do not count.

## Coordinator-relative roles

These roles follow the runtime that runs `/orca-implement`.


| Role                 | Claude coordinator   | Codex coordinator      | Effort (Claude / Codex) | Notes                                                                                             |
| -------------------- | -------------------- | ---------------------- | ----------------------- | ------------------------------------------------------------------------------------------------- |
| Coordinator          | the invoking session | the invoking session   | session / session       | never writes implementation code; trivial-fix and trivial-merge-conflict exceptions only          |
| Browser verification | `sonnet` subagent    | `gpt-5.6-sol` subagent | `medium` / `medium`     | mapped browser skill (`references/skill-map.md`), headless; native subagent, not an Orca terminal |


This browser row governs the round 1 browser verification in Phase 7 and its scoped reruns. Worker-invoked skills own the routing of any subagents they spawn.

## Pinned roles

Identical regardless of coordinator.


| Role                          | Runtime / model                                                                                                        | Effort          | Fallback                                                | Notes                                                                                                                                                                                                        |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------- | --------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Scouts                        | Codex `gpt-5.6-luna`                                                                                                   | `high`          | —                                                       | read-only; Orca terminals in `<WT>`; one report per lens                                                                                                                                                     |
| Plan fact check               | Codex `gpt-5.6-luna`                                                                                                   | `high`          | —                                                       | read-only; Orca terminal in `<WT>`; verifies checkable plan claims only; runs before critique and again after it when critique changed the plan                                                              |
| Acceptance check              | Claude `opus`                                                                                                          | `high`          | `Codex gpt-5.6-sol`                                     | read-only; Orca terminal in `<WT>`; verifies each acceptance criterion against the integrated HEAD; one report per pass                                                                                      |
| Planner, `low`/`medium` tier  | Claude `fable`                                                                                                         | `medium`        | coordinator drafts the plan                             | single planner; a complete plan from the brief; writes only its own draft file                                                                                                                               |
| Planners, `high`/`xhigh` tier | Claude `fable` + Codex `gpt-6-astra`                                                                                   | `high` all      | continue with the surviving planner                     | independent complete plans from the brief; each writes only its own draft file                                                                                                                               |
| Plan critics                  | Claude `fable` + Codex `gpt-6-astra`                                                                                   | `xhigh` all     | continue with the surviving critic                      | both, one round only; critique adversarially; read-only by instruction                                                                                                                                       |
| Builder, `low` complexity     | Codex `gpt-5.6-sol`                                                                                                    | `medium`        | —                                                       |                                                                                                                                                                                                              |
| Builder, `medium`             | Codex `gpt-6-astra`                                                                                                    | `medium`        | —                                                       | default builder                                                                                                                                                                                              |
| Builder, `high`               | Codex `gpt-6-astra`                                                                                                    | `high`          | `Claude fable or Claude opus or Codex gpt-5.6-sol`      | many-file or mechanically hard, but fully specified by plan + contracts                                                                                                                                      |
| Builder, `xhigh`              | Claude `fable`                                                                                                         | `xhigh`         | `Codex gpt-6-astra or Claude opus or Codex gpt-5.6-sol` | the remaining reasoning is the risk: see the task complexity rubric                                                                                                                                          |
| Code reviewers                | Claude `fable` + Codex `gpt-6-astra`                                                                                   | `high` / `high` | `Codex gpt-5.6-sol or Claude Opus`                      | both each round; round cap from `run_complexity`                                                                                                                                                             |
| Security reviewers            | Claude `fable` + Codex `gpt-6-astra`                                                                                   | `high` / `high` | `Codex gpt-5.6-sol or Claude Opus`                      | `medium` and above only; both in round 1, dispatched alongside the code reviewers; later rounds only on the Phase 7 security trigger; each runs the mapped security-review skill (`references/skill-map.md`) |
| Adversarial QA                | Cross-model to the builder of the highest-complexity merged task: Claude → Codex `gpt-6-astra`; Codex → Claude `fable` | `high`          | `Claude opus or Codex gpt-5.6-sol`                      | `medium`/`high`/`xhigh` runs only; runs once after all code-review rounds and fixes; disposable worktree, branch never merged                                                                                |


If a Fable worker fails to boot or run, use the listed fallback model.

Classify every fix with the task-complexity rubric and route it through the matching builder row, including that row's fallback.

## Review tiers and depth

Review depth uses two assessments of aggregate risk. Consider affected area, coupling, novelty, failure impact, and observability.

Classify `plan_review_tier` after the understanding check. It controls the drafting mode.

Classify `run_complexity` from the reviewed plan. It controls code-review depth and QA. It may be higher or lower than `plan_review_tier`.

Both are independent of per-task builder complexity.


| Tier     | Typical run shape                                                                                             | Code-review rounds when used as `run_complexity` | Security review from `run_complexity`      | Adversarial QA from `run_complexity` |
| -------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------ | ------------------------------------ |
| `low`    | narrow, localised, established pattern, low-impact failure, strong existing coverage                          | 1                                                | no                                         | no                                   |
| `medium` | several files or one subsystem, ordinary cross-layer interaction, moderate blast radius                       | 2                                                | with code review: round 1, then on trigger | yes, after code review               |
| `high`   | broad or highly coupled change, important state or user-flow risk, weak observability, or high failure impact | 3                                                | with code review: round 1, then on trigger | yes, after code review               |
| `xhigh`  | systemic or novel change with subtle invariants, architectural consequences, or severe failure impact         | 5                                                | with code review: round 1, then on trigger | yes, after code review               |


This table is the sole tier-to-policy mapping. Auth/authz, payments, destructive data migration, security-critical logic, and concurrency or consistency primitives are never below `high`.

## Task complexity and builder routing

Classify each task after drafting the plan. Task complexity is what remains for the builder once the plan pins contracts, constraints, and relevant-code pointers. If planning removed the judgement, the tier drops.


| Tier     | What remains for the builder        | Typical signals                                                                                                                                                                                                                                                                                                                                                                                                  |
| -------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `low`    | Execute a near-dictated diff        | the solution is already clear, with one or two trivial touchpoints: renames, formatting, config/copy changes, plumbing a field through an existing pipeline, a change spelled out that needs no interpretation                                                                                                                                                                                                   |
| `medium` | Local decisions inside one area     | one module or layer, established conventions; more modules only when the changes are simple with a small impact surface: a new endpoint or component following existing shapes, a bugfix needing investigation within one subsystem; changes stay behind existing interfaces; moving a contract other modules depend on means `high` or above                                                                    |
| `high`   | Heavy execution, routine reasoning  | crosses module or layer boundaries with substantial changes on each side, but the plan pins every decision: cross-layer features against pinned contracts, mechanical migrations, specified algorithms with a wide but enumerable blast radius; the hard part is volume, sequencing, and consistency, not invention                                                                                              |
| `xhigh`  | The remaining reasoning is the risk | the plan cannot pin the hard part, because correctness depends on sustained, subtle reasoning during implementation: concurrency and consistency invariants, intricate algorithms or complex state, security-critical logic, contract or schema changes that propagate to consumers, novel abstractions others build on, refactors whose "how" only emerges mid-implementation, ambiguity that survives planning |


Rules:

- The hardest remaining part sets the tier, not the amount of code. A 30-file mechanical rename is `high`; a one-file lock-ordering change can be `xhigh`.
- When two adjacent tiers up to `high` both appear plausible, choose the higher. The cost is only effort.
- Between `high` and `xhigh`, ask whether more planning would make the work routine. If so, pin the decision and use `high`.
- Use `xhigh` when difficult reasoning or ambiguity remains during implementation. Nothing should reach a builder with its key decisions unresolved.
- Apply two tie-break tests:
  1. Would two competent developers produce much the same diff? If yes, use `high`.
  2. Would a mistake fail loudly in build, tests, or review, or could it reach the PR silently? A silent failure points to `xhigh`.
- Auth/authz, payments, data migration or deletion, and concurrency primitives: never below `high`; use `xhigh` when the approach is not pinned.
- `xhigh` judgement operates within the human-approved plan. Settle a decision the human must own, such as an architectural fork, a security decision, or a destructive data operation, at the understanding check or the plan gate. Never delegate it to a builder.
- Split a task that reads `xhigh` because it mixes concerns. Concentrate the judgement in one `xhigh` task so the remainder drops to `high` or below.

## Worker boot

Boot workers with `terminal create` and an explicit `--command`, never `worker-start`. Orca command syntax comes from the guides loaded at intake through the `orchestration` skill.

- Substitute model and effort from the tables. Title each terminal `<role>:<slug>`.
- The `nclaude` and `ncodex` aliases run workers through the `my-claude` and `my-codex` nono profiles. The outer nono sandbox controls network and filesystem access.
- Codex's sandbox cannot nest inside nono. Pass `--sandbox danger-full-access` to each Codex worker command. Do not set it in machine configuration.
- Workers in `<WT>` use the aliases. Workers in task or QA worktrees write to `<RUNDIR>` in the integration worktree, which the aliases do not grant, so boot them with `nono run` and `--allow "<RUNDIR>"`. For Codex, `--add-dir` only tells Codex the directory exists. The nono grant enforces access.

**Claude in `<WT>`** (planner, critic, reviewer, acceptance check):

```bash
nclaude --model <fable|opus> --effort <effort> --permission-mode bypassPermissions
```

**Claude in a task or QA worktree** (builder, fix, QA):

```bash
nono run --profile my-claude --allow-cwd --allow "<RUNDIR>" -- claude --model <fable|opus> --effort <effort> --permission-mode bypassPermissions
```

**Codex in `<WT>`** (scout, plan fact check, planner, critic, reviewer):

```bash
ncodex --model <gpt-5.6-luna|gpt-6-astra|gpt-5.6-sol> -c 'model_reasoning_effort="<effort>"' --sandbox danger-full-access --ask-for-approval never
```

**Codex in a task or QA worktree** (builder, fix, QA):

```bash
nono run --profile my-codex --allow-cwd --allow "<RUNDIR>" -- codex --model <gpt-6-astra|gpt-5.6-sol> -c 'model_reasoning_effort="<effort>"' --sandbox danger-full-access --add-dir "<RUNDIR>" --ask-for-approval never
```

