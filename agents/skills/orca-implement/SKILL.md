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

You may make only:

- typo, comment, or docstring corrections;
- unused-import removal;
- formatting fixes by hand or through the recorded Format write command;
- resolutions of trivial text merge conflicts.

Put coordinator changes in a separate commit. Dispatch every other code change to a worker.

Workers do not create Orca tasks, dispatches, or terminals. You own all Orca coordination. Critics, reviewers, and QA workers may use their runtime's native subagents for the work their context allows. They must clean up those subagents before reporting completion.

### Human touchpoints

The run has four human touchpoints:

1. invocation;
2. understanding check;
3. plan gate;
4. PR review.

After plan approval, continue autonomously to the PR. Record each judgement in `summary.md`.

Settle human-owned scope, security, destructive-operation, and architectural decisions by the plan gate. If one arises later and you cannot resolve it within the approved task contract, run the abort routine with status `blocked`. Do not open another decision round during implementation.

### Evidence and manifest

Report what happened, not what a worker or plan claimed would happen.

`references/run-state.md` is the sole manifest schema. Update `<RUNDIR>/run-state.json` after every state transition and before the next Orca mutation.

### Shared Orca state

Orca's task store and terminal list contain resources from other runs and repositories.

Act only on ids, handles, and paths recorded in this run's manifest. The recorded Orca run id identifies this run's tasks and messages.

### Role configuration

- `references/routing.md` owns role routing, effort, and worker boot commands.
- `references/skill-map.md` owns the skill assigned to each role.
- `references/context/` holds one file per role. Read it completely when its phase starts, and not before.
- `references/orca-mechanics.md` owns how to dispatch, collect, and retry phase workers. Phase instructions name the task and the phase's deviations.

## Intake

`/orca-implement {TASK-REF | prompt}`

Load the `orchestration` skill. Resolve the Orca executable and load the guides it serves for `orchestration` and `orca-cli`.

`orca` in this skill means the resolved executable. The guides own command names, flags, and message mechanics. This skill owns process, ownership, and safety.

Resolve the argument:

- **GitHub issue** (`#123` or issue URL): `gh issue view <n> --json title,body,comments`
- **Linear issue** (`ABC-123` or Linear URL): `orca linear issue <ref> --full --json`
- **File path** (markdown docs, specs): read it directly.
- **Anything else**: an ad-hoc prompt. Draft the requirements in the brief and the acceptance criteria in the plan. The human vets them at the understanding check and the plan gate.

Stop before creating anything when an intake read fails or returns empty, such as a missing Linear connection, an unresolvable issue, or an unreadable file.

The brief distils what intake read into requirements and cites the source, in the shape of `references/templates/brief-template.md`. The plan turns the approved brief into acceptance criteria and tasks, in the shape of `references/templates/plan-template.md`. Both stand alone, because a worker cannot reach a URL or a path outside its sandbox. The run works from what intake read. A ticket that changes mid-run does not change the plan.

## Phase 0: Setup

Complete every step in order. Do not start Phase 1 until all steps finish.

1. **Load the run mechanics.**

   Follow [Orca runtime mechanics](#orca-runtime-mechanics). Read `references/orca-mechanics.md` completely before the first Orca mutation. Read `references/run-state.md` completely before initialising the manifest.

2. **Pin the base.**

   Use the base branch named in the invocation or the task source. Otherwise use the repository's default branch. Record it as `base_ref` in the manifest.

   ```bash
   BASE_SHA=$(git rev-parse <base-ref>)
   ```

   Every diff, review, and changed-file computation from here on uses `BASE_SHA`, never the symbolic ref. The ref serves twice more: as the worktree's starting point in step 5, and as the PR's target branch.

3. **Name the run.**

   Set `<RUN>` to:

   ```text
   {yyyymmdd-hhmm}-{ref?}-{run-slug}
   ```

   Build it from:

   - the UTC datestamp from `date -u +%Y%m%d-%H%M`;
   - the normalised source ref, such as `gh-123` or `lin-abc-123`;
   - a run slug from the source title or prompt, using lowercase alphanumerics and hyphens.

   Omit the source-ref segment for an ad-hoc prompt.

4. **Bind the Orca Run.**

   Create the Orca Run with objective `<RUN>`. Record the run id when you initialise `run-state.json`.

   Pass that run id to every `task-create`. Tasks and messages outside that run are not yours.

5. **Create the integration worktree.**

   Create the worktree named `<RUN>` from the base ref. Link it to the source issue when one exists.

   A duplicate-name failure means another run holds the name. Adjust the slug and retry.

   Capture these values from Orca's JSON response:

   - `<WT>`, the worktree id;
   - `<WT-PATH>`, the absolute worktree path.

   Capture the Orca-derived branch. Use only captured names from this point onwards.

   ```bash
   git -C <WT-PATH> branch --show-current
   # Record the result as <RUN-BRANCH>.

   git -C <WT-PATH> rev-parse HEAD
   # The result must equal BASE_SHA. Reset to BASE_SHA if it does not.
   ```

   `<WT>` is the integration point. Task branches merge into `<RUN-BRANCH>` there, and whole-run verification and code review run there. Every build and fix task receives its own worktree when Phase 5 dispatches it.

6. **Create the run folder inside the integration worktree.**

   ```bash
   RUNDIR="<WT-PATH>/.agents/orca/orchestration/<RUN>"
   mkdir -p "$RUNDIR/plan" "$RUNDIR/tasks" "$RUNDIR/review" \
     "$RUNDIR/screenshots" "$RUNDIR/scratch"
   ```

   The run folder holds exactly this:

   ```text
   run-state.json                             run manifest
   summary.md                                 run narrative, started in Phase 0, finalised at Phase 9
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
   scratch/fact-check.md                      plan claim verification
   scratch/critique-<critic>-r<ROUND>.md      one per critic per round
   scratch/<claude|codex>-review-r<ROUND>.md  one per code reviewer per round
   scratch/security-<reviewer>-review-r<ROUND>.md one per security reviewer per round
   scratch/qa-findings.md                     QA worker report, when qa_policy is run
   ```

   The run folder belongs to `<RUN-BRANCH>`. Commit each artifact as soon as it exists and at every phase boundary. `scratch/` holds worker reports and the coordinator's working files. Do not write ignore rules for it.

   Do not commit between recording `<WT>` HEAD for a collection check and running that check.

7. **Initialise `run-state.json`.**

   Initialise the manifest from the Initial manifest section of `references/run-state.md` before creating or closing another run resource. Fill every value already known from intake, run creation, and worktree creation.

   Record every auto-started terminal from the worktree-create response or terminal list before any other action, then handle it as mechanics 7.0 requires.

8. **Start the summary and commit Phase 0 state.**

   Start `summary.md` with the run name, source, and start datetime. Commit the run folder before Phase 1.

## Phase 1: Scout

Run these read-only lenses in parallel:

- **Discovery**: find project mechanics, tooling commands, `.env` presence, the commit-message convention, and relevant code locations.
- **Comprehension**: establish current behaviour, affected code, and dependencies on existing code.
- **Test coverage**: find existing coverage that needs adjustment and important gaps to close.
- **Additional lenses**: add a lens when the task needs evidence not covered above.

Read `references/context/scout.md` and write one self-contained task context per lens. Dispatch one scout per lens in `<WT>` as task `scout-<SLUG>`, collect, and retry once.

After all retries:

1. Record each missing scout role.
2. Add the questions that role should have answered to the brief.
3. Confirm that the completed reports still cover project mechanics, current behaviour, and tests.
4. Run the abort routine if any of those three areas lacks coverage.

Read every completed report. Carry confirmed findings into the brief and the planner brief. Put every unresolved assumption in the brief as a question for the human.

## Phase 2: Understanding check

The understanding check settles the task contract before planning. It reconciles the task source, repository evidence, and human intent, and puts every decision the coordinator must not make alone to the human before autonomous work begins.

Write `<RUNDIR>/plan/brief.md` in the shape of `references/templates/brief-template.md`.

Put every known question in the first version. Open `brief.md` with the mapped `{human-review-skill}` and run its documented review loop.

Apply every answer and comment to the brief: fold each answer into the section it settles and remove the question. If an answer reveals more questions, group all of them into the next version. Reopen the brief and run the printed next-round command.

Continue until every question is answered and the human completes a round with no comments. Treat the approved brief and every human answer as settled facts during planning. Do not carry a known question into the plan as an open assumption.

If the mapped review skill is unavailable, run the same loop in the conversation and require explicit approval. An explicit rejection or cancellation runs the abort routine with status `blocked`. Commit the approved brief and manifest before Phase 3.

## Phase 3: Plan

### Step 1: Set the plan-review tier

1. Classify `plan_review_tier` from the requirements and scout evidence. Use the rubric in `references/routing.md`.
2. Read the matching plan-review cap from `references/routing.md`.
3. Record the tier and cap in `run-state.json`.

The tier selects the planner panel and plan-review depth. It remains fixed through plan critique.

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

Correct every reported mismatch in `plan/plan.md` and commit before Step 4.

### Step 4: Critique the plan

Read `references/context/plan-critic.md`. Start the critic panel from `references/routing.md`. Critic terminals stay open across rounds.

For each `<ROUND>` from 1 through `<PLAN_REVIEW_CAP>`:

1. Add the round to the plan-review record with `plan_changed=false` and the current `<WT>` HEAD.
2. Dispatch `plan-critique-<M>-r<ROUND>` to every critic, collect, and retry a failed lens once within the round.
3. When a retry also fails, record the lens in the round's `missing_lenses`, continue with the surviving critics, and start a fresh routed terminal for that lens before the next round. If every critic fails, stop the loop with stop reason `all critics failed` and carry the failure to the plan gate, where the human decides whether to approve the uncritiqued plan or cancel the run.
4. Assess every finding on its merits. Severity and verdict are evidence, not decisions. Revise `plan/plan.md` for each accepted finding. Set `plan_changed=true` only when plan content changes.
5. Commit the revised plan and manifest.
6. If `plan_changed=false`, stop with stop reason `no plan change`. If rounds remain, start the next round. If the cap is reached, stop with stop reason `cap reached` and record that no critic reviewed the final edits.

Record the stop reason in the plan-review record.

#### Finish plan critique

1. Close every critic terminal.
2. Assess `run_complexity` from the reviewed plan. It may be higher or lower than `plan_review_tier`.
3. Read the downstream review and QA policy from `references/routing.md`.
4. Update plan frontmatter, the plan's Review Policy, and `run-state.json`, including `code_review_cap` and `qa_policy`.
5. Keep the original plan-review tier, cap, rounds run, and stop reason in the manifest.
6. Commit the updates before Phase 4.

## Phase 4: Plan gate

The plan gate gives the human final control before implementation starts. The human approves the scope, task boundaries, contracts, open assumptions, and review cost.

Changes at the plan gate do not reopen critique or fact checking.

Present through the mapped `{human-review-skill}`:

- `plan/plan.md`;
- `plan_review_tier` and the review cap already used;
- final `run_complexity`;
- the code-review cap and QA policy for that complexity;
- critic outcomes and rounds run;
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

After approval, commit the plan and manifest before Phase 5. An explicit rejection or cancellation runs the abort routine.

## Phase 5: Build (parallel where deps allow)

Read `references/context/builder.md`.

Register the build DAG. Orca task specs are immutable, and the worktree path and dependency outputs are unknown until a task becomes ready, so each task spec holds only the agent-task pointer from the builder context.

For each planned task, use title `{seq}-{slug}`, set dependencies by owned build-task id, resolve the builder context's required task-spec values, and use its Orca task spec.

Record every returned task id in `run-state.json` as the build-owned set. This set contains build and fix tasks only. Keep scout, fact-check, planner, critic, and reviewer task ids in their phase dispatch records, and the QA task id in the QA record.

### Dispatch ready tasks

Select ready tasks only from the build-owned set. Never dispatch directly from the runtime-global `task-list --ready` result. Run at most the builder concurrency cap from `references/routing.md`.

For each ready task:

1. Create worktree `<RUN>-{seq}-{slug}` from `<RUN-BRANCH>` with parent worktree `<WT>`.
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

This re-dispatch counts towards the task's verify-to-fix limit. It is not the retry protocol's replacement.

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

3. Accept no commits only when the worker reported an explicit no-change outcome and the worktree is clean.
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

Merge each verified task immediately. Do not batch task merges.

1. Merge the task branch into `<RUN-BRANCH>` in `<WT>`.
2. Resolve a trivial text conflict yourself only under the coordinator's exceptions in the run-wide rules.
3. For a semantic conflict:

   1. Abort the merge.
   2. Register a conflict-resolution fix task.
   3. Require that task to merge the original task branch into its fix branch and produce the conflict-resolution commit.
   4. Keep the original task marked `completed` in the manifest until the conflict task merges.
   5. Collect and verify the conflict task through the normal build flow.
   6. Merge the conflict task, then continue finalising the original task.

4. Run the checks in the plan's Integration Verification section for the boundaries this task touches.

Increment the original task's resolve-to-verify count for each conflict task. Allow at most three resolve-to-verify cycles. After the third failed cycle, use the retry protocol.

### Finalise a merged task

Only after merge and integration verification pass:

1. Mark the task merged in the manifest.
2. Allow dependent tasks to become ready.
3. Release the accepted dispatch.
4. Close the builder terminal and every other terminal recorded for the worktree.
5. Remove the task worktree by its recorded id and require an `.ok` response.
6. Delete the task branch with:

   ```bash
   git -C <WT-PATH> branch -d <task-branch>
   ```

   `-d` refuses an unmerged branch. A branch that Orca already removed with the worktree is acceptable.

7. Update and commit the manifest.
8. Dispatch newly ready tasks from the build-owned set up to the concurrency cap.

### Stop contract drift

Contract drift is parallel tasks repeatedly making incompatible changes to one shared interface while both workers stay active.

When you detect contract drift:

1. Compare both implementations with the contract approved in the plan.
2. Fix the contract to one explicit definition within the approved plan.
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

Run the commands recorded in the plan:

1. Build.
2. Lint.
3. Typecheck.
4. Full test suite.
5. Format check.
6. Every command in the plan's Post-Merge Validation section.

Record the result of every applicable command.

Verify each acceptance criterion separately. Verify every boundary in the plan's Integration Verification section. Record the evidence for `summary.md`.

### Verify UI changes

Run browser verification when the diff touches components, pages, layouts, styles, or templates, or when the visual effect is uncertain.

1. Read `references/context/browser-verification.md`.
2. Start one native subagent with the mapped browser skill and the model from `references/routing.md`.
3. Resolve every required value and use the reference's dispatch template and failure policy.
4. Read the screenshots yourself. A browser report without screenshots is not verified.

### Confirm the review policy

Compare the integrated diff and observed failures with the approved `run_complexity`. Planning can underestimate risk that becomes visible only after implementation.

If the implementation has greater aggregate risk:

1. Raise `run_complexity`.
2. Recalculate the code-review cap and QA policy from `references/routing.md`.
3. Update plan frontmatter, the plan's Review Policy, and `run-state.json`.
4. Record the evidence and reason in `summary.md`.
5. Confirm that all three policy records agree.

### Fix verification failures

Turn each failure into a fix task through the Phase 5 fix-task procedure. Put the failing command, its output, and the expected result in the agent task.

After each fix merge:

1. Rerun the failed check.
2. Rerun any checks affected by the fix.
3. Start another fix wave if a check still fails.

Record each wave in `verification.fix_waves`. Allow at most three verification fix waves. Run the abort routine after the third failed wave.

Start Phase 7 only when every project check passes and every acceptance criterion is verified or recorded as not verified with its reason. Record a gap only when this environment cannot verify it, such as an unavailable dev server. A failing check is never a recorded gap.

### Record the verification evidence

Update `<RUNDIR>/summary.md` with the implementation decisions so far, the evidence for each acceptance criterion, every incident, and every unverified gap with its reason. Reviewers and QA read this file. Commit it before Phase 7.

## Phase 7: Code review

Each round gives independent code and security lenses the same committed HEAD. The loop stops when a round produces no substantive code or test change, or when it reaches the approved round cap.

### Prepare the review

1. Read `references/context/review.md`.
2. Read `<CODE_REVIEW_CAP>` from the plan's Review Policy.
3. Set `review_fixes_applied=false` in the manifest.
4. Start every routed code reviewer and security reviewer in `<WT>` from `references/routing.md`. Reviewer terminals stay open across rounds.

### Run a review round

For each `<ROUND>` from 1 through `<CODE_REVIEW_CAP>`:

1. Add the round to `review_rounds` with `code_changed=false` and the current `<WT>` HEAD.
2. Resolve every required value in `references/context/review.md`, including the round context after round 1.
3. Dispatch a fresh task with a unique report path to every code reviewer and security reviewer, collect, and retry a failed lens once within the round.
4. When a retry also fails, record the lens in the round's `missing_lenses` and in the round review, and start a fresh terminal for it before any later round. Run the abort routine if both code-review lenses are unavailable. Continue with the surviving lenses only when every missing security lens is recorded.

### Write the round review

Write `<RUNDIR>/review/review-r<ROUND>.md`. It is the review of record for the round and stands alone: a reader must not need the lens reports. Treat every completed code-review and security-review lens as a separate source.

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

Do not add findings, change severity, or judge validity while combining.

### Triage the findings

Assess each surviving finding against the code and its reproduction.

- Discard a finding that does not hold.
- Accept a finding that holds.
- Treat attribution and severity as evidence, not a verdict.
- Fix every accepted finding in this run unless:
  - it needs a decision owned by the human; or
  - the approved plan explicitly excludes the work.

Record an excluded finding in the PR with the reason it remains.

Append a Triage section to `review/review-r<ROUND>.md`. For each finding, record the outcome, the evidence you checked, and the reason. Commit the round review and manifest before starting a fix wave.

If no finding needs a code or test fix:

1. Leave `code_changed=false`.
2. Record `no accepted fixes` as the stop reason.
3. Stop the review loop.

### Apply review fixes

Turn accepted fixes into Phase 5 fix tasks.

For each fix:

1. Verify the task through the normal build flow.
2. Rerun the finding's reproduction or check.
3. Start another fix wave if the finding still reproduces.
4. Record the fix commit and its verification evidence against the finding in the round review.

Allow at most three fix waves in one review round. After the third failed wave, run the abort routine and attach the round review.

Set `code_changed=true` only after a substantive code or test change is merged and verified in `<WT>`. Report files, bookkeeping changes, and findings that need no implementation change do not count.

When `code_changed=true`, set `review_fixes_applied=true` and continue to the next round unless this round reached `<CODE_REVIEW_CAP>`. At the cap, stop after the verified fix wave and record that no reviewer saw the final fixes.

When `code_changed=false`, stop the review loop.

### Finish code review

1. Close every reviewer terminal.
2. If `review_fixes_applied=true`, rerun Phase 6 project checks and applicable browser checks against the post-review HEAD.
3. Treat verification fixes as post-review and unreviewed. Use the Phase 6 fix procedure with its own three-wave limit, recorded in `verification.post_review_fix_waves`. Do not reopen code review.
4. If no review fix changed the implementation, retain the existing Phase 6 evidence.
5. Require current verification evidence or an explicit reason for every remaining unverified gap.
6. Set `code_review_complete=true` in `run-state.json`.
7. Record the review stop reason.
8. Commit the final round review, verification evidence, and manifest.

## Phase 8: Final adversarial QA

Adversarial QA attempts to break the committed implementation after code review and post-review verification. It runs once. Verify QA fixes, but do not reopen code review for them.

Require a clean integration worktree:

```bash
git -C <WT-PATH> status --porcelain
```

### Apply the QA policy

When `qa_policy` is `skip`:

1. Do not create a QA task, terminal, worktree, dispatch, or findings file.
2. Set `qa.status` to `skipped` and `qa.reason` to `run complexity policy` in `run-state.json`. Record the same result in `summary.md`.
3. Commit the skip record.
4. Continue to Phase 9.

When `qa_policy` is `run`, run the procedure below.

### Prepare the QA worktree

1. Record:

   ```bash
   QA_HEAD=$(git -C <WT-PATH> rev-parse HEAD)
   ```

2. Create a disposable worktree named `<RUN>-qa` from the current `<RUN-BRANCH>`, using `<WT>` as its parent worktree.
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
2. Commit the incident.
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
- carry it to the PR only when it needs a human-owned decision or the approved plan excludes it.

Write `<RUNDIR>/review/qa-review.md`. It is the QA review of record and stands alone: a reader must not need the worker report. Carry every finding from `scratch/qa-findings.md` over in the QA skill's own format, complete and unedited: Severity, Category, Type, Location, Finding, Reproduction, Expected, Actual, Evidence, and Regression test. Carry the coverage list and verdict as written. Then append a Triage section: for each finding, the outcome, the evidence you checked, and the reason. Commit the QA review and manifest before starting fixes.

Create accepted fixes as Phase 5 fix tasks from the current `<RUN-BRANCH>`. Never make lasting fixes in the disposable QA worktree.

For every fix wave:

1. Verify each fix task.
2. Rerun each finding's exact reproduction.
3. Rerun the Phase 6 project checks and applicable browser checks.
4. Record the fix commit and its verification evidence against the finding in the QA review.
5. Start another wave if a finding still reproduces.

Allow at most three QA fix waves. After the third failed wave, run the abort routine and attach the QA review.

Set `qa.status` to `completed` and clear `qa.reason`. Commit the final QA, fix, and verification evidence before Phase 9.

## Phase 9: PR

### Finalise the run evidence

Complete `<RUNDIR>/summary.md` with:

- start and end datetimes;
- what the PR contains;
- plan-review tier and cap used;
- final run complexity and downstream review policy;
- plan-review and code-review rounds with stop reasons;
- security-review coverage for each round, including why a lens was missing;
- QA result or policy skip;
- decisions and judgement calls with their reasons;
- each acceptance criterion and its evidence;
- incidents, including reset reviewer trees and superseded dispatches;
- open questions;
- every remaining unverified or unfixed item and its reason.

Commit all outstanding evidence and state. Require:

```bash
git -C <WT-PATH> status --porcelain
```

to return no output.

### Publish the branch and PR

1. Push `<RUN-BRANCH>`. It is the only branch that may reach the remote.
2. Open the PR through the mapped `{pr-skill}` against the base branch.
3. Write the PR body from `plan/plan.md` and `summary.md`. Do not copy either document verbatim.
4. Include:
   - a concise implementation summary;
   - acceptance criteria with evidence;
   - the source issue link when one exists;
   - review rounds and security coverage;
   - fixed findings and their verification evidence;
   - every unfixed finding with its reason and attribution;
   - the QA result or policy skip;
   - screenshot references for UI changes;
   - the sign-off block below.

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
4. Do not sweep or act on unfiltered `terminal list` or `worktree list` output. Orca is shared with other runs.
5. Keep the integration worktree until the PR merges and mark it `retained`. Its later removal with `orca worktree rm` belongs to the human.
6. Set `cleanup.status` to `complete` when no removable resource remains. Otherwise set it to `partial` and record every remaining handle or worktree id.

### Record PR state

1. Set `run-state.json` status to `pr`.
2. Record the PR URL.
3. Commit and push the final state update.
4. Report:
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
3. If recovery needs a human-owned scope, security, destructive-operation, or architectural decision, run the abort routine with status `blocked`.
4. Append a retry briefing to the agent task:
   - what each cycle attempted;
   - each failure and its output;
   - the relevant cycle-report paths;
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

Allow independent in-flight tasks to finish through collection, verification, and merge. Dispatch no new tasks. Then run the abort routine.

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
6. Update `summary.md` with:
   - final status;
   - what was attempted;
   - observed failures;
   - preserved branches;
   - what remains.
7. Update `run-state.json`.
8. Report the failure or blocker to the human.

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

On a context-limit or unexpected coordinator error, attempt recovery first. If recovery fails, record as much of the abort state as possible.

A fresh coordinator session resumes from durable state:

1. Load `run-state.json`, the task DAG, `<RUNDIR>`, and the run branch.
2. Reconcile them with live Orca state.
3. Treat merge commits and task branches as authoritative when they conflict with manifest task status.
4. Reacquire stale terminal handles by matching the recorded title and worktree.
5. Collect pending `worker_done` messages before dispatching anything.
6. Do not re-dispatch work already committed on a task branch.
7. Do not re-merge an already merged branch.
8. In Phases 6 through 8, resume from the recorded round and fix-wave counts.

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
