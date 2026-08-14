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

You are the coordinator. You take one task and deliver a shipped PR: plan it, dispatch workers to build it, verify their work, run a cross-model review, and open the PR.

Rules that hold for the whole run:

- **You never write implementation code**: the only exceptions are trivial fixes (typos, docstrings/comments, unused imports, formatting via hand edit or Format write, in its own commit) and trivial textual merge conflicts. Everything else goes to a worker.
- **Workers never create Orca tasks, dispatches, or terminals**: All Orca coordination is yours. Workers may fan out their own runtime's native subagents internally (the review and QA skills do); they own and clean up that fan-out themselves.
- **Four human touchpoints**: the invocation, the understanding check, the plan gate, the PR. After the plan gate, run autonomously to the PR: never stop to ask; every judgment call is yours, logged in `summary.md`. Anything that genuinely needs the human (scope, security, destructive operations, architectural forks) must be settled by the plan gate; a mid-run blocker you cannot resolve ends the run through the abort routine, not a question.
- **Report what actually happened**: never what was supposed to happen.
- **Maintain `<RUNDIR>/run-state.json`**: the run manifest, updated after every state transition. It records:
  - run name, Orca run id, source, and current phase;
  - base branch and pinned base SHA;
  - plan-review tier and snapshotted cap, current run complexity, and the downstream review/QA policy;
  - integration worktree (id, path, branch);
  - per-task records: seq, slug, kind (`build` | `fix`, with originating phase and round for fixes), task id, worktree id/path, branch, starting commit, terminal handle and title, routed model and effort, active dispatch id, superseded dispatch ids, verify→fix and resolve→verify cycle counts, assignment/report paths, and status (`ready` | `dispatched` | `completed` | `failed`);
  - planner/critic/review/QA dispatch records, including skipped QA;
  - review-round records (start HEAD, synthesis path) and fix-wave counts per phase and round;
  - cleanup state.
- **Orca state is runtime-global**: Other runs and repos share the task store and terminal list. Act only on ids, handles, and paths recorded in your manifest; never dispatch, complete, close, or remove anything the run doesn't own. The recorded run id namespaces this run's tasks and messages.

Model and effort routing for every role, plus worker boot commands: `references/routing.md`. The skill each role invokes: `references/skill-map.md`.

## Intake

`/orca-implement {TASK-REF | prompt}`

Normalize the argument into requirements:

- **GitHub issue** (`#123` or issue URL): `gh issue view <n> --json title,body,comments`
- **Linear issue** (`ABC-123` or Linear URL): `orca linear issue <ref> --full --json`
- **File path** (markdown docs, specs): read it directly.
- **Anything else**: an ad-hoc prompt; you draft the requirements and acceptance criteria yourself during planning, and the human vets them at the understanding check and the plan gate.

Any intake read that fails or returns empty (missing Linear connection, unresolvable issue, unreadable file) is an intake failure: stop before allocating anything.

The plan distills what intake read into requirements and acceptance criteria, citing its source (format: `references/plan-template.md`). It must stand alone: a worker cannot be relied on to reach a URL or a path outside its sandbox. The run works from what intake read; a ticket changing mid-run does not change the plan.

## Phase 0: Setup

**Preflight.** Run all checks before allocating anything; any failure stops the run with a clear message:

1. Load the `orchestration` skill: resolve the Orca executable and load the guides it serves for `orchestration` and `orca-cli`. `orca` in this skill means the resolved executable. The guides own command names, flags, and message mechanics; this skill owns process, ownership, and safety.
2. Orca ready: `orca status --json` satisfies `jq -e '.ok == true and .result.runtime.reachable == true and .result.runtime.state == "ready"'`.
3. You are inside an Orca-managed terminal: `[ -n "$ORCA_TERMINAL_HANDLE" ]`. If not, tell the human to relaunch inside Orca.
4. Repo registered: `orca repo list --json` contains this repo. Base ref clean.

**Pin the base**: `BASE_SHA=$(git rev-parse <base-ref>)`. Every diff, review, and changed-file computation from here on uses `BASE_SHA`, never the symbolic ref. The ref serves only once more, as the PR's target branch.

**Name the run**: `<RUN>` = `{yyyymmdd-hhmm}-{ref?}-{run-slug}`, built from the UTC datestamp (`date -u +%Y%m%d-%H%M`), the normalized ref (`gh-123` / `lin-abc-123`, omitted for ad-hoc), and a run slug from the source title or prompt in lowercase alphanumerics and hyphens.

**Bind the Orca Run**: create it with objective `<RUN>` and record the run id in `run-state.json` at initialization. Every `task-create` passes that run id; tasks and messages outside it are not yours.

**Create the integration worktree.** Capture the Orca-derived branch and use only captured names from here on. Create it named `<RUN>` from the base ref, linked to the source issue when there is one; a duplicate-name failure means another run holds the name: adjust the slug and retry. Capture `<WT>` (worktree id) and `<WT-PATH>` (absolute path) from the JSON, then:

```bash
git -C <WT-PATH> branch --show-current    # → <RUN-BRANCH>; record it
git -C <WT-PATH> rev-parse HEAD           # must equal BASE_SHA; reset to BASE_SHA if not
```

**Allocate the run folder inside the worktree**:

```bash
RUNDIR="<WT-PATH>/.agents/orca/orchestration/<RUN>"
mkdir -p "$RUNDIR/plan" "$RUNDIR/tasks" "$RUNDIR/review" "$RUNDIR/screenshots"
```

The run folder holds exactly this:

```text
run-state.json                             run manifest
summary.md                                 run narrative, finalized at Phase 9
plan/plan.md                               spec of record
plan/draft-<fable|opus|sol>.md             one per planner on the tier's panel
plan/critique-<fable|opus|sol>-r<ROUND>.md one per critic per round
tasks/{seq}-{slug}-assignment.md           coordinator to builder
tasks/{seq}-{slug}-report.md               builder to coordinator
review/<claude|codex>-review-r<ROUND>.md   one per code reviewer per round
review/security-review-r<ROUND>.md         security reviewer, one per round
review/synthesis-r<ROUND>.md               deduped findings for the round
review/qa-findings.md                      high/xhigh runs only
screenshots/{description}_{sequence}.png
```

The run folder lives on the run branch like any other work: commit it as artifacts land (each phase boundary at minimum), but never between recording `<WT>` HEAD for a collection check and running that check.

Initialize `run-state.json` immediately, before creating or closing anything further: run name, Orca run id, source, start datetime (UTC), `phase: setup`, base ref, `BASE_SHA`, `plan_review_tier: pending`, `plan_review_cap: pending`, `run_complexity: pending`, downstream review/QA policy pending, `review_fixes_applied: false`, integration worktree (id, path, branch), and any terminal that `worktree create` auto-spawned (find it in the JSON or the terminal list). Close an auto-spawned terminal only after confirming it is an unused shell; a configured default tab stays recorded in the manifest and closes at teardown. Every terminal in this run must be a captured, manifest-recorded handle.

`<WT>` is your integration point: task branches merge into `<RUN-BRANCH>` here; whole-run verification and review run here. Every build and fix task gets its own worktree at dispatch (Phase 5).

## Phase 1: Scout

Scout with your own runtime's native subagents (read-only explorers), not Orca terminals. Dispatch in parallel (models: `references/routing.md`):

- **Discovery scouts**: project mechanics and inventory. Tooling commands (Install, Build, Test, Lint, Typecheck, and Format in both check and write forms), `.env` presence, the repo's commit-message convention, where the relevant code lives.
- **Comprehension scouts**: blast radius and current behaviour of the code being changed, and dependencies on existing code.
- **Test coverage scouts**: existing coverage that will need adjusting, and important gaps to close for the implementation goals.
- **Additional scouts**: any others you judge the task needs, on the same read-only terms and routing.

Require `path:line` evidence for claims. Mark every assumption scouting could not confirm; unresolved assumptions go into the plan for the critics and the human.

Scouts return their findings in their final message; what survives scouting goes into `plan/plan.md`.

## Phase 2: Understanding check

Present to the human your understanding of the task: requirements and intended scope as you read them, what is explicitly out, and the scouting findings that shape the approach. Then ask your questions **one at a time** (ambiguities, missing acceptance criteria, conflicts between the source and the code), waiting for each answer before asking the next. When nothing remains open, ask for the go-ahead. Answers are settled facts in the plan; a question you could ask here never becomes an open assumption.

## Phase 3: Plan

**Step 1: Tier.** Classify `plan_review_tier` from the requirements and scout evidence (rubric: `references/routing.md`) and snapshot it with its plan-review cap in `run-state.json`. The tier selects the drafting mode and stays fixed through critique.

**Step 2: Draft.** The tier sets the planner panel (`references/routing.md`): a single planner on `low` | `medium`, competitive drafting across three on `high` | `xhigh`. In both modes:

1. Compose the drafting brief: requirements and acceptance criteria, scouting findings with their evidence, settled answers from the understanding check, open assumptions, project tooling verbatim, and the required plan structure copied from `references/plan-template.md`; drafters cannot read this skill's files, so the brief must stand alone. The brief goes verbatim into each planner's task spec.
2. Record `git -C <WT-PATH> rev-parse HEAD`. Boot the tier's planner terminals (panel, models, effort, and commands: `references/routing.md`). Per planner (`<P>` from the panel): wait for terminal readiness, create a task titled `plan-draft-<P>` with the spec below, and dispatch it injected to `<H_PLANNER_P>`; record the dispatch id.

   ```text
   Independently write a complete implementation plan to <RUNDIR>/plan/draft-<P>.md following the plan structure given in the brief below. Do not read any other draft-*.md file. Your draft is the only file you may write. Then report completion.

   BRIEF:
   <the composed brief>
   ```
3. Collect every panel draft with the bounded-wait loop and correlation rules. A failed, overdue, or draftless planner: mark its task `failed`, close its terminal, then **retry that lens once**: boot a fresh terminal for that lens per its routing row, create a fresh task with the identical brief, and dispatch. Collect the retry on the same loop. A lens that fails twice is done: judge the surviving drafts; a sole surviving draft continues as the base with no grafting source; no surviving drafts means writing `<RUNDIR>/plan/plan.md` yourself, following `references/plan-template.md` exactly. Record every retry and any reduction. Run the read-only collection check, then commit the drafts.
4. Judge the complete drafts on the axes the critics will use: decomposition seams, requirement coverage, correctness against the requirements, verification adequacy, sizing in both directions. The strongest draft is the base of the final plan. Correct anything your judgment or the brief contradicts, graft in elements where another draft is genuinely better, and write `<RUNDIR>/plan/plan.md` yourself following the template; the plan must read as one author's work, never a concatenation. Close the planner terminals.

Key obligations for `plan/plan.md` in both modes:

- Frontmatter carries the pinned `base_sha`, captured `<RUN-BRANCH>`, a `plan_review_tier`, and `run_complexity: pending` until critique ends.
- The Review Policy snapshots the plan-review cap from `plan_review_tier`. Final code-review depth and QA remain pending until the reviewed plan determines `run_complexity`.
- Requirements and acceptance criteria with `AC-n` IDs; every criterion covered by at least one task.
- Task table with explicit deps, complexity, and builder routing. Prefer the smallest viable task set.
- Contracts: pin every interface shared across tasks before dispatch.
- Assumptions split validated (with evidence) vs open (assigned to the task that must verify them).
- Project tooling verbatim, including Build and separate Format check / Format write.
- Verification requirements target behaviour on critical paths; the goal is to cover the important behaviours and edge cases, not every line.

**Step 3: Fact check.** Dispatch one read-only native subagent (model: `references/routing.md`) to verify every checkable claim in the plan against the repo: file paths, `path:line` evidence, command names, symbols and interfaces cited in contracts. It does not assess reasoning, decomposition, scope, or the run-complexity judgment; it reports mismatches only. Fix every mismatch in the plan before booting the critics.

**Step 4: Cross-model critique loop.** `<PLAN_REVIEW_CAP>` and `plan_review_tier` were snapshotted at Step 1 and are fixed for this critique loop, even if the plan's risk changes. Boot the tier's critic terminals (panel, models, effort, fallback, and worker boot: `references/routing.md`), then run rounds 1 through `<PLAN_REVIEW_CAP>`:

1. Set `PLAN_CHANGED=false` before dispatch. Record `git -C <WT-PATH> rev-parse HEAD`. Per critic (`<M>` from the panel): wait for terminal readiness, create a fresh task for this round titled `plan-critique-<M>-r<ROUND>` with the spec below, and dispatch it injected to `<H_CRITIC_M>`; record the dispatch id.

   ```text
   Read <RUNDIR>/plan/plan.md. Adversarially critique it: you are a critic, not an approver, and your job is to try to break this plan. Find the strongest reasons it fails: the weakest assumption, the missed or miscovered requirement, the seam most likely to produce an integration failure, the verification gap a bug would slip through. Judge decomposition seams, coverage of every requirement, correctness against the requirements, verification adequacy, and sizing in both directions (would fewer tasks beat coordination cost; is any single task too complex to land reliably). Out of scope: implementation detail, style, scope expansion. Each finding: plan section, concrete failure scenario, severity BLOCKING|RISKY|NOTE. A round with no genuine findings is a valid outcome, but reach it by failed attack, not benign reading. End with a verdict: proceed|revise|re-plan. Write your full critique to <RUNDIR>/plan/critique-<M>-r<ROUND>.md. That file is the only file you may write. Then report completion.
   ```
2. Collect every panel critique with the bounded-wait loop and correlation rules below. Mark a failed, overdue, or reportless critic task `failed`, close its terminal, and continue with the surviving lenses; note the failure at the plan gate and boot a fresh terminal for that lens before a later round. If all panel critics fail in one round, retry their dispatches once on fresh terminals; if the retry also fails, stop the critique loop and carry the failure to the plan gate, where the human decides whether to proceed on the plan as it stands or cancel the run.
3. Evaluate every finding on its merits. Severity labels are evidence, not verdicts. Revise the plan for accepted findings. Set `PLAN_CHANGED=true` only after changing the plan; critic verdicts, critique artifacts, timestamps, discarded findings, and findings accepted but needing no edit do not count.
4. Run the read-only collection check, then commit the plan and critique artifacts.
5. If `PLAN_CHANGED=false`, stop immediately. If it is true and the cap is not exhausted, run the next round against the revised plan. At the cap, stop; the final round's revisions are not re-critiqued.

Close the critic terminals when the loop stops. Assess `run_complexity` from the reviewed plan; it may be higher or lower than `plan_review_tier`. Fill the downstream Review Policy from `references/routing.md`, then update plan frontmatter and `run-state.json`. Preserve `plan_review_tier`, `<PLAN_REVIEW_CAP>`, rounds run, and the stop reason as historical inputs. Commit these updates before Phase 4.

## Phase 4: Plan gate

The human gate is an unlimited approval loop and is not subject to either review cap. Plan critique and fact checking are finished before this phase and never reopen here.

Present the plan, `plan_review_tier`, current `run_complexity` and its review/QA policy, critic outcomes, rounds run, and open assumptions. Conduct the gate through the mapped `{plan-gate-skill}`: run its documented loop (address every unresolved comment, re-present the live plan, and run the printed next-round command). Approval is a subsequent round the human finishes with zero comments; a gate command exiting with feedback is not approval. If the skill is unavailable, conduct the gate in-session, incorporate requested changes, and re-present until the human explicitly approves by message. Silence, no requested changes, and critic verdicts are never approval.

If feedback suggests changing `run_complexity` in either direction, present the current tier, proposed tier, rationale, and resulting code-review cap/QA policy, then ask for a direct answer on that tier change. General plan approval or a zero-comment gate round does not approve a complexity change. At this gate, update the plan and manifest only after explicit tier approval; Phase 6 may raise the tier on its own evidence. Continue at this gate until final plan approval; then commit the approved plan and manifest before Phase 5. An explicit rejection or cancellation invokes the abort routine.

## Phase 5: Build (parallel where deps allow)

Register the DAG with **thin pointer specs** (task specs are immutable after creation): per task, title `{seq}-{slug}`, deps by owned task id, and this spec:

```text
Run <RUN> assignment {seq}-{slug}. Read your full assignment first: <RUNDIR>/tasks/{seq}-{slug}-assignment.md (absolute path).
```

Record every returned task id in `run-state.json`: the run's owned set.

**Dispatch loop**: launch every ready task *from the owned set* (never from raw `task-list --ready`; it is runtime-global), up to the concurrency cap (`references/routing.md`). Per task:

1. **Create the task worktree** named `<RUN>-{seq}-{slug}` from `<RUN-BRANCH>` with parent worktree `<WT>`. Capture id, path, and actual branch (`git -C <path> branch --show-current`); close the auto-spawned terminal after confirming it is an unused shell, recording a configured default tab instead; record the starting commit (`git -C <path> rev-parse HEAD`).
2. **Write the assignment file** `<RUNDIR>/tasks/{seq}-{slug}-assignment.md` from `references/assignment-context.md`, now that its contents exist: the worktree path and branch just captured, inputs and sync artifacts from completed dependencies, contracts, tooling verbatim, report path. Resolved context goes in this file, never inline into a shell argument.
3. **Boot the routed builder** there (worker boot: `references/routing.md`), wait for terminal readiness, then dispatch the task injected to its terminal. Record the dispatch id and set the task's manifest status to `dispatched`.

**Collect loop**: wait on `worker_done`, `escalation`, and `question` in bounded slices of at most 540000 ms. Process every message in a delivery, then acknowledge it and keep waiting. For each message:

- Correlate `payload.taskId` + `payload.dispatchId` against the manifest's **active** dispatches. Messages for other runs' tasks or superseded dispatches: log and ignore. `question` and `escalation`: handle them yourself. Answer with an orchestration reply, never via files, or adjust the assignment; one you cannot resolve goes to the abort routine, not to the human. Neither is a completion.
- On a correlated `worker_done`: run the per-task verify+merge below, then dispatch owned ready tasks up to the cap, then loop.
- Loop until every owned dispatch is terminal. If a worker is overdue (two consecutive empty waits with no new commits on its branch), `orca terminal read` it: actively working means keep waiting; stuck, prompting, or crashed means stop it, close its terminal, inspect its committed work, boot a fresh terminal on the same branch and worktree, set the task back to `ready`, and re-dispatch with that work as context; record the old dispatch id as superseded. This counts toward the verify→fix limit.

**Per completed task: verify, then merge immediately** (never batch merges):

1. Commits exist past the recorded starting commit (`git log <starting-commit>..<task-branch> --oneline`); worktree clean (`git -C <task-worktree> status --porcelain`). No commits + clean tree is valid only for explicitly no-change outcomes. Uncommitted changes: do not merge; run a fix cycle.
2. Read the report (`<RUNDIR>/tasks/{seq}-{slug}-report.md`) and check its claims by running the checks it says passed: Build first, then Lint, Typecheck, Tests, Format check.
3. Requirements met against the plan. If not, run a **fix cycle**: append your findings to the assignment file, set the task back to `ready`, re-dispatch injected to the same terminal, record the fresh dispatch id and supersede the old one, increment the cycle counter. **Max 3 verify→fix cycles per task**, then the retry protocol.
4. **Merge the task branch into `<RUN-BRANCH>`** in `<WT>`. Trivial textual conflicts (imports, adjacent independent hunks) resolve yourself under the trivial-fix exception; semantic conflicts: abort the merge and register and dispatch a conflict-resolution fix task (fix-task discipline below) whose deliverable is the conflicted task branch merged into its fix branch with conflicts resolved, so the resolving commit is attributable. The original task stays `dispatched` in the manifest; collect the conflict task through the normal loop, and after its own verify, merge, and step 5, run the original task's step 5. Run integration checks in `<WT>` guided by the scouted blast radius. **Max 3 resolve→verify cycles per original task**, then the retry protocol.
5. The accepted `worker_done` already completed the task and dispatch in Orca; that is the worker's signal, not the run's truth. Mark the task merged in the manifest now; a dependent dispatches only when the manifest shows every dependency merged. Release the dispatch, close the builder terminal, remove the task worktree by recorded id (check `.ok`), delete the merged task branch (`git -C <WT-PATH> branch -d <task-branch>`; `-d` refuses if it is unmerged; already gone after worktree removal is fine), update and commit the manifest, dispatch owned ready tasks up to the cap.

**Contract watch**: when two parallel tasks keep reshaping a shared interface to fit their own side, neither is stuck but the work is cycling. Freeze the contract yourself and dispatch explicit conform-to-contract fixes.

**Fix tasks** (Phase 6 failures, Phase 7 review fixes, Phase 8 QA fixes, conflict resolution): fix tasks are build tasks. Classify each with the task-complexity rubric, route via the matching builder row and fallback (`references/routing.md`), and run the full flow above: register (continuing the run's `{seq}` numbering), task worktree from the current `<RUN-BRANCH>`, assignment file, dispatch, collect, verify, merge, cleanup. Default to a single fix task per wave; split into parallel tasks (under the concurrency cap) only when the fixes are independent and the wave is large enough that parallelism beats the coordination overhead. Sequence split tasks with deps where they are not independent.

## Phase 6: Whole-run verification

After the last merge, in `<WT>`:

- Full test suite plus Build, Lint, Typecheck, Format check.
- **Browser verification** when the changeset touches UI (components, pages, layouts, styles, templates); skip only for purely non-visual changes, and if in doubt, dispatch:
  - Spawn one coordinator-native subagent (not an Orca terminal) with the mapped `{browser-skill}` in headless mode (never headed); model per `references/routing.md`.
  - Brief it with the dev server URL or start command (run from `<WT-PATH>` on a free port), every affected page, the changed feature to interact with, and what correct behaviour looks like.
  - Screenshots go to `<RUNDIR>/screenshots/` as `{description}_{sequence}.png`, required for PASS and FAIL alike. If interaction mutates real data, undo it.
  - If the dev server won't start: recover (different port, `.env` present, re-install), cap 3 attempts, then record "not verified: dev server unavailable" with the errors. The subagent stops any dev server it started before reporting.
  - Read the screenshots yourself; a report without screenshots is not verified.
- Acceptance criteria, criterion by criterion, evidence recorded for `summary.md`.
- **Review-policy confirmation**: compare the actual diff and observed failure modes with approved `run_complexity`. If implementation revealed greater aggregate risk, raise the tier, recompute the code-review cap and QA decision, update plan frontmatter, Review Policy, and `run-state.json`, and record the rationale in `summary.md`. Verify the three policy records agree before Phase 7.

Any failure here becomes a fix task (fix-task discipline, Phase 5): write an assignment with the failing check and output, register and dispatch, routed by complexity, re-verify after the merge; a check still failing starts another wave. **Max 3 fix waves**, then the abort routine. Phase 7 starts only once whole-run verification passes, or with every remaining gap explicitly recorded as not verified (with reasons), never with silent failures.

## Phase 7: Code Review

Set `<CODE_REVIEW_CAP>` from the plan's Review Policy and set both `REVIEW_FIXES_APPLIED=false` and manifest `review_fixes_applied=false`. Boot the Claude and Codex code-reviewer terminals and the security-reviewer terminal in `<WT>` (worker boot: `references/routing.md`), wait for each to reach readiness, then run rounds 1 through `<CODE_REVIEW_CAP>`:

1. Set `CODE_CHANGED=false` before dispatch and record `<WT>` HEAD in the round's manifest record. Create fresh reviewer tasks and reports for `<ROUND>`. For rounds after the first, include as context the commit range from the previous round's recorded HEAD to the current HEAD, and the preceding synthesis path. Dispatch each code reviewer with:

   ```
   Run /{code-review-skill} (it exists; do not check) and follow the prompt. Review
   the current branch against base commit <BASE_SHA>. Exclude .agents/orca/orchestration/
   (run bookkeeping, not the implementation). Write your FULL report to
   <RUNDIR>/review/<claude|codex>-review-r<ROUND>.md. That file is the only file
   you may write; do not edit code. Then report completion.
   ```

   Dispatch the security reviewer alongside the code reviewers with:

   ```
   Run /{security-review-skill} (it exists; do not check) and follow the prompt. Review
   the current branch against base commit <BASE_SHA>. Exclude .agents/orca/orchestration/
   (run bookkeeping, not the implementation). Write your FULL report to
   <RUNDIR>/review/security-review-r<ROUND>.md. That file is the only file
   you may write; do not edit code. Then report completion.
   ```
2. Collect all three reviewers via the bounded-wait loop with dispatch-id correlation; the round proceeds only once every reviewer dispatch is terminal. Mark a failed or reportless reviewer task `failed` and close its terminal, then **retry that lens once within the round**: boot a fresh terminal per its routing row, create a fresh task with the identical dispatch text, and collect it on the same loop. A lens failing twice in one round is out for the round: continue with the survivors and record the missing lens in the synthesis; boot a fresh terminal for it before a later round. If both code-review lenses are out for a round, run the abort routine; if only the security lens is out, the round proceeds with the synthesis recorded as lacking security coverage. Run the read-only collection check against the recorded HEAD, then commit the reports and manifest.
3. Synthesize to `<RUNDIR>/review/synthesis-r<ROUND>.md`. Sources are `claude`, `codex`, and `security`. Apply these mechanics only:
   - Drop findings whose cited file exists neither at HEAD nor at `BASE_SHA`; deleted files are valid citations. Keep a finding in untouched code only when it traces a causal path to a changed file. Record drops in an appendix.
   - Dedupe by finding identity, not wording.
   - Preserve attribution and every source's severity.
   - Record base SHA, branch, round, lenses run, and counts (raw → after existence → after dedupe). Do not add findings, re-score, or judge validity during synthesis.
4. Triage every finding on its merits: discard the ones that do not hold, and accept the rest as fixes. Attribution and severity are evidence, not verdicts. A finding that holds is fixed in this run unless fixing it needs a decision the human owns or work the plan explicitly put out of scope, which makes it an exception carried to the PR with the reason it stands. Merely accepting a finding does not set `CODE_CHANGED=true`. Commit the synthesis and manifest before starting the fix wave.
5. If there are no accepted fixes, explicitly leave `CODE_CHANGED=false`, record `no accepted fixes`, and stop.
6. Turn the accepted fixes into fix tasks (fix-task discipline, Phase 5). Verify each task and re-run each finding's own reproduction or check; a finding still failing starts another wave. **Max 3 fix waves per round**, then the abort routine with all syntheses attached.
7. Set `CODE_CHANGED=true` only after substantive code or test fixes are merged and verified in `<WT>`, then set `REVIEW_FIXES_APPLIED=true` and manifest `review_fixes_applied=true`. If the fix wave makes no substantive implementation change, leave `CODE_CHANGED=false`; report/artifact edits and findings accepted but needing no code change do not count. Stop when `CODE_CHANGED=false`.
8. If `<ROUND>` equals `<CODE_REVIEW_CAP>`, stop after the verified fix wave. Record that the cap was reached and the final fixes were not re-reviewed. Otherwise continue to the next round.

Close all reviewer terminals when the loop stops. If `REVIEW_FIXES_APPLIED=true`, rerun Phase 6's full project and applicable browser checks against the post-review HEAD; verification fixes follow Phase 6's fix discipline, are recorded as post-review and unreviewed, and do not reopen code review. Otherwise retain the existing Phase 6 evidence. Once verification is current or every remaining gap is explicitly recorded, set `code_review_complete=true` in `run-state.json`, record the stop reason and persisted `review_fixes_applied`, and commit the final review and verification artifacts.

## Phase 8: Final adversarial QA

Adversarial QA begins only after code review and post-review verification complete. Require `git -C <WT-PATH> status --porcelain` to be empty; QA starts from that exact committed, verified HEAD.

`low` or `medium`: do not create a QA task, terminal, worktree, dispatch, or findings file. Record `adversarial_qa: skipped` with reason `run complexity policy` in `run-state.json` and `summary.md`, commit the skip record, then continue to Phase 9.

`high` or `xhigh`, in order:

1. Record `QA_HEAD=$(git -C <WT-PATH> rev-parse HEAD)`.
2. Create the disposable worktree named `<RUN>-qa` from the current `<RUN-BRANCH>` with parent worktree `<WT>`. Capture its id, path, and actual QA branch; close the auto-spawned terminal after confirming it is an unused shell; verify its HEAD equals `QA_HEAD`.
3. Boot the routed QA worker there (worker boot: `references/routing.md`), wait for terminal readiness, then dispatch:

   ```
   Run /{adversarial-qa-skill} (it exists; do not check) against the current branch
   vs base commit <BASE_SHA>: code-level and browser-based attempts to break the
   implementation. Exclude .agents/orca/orchestration/ (run bookkeeping, not the
   implementation). Browser work runs headless. This worktree starts at the latest
   post-review HEAD <QA_HEAD>. Write findings, each with a reproduction (test
   scenario or screenshot), to <RUNDIR>/review/qa-findings.md; a no-findings run still
   writes the full report (what was attacked, how, and that it held). That report and
   screenshots under <RUNDIR>/screenshots/ are the only paths you may write
   outside your worktree. Clean up throwaway test files; for tests that produced a FAIL,
   capture the exact scenario in the finding before cleanup. Then report
   completion.
   ```
4. Collect the QA task with dispatch-id correlation. On success, require a non-empty `qa-findings.md`, then record it completed in the manifest. On failure or a missing report, mark it `failed`, record QA as not verified, clean up its terminal, worktree, and branch, commit the incident, and continue to Phase 9 without triage.
5. Close the QA terminal, remove its worktree by recorded id, and delete its branch. No QA branch merges.
6. Triage each concrete finding on its merits: discard the ones that do not hold, and accept the rest as fixes on the same terms as Phase 7. Commit the report and the manifest before starting the fix wave.
7. Turn the accepted fixes into fix tasks (fix-task discipline, Phase 5), never in the disposable QA worktree. Verify each task, re-run every finding's exact reproduction, then rerun Phase 6's full project and applicable browser checks; a finding still failing starts another wave. **Max 3 QA fix waves**, then the abort routine with `qa-findings.md` attached.
8. Commit final QA and fix evidence with manifest updates before Phase 9.

QA runs once and code review does not reopen; final QA fixes are verified but not code-reviewed.

## Phase 9: PR

1. Finalize `<RUNDIR>/summary.md`: start/end datetimes, what shipped, plan-review tier and cap used, final run complexity and downstream review policy, plan/code-review rounds run with stop reasons, security-review coverage per round (run, or why it was missing), QA run/skip result, decisions and judgment calls with reasoning (accumulated throughout the run), acceptance criteria with evidence, incidents (reset reviewer trees, superseded dispatches), open questions.
2. Ensure everything is committed: `git -C <WT-PATH> status --porcelain` must be empty after committing whatever is outstanding (`summary.md`, final `run-state.json`).
3. Push the run branch: the only branch that ever reaches the remote, and only now.
4. Open the PR (the mapped `{pr-skill}` flow) against the base *branch*. The body carries:
   - a summary written from `plan/plan.md` and `summary.md`, not copied from them;
   - acceptance criteria with evidence;
   - the source issue link when there is one;
   - a review appendix: rounds run, security-lens coverage per round, fixed findings and re-verification evidence, and every finding left unfixed with its reason and attribution;
   - the QA result when run, otherwise its policy skip;
   - screenshot references for UI changes;
   - the sign-off block below, which replaces the PR skill's own sign-off:

```markdown
---
:space_invader: Built with Orca
Build: {display names of every model that produced or fixed shipped code, deduped; no effort levels}
Code review: {display names of the code-reviewer models behind completed lenses, with rounds run; no effort levels}
Security review: {security-reviewer model when its lens completed, with rounds run; otherwise "not run"; no effort levels}
```

5. Teardown, verified **against the manifest**: close every terminal handle recorded in `run-state.json`, remove any remaining task/QA worktrees by recorded id, confirm each is gone. Never sweep unfiltered `terminal list` / `worktree list` output; the runtime is shared. Only the integration worktree survives, kept until the PR merges (`orca worktree rm` is the human's post-merge step, not yours).
6. Update `run-state.json` (status: shipped, PR URL), commit and push it, then report to the human: PR URL, what shipped, what review and QA fixed, anything they surfaced that stands unfixed and why, anything unverified.

## Failure handling

- **Retry protocol** (a task exhausts its 3 cycles): Diagnose whether the failure lies in the approach or the execution. Adjust the assignment or plan, and append a retry briefing to the assignment file: what each cycle attempted, what failed and how (failing checks with output, from the cycle reports), and your diagnosis of why. Then respawn a fresh worker on the same branch and worktree (supersede the old dispatch). If the replacement also exhausts 3 cycles, the task is **permanently failed**: set it `failed` in Orca and the manifest, mark owned dependent tasks `failed` (dependency failed), close its terminal, remove its worktree (branch preserved for manual review; verify the branch survives `worktree rm` on first use, and if it does not, tag the tip `git tag orca-run/<RUN>/{slug} <sha>` before removal, never pushed), and record attempts and branch name in `summary.md`. Let independent in-flight tasks finish (collect, verify, merge); dispatch nothing new; then run the abort routine.
- **Abort routine** (one idempotent path, used for permanent task failure, fix-wave exhaustion, plan rejection, both-code-reviewers failure, and unresolvable critical escalations): mark this run's remaining non-terminal tasks `failed`; close all manifest-owned terminals; remove disposable/task worktrees by recorded id (failure branches preserved; delete the QA branch if one was created); write `summary.md` with `status: failed|blocked`, what was attempted, and what remains; update `run-state.json`; report to the human. The integration worktree and run branch survive for inspection.
- **Infeasibility**: consecutive tasks failing for structurally similar reasons, or verification failing on the same criterion regardless of implementation, means the plan or requirements are wrong, not the workers. Stop respawning and run the abort routine, recording what you observed, which assumptions the plan depends on that look wrong, and your best read of what is feasible.
- **Coordinator failure** (context limit, unexpected error): attempt recovery; otherwise execute as much of the abort routine's recording as possible. `run-state.json`, the DAG, the run branch, and `<RUNDIR>` survive. A fresh session resumes from the manifest's `phase`, reconciled against live Orca state and the run branch: merge commits and task branches are authoritative over manifest task status; collect pending `worker_done` messages before dispatching anything; never re-dispatch work already committed on a task branch or re-merge a merged branch. Inside Phases 6-8, the review-round records and fix-wave counts say which round or wave was live and how much of its budget is spent.
- Orca's dispatch circuit breaker marking a task `failed` is retry-protocol entry, not a failure to retry in place. Never run `orca orchestration reset`; the store is shared with other runs.

## Orca mechanics

- Capture handles, ids, paths, branch names, and dispatch ids at creation into `run-state.json`; none can be recomputed. If Orca restarts mid-run, handles go stale: re-acquire from the terminal list, matching recorded title and worktree against the manifest, before continuing.
- Command syntax comes from the preflight-loaded guides; never guess flags from memory. Where a guide's generic pattern conflicts with this skill's process, ownership, or safety rules, this skill wins.
- `check --wait` returns one delivery at a time; run it in ≤ 540000 ms slices in a loop; a killed or empty wait means loop again. Process every message in a delivery, then acknowledge it.
- Correlate every message by `taskId` + `dispatchId` against active dispatches; inspect the dispatch (`dispatch-show`) when state is uncertain. The collection, correlation, and overdue rules apply to every bounded-wait loop: critics, builders, reviewers, QA. Mark a collected task completed in the manifest only after confirming its report is non-empty.
- A valid `worker_done` completes its task and dispatch in Orca automatically; never follow it with a manual completion. Manual `task-update` is recovery only: `ready` for fix cycles, `failed` for failures. Orca task status is the worker's signal; the manifest is the run's truth for verified and merged.
- Release a dispatch once you accept its `worker_done` and will not reuse its terminal; a fix cycle reuses the terminal, so release only at task completion or permanent failure.
- **Read-only collection check** (planners, critics, reviewers; `<H>` = the recorded HEAD): `git -C <WT-PATH> status --porcelain -- ':!.agents/orca/orchestration'` must be empty and HEAD must equal `<H>`. Any failure: `git -C <WT-PATH> reset --mixed <H> && git -C <WT-PATH> restore --worktree -- . ':!.agents/orca/orchestration' && git -C <WT-PATH> clean -fd -- ':!.agents/orca/orchestration'`, re-run the check (it must pass before any artifact commit), and record the incident.
- Never dispatch into a terminal that has not reached readiness (tui-idle); a terminal mid-startup drops injected input. This applies to every boot, including retried lenses and respawned workers. After every dispatch, read the terminal and confirm the worker has received the instruction; a terminal still starting up, or idle with no trace of the dispatch, means wait for readiness again and inject the same dispatch once more. An Orca CLI call that fails or a readiness wait that times out: read the terminal and retry once. A second failure of any of these three (a dispatch still unconfirmed after reinjection, a failed Orca CLI call, or a timed-out readiness wait) follows the current phase's failure path; builders enter fix/retry handling.
- Prefer structured `worker_done` payloads and report files over parsing terminal output; the bounded `terminal read` buffer is for status, not results.
- `worktree create` controls the worktree name only (capture the Orca-derived branch) and may auto-spawn a first terminal: close it after confirming it is an unused shell; a configured default tab stays recorded in the manifest and closes at teardown.
- Close terminals when their phase no longer reuses them: builders at task completion or permanent failure (the fix cycle re-dispatches into the same terminal), QA after collection, planners after plan selection, critics and reviewers after their round loop. Remove task worktrees once merged. The concurrency cap applies to builders; planner, critic, reviewer, and QA terminals are additional and phase-bound.

## Safety constraints

- Code reaches main only through a human-approved PR; approving and merging it is always the human's.
- Only the run branch reaches the remote, and only at Phase 9.
- Workers write code only in their assigned worktree; `<RUNDIR>` writes are limited to each worker's designated files.
- Planners, reviewers, and the plan critics are read-only by instruction, enforced at collection: clean tree outside the run folder and unchanged HEAD in `<WT>` after each reports, or you reset the tree and record the incident. On a `high`/`xhigh` run, the final adversarial QA worker writes only in its disposable worktree, `qa-findings.md`, and `<RUNDIR>/screenshots/`; its branch never merges.
- Never act on unfiltered runtime-global state: the manifest defines what this run owns.
