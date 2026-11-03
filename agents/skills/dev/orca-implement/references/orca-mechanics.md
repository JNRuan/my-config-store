# Orca runtime mechanics

This file defines the integration policy for `/orca-implement`. Use Orca Orchestration to register
and manage supervised workers. Load the `orchestration` skill and follow its instructions for
assignment, messages, follow-ups, recovery, and cleanup. Use `orca-cli` for other Orca resources.

Phase instructions own workflow, verification, retry limits, and resource ownership.
`references/routing.md` owns sandboxed launch commands. Orca Orchestration owns command syntax,
response fields, and worker lifecycle mechanics.

## 1.0 Record run ownership

1. Record every handle, id, path, branch, and dispatch id in `run-state.json` when Orca creates it.
2. Use the manifest rather than deriving identifiers later.
3. After an Orca restart, recover worker identities through Orca Orchestration using the recorded
   run and dispatch ids. Treat terminal titles as metadata, not proof of identity or ownership.
4. Act on a live resource only when the manifest proves that this run owns it.

## 2.0 Use Orca Orchestration

Follow the `orchestration` skill for worker operations and `orca-cli` for other Orca resources.
Follow each receipt's next action. Resolve uncertain startup or cleanup through Orca Orchestration
before another mutation. When a required operation is unsupported, use the current phase's failure
path. Preserve the sandbox requirements in `references/routing.md` during every recovery.

## 3.0 Receive orchestration messages

1. Follow Orca Orchestration for waiting, message consumption, and recovery of interrupted reads.
2. Save the current phase and worker identities before yielding. Keep the run `active` while it
   awaits workers. Reserve `awaiting_input` for a decision the human must make.
3. Correlate messages with this run's recorded active Orca task and dispatch ids. Record messages
   for superseded attempts without applying them to the current attempt. Ignore other runs' mail.
4. Resolve questions within the approved brief. Use the Human touchpoints rule for other decisions.
5. Follow Orca Orchestration to inspect and continue stopped workers. Silence or a timeout alone
   does not authorise stopping or replacing a worker.
6. Require a successful completion outcome and a non-empty report from the active attempt before
   marking a collected task complete in the manifest.

Orca Orchestration owns task and dispatch settlement. Follow its recovery instructions for failed
attempts. Do not manually mark a worker's reported failure as successful.

Orca task state records the worker signal. The manifest records whether the coordinator verified and
merged the result.

## 4.0 Dispatch a phase worker

Phase workers are scouts, fact checks, planners, critics, the acceptance check, reviewers, and QA.
Builders follow Phase 5 and the rules for every worker below.

1. For a worker in `<WT>`, record `<WT>` HEAD as `<H>`.
2. Resolve every required value in the role context and task template.
3. Launch the routed sandboxed terminal from `references/routing.md`, titled `<role>:<slug>`.
   Record it as a run-owned terminal before assignment.
4. Register that terminal and assign the task under this run through Orca Orchestration.
5. Record the task, dispatch, and worker identities returned in the manifest. Record terminal
   metadata only when Orca identifies a terminal. Confirm assignment through the startup receipt.

For every worker, including builders:

- Follow Orca Orchestration for readiness, delivery confirmation, and command failure. Do not
  resend a task or start a replacement while the previous operation's outcome is unresolved.
- After one confirmed recovery failure, follow the current phase's failure path. Builders enter fix
  or retry handling.

Use Orca Orchestration to inspect worker status and output. Structured completion outcomes and
designated report files are the result; status output alone is not.

## 5.0 Collect a phase worker

1. Collect through [Receive orchestration messages](#30-receive-orchestration-messages) until the
   dispatch settles. Resolve questions and permission prompts before considering a retry.
2. Require a successful completion outcome and a non-empty report from the active attempt.
3. For a worker in `<WT>`, run the read-only check. For a parallel panel, defer the check until
   every worker and allowed retry has reached a terminal outcome, then check the whole panel once.
4. Record the collected reports in the manifest after the check passes.
5. Follow [Manage terminals and worktrees](#70-manage-terminals-and-worktrees) for cleanup or reuse.

### Read-only check

Require:

```bash
git -C <WT-PATH> status --porcelain -- ':!.agents/orca/orchestration'
git -C <WT-PATH> status --porcelain --ignored=matching -- .agents/orca/orchestration
git -C <WT-PATH> rev-parse HEAD
```

The first command must return no output. The second must list only reports expected from the worker
or whole panel being collected, including retries, and the coordinator's own manifest and artifact
edits. HEAD must equal `<H>`. Do not commit anything between recording `<H>` and running the check.

Before deleting files or restoring the worktree, stop any workers that can
still write to it. Confirm that the changes and files to be discarded come
from this run's read-only workers. If ownership is unclear or any affected
work belongs to someone else, leave it intact and follow the current phase's
failure path.

Delete any unexpected file under the run folder and record the incident.

If the first or third check fails, restore the integration worktree while preserving the run folder:

```bash
git -C <WT-PATH> reset --mixed <H>
git -C <WT-PATH> restore --worktree -- . ':!.agents/orca/orchestration'
git -C <WT-PATH> clean -fd -- ':!.agents/orca/orchestration'
```

Rerun all three checks. They must pass before recording any report. Record the incident in the
manifest and `summary.md`.

## 6.0 Retry a phase worker

For a confirmed failed attempt, or a settled dispatch with a missing or empty report:

1. Follow Orca Orchestration's recovery instructions. Confirm the previous worker stopped before
   starting a replacement or closing its terminal. Leave unresolved resources intact.
2. Launch a fresh sandboxed terminal from `references/routing.md`. Use the listed fallback when
   the model is unavailable. Never substitute one panel member for another.
3. Register the replacement through Orca Orchestration. Retry an execution failure on the same Orca
   Task in its owning Run; for a settled success with a missing report, follow its follow-up
   procedure. Record returned identities and retain the previous dispatch id before collection.

Retry each worker once, subject to Orca Orchestration's recovery requirements and circuit breaker.
The phase says what happens when the retry also fails.

## 7.0 Manage terminals and worktrees

- `worktree create` controls the requested worktree name. Record the actual branch returned by Orca.
- Inspect any terminal that worktree creation starts. A running setup terminal is the repository's
  `orca.yaml` setup script. Wait for it to exit before booting a worker there. A non-zero exit is a
  worktree-setup failure. Read its output, remove the worktree, and retry the create once. If it
  fails again, follow the current phase's failure path. Close any other terminal only when it is an
  unused shell. Record any terminal you keep.
- Record the integration worktree's default terminal in the manifest and keep it until teardown. For
  an adopted integration worktree, record no pre-existing terminal. Teardown touches only recorded
  terminals. Record custom sandboxed worker launches here too. Orca-managed resources are tracked
  by their dispatch ids; do not infer ownership from a terminal title.
- Follow Orca Orchestration for worker release, reuse, and recovery. Reuse builder and reviewer
  conversations subject to `references/routing.md`'s sandbox policy. If safe conversation resume is
  unavailable, give a fresh sandboxed worker the agent task and prior reports as context.
- Before removing a task or QA worktree, confirm no worker can still write to it. Resolve every
  recorded dispatch's resources through Orca Orchestration. Use `orca-cli` for separately created,
  run-owned terminals only after confirming their identity and that no worker still uses them.
  Respect retention and ownership refusals. Record unresolved resources as partial cleanup.
- Remove task worktrees after their branches merge.
- If a failed task's worktree contains uncommitted or untracked changes, retain it. Record its id
  and path in the manifest and `summary.md`, and mark cleanup `partial`.
- Before removing a failed task's worktree, confirm that removal preserves its branch. If it does
  not, create the local tag `orca-run/<RUN>/{slug}` at the branch tip first. Never push the tag.
- Apply the concurrency cap only to builders. Scout, fact-check, planner, critic, acceptance-check,
  reviewer, and QA terminals are additional phase-bound resources.

## 8.0 Operational safety

- Code reaches the target branch only through a human-approved PR. The human owns approval and
  merge.
- Only `<RUN-BRANCH>` may reach the remote, and only in Phase 9.
- Workers write code only in their assigned worktree.
- Workers write under `<RUNDIR>` only to their designated files.
- Enforce read-only workers through the read-only check above.
- When `qa_policy` is `run`, QA may write only:
  - its disposable worktree;
  - `<RUNDIR>/scratch/qa-findings.md`;
  - `<RUNDIR>/screenshots/`.
- Never merge the QA branch.
