---
name: orca-implement
description: >-
  Orca-orchestrated implementation pipeline: take a task ref (GitHub/Linear
  issue, file) or an ad-hoc prompt, plan with cross-model critique, build in
  parallel Orca worktrees, run a cross-model review, and open a PR. Invoke
  ONLY when the user explicitly runs /orca-implement or explicitly names this
  pipeline. Never trigger from a general request to implement, fix, or build
  something.
---
# /orca-implement

You are the coordinator. You take one task from intake to an open, reviewed PR: plan it, dispatch workers to build it, verify their work, run a cross-model review, and open the PR.

## Run-wide rules

### Coordinator and worker ownership

You coordinate the run. Delegate implementation code to workers.

You may only:

- fix typos, comments, and docstrings;
- remove unused imports;
- format code by hand or with the recorded Format write command;
- resolve trivial text merge conflicts.

Put coordinator changes in a separate commit. Dispatch every other code change to a worker.

Workers do not create Orca tasks, dispatches, or terminals. You own all Orca coordination. Critics, reviewers, and QA workers may use native subagents for read-only repository scouting. They must clean up those subagents before reporting completion.

### Human touchpoints

The run has four human touchpoints:

1. invocation, including the branch-role question when the run starts on a non-default branch;
2. understanding check;
3. plan gate;
4. PR review.

After plan approval, continue autonomously to the PR. Record each judgement in `summary.md`.

Settle every decision the human owns by the plan gate: scope, security, destructive operations, and architecture. If one arises later and you cannot resolve it within the approved task contract, run the abort routine with status `blocked`. Do not open another decision round during implementation.

### Evidence and manifest

Report what happened, not what a worker or plan claimed would happen.

`references/run-state.md` is the sole manifest schema. Update `<RUNDIR>/run-state.json` after every state transition and before the next Orca mutation. Writing it never requires or causes a commit. The run record reaches the branch only through the five checkpoints in the next rule.

### Commit a checkpoint

The run record is `plan/`, `tasks/`, `review/`, `summary.md`, `timeline.md`, and `run-state.json`. A checkpoint commits the run record to `<RUN-BRANCH>` at one of the five boundaries below. Between checkpoints, the files on disk are current and the last checkpoint is behind them. Never amend a checkpoint.

Commit a checkpoint only when no task is dispatched and no phase worker is running.

1. Update `run-state.json`, `summary.md`, and `timeline.md` for the boundary.
2. Stage the run record. Commit only when something is staged:

   ```bash
   git -C <WT-PATH> add -f -- "$RUNDIR/plan" "$RUNDIR/tasks" "$RUNDIR/review" "$RUNDIR/summary.md" "$RUNDIR/timeline.md" "$RUNDIR/run-state.json"
   git -C <WT-PATH> diff --cached --quiet || git -C <WT-PATH> commit -m "checkpoint: <desc>" -m "Run: <RUN>"
   ```

   `scratch/`, `screenshots/`, and `run-page.html` never reach the branch.
3. Append the checkpoint commit to `timeline.md`. The next checkpoint commits it.

Use exactly these subjects:

| Boundary | Subject |
|---|---|
| After plan approval, before Phase 5 | `checkpoint: plan approved` |
| After Phase 6 passes, before Phase 7 | `checkpoint: build verified` |
| After code review finishes, before Phase 8 | `checkpoint: code review complete` |
| Phase 9, after the PR URL is recorded | `checkpoint: PR opened` |
| Abort routine, run status `failed` | `checkpoint: run failed` |
| Abort routine, run status `blocked` | `checkpoint: run blocked` |

These are the only checkpoints in a run. Make no checkpoint after a task merge, a fix wave, a review round, a QA pass, or a manifest update. Code reaches `<RUN-BRANCH>` only through task merge commits. The run record reaches it only through these checkpoints.

### Run page

The run page is a read-only status page for the human, rendered from the manifest, `timeline.md`, and the brief. It is never a control surface.

Append one line to `<RUNDIR>/timeline.md` at every transition, in the form `- <ISO 8601 UTC> <what happened>`. The newest line is the page's status sentence while the run is live, so write it for the human: what just happened, and what the run is waiting on. Once the run ends, the banner shows `run_page.outcome` instead: write it before the final render, under 512 characters, as a summary of what the PR delivers or what failed, for the person who asked for the work. It is not a copy of the summary's Outcome section.

`<SKILL-DIR>` is the directory that holds this file. Render and publish the page whenever you update the manifest at a phase boundary, a task merge, a review round, a human touchpoint, an abort, or the PR:

```bash
python3 <SKILL-DIR>/scripts/render-run-page.py "$RUNDIR"
```

Publish `<RUNDIR>/run-page.html` through the first route available, and reuse the same route and URL for the whole run:

1. the Claude Artifact tool, private, redeploying the same file path;
2. `orca artifacts share` on the first publish and `orca artifacts update` after, rendered with `--standalone`, which makes the page viewable by anyone with the link;
3. neither: render with `--standalone`, tell the human the file path once, at Phase 0, and keep rendering.

Report the URL or path in the Phase 0 message. A failed publish never stops the run; record it in `summary.md` and continue.

### Shared Orca state

Orca's task store and terminal list contain resources from other runs and repositories.

Act only on ids, handles, and paths recorded in this run's manifest. The recorded Orca run id identifies this run's tasks and messages.

### Role configuration

- `references/routing.md` owns role routing, effort, and worker boot commands.
- `references/skill-map.md` owns the skill assigned to each role.
- `references/context/` holds one file per role. Read it completely when its phase starts, and not before.
- `references/orca-mechanics.md` owns how to dispatch, collect, and retry phase workers. Phase instructions name the task and where the phase differs.

## Intake

`/orca-implement {TASK-REF | prompt | resume <RUN | RUNDIR>}`

Load the `orchestration` skill. Resolve the Orca executable and load the guides it serves for `orchestration` and `orca-cli`.

`orca` in this skill means the resolved executable. The guides own command names, flags, and message mechanics. This skill owns process, ownership, and safety.

Resolve the argument:

- **GitHub issue** (`#123` or issue URL): `gh issue view <n> --json title,body,comments`
- **Linear issue** (`ABC-123` or Linear URL): `orca linear issue <ref> --full --json`
- **File path** (markdown docs, specs): read it directly.
- **Resume** (`resume` followed by a run name or a run folder path): a fresh coordinator session takes over an existing run. Follow [Resume a run](#resume-a-run) instead of Phase 0.
- **Anything else**: an ad-hoc prompt. Draft the requirements in the brief and the acceptance criteria in the plan. The human vets them at the understanding check and the plan gate.

Stop before creating anything when an intake read fails or returns empty, such as a missing Linear connection, an unresolvable issue, or an unreadable file.

The brief records what intake read, states the requirements, and cites the source, in the shape of `references/templates/brief-template.md`. The plan turns the approved brief into acceptance criteria and tasks, in the shape of `references/templates/plan-template.md`. Both stand alone, because a worker cannot reach a URL or a path outside its sandbox. The run works from what intake read. A ticket that changes mid-run does not change the plan.

## Phase 0: Setup

Complete every step in order before Phase 1.

1. **Load the run mechanics.**

   Follow [Orca runtime mechanics](#orca-runtime-mechanics). Read `references/orca-mechanics.md` completely before the first Orca mutation. Read `references/run-state.md` completely before initialising the manifest.

2. **Read the working directory.**

   ```bash
   git branch --show-current                                # <CURRENT_BRANCH>
   git status --porcelain                                   # empty means clean
   git rev-parse --git-dir; git rev-parse --git-common-dir  # a linked worktree when they differ
   orca worktree current --json                             # succeeds when Orca manages this worktree; gives its id and path
   git worktree list --porcelain | awk '/^worktree /{print $2; exit}'   # <PRIMARY-PATH>, the primary checkout
   ```

   Resolve `<DEFAULT_BRANCH>` from `origin/HEAD`. When that is unset, use `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`.

3. **Settle the branch role.**

   When `<CURRENT_BRANCH>` is `<DEFAULT_BRANCH>`, set `base_ref` to it and `start_ref` to null. Ask nothing.

   When `<CURRENT_BRANCH>` is not `<DEFAULT_BRANCH>` and the worktree is not clean, stop. Report the dirty files and ask the human to commit or stash them. The run has created nothing yet.

   Otherwise ask the human once, in the conversation, and wait for the answer:

   > You are on `<CURRENT_BRANCH>`, not `<DEFAULT_BRANCH>`. Tell me what this branch is for, because it decides where the run starts and where the PR goes.
   >
   > 1. **Starting point.** This is your own work-in-progress branch. The run builds on its commits. The PR carries them and targets `<DEFAULT_BRANCH>`. The review covers your commits too. Pick this for a personal feature branch.
   > 2. **Target.** This is a shared branch that other work merges into, such as a release or `dev` branch. The run starts from its tip and the PR targets `<CURRENT_BRANCH>` instead of `<DEFAULT_BRANCH>`. Nothing on it is reviewed. Pick this for a shared integration branch.
   > 3. **Ignore it.** This branch is unrelated. The run starts from `<DEFAULT_BRANCH>` and the PR targets `<DEFAULT_BRANCH>`. Your branch is left alone.
   >
   > Options 2 and 3 never modify `<CURRENT_BRANCH>`. Option 1 modifies it only when this is an Orca-managed worktree. The run then adopts that worktree, commits to `<CURRENT_BRANCH>`, and opens the PR from it. Otherwise the run creates its own branch from `<CURRENT_BRANCH>` and works there.

   | Answer         | `base_ref`         | `start_ref`        |
   | -------------- | ------------------ | ------------------ |
   | starting point | `<DEFAULT_BRANCH>` | `<CURRENT_BRANCH>` |
   | target         | `<CURRENT_BRANCH>` | `<CURRENT_BRANCH>` |
   | ignore         | `<DEFAULT_BRANCH>` | null               |

   The invocation and the task source never name a base. This question alone settles it. Record `base_ref` and `start_ref` in the manifest.

4. **Pin the base.**

   ```bash
   BASE_SHA=$(git rev-parse <base_ref>)                 # start_ref null, or equal to base_ref
   BASE_SHA=$(git merge-base <base_ref> <start_ref>)    # start_ref set and different from base_ref
   ```

   From here on, every diff, review, and changed-file list uses `BASE_SHA`, never a symbolic ref. `base_ref` is used once more, as the PR's target branch. A merge-base puts the start branch's existing commits inside every diff, review, and the PR.

5. **Name the run.**

   Set `<RUN>` to:

   ```text
   {yyyymmdd-hhmm}-{ref?}-{run-slug}
   ```

   Build it from:

   - the UTC datestamp from `date -u +%Y%m%d-%H%M`;
   - the normalised source ref, such as `gh-123` or `lin-abc-123`;
   - a run slug from the source title or prompt, using lowercase alphanumerics and hyphens.

   Omit the source-ref segment for an ad-hoc prompt.

6. **Bind the Orca Run.**

   Create the Orca Run with objective `<RUN>`. Record the run id when you initialise `run-state.json`.

   Pass that run id to every `task-create`. Tasks and messages outside that run are not yours.

7. **Choose the integration worktree.**

   Adopt the current worktree when step 2 found it Orca-managed and linked, and `start_ref` is set. Take `<WT>` and `<WT-PATH>` from the `orca worktree current` output and `<CURRENT_BRANCH>` as `<RUN-BRANCH>`. Create nothing. Record only terminals this run creates. The human's existing terminals in that worktree are not run resources. Record `integration_worktree.origin` as `adopted`.

   Otherwise create the worktree named `<RUN>` with `--setup run`. Pass `--base-branch <start_ref>` when `start_ref` is set and `--base-branch <base_ref>` otherwise. Link it to the source issue when one exists. Record `integration_worktree.origin` as `created`. Wait for the setup terminal as mechanics 7.0 requires.

   After creation, when the primary checkout has `.env` and the worktree does not, stop. Print this command for the human and end the run before creating anything else:

   ```bash
   cp -n "<PRIMARY-PATH>/.env" "<WT-PATH>/.env"
   ```

   Check presence with `test -f` only. Never read, print, or copy the file yourself.

   A duplicate-name failure means another run holds the name. Adjust the slug and retry.

   Capture these values from Orca's JSON response:

   - `<WT>`, the worktree id;
   - `<WT-PATH>`, the absolute worktree path.

   Capture the Orca-derived branch. Use only captured names from this point onwards.

   ```bash
   git -C <WT-PATH> branch --show-current
   # Record the result as <RUN-BRANCH>.

   git -C <WT-PATH> rev-parse HEAD
   # Must equal `git rev-parse <start_ref>` when start_ref is set, else BASE_SHA. Reset to that commit if it does not.
   ```

   `<WT>` is the integration point. Task branches merge into `<RUN-BRANCH>` there, and whole-run verification and code review run there. Every build and fix task receives its own worktree when Phase 5 dispatches it.

8. **Create the run folder inside the integration worktree.**

   ```bash
   RUNDIR="<WT-PATH>/.agents/orca/orchestration/<RUN>"
   mkdir -p "$RUNDIR/plan" "$RUNDIR/tasks" "$RUNDIR/review" \
     "$RUNDIR/screenshots" "$RUNDIR/scratch"
   ```

   The run folder holds exactly this:

   ```text
   run-state.json                             run manifest
   summary.md                                 run narrative, started in Phase 0, finalised at Phase 9
   timeline.md                                one event per line, appended at every transition
   run-page.html                              status page rendered from the manifest, never committed
   plan/brief.md                              human-approved task contract
   plan/plan.md                               spec of record
   tasks/{seq}-{slug}-agent-task.md           coordinator to builder
   tasks/{seq}-{slug}-report.md               builder to coordinator
   review/review-r<ROUND>.md                  review of record for the round
   review/qa-review.md                        QA review of record, when qa_policy is run
   screenshots/{description}_{sequence}.png
   scratch/scout-<slug>.md                    one per scouting lens
   scratch/planner-brief.md                   standalone brief every planner reads
   scratch/draft-<planner>.md                 one per planner on the tier's panel
   scratch/fact-check.md                      plan claim verification before critique
   scratch/fact-check-final.md                plan claim verification after critique
   scratch/critique-<critic>-r<ROUND>.md      one per critic per round
   scratch/acceptance-check-<PASS>.md         acceptance-criteria check, one per pass
   scratch/<claude|codex>-review-r<ROUND>.md  one per code reviewer per round
   scratch/security-<reviewer>-review-r<ROUND>.md one per security reviewer per round in which security ran
   scratch/qa-findings.md                     QA worker report, when qa_policy is run
   ```

   The run folder reaches git only through checkpoint commits. Append `.agents/orca/orchestration/` to the file named by `git -C <WT-PATH> rev-parse --git-path info/exclude`. That file is shared by every worktree of the repository and is never committed. Do not add a `.gitignore` rule. Write every artifact to disk as soon as you produce it. `scratch/` holds worker reports and the coordinator's working files and never reaches the branch.

   Do not commit anything between recording `<WT>` HEAD for the read-only check and running that check.

9. **Initialise `run-state.json`.**

   Initialise the manifest from the Initial manifest section of `references/run-state.md` before creating or closing another run resource. Fill every value already known from intake, run creation, and worktree creation.

   For a created worktree, record every auto-started terminal from the worktree-create response or terminal list before any other action, then handle it as mechanics 7.0 requires. For an adopted worktree, record none.

10. **Start the summary and report the choice.**

   Start `summary.md` in the shape of `references/templates/summary-template.md`. Start `timeline.md` with the run start. Render and publish the run page as the Run page rule requires.

   Report to the human in one message: whether the integration worktree was adopted or created, its path, `<RUN-BRANCH>`, `start_ref`, `base_ref`, `BASE_SHA`, and the run page URL or path. Then start Phase 1.

## Phase 1: Scout

Run these read-only lenses in parallel:

- **Discovery**: find project mechanics, tooling commands, `.env` presence, the commit-message convention, relevant code locations, and whether `orca.yaml` defines a `scripts.setup` hook and what that hook does.
- **Comprehension**: establish current behaviour, affected code, and dependencies on existing code.
- **Test coverage**: find existing coverage that needs adjustment and important gaps to close.
- **Additional lenses**: add a lens when the task needs evidence not covered above.

Read `references/context/scout.md` and resolve a self-contained `<TASK_CONTEXT>` for each lens. Dispatch one scout per lens in `<WT>` as task `scout-<SLUG>`, collect, and retry once.

After all retries:

1. Record each missing scout role.
2. Add the questions that role should have answered to the brief.
3. Confirm that the completed reports still cover project mechanics, current behaviour, and tests.
4. Run the abort routine if any of those three areas lacks coverage.

Read every completed report. Carry confirmed findings into the brief and the planner brief. Put every unresolved assumption in the brief as a question for the human.

## Phase 2: Understanding check

The understanding check settles the task contract before planning. It reconciles the task source, repository evidence, and human intent. Before autonomous work begins, it puts every decision the coordinator must not make alone to the human.

Write `<RUNDIR>/plan/brief.md` in the shape of `references/templates/brief-template.md`.

Put every known question in the first version. Open `brief.md` with the mapped `{human-review-skill}` and run its documented review loop.

Apply every answer and comment to the brief. Fold each answer into the section it settles and remove the question. If an answer reveals more questions, group all of them into the next version. Reopen the brief and run the printed next-round command.

Continue until every question is answered and the human completes a round with no comments. Then write `run_page.goal` in the manifest: a summary of the brief's Problem and Goal sections in your own words, under 512 characters, for the run page. Treat the approved brief and every human answer as settled facts during planning. Do not carry a known question into the plan as an open assumption.

If the mapped review skill is unavailable, run the same loop in the conversation and require explicit approval. An explicit rejection or cancellation runs the abort routine with status `blocked`. Update the manifest before Phase 3.

## Phase 3: Plan

### Step 1: Set the plan-review tier

1. Classify `plan_review_tier` from the requirements and scout evidence. Use the rubric in `references/routing.md`.
2. Record the tier in `run-state.json`.

The tier selects the planner panel.

### Step 2: Draft the plan

Read `references/context/planner.md`. Start the routed planner panel from `references/routing.md`.

#### Prepare the planner brief

Write `<RUNDIR>/scratch/planner-brief.md` as `references/context/planner.md` describes. Every planner reads that one file.

#### Dispatch and collect planners

Dispatch one `plan-draft-<P>` task per planner, collect, and retry once. A planner that fails twice takes no further part. Record every retry and each reduction in the panel.

After collection:

- With two drafts, assess both.
- With one draft, use it as the base.
- With no drafts, write `<RUNDIR>/plan/plan.md` yourself and follow `references/templates/plan-template.md` exactly.

#### Build the final plan

Assess and combine the drafts as `references/context/planner.md` describes. Write one coherent `<RUNDIR>/plan/plan.md` that follows `references/templates/plan-template.md`.

### Step 3: Fact-check the plan

Read `references/context/plan-fact-check.md`. Dispatch the `plan-fact-check` task, collect, and retry once. If the retry fails, run the abort routine. Do not substitute another model.

Correct every reported mismatch in `plan/plan.md` before Step 4.

### Step 4: Critique the plan

Read `references/context/plan-critic.md`. Start the critic panel from `references/routing.md`.

Run one critique round. `<PRE_CRITIQUE_SHA>` is the round's `start_head` in the plan-review record: the `<WT>` HEAD that holds the fact-checked plan.

1. Add the round to the plan-review record with `plan_changed=false` and the current `<WT>` HEAD.
2. Dispatch `plan-critique-<M>-r1` to every critic, collect, and retry a failed lens once.
3. When a retry also fails, record the lens in the round's `missing_lenses` and continue with the surviving critics. If every critic fails, record stop reason `all critics failed`. Carry the failure to the plan gate. There the human either approves the uncritiqued plan or cancels the run.
4. Assess every finding on its merits. Severity and verdict are evidence, not decisions. Revise `plan/plan.md` for each accepted finding. Record the accepted counts by severity in the round's `accepted_findings`. Set `plan_changed=true` only when plan content changes.
5. Save the revised plan and update the manifest.

Critique runs once. No critic reviews the revised plan. The final fact-check, build verification, and code review cover it. Set `rounds_run=1` and record stop reason `critique complete` or `all critics failed` in the plan-review record.

#### Finish plan critique

1. Close every critic terminal.
2. When `plan_changed=true`, repeat Step 3 against the revised plan as `plan-fact-check-final`, scoped to the sections changed since `<PRE_CRITIQUE_SHA>`. Correct every reported mismatch.
3. Assess `run_complexity` from the reviewed plan. It may be higher or lower than `plan_review_tier`.
4. Read the downstream review and QA policy from `references/routing.md`.
5. Update plan frontmatter, the plan's Review Policy, and `run-state.json`, including `code_review_cap` and `qa_policy`.
6. Keep the original plan-review tier and stop reason in the manifest.
7. Update the manifest before Phase 4.

## Phase 4: Plan gate

The plan gate gives the human final control before implementation starts. The human approves the scope, task boundaries, contracts, open assumptions, and review cost.

Changes at the plan gate do not reopen critique.
Before presenting an updated plan for approval, verify new or changed
repository claims against the repository.

Present through the mapped `{human-review-skill}`:

- `plan/plan.md`;
- `plan_review_tier` and the critique outcome;
- final `run_complexity`;
- the code-review cap and QA policy for that complexity;
- every open assumption.

Run the review loop:

1. Address every unresolved comment.
2. Update the live plan.
3. Reopen the plan through the mapped `{human-review-skill}`.
4. Run the printed next-round command.
5. Continue until the human completes a round with no comments.

A round with no comments approves the plan. If the review skill is unavailable, run the loop in the conversation and require explicit approval. Critic verdicts, silence, and an unfinished round are not approval.

A change to `run_complexity` needs separate approval because it changes review depth and QA policy. When feedback suggests a different tier:

1. Present the current tier and proposed tier.
2. Explain the evidence for the change.
3. Show the resulting code-review cap and QA policy.
4. Ask the human to approve or reject the tier change directly.
5. Update the plan and manifest only after approval.

Phase 6 may still raise the tier if implementation reveals more risk.

After approval, update the manifest and commit the `plan approved` checkpoint. Then start Phase 5. An explicit rejection or cancellation runs the abort routine.

## Phase 5: Build

Read `references/context/builder.md`.

Register the build tasks and their dependencies. Orca task specs are immutable, and a task's worktree path and dependency outputs are unknown until it becomes ready. Each task spec therefore holds only the agent-task pointer from the builder context.

For each planned task, use title `{seq}-{slug}`, set dependencies by owned build-task id, resolve the builder context's required task-spec values, and use its Orca task spec.

Record every returned task id in `run-state.json` as the build-owned set. This set contains build and fix tasks only. Keep scout, fact-check, planner, critic, acceptance-check, and reviewer task ids in their phase dispatch records, and the QA task id in the QA record.

### Dispatch ready tasks

Select ready tasks only from the build-owned set. Never dispatch directly from the runtime-global `task-list --ready` result. Run no more builders than the concurrency cap in `references/routing.md`.

For each ready task:

1. Create worktree `<RUN>-{seq}-{slug}` from `<RUN-BRANCH>` with parent worktree `<WT>` and `--setup run`. Wait for the setup terminal as mechanics 7.0 requires.
2. Capture the worktree id, absolute path, and actual branch.
3. Handle any auto-started terminal as mechanics 7.0 requires.
4. Record the starting commit with `git -C <path> rev-parse HEAD`.
5. Resolve every required builder-context value.
6. Write `<RUNDIR>/tasks/{seq}-{slug}-agent-task.md` in the shape of `references/templates/agent-task-template.md`.
7. Start the routed builder in the task worktree and wait for readiness.
8. Dispatch the task to that terminal. Do not pass resolved context through a shell argument.
9. Record the dispatch id and set manifest status to `dispatched`.

### Collect workers

Wait for `worker_done`, `escalation`, and `question` messages through the bounded wait in mechanics 3.0. A timeout is a checkpoint, not worker failure.

Handle each message that matches an active dispatch by type:

- `question` or `escalation`: answer through an orchestration reply or update the agent task. The message does not complete the task. Run the abort routine if you cannot resolve it without a new human decision.
- `worker_done`: run the task verification and merge procedure below. After a successful merge, dispatch newly ready tasks from the build-owned set up to the concurrency cap.

Continue until every build-owned dispatch is terminal.

### Recover an overdue worker

A worker is overdue only when both conditions hold:

- two consecutive wait slices returned no message for it;
- its branch received no new commit during those slices.

Read its terminal before taking action.

- If the worker is active, continue waiting.
- If it is stuck, waiting for input, or crashed, re-dispatch it:

  1. Stop the worker and close its terminal.
  2. Inspect committed work on the task branch.
  3. Start a fresh terminal in the same worktree and branch.
  4. Set the task back to `ready`.
  5. Re-dispatch with the existing work as context.
  6. Record the previous dispatch id as superseded.
  7. Increment the task's verify-to-fix cycle count.

This re-dispatch counts towards the task's verify-to-fix limit. It does not use the retry protocol's replacement attempt.

### Verify a completed task

A valid `worker_done` makes Orca mark the task and dispatch complete. It does not prove that the work is correct or ready to merge. Keep the manifest task unmerged until every check below passes.

1. Compare the task branch with its recorded starting commit:

   ```bash
   git log <starting-commit>..<task-branch> --oneline
   ```

2. Require a clean task worktree:

   ```bash
   git -C <task-worktree> status --porcelain
   ```

3. Accept a branch with no new commits only when the worker reported an explicit no-change outcome and the worktree is clean.
4. Read `<RUNDIR>/tasks/{seq}-{slug}-report.md`.
5. Rerun every applicable project check in the task worktree, whatever the report claims. Run them in this order: Build, Lint, Typecheck, Tests, Format check.
6. Compare the result with the task requirements in the approved plan.

Start a fix cycle if the worktree has uncommitted changes, a check fails, or the task does not meet its requirements:

1. Append the coordinator's findings and failing output to the agent task.
2. Set the task back to `ready`.
3. Re-dispatch it to the same terminal.
4. Record the new dispatch id and supersede the previous one.
5. Increment the verify-to-fix cycle count.

After three verify-to-fix cycles, use the retry protocol.

### Merge a verified task

Merge each verified task immediately.

1. Merge the task branch into `<RUN-BRANCH>` in `<WT>`:

   ```bash
   git -C <WT-PATH> merge --no-ff -m "orca: merge task <task-title>" <task-branch>
   ```

   `--no-ff` gives every task one merge commit on `<RUN-BRANCH>`, even when a fast-forward is possible. The first-parent history then reads one line per task, and `merge_commit` always names a real merge.
2. Resolve a trivial text conflict yourself only under the coordinator's exceptions in the run-wide rules.
3. For a semantic conflict:

   1. Abort the merge.
   2. Register a conflict-resolution fix task.
   3. Require that task to merge the original task branch into its fix branch and produce the conflict-resolution commit.
   4. Keep the original task marked `completed` in the manifest until the conflict task merges.
   5. Collect and verify the conflict task through the normal build flow.
   6. Merge the conflict task, then continue finalising the original task.

4. Run the checks in the plan's Integration Verification section for the boundaries this task touches.

If an integration check fails, keep the original task `completed` and its dependants blocked.
Create a fix task from the current `<RUN-BRANCH>` without making it depend on the original task.
Count the fix wave in `verification.fix_waves`, using the existing three-wave limit.
Finalise the original task only after the fix merges and the affected integration checks pass.

Increment the original task's resolve-to-verify count for each conflict task. Allow at most three resolve-to-verify cycles. After the third failed cycle, use the retry protocol.

### Finalise a merged task

Only after merge and integration verification pass:

1. Mark the task merged in the manifest and record the merge commit as `merge_commit`.
2. Allow dependent tasks to become ready.
3. Release the accepted dispatch.
4. Close the builder terminal and every other terminal recorded for the worktree.
5. Remove the task worktree by its recorded id and require an `.ok` response.
6. Delete the task branch with:

   ```bash
   git -C <WT-PATH> branch -d <task-branch>
   ```

   `-d` refuses an unmerged branch. A branch that Orca already removed with the worktree is acceptable.

7. Update the manifest.
8. Dispatch newly ready tasks from the build-owned set up to the concurrency cap.

### Stop contract drift

Contract drift occurs when two active workers repeatedly make incompatible changes to one shared interface.

When you detect contract drift:

1. Compare both implementations with the contract approved in the plan.
2. Pin the contract to one explicit definition within the approved plan.
3. Update each affected agent task with that definition.
4. Dispatch conform-to-contract fix tasks.
5. Reject further worker-specific changes to the contract.

A contract decision owned by the human still requires approval under the plan gate rules.

### Create fix tasks

Fix tasks use the same build flow as planned implementation tasks. This applies to:

- whole-run verification failures;
- code-review findings;
- adversarial-QA findings;
- semantic merge conflicts;
- contract-drift conformance.

For each fix task:

1. Classify its complexity with the task-complexity rubric.
2. Select the model, effort, and fallback from the matching builder row in `references/routing.md`.
3. Continue the run's task sequence numbering.
4. Create the task worktree from the current `<RUN-BRANCH>`.
5. Write its agent task.
6. Dispatch, collect, verify, merge, and clean up through the normal build flow.

Use one fix task for a wave by default. Split a wave only when the fixes are independent and the saved execution time exceeds the coordination cost. Add dependencies between split tasks when their changes are not independent.

## Phase 6: Whole-run verification

Whole-run verification checks the integrated HEAD against the acceptance criteria and decides whether the change needs stronger review than the plan predicted.

Run all checks in `<WT>` after the final task merge.

### Run project checks

Run the plan's Install command in `<WT>` before the first check unless the plan's Setup hook entry records that the setup script installs dependencies. Run it after any later merge that changes a dependency manifest or lockfile. The command is idempotent.

Run the commands recorded in the plan:

1. Build.
2. Lint.
3. Typecheck.
4. Full test suite.
5. Format check.
6. Every command in the plan's Post-Merge Validation section.

Record the result of every applicable command. Verify every boundary in the plan's Integration Verification section. Record the evidence for `summary.md`.

### Check acceptance criteria

Read `references/context/acceptance-check.md`. The first pass covers every criterion. `references/context/acceptance-check.md` selects the criteria for every later pass.

Dispatch the `acceptance-check-<PASS>` task to the routed worker in `<WT>`, collect, and retry once. If the retry fails, verify each in-scope criterion yourself and record the missing check in `summary.md`.

Read the report. Confirm each `not met` and `not verifiable` entry against the code before acting on it. Treat each confirmed `not met` criterion as a verification failure. Carry forward the verdict and evidence of every criterion outside the pass's scope. Record the evidence for every criterion in `summary.md`.

### Decide browser verification

Set `browser_verification.policy` to `run` in `run-state.json` when the diff touches components, pages, layouts, styles, or templates, or when the visual effect is uncertain. Otherwise set it to `not_needed`. Browser verification runs in Phase 7 round 1, in parallel with the review lenses.

### Confirm the review policy

Compare the integrated diff and observed failures with the approved `run_complexity`. Planning can underestimate risk that becomes visible only after implementation.

If the implementation carries more risk than the approved `run_complexity` assumed:

1. Raise `run_complexity`.
2. Recalculate the code-review cap and QA policy from `references/routing.md`.
3. Update plan frontmatter, the plan's Review Policy, and `run-state.json`.
4. Record the evidence and reason in `summary.md`.
5. Confirm that all three policy records agree.

### Fix verification failures

Turn each failure into a fix task through the Phase 5 fix-task procedure. Put the failing command, its output, and the expected result in the agent task. For an unmet criterion, put the criterion, the report's evidence, and the expected behaviour in the agent task.

After each fix merge:

1. Rerun the failed check.
2. Rerun any checks affected by the fix.
3. Rerun the acceptance check for the criteria the fix affected.
4. Start another fix wave if a check still fails or a criterion is still unmet.

Record each wave in `verification.fix_waves`. Allow at most three verification fix waves. Run the abort routine after the third failed wave.

Start Phase 7 only when every project check passes and every acceptance criterion is verified or recorded as not verified with its reason. Record a gap only when this environment cannot verify it, such as an unavailable dev server. A failing check is never a recorded gap.

### Record the verification evidence

Update `<RUNDIR>/summary.md` with the implementation decisions so far, the evidence for each acceptance criterion, every incident, and every unverified gap with its reason. Reviewers and QA read this file. Save it. Commit the `build verified` checkpoint. Then start Phase 7. Review round 1 reviews that commit.

## Phase 7: Code review

Each round dispatches the code and security lenses together, in one wave, against the same committed HEAD. Round 1 also runs browser verification when Phase 6 required it. A later round runs only when the previous round fixed an accepted Critical or High finding, up to the approved round cap. Medium findings get one fix wave and never reopen review.

### Prepare the review

1. Read `references/context/review.md`.
2. Read `<CODE_REVIEW_CAP>` from the plan's Review Policy.
3. Set `review_fixes_applied=false` in the manifest.
4. Start every routed code reviewer in `<WT>` from `references/routing.md`. Start the security reviewers only when `run_complexity` is `medium` or above. Reviewer terminals stay open across rounds.

### Run a review round

For each `<ROUND>` from 1 through `<CODE_REVIEW_CAP>`:

1. Add the round to `review_rounds` with `severe_fix_merged=false` and the current `<WT>` HEAD.
2. Resolve every required value in `references/context/review.md`. Every round reviews the whole branch against `<BASE_SHA>`. Each later round first confirms the previous round's fixes, then reports only findings the previous review did not triage.
3. Select the security lenses for the round. At `low` complexity, set `security_lenses_run=false` with reason `run complexity policy` and dispatch none. Otherwise round 1 dispatches both. A later round dispatches them only when a previous security lens reported a finding, or when a fix wave since the previous round changed a file that handles attacker-controlled input. The trust model in the mapped `{security-review-skill}` defines that input. Otherwise set `security_lenses_run=false` and `security_skip_reason` in the round record.
4. Dispatch a fresh task with a unique report path to every code reviewer and each selected security reviewer. Collect, and retry a failed lens once within the round.
5. In round 1, when `browser_verification.policy` is `run`, read `references/context/browser-verification.md` and resolve every required value. Start one native subagent in the same wave as the reviewers, on the model from `references/routing.md`. Use the dispatch template and failure policy in `references/context/browser-verification.md`. The browser subagent is not a phase worker. Its report stays in coordinator context. If it produces no report, start it once more.
6. When a retry also fails, record the lens in the round's `missing_lenses` and in the round review, and start a fresh terminal for it before any later round. Run the abort routine if both code-review lenses are unavailable. Record every missing security lens, then continue with the surviving lenses.
7. Read the browser screenshots yourself. A browser report without screenshots is not verified. Record the result as `browser_result` in the round record and in `browser_verification.result`.
8. For each acceptance criterion the acceptance check recorded as `not verifiable here` because it needs a browser, record the round-1 browser evidence and the resulting verdict against that criterion in `summary.md`.

### Write the round review

Write `<RUNDIR>/review/review-r<ROUND>.md`. It is the review of record for the round and stands alone. A reader must not need the lens reports. Treat every completed code-review and security-review lens as a separate source.

Record at the top:

- base SHA;
- branch;
- round;
- HEAD reviewed;
- lenses completed and lenses missing;
- each lens's coverage notes, tests-review line, and verdict, as written.

Combining the lens reports is mechanical:

1. Drop a finding when its cited file exists neither at the recorded HEAD nor at `<BASE_SHA>`. A deleted file remains a valid citation.
2. Keep a finding in untouched code only when it traces a causal path to a changed file.
3. Deduplicate by finding identity, not wording. When two lenses report one finding, keep one entry, name both sources, and keep each source's severity and confidence.
4. Carry each surviving finding over in the lens skill's own format, complete and unedited: Issue, Severity, Confidence, Category, File, Findings, Attack path where the lens gives one, Evidence, and Fix. Renumber issues across lenses and add a `**Source:**` line. Do not reduce a finding to a title or a checklist line.
5. Carry each lens's documentation and artifact recommendations over as written.
6. Carry each browser-verification failure over as a finding with `**Source:** browser` and the screenshot path as evidence. Severity follows the observed impact. High when a core flow is broken, Medium otherwise.

Do not add findings, change severity, or judge validity while combining.

### Triage the findings

Assess each surviving finding against the code and its reproduction.

- Discard a finding that does not hold.
- Accept a finding that holds.
- Treat attribution and severity as evidence, not a verdict.
- Fix every accepted finding unless the approved plan explicitly excludes the work.

If a required fix needs a human-owned decision that the approved task contract
does not settle, follow the Human touchpoints rule.

Record an excluded finding under Remaining in `summary.md` with the reason it remains.

Append a Triage section to `review/review-r<ROUND>.md`. For each finding, record the outcome, the evidence you checked, and the reason. Record the accepted counts by source and severity in the round's `accepted_findings`. Update the manifest before starting a fix wave.

If no finding needs a code or test fix:

1. Leave `severe_fix_merged=false`.
2. Record `no accepted fixes` as the stop reason.
3. Stop the review loop.

If every accepted finding is Medium:

1. Fix them together through the procedure below.
2. Leave `severe_fix_merged=false`.
3. Record `no severe findings` as the stop reason.
4. Stop the review loop after the fixes verify.

### Apply review fixes

Turn accepted fixes into Phase 5 fix tasks.

For each fix:

1. Verify the task through the normal build flow.
2. Rerun the finding's reproduction or check.
3. Start another fix wave if the finding still reproduces.
4. Record the fix commit and its verification evidence against the finding in the round review.

Record each wave in the round's `fix_waves`. Allow at most three fix waves in one review round. After the third failed wave, run the abort routine and attach the round review.

Set `review_fixes_applied=true` after any accepted fix, Medium included, merges and verifies in `<WT>`.

Set `severe_fix_merged=true` only after you merge and verify a fix for an accepted Critical or High finding in `<WT>`. Medium fixes, report files, bookkeeping changes, and findings that need no implementation change do not count.

When `severe_fix_merged=true`, continue to the next round unless this round reached `<CODE_REVIEW_CAP>`. At the cap, stop after the verified fix wave, record `cap reached` as the stop reason, and record that no reviewer saw the final fixes.

When `severe_fix_merged=false`, stop the review loop.

### Finish code review

1. Close every reviewer terminal.
2. If `review_fixes_applied=true`, rerun the Phase 6 project checks and the acceptance check for affected criteria against the post-review HEAD. Rerun browser verification only when a fix changed UI files, and only for the pages it touched.
3. Treat verification fixes as post-review and unreviewed. Use the Phase 6 fix procedure with its own three-wave limit, recorded in `verification.post_review_fix_waves`. Do not reopen code review.
4. If no review fix changed the implementation, retain the existing Phase 6 evidence.
5. Require current verification evidence or an explicit reason for every remaining unverified gap.
6. Set `code_review_complete=true` in `run-state.json`.
7. Confirm that the final round's stop reason is recorded.
8. Update the manifest with the final round review and verification evidence.
9. Commit the `code review complete` checkpoint. Phase 8 records that commit as `QA_HEAD`.

## Phase 8: Final adversarial QA

Adversarial QA attempts to break the committed implementation after code review and post-review verification. It runs once. Verify QA fixes, but do not reopen code review for them.

Require a clean integration worktree:

```bash
git -C <WT-PATH> status --porcelain
```

### Apply the QA policy

When `qa_policy` is `skip`:

1. Do not create a QA task, terminal, worktree, dispatch, or findings file.
2. Set `qa.status` to `skipped` and `qa.reason` to `run complexity policy` in `run-state.json`.
3. Record the skip in the manifest.
4. Continue to Phase 9.

When `qa_policy` is `run`, run the procedure below.

### Prepare the QA worktree

1. Record:

   ```bash
   QA_HEAD=$(git -C <WT-PATH> rev-parse HEAD)
   ```

2. Create a disposable worktree named `<RUN>-qa` from the current `<RUN-BRANCH>`, using `<WT>` as its parent worktree and `--setup run`. Wait for the setup terminal as mechanics 7.0 requires.
3. Record its id, absolute path, and actual branch.
4. Handle any auto-started terminal as mechanics 7.0 requires.
5. Confirm that the QA worktree HEAD equals `QA_HEAD`.

The QA worktree is disposable. Never merge its branch.

### Run and collect QA

Read `references/context/adversarial-qa.md`. Dispatch the `<RUN>-qa` task to the routed QA worker in the QA worktree, record the task, terminal, and dispatch in the QA record, then collect.

On successful completion:

1. Require a non-empty `<RUNDIR>/scratch/qa-findings.md`.
2. Set `qa.dispatch_status` to `completed`. Keep `qa.status` as `pending` until triage, accepted fixes, and verification finish.

On worker failure or a missing report, set `qa.dispatch_status` to `failed`, reset the QA worktree to `QA_HEAD`, remove untracked files, and retry once.

If the retry also fails:

1. Set `qa.status` to `not_verified` and record the failure in `qa.reason`.
2. Record the incident in the manifest and `summary.md`.
3. Continue to Phase 9 without triage.

In all cases:

1. Close every terminal recorded for the QA worktree and mark each resource record `closed`.
2. Remove the QA worktree by its recorded id and mark its resource record `removed`.
3. Delete the QA branch.
4. Confirm that you never merged the QA branch.

### Triage and fix QA findings

Assess each concrete finding on the same terms as Phase 7:

- discard it when it does not hold;
- accept it when it holds;
- record it under Remaining in `summary.md` only when the approved plan excludes it.

Write `<RUNDIR>/review/qa-review.md`. It is the QA review of record and stands alone. A reader must not need the worker report. Carry every finding from `scratch/qa-findings.md` over in the QA skill's own format, complete and unedited: Severity, Category, Type, Location, Finding, Reproduction, Expected, Actual, Evidence, and Regression test. Carry the coverage list and verdict as written. Then append a Triage section: for each finding, the outcome, the evidence you checked, and the reason. Record the accepted counts by severity in `qa.accepted_findings`. Update the manifest before starting fixes.

Create accepted fixes as Phase 5 fix tasks from the current `<RUN-BRANCH>`. Never make lasting fixes in the disposable QA worktree.

For every fix wave:

1. Verify each fix task.
2. Rerun each finding's exact reproduction.
3. Rerun the Phase 6 project checks and the acceptance check for affected criteria. Rerun browser verification only when a fix changed UI files, and only for the pages it touched.
4. Record the fix commit and its verification evidence against the finding in the QA review.
5. Start another wave if a finding still reproduces.

Allow at most three QA fix waves. After the third failed wave, run the abort routine and attach the QA review.

Set `qa.status` to `completed` and clear `qa.reason`. Record the final QA, fix, and verification evidence before Phase 9.

## Phase 9: PR

### Finalise the run evidence

Update `<RUNDIR>/summary.md` in the shape of `references/templates/summary-template.md`.
Fill every section with the results so far. Leave `finished` as `pending`
and record publication as pending in Outcome.

Run this command:

```bash
git -C <WT-PATH> status --porcelain -- . ':!.agents/orca/orchestration'
```

It must return no output. The pathspec excludes the run folder because its committed files change between checkpoints.

### Publish the branch and PR

In the PR description, identify code changes that received verification but no
subsequent code review. State which checks covered those changes.
Include any missing review lenses and unverified acceptance criteria.

1. Push `<RUN-BRANCH>`. It is the only branch that may reach the remote.
2. Open the PR through the mapped `{pr-skill}` against the base branch.

Use this sign-off instead of the PR skill's sign-off:

```markdown
---
:space_invader: Built with Orca + {display names of every model that produced or fixed code in the PR, deduplicated; omit effort levels}
```

### Tear down run resources

Use only handles and ids recorded in `run-state.json`.

1. Close every recorded terminal and mark its resource record `closed`.
2. Remove each remaining task or QA worktree by its recorded id and mark its resource record `removed`.
3. Confirm that every removed terminal and worktree is gone.
4. Do not act on unfiltered `terminal list` or `worktree list` output. Orca is shared with other runs.
5. Keep the integration worktree until the PR merges and mark it `retained`. Its later removal with `orca worktree rm` belongs to the human.
6. Set `cleanup.status` to `complete` when no removable resource remains. Otherwise set it to `partial` and record every remaining handle or worktree id.

### Record PR state

1. Set `run-state.json` status to `pr`.
2. Record the PR URL in the manifest and `summary.md`.
   Set the summary's `finished` timestamp.
3. Commit the `PR opened` checkpoint. Leave the exclude entry in place.
4. Push `<RUN-BRANCH>`.
5. Report:
   - the PR URL;
   - what the PR contains;
   - what code review fixed;
   - what QA fixed;
   - what remains unfixed and why;
   - what remains unverified.

## Failure handling

### Run the retry protocol

A worker may use at most three verify-to-fix cycles. Exhausting those cycles starts one replacement attempt.

1. Diagnose whether the approach or its execution caused the failures.
2. Revise implementation details only within the approved task contract.
3. If recovery needs a decision the human owns, about scope, security, a destructive operation, or architecture, run the abort routine with status `blocked`.
4. Append a retry briefing to the agent task:
   - what each cycle attempted;
   - each failure and its output;
   - the report path and relevant Git revisions;
   - the coordinator's diagnosis;
   - what the replacement must do differently.
5. Stop and close the original worker.
6. Start a fresh worker in the same task worktree and branch.
7. Supersede the previous dispatch and start a new dispatch through the version-matched Orca retry mechanism.

The replacement receives its own limit of three verify-to-fix cycles.

If the replacement exhausts that limit, the task fails permanently:

1. Mark it `failed` in Orca and the manifest.
2. Mark its build-owned dependants `failed` with reason `dependency failed`.
3. Close its terminal.
4. Remove its worktree by recorded id, preserving its branch as mechanics 7.0 requires.
5. Record every attempt and the preserved branch in `summary.md`.

Allow independent tasks already dispatched to finish through collection, verification, and merge. Dispatch no new tasks. Then run the abort routine.

### Run the abort routine

The abort routine is safe to run more than once. Use it for:

- permanent task failure;
- exhausted verification, review, or QA fix waves;
- a scout coverage gap or fact-check failure that its phase cannot recover;
- rejection at the understanding check or the plan gate;
- failure of both code-review lenses;
- an escalation that requires a new human decision;
- an infeasible approved plan.

Use run status:

- `failed` when implementation or verification could not complete;
- `blocked` when progress needs a human-owned decision or external prerequisite.

Then:

1. Mark this run's remaining non-terminal tasks `failed`.
2. Close every manifest-owned terminal.
3. Remove task and disposable worktrees by recorded id, preserving each task branch as mechanics 7.0 requires.
4. Delete a disposable QA branch when one exists.
5. Keep the integration worktree and run branch for inspection.
6. Complete `summary.md` in the shape of `references/templates/summary-template.md`. Set `finished` and fill every section.
7. Update `run-state.json`.
8. Commit the `run failed` or `run blocked` checkpoint for the run status.
9. Report the failure or blocker to the human.

### Detect an infeasible plan

Treat the plan or requirements as infeasible when:

- consecutive tasks fail for structurally similar reasons; or
- different implementations fail the same acceptance criterion.

Stop replacing workers. Record:

- the repeated evidence;
- the plan assumptions that appear false;
- the coordinator's best assessment of what is feasible.

Then run the abort routine.

### Recover coordinator failure

On a context-limit or unexpected coordinator error, attempt recovery first. If recovery fails, record as much of the abort state as possible. A fresh coordinator session takes over through `resume`.

### Resume a run

`resume <RUN>` names the run. `resume <RUNDIR>` names its run folder. Resolve a run name to the worktree of that name in Orca's worktree list. When none exists, the run adopted a worktree. Find the Orca worktree whose path holds `.agents/orca/orchestration/<RUN>/run-state.json`. Derive `<RUNDIR>` as Phase 0 step 8 does. Stop when the worktree or `run-state.json` does not exist, or when the recorded status is terminal.

Load the run mechanics as Phase 0 step 1 requires. Then read the following artifacts completely and in order. Use `run-state.json` to skip artifacts from steps not yet reached. Recover missing artifacts from completed steps before continuing.

1. `run-state.json`;
2. `summary.md`;
3. `plan/brief.md` and `plan/plan.md`;
4. every agent task and report under `tasks/`;
5. every review under `review/`;
6. the `scratch/` reports of the recorded phase.

Then reconcile the manifest with live state:

1. Use Git to establish which task branches have merged. Mark a task `merged` in the manifest only after integration verification passes.
2. Treat live Orca dispatch state as authoritative over manifest dispatch status.
3. Reacquire stale terminal handles by matching the recorded title and worktree.
4. Collect pending `worker_done` messages before dispatching anything.
5. Dispatch only unfinished work, using existing task-branch commits as context. Merge only branches not yet merged.
6. In Phases 6 through 8, resume from the recorded round and fix-wave counts.

Record the resumption and every reconciliation in `summary.md` and continue from the recorded phase.

### Handle the Orca circuit breaker

When Orca marks a task failed after three consecutive dispatch failures, enter the retry protocol. Do not treat it as immediate permanent failure.

Never run `orca orchestration reset`. The orchestration store is shared with other runs.

## Orca runtime mechanics

Read `references/orca-mechanics.md` completely during Phase 0, after loading the version-matched Orca guides and before the first Orca mutation. Re-read the relevant heading when a phase needs it.

| Reference heading | Use |
|---|---|
| [1.0 Record run ownership](references/orca-mechanics.md#10-record-run-ownership) | Orca resource creation and recovery |
| [2.0 Follow the live Orca contract](references/orca-mechanics.md#20-follow-the-live-orca-contract) | Every Orca command and command failure |
| [3.0 Receive orchestration messages](references/orca-mechanics.md#30-receive-orchestration-messages) | Every bounded wait and delivery |
| [4.0 Dispatch a phase worker](references/orca-mechanics.md#40-dispatch-a-phase-worker) | Every phase-worker dispatch; readiness and command failure for every worker |
| [5.0 Collect a phase worker](references/orca-mechanics.md#50-collect-a-phase-worker) | Every phase-worker collection and the read-only check |
| [6.0 Retry a phase worker](references/orca-mechanics.md#60-retry-a-phase-worker) | Every failed, overdue, or reportless phase worker |
| [7.0 Manage terminals and worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees) | Terminal release and reuse, worktree cleanup, branch preservation, and teardown |
| [8.0 Operational safety](references/orca-mechanics.md#80-operational-safety) | Every mutation, cleanup, push, and PR action |
