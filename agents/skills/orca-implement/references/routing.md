# Routing &amp; worker boot recipes

**Concurrency cap**: 5 concurrent builders (Orca worker terminals; workers' internal native subagents are not counted).

## Coordinator-relative roles

Resolved by which runtime runs `/orca-implement`.


| Role                 | Claude coordinator   | Codex coordinator       | Effort (Claude / Codex) | Notes                                                                                      |
| -------------------- | -------------------- | ----------------------- | ----------------------- | ------------------------------------------------------------------------------------------ |
| Coordinator          | the invoking session | the invoking session    | session / session       | never writes implementation code; trivial-fix and trivial-merge-conflict exceptions only   |
| Scouts               | `sonnet` subagent    | `gpt-5.6-luna` subagent | `medium` / `medium`     | read-only; native subagents, not Orca terminals                                            |
| Plan fact check      | `sonnet` subagent    | `gpt-5.6-luna` subagent | `medium` / `high`       | read-only; verifies the plan's checkable claims only, no content judgment; native subagent |
| Browser verification | `sonnet` subagent    | `gpt-5.6-luna` subagent | `high` / `xhigh`        | `agent-browser`, headless; native subagent, not an Orca terminal                           |


## Pinned roles

Identical regardless of coordinator.


| Role                      | Runtime / model                                      | Effort          | Fable unavailable fallback      | Notes                                                                                                                                                                                                                                                                                            |
| ------------------------- | ---------------------------------------------------- | --------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Plan drafters             | Claude `fable` + Codex `gpt-5.6-sol`                 | `high` / `high` | Opus `high`                     | `medium`/`high`/`xhigh` `plan_review_tier` only; independent complete plans from the brief; each writes only its own draft file; a drafter lost at runtime is retried once on a fresh terminal; failing twice, its surviving peer's draft becomes the base, no drafts → coordinator drafts alone |
| Plan critics              | Claude `fable` + Claude `opus` + Codex `gpt-5.6-sol` | `high` all      | continue with surviving critics | all three each round; adversarial mandate; read-only by instruction; round cap comes from `plan_review_tier`                                                                                                                                                                                     |
| Builder, `low` complexity | Codex `gpt-5.6-sol`                                  | `medium`        | —                               |                                                                                                                                                                                                                                                                                                  |
| Builder, `medium`         | Codex `gpt-5.6-sol`                                 | `high`          | —                               | default builder                                                                                                                                                                                                                                                                                  |
| Builder, `high`           | Claude `opus`                                        | `high`          | —                               | many-file or mechanically hard, but fully specified by plan + contracts                                                                                                                                                                                                                          |
| Builder, `xhigh`          | Claude `fable`                                       | `high`          | `gpt-5.6-sol` `xhigh`           | the remaining reasoning is the risk: see the task complexity rubric                                                                                                                                                                                                                              |
| Reviewers                 | Claude `fable` + Codex `gpt-5.6-sol`                 | `high` / `high` | Opus `high`                     | both each round; round cap comes from `run_complexity`                                                                                                                                                                                                                                           |
| Adversarial QA            | Claude `fable`                                        | `high`          | Opus `high`                     | `high`/`xhigh` runs only; runs once after all code-review rounds and fixes; disposable worktree, branch never merged                                                                                                                                                                             |


If a Fable worker fails to boot or run, use the listed fallback model. Record the requested model, selected model, and reason in `run-state.json`. If the fallback agent also does not run, use the role's normal phase failure path.

Every fix is classified with the task-complexity rubric and routed through the matching builder row, including that row's fallback.

## Review tiers and depth

Review depth uses two separate assessments of aggregate risk (blast radius, coupling, novelty, failure impact, and observability), both independent of per-task builder complexity:

1. After the understanding check, classify the run as `plan_review_tier` from the requirements and scout evidence, and snapshot only the plan-critique cap. The tier selects the plan drafting mode — `medium`/`high`/`xhigh` runs competitive drafting, `low` the coordinator drafts alone — and stays fixed with its cap throughout critique.
2. After critique ends, assess canonical `run_complexity` from the reviewed plan. It may be higher or lower than `plan_review_tier` and determines code-review depth and QA.


| Tier     | Typical run shape                                                                                             | Plan rounds when used as `plan_review_tier` | Code-review rounds when used as `run_complexity` | Adversarial QA from `run_complexity` |
| -------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------ | ------------------------------------ |
| `low`    | narrow, localized, established pattern, low-impact failure, strong existing coverage                          | 1                                           | 1                                                | no                                   |
| `medium` | several files or one subsystem, ordinary cross-layer interaction, moderate blast radius                       | 2                                           | 2                                                | no                                   |
| `high`   | broad or highly coupled change, important state or user-flow risk, weak observability, or high failure impact | 3                                           | 3                                                | yes, after code review               |
| `xhigh`  | systemic or novel change with subtle invariants, architectural consequences, or severe failure impact         | 5                                           | 5                                                | yes, after code review               |


This table is the sole tier-to-policy mapping. Auth/authz, payments, destructive data migration, security-critical logic, and concurrency or consistency primitives are never below `high`.

## Task complexity and builder routing

Classify each task after the plan is drafted: task complexity is what remains for the builder once contracts, constraints, and relevant-code pointers are pinned. If planning removed the judgment, the tier drops.


| Tier     | What remains for the builder        | Typical signals                                                                                                                                                                                                                                                                                                                                                                                       |
| -------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `low`    | Execute a near-dictated diff        | the solution is simple and already clear, with one or two simple or trivial touchpoints: renames, formatting, config/copy changes, plumbing a field through an existing pipeline, a change spelled out explicitly that needs no interpretation                                                                                                                                                        |
| `medium` | Local decisions inside one area     | one module or layer, established conventions — more modules only when the changes are simple with a small impact surface: a new endpoint or component following existing shapes, a bugfix needing investigation within one subsystem; changes stay behind existing interfaces — a contract other modules depend on moving means `high` or above                                                       |
| `high`   | Heavy execution, routine reasoning  | crosses module or layer boundaries with substantial changes on each side, but the plan pins every decision: cross-layer features against pinned contracts, mechanical migrations, specced algorithms — blast radius wide but enumerable; the hard part is volume, sequencing, and consistency, not invention                                                                                          |
| `xhigh`  | The remaining reasoning is the risk | the plan cannot pin the hard part — correctness hinges on sustained, subtle reasoning during implementation: concurrency and consistency invariants, intricate algorithms or complex state, security-critical logic, contract or schema changes that ripple to consumers, novel abstractions others build on, refactors whose "how" only emerges mid-implementation, ambiguity that survives planning |


Rules:

- The tier is set by the hardest remaining part, not its bulk. Signals trump size: a 30-file mechanical rename is `high`; a one-file lock-ordering change can be `xhigh`.
- Torn between adjacent tiers up through `high`: take the higher — the cost is only effort. Torn between `high` and `xhigh`: ask whether more planning would make the remaining work routine — pin what can be pinned and route `high`. Nothing should reach a builder undecided; route `xhigh` when the difficulty lives in the reasoning itself, or when complex ambiguity survives planning. Two tests break the tie: would two competent developers produce essentially the same diff (same → `high`), and would a mistake fail loudly in build, tests, or review, or ship silently (silent → `xhigh`)?
- Auth/authz, payments, data migration or deletion, and concurrency primitives: never below `high`; `xhigh` when the approach is not pinned.
- `xhigh` judgment operates within the human-approved plan. A decision the human must own (architectural fork, security decision, destructive data operation) is settled at the understanding check or the plan gate — never delegated to a builder.
- A task that reads `xhigh` because it mixes concerns is a decomposition smell: split it so the judgment concentrates in one `xhigh` task and the remainder drops to `high` or below.

## Boot recipes

- Substitute model and effort from the tables.
- Confinement comes from the outer nono sandbox (the `nclaude`/`ncodex` aliases, backed by the `my-claude`/`my-codex` profiles), which also governs network access. Codex's own sandbox cannot nest inside nono: every Codex worker passes `--sandbox danger-full-access` in the recipe, never relying on machine config.
- Codex workers booted outside the integration worktree (builders and fix workers in task worktrees, QA in its disposable worktree) need `<RUNDIR>` for their report/findings paths, which live in the integration worktree. `--add-dir` informs Codex only; the nono grant requires `--allow "<RUNDIR>"`, so these workers boot with the expanded `nono run` command instead of the `ncodex` alias.
- Workers booted in `<WT>` (reviewers, plan critics) use the `ncodex` alias with no extra grant.
- After every `terminal create`, capture `.result.terminal.handle` into the run manifest and `terminal wait --for tui-idle --timeout-ms 120000` before dispatching.

**Claude worker (builder / reviewer / fix)**:

```bash
orca terminal create --worktree <WT-or-task-worktree> --title "<role>:<slug>" \
  --command "nclaude --model <fable|opus> --effort <effort> --permission-mode bypassPermissions" --json
```

**Codex worker in `<WT>` (reviewer)**:

```bash
orca terminal create --worktree <WT> --title "<role>:<slug>" \
  --command "ncodex --model gpt-5.6-sol -c 'model_reasoning_effort=\"<effort>\"' --sandbox danger-full-access --ask-for-approval never" --json
```

**Codex worker in a task or QA worktree (builder / fix / QA)**:

```bash
orca terminal create --worktree <task-or-qa-worktree> --title "<role>:<slug>" \
  --command "nono run --profile my-codex --allow-cwd --allow \"<RUNDIR>\" -- codex --model gpt-5.6-sol -c 'model_reasoning_effort=\"<effort>\"' --sandbox danger-full-access --add-dir \"<RUNDIR>\" --ask-for-approval never" --json
```

**Plan drafters**:

```bash
orca terminal create --worktree <WT> --title "plan-draft-fable" \
  --command "nclaude --model fable --effort high --permission-mode bypassPermissions" --json
# Fable-unavailable fallback: same recipe with --model opus

orca terminal create --worktree <WT> --title "plan-draft-sol" \
  --command "ncodex --model gpt-5.6-sol -c 'model_reasoning_effort=\"high\"' --sandbox danger-full-access --ask-for-approval never" --json
```

**Plan critics**:

```bash
orca terminal create --worktree <WT> --title "plan-critic-fable" \
  --command "nclaude --model fable --effort high --permission-mode bypassPermissions" --json

orca terminal create --worktree <WT> --title "plan-critic-opus" \
  --command "nclaude --model opus --effort high --permission-mode bypassPermissions" --json

orca terminal create --worktree <WT> --title "plan-critic-sol" \
  --command "ncodex --model gpt-5.6-sol -c 'model_reasoning_effort=\"high\"' --sandbox danger-full-access --ask-for-approval never" --json
```

