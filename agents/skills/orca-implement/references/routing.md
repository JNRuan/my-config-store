# Routing & worker boot recipes

**Concurrency cap**: 5 concurrent builders (Orca worker terminals; workers' internal native subagents are not counted).

## Coordinator-relative roles

Resolved by which runtime runs `/orca-implement`.


| Role                  | Claude coordinator   | Codex coordinator        | Effort   | Notes                                                                                         |
| --------------------- | -------------------- | ------------------------ | -------- | --------------------------------------------------------------------------------------------- |
| Coordinator           | the invoking session | the invoking session     | session  | never writes implementation code; trivial-fix and trivial-merge-conflict exceptions only      |
| Scouts                | `sonnet` subagent    | `gpt-5.6-luna` subagent  | `medium` | read-only; native subagents, not Orca terminals                                               |
| Plan fact check       | `sonnet` subagent    | `gpt-5.6-luna` subagent  | `medium` | read-only; verifies the plan's checkable claims only, no content judgment; native subagent    |
| Browser verification  | `sonnet` subagent    | `gpt-5.6-terra` subagent | `high`   | `agent-browser`, headless; native subagent, not an Orca terminal                              |

## Pinned roles

Identical regardless of coordinator.


| Role                             | Runtime / model                      | Effort            | Notes                                                                                                                               |
| -------------------------------- | ------------------------------------ | ----------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Plan critics                     | Claude `fable` + Codex `gpt-5.6-sol` | `xhigh` / `xhigh` | both, always; read-only by instruction (see recipes); two Orca terminals; up to two rounds                                          |
| Builder, `low` complexity        | Codex `gpt-5.6-sol`                  | `medium`          |                                                                                                                                     |
| Builder, `medium`                | Codex `gpt-5.6-sol`                  | `high`            | default builder                                                                                                                     |
| Builder, `high`                  | Codex `gpt-5.6-sol`                  | `xhigh`           | many-file or mechanically hard, but fully specified by plan + contracts                                                             |
| Builder, `xhigh`                 | Claude `fable`                       | `high`            | the remaining reasoning is the risk: see the complexity rubric                                                                      |
| Reviewers                        | Claude `fable` + Codex `gpt-5.6-sol` | `high` / `high`   | both, always; two rounds (round 2 skipped when round 1 fixed nothing)                                                               |
| Adversarial QA                   | Codex `gpt-5.6-sol`                  | `high`            | runs `/adversarial-review`; round 1 only; requires the skill in the Codex skills dir Orca terminals see; disposable worktree, branch never merged |
| Fix wave                         | per triage                           | per complexity    | prefer the model that did not write the code under fix; otherwise route by complexity                                              |


## Complexity rubric

Classify each task after the plan is drafted, not before: complexity is what remains for the builder once contracts, constraints, and relevant-code pointers are pinned. If planning removed the judgment, the tier drops.

| Tier     | What remains for the builder            | Typical signals                                                                                                                                                          |
| -------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `low`    | Execute a near-dictated diff            | one concern, existing pattern, few files: renames, plumbing a field through an existing pipeline, config changes, a bugfix with a known root cause                       |
| `medium` | Local decisions inside one area         | one module or layer, established conventions, several files: a new endpoint or component following existing shapes, a bugfix needing investigation within one subsystem |
| `high`   | Heavy execution, routine reasoning      | many files or layers, careful sequencing, wide but predictable blast radius, every step conventional once the plan pins the target: cross-layer features against pinned contracts, mechanical migrations, specced algorithms |
| `xhigh`  | The remaining reasoning is the risk     | correctness hinges on sustained, subtle reasoning no plan can pre-chew: concurrency and consistency invariants, intricate algorithms or state machines, security-critical logic, novel abstractions others build on, refactors whose "how" only emerges mid-implementation, complex ambiguity that survives planning |

Rules:

- Signals trump size: a 30-file mechanical rename is `high`; a one-file lock-ordering change can be `xhigh`.
- Torn between adjacent tiers up through `high`: take the higher — the cost is only effort. Torn between `high` and `xhigh`: ask whether more planning would make the remaining work routine — pin what can be pinned and route `high`. Nothing should reach a builder undecided; route `xhigh` when the difficulty lives in the reasoning itself, or when complex ambiguity survives planning.
- Auth/authz, payments, data migration or deletion, and concurrency primitives: never below `high`; `xhigh` when the approach is not pinned.
- `xhigh` judgment operates within the human-approved plan. A decision the human must own (architectural fork, security decision, destructive data operation) is settled at the understanding check or the plan gate — never delegated to a builder.
- A task that reads `xhigh` because it mixes concerns is a decomposition smell: split it so the judgment concentrates in one `xhigh` task and the remainder drops to `high` or below.

Fix-wave tasks classify by the same rubric, applied to the fix, not the original task.

## Boot recipes

Substitute model and effort from the tables. Codex workers booted outside the integration worktree (builders in task worktrees, QA in its disposable worktree) get `--add-dir "<RUNDIR>"` — their report/findings paths live in the integration worktree, outside their sandbox. Workers booted in `<WT>` (reviewers, plan critics, fix workers) omit it. After every `terminal create`, capture `.result.terminal.handle` into the run manifest and `terminal wait --for tui-idle --timeout-ms 120000` before dispatching.

**Claude worker (builder / reviewer / fix)**:

```bash
orca terminal create --worktree <WT-or-task-worktree> --title "<role>:<slug>" \
  --command "claude --model fable --effort <effort> --permission-mode bypassPermissions" --json
```

**Codex worker (builder / reviewer / QA / fix)**:

```bash
orca terminal create --worktree <WT-or-task-worktree> --title "<role>:<slug>" \
  --command "codex --model gpt-5.6-sol -c 'model_reasoning_effort=\"<effort>\"' -c 'sandbox_mode=\"workspace-write\"' -c 'sandbox_workspace_write.network_access=true' --add-dir \"<RUNDIR>\" --ask-for-approval never" --json
# drop --add-dir when booting in <WT> (reviewers, fix workers)
```

**Plan critics** (both boot, regardless of coordinator) — read-only by instruction, not by sandbox: each must write its `<RUNDIR>/plan-critique-<M>[-r2].md` and send its completion; the mandate text names its critique file as the only permitted write, and the coordinator verifies the integration worktree is untouched outside the run folder after collection.

```bash
# Codex critic (no network flag: critics only read the repo and write their critique):
orca terminal create --worktree <WT> --title "plan-critic-codex" \
  --command "codex --model gpt-5.6-sol -c 'model_reasoning_effort=\"xhigh\"' -c 'sandbox_mode=\"workspace-write\"' --ask-for-approval never" --json

# Claude critic:
orca terminal create --worktree <WT> --title "plan-critic-claude" \
  --command "claude --model fable --effort xhigh --permission-mode bypassPermissions" --json
```
