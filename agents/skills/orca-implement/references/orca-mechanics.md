# Orca runtime mechanics

This file defines how to run shared Orca operations for `/orca-implement`. Phase instructions define what happens and when. The version-matched Orca guides own command syntax, capabilities, response fields, and recovery commands.

## 1.0 Record run ownership

1. Record every handle, id, path, branch, and dispatch id in `run-state.json` when Orca creates it.
2. Use the manifest rather than deriving identifiers later.
3. After an Orca restart, treat terminal handles as stale. Reacquire them by matching the recorded terminal title and worktree with live terminal state.
4. Act on a live resource only when the manifest proves that this run owns it.

## 2.0 Follow the live Orca contract

Load the version-matched `orchestration` and `orca-cli` guides before the first Orca mutation.

The guides own command names, flags, capabilities, response fields, and recovery commands. The skill owns workflow, resource ownership, and safety policy.

Do not guess syntax or repeat a mutation from memory. When a guide does not support a required operation, stop through the current phase's failure path.

## 3.0 Receive orchestration messages

1. Run `check --wait` in slices of at most 540000 ms. Use a shorter slice when the coordinator runtime's command timeout is lower.
2. Treat a timeout or empty delivery as a checkpoint.
3. Process every message in a delivery before acknowledging it.
4. Correlate `payload.taskId` and `payload.dispatchId` with an active manifest dispatch. Log and ignore messages for another run or a superseded dispatch.
5. Use `dispatch-show` when dispatch state is uncertain.
6. Mark a collected task complete in the manifest only after confirming that its required report is non-empty.

A valid `worker_done` completes its task and dispatch in Orca automatically. Do not follow it with a manual completion update.

Use manual task updates only for recovery:

- `ready` for a fix cycle;
- `failed` for a confirmed failure.

Orca task state records the worker signal. The manifest records whether the coordinator verified and merged the result.

## 4.0 Dispatch a phase worker

Phase workers are scouts, the fact check, planners, critics, reviewers, and QA. Builders follow Phase 5 and the rules for every worker below.

1. For a worker in `<WT>`, record `<WT>` HEAD as `<H>`.
2. Create the task under this run.
3. Start the routed terminal from `references/routing.md`, titled `<role>:<slug>`.
4. Wait for `tui-idle`. A terminal that is still starting drops injected input.
5. Resolve every required value in the role context and dispatch its template.
6. Record the task id, terminal handle, and dispatch id in the manifest.
7. Confirm receipt from the terminal and dispatch state. If the prompt left no trace, wait for readiness and inject it once more.

For every worker, including builders:

- If readiness times out, inspect the terminal before deciding whether the worker failed.
- If an Orca CLI command returns an error or loses its response, inspect its structured result and live Orca state, determine whether the command had an effect, and retry only when the live guide permits it or state proves that no effect occurred.
- After one confirmed recovery failure, follow the current phase's failure path. Builders enter fix or retry handling.

Prefer structured `worker_done` payloads and report files. Use bounded terminal output for status, not as the result.

## 5.0 Collect a phase worker

1. Wait through 3.0 until the dispatch is terminal. A worker is overdue after two consecutive slices with no message for it. Read its terminal. If it is active, keep waiting. Otherwise treat it as failed.
2. Require a non-empty report.
3. For a worker in `<WT>`, run the read-only check.
4. Commit the report and manifest.
5. Close the terminal unless the phase keeps it across rounds.

### Read-only check

Require:

```bash
git -C <WT-PATH> status --porcelain -- ':!.agents/orca/orchestration'
git -C <WT-PATH> status --porcelain -- .agents/orca/orchestration
git -C <WT-PATH> rev-parse HEAD
```

The first command must return no output. The second must list only the reports expected from this collection and the coordinator's own manifest and artifact edits. HEAD must equal `<H>`.

Delete any unexpected file under the run directory and record the incident.

If the first or third check fails, restore the integration worktree while preserving the run directory:

```bash
git -C <WT-PATH> reset --mixed <H>
git -C <WT-PATH> restore --worktree -- . ':!.agents/orca/orchestration'
git -C <WT-PATH> clean -fd -- ':!.agents/orca/orchestration'
```

Rerun all three checks. They must pass before committing any report. Record the incident in the manifest and `summary.md`.

## 6.0 Retry a phase worker

For a failed, overdue, or reportless worker:

1. Mark its task `failed` and close its terminal.
2. Start a fresh routed terminal. Use the listed fallback when the model is unavailable. Never substitute one panel member for another.
3. Create a fresh task with the same prompt, then dispatch and collect it.

Retry each worker once. The phase says what happens when the retry also fails.

## 7.0 Manage terminals and worktrees

- `worktree create` controls the requested worktree name. Record the actual branch returned by Orca.
- Inspect any terminal that worktree creation starts. Close it only when it is an unused shell. Record any terminal you keep.
- Keep a configured default tab of the integration worktree in the manifest until teardown. Close every terminal recorded for a task or QA worktree before removing that worktree.
- After accepting `worker_done`, follow the live guide's release or reuse procedure. Keep a terminal only for reuse. A builder keeps its terminal through fix cycles. Critics and reviewers keep theirs through their round loop.
- Remove task worktrees after their branches merge.
- Before removing a failed task's worktree, confirm that removal preserves its branch. If it does not, create the local tag `orca-run/<RUN>/{slug}` at the branch tip first. Never push the tag.
- Apply the concurrency cap only to builders. Scout, fact-check, planner, critic, reviewer, and QA terminals are additional phase-bound resources.

## 8.0 Operational safety

- Code reaches the target branch only through a human-approved PR. The human owns approval and merge.
- Only `<RUN-BRANCH>` may reach the remote, and only in Phase 9.
- Workers write code only in their assigned worktree.
- Worker writes under `<RUNDIR>` are limited to their designated files.
- Enforce read-only workers through the collection check above.
- When `qa_policy` is `run`, QA may write only:
  - its disposable worktree;
  - `<RUNDIR>/review/qa-findings.md`;
  - `<RUNDIR>/screenshots/`.
- Never merge the QA branch.
- Act only on runtime-global state that the manifest assigns to this run.
