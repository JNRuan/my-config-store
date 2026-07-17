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

- **You never write implementation code**: the only exceptions are trivial fixes (typos, docstrings/comments, unused imports, formatting — manual or via Format write, committed as its own commit) and trivial textual merge conflicts. Everything else goes to a worker.
- **Workers never create Orca tasks, dispatches, or terminals**: All Orca coordination is yours. Workers may fan out their own runtime's native subagents internally (the review and QA skills do); they own and clean up that fan-out themselves.
- **Four human touchpoints**: the invocation, the understanding check, the plan gate, the PR. After the plan gate, run autonomously to the PR — never stop to ask; every judgment call is yours, logged in `summary.md`. Anything that genuinely needs the human (scope, security, destructive operations, architectural forks) must be settled by the plan gate; a mid-run blocker you cannot resolve ends the run through the abort routine, not a question.
- **Report what actually happened**: never what was supposed to happen; agents and the human debug from your records.
- **Maintain `<RUNDIR>/run-state.json`**: This is the run manifest — after every state transition: run name, source, base branch + pinned base SHA, plan-review tier and snapshotted cap, current run complexity and downstream review/QA policy, integration worktree (id, path, branch), per-task records (seq, slug, task id, worktree id/path, branch, starting commit, terminal handle, active dispatch id, superseded dispatch ids, cycle count, assignment/report paths, status), critic/review/QA dispatch records (including skipped QA), cleanup state. Nothing in it can be recomputed later; it is also what makes a crashed run resumable.
- **Orca state is runtime-global**: Other runs and repos share the task store and terminal list. Act only on ids, handles, and paths recorded in your manifest; never dispatch, complete, close, or remove anything it doesn't own.

Model and effort routing for every role, plus worker boot recipes: `references/routing.md`.

## Intake

`/orca-implement {TASK-REF | prompt}`

Normalize the argument into requirements:

- **GitHub issue** (`#123` or issue URL): `gh issue view <n> --json title,body,comments`
- **Linear issue** (`ABC-123` or Linear URL): `orca linear issue <ref> --full --json`
- **File path** (markdown docs, specs): read it directly.
- **Anything else**: an ad-hoc prompt; you draft the requirements and acceptance criteria yourself during planning, and the human vets them at the understanding check and the plan gate.

Any intake read that fails or returns empty (missing Linear connection, unresolvable issue, unreadable file) is an intake failure: stop before allocating anything.

The requirements are quoted into the plan, which is the run's spec of record. The run works from what intake read; a ticket changing mid-run does not change the plan.

## Phase 0: Setup

**Preflight** — all of it before anything is allocated; any failure stops the run with a clear message:

1. Orca ready: `orca status --json` satisfies `jq -e '.ok == true and .result.runtime.reachable == true and .result.runtime.state == "ready"'`.
2. You are inside an Orca-managed terminal: `[ -n "$ORCA_TERMINAL_HANDLE" ]`. If not, tell the human to relaunch inside Orca; dispatch and completion routing need your terminal identity.
3. Repo registered: `orca repo list --json` contains this repo. Base ref clean.

**Pin the base**: `BASE_SHA=$(git rev-parse <base-ref>)`. Every diff, review, and changed-file computation from here on uses `BASE_SHA`, never the symbolic ref. The ref is used once more as the PR's target branch.

**Name the run**: `<RUN>` = `{yyyymmdd-hhmm}-{ref?}-{run-slug}` — UTC datestamp first so run folders sort chronologically (`date -u +%Y%m%d-%H%M`), normalized ref (`gh-123` / `lin-abc-123`, omitted for ad-hoc), run slug in lowercase alphanumerics and hyphens. The datestamp also makes re-runs of the same ref unique.

**Create the integration worktree.** The CLI controls worktree names, not branch names — Orca derives the branch, so capture it and use only captured names from here on:

```bash
orca worktree create --repo <selector> --name "<RUN>" --base-branch <base-ref> --json
# add --issue <n> or --linear-issue <ref> when the source is an issue
# a duplicate-name failure means another run holds the name: adjust the slug and retry
# capture <WT> (worktree id) and <WT-PATH> (absolute path) from the JSON
git -C <WT-PATH> branch --show-current    # → <RUN-BRANCH>; record it
git -C <WT-PATH> rev-parse HEAD           # must equal BASE_SHA; reset to BASE_SHA if not
```

**Allocate the run folder inside the worktree**:

```bash
RUNDIR="<WT-PATH>/.agents/orca/orchestration/<RUN>"
mkdir -p "$RUNDIR/tasks" "$RUNDIR/review" "$RUNDIR/screenshots"
```

The run folder lives on the run branch like any other work: commit it as artifacts land (each phase boundary at minimum) — but never between recording `<WT>` HEAD for a collection check and running that check, and never while a fix worker is writing in `<WT>`.

Initialize `run-state.json` immediately — before creating or closing anything further: run name, source, start datetime (UTC), base ref, `BASE_SHA`, `plan_review_tier: pending`, `plan_review_cap: pending`, `run_complexity: pending`, downstream review/QA policy pending, `review_fixes_applied: false`, integration worktree (id, path, branch), and the first terminal `worktree create` auto-spawned (find it in the JSON, or `orca terminal list --worktree id:<WT> --json`). Then close that terminal. Every terminal in this run must be a captured, manifest-recorded handle.

`<WT>` is your integration point: task branches merge into `<RUN-BRANCH>` here; whole-run verification, review, and fix workers run here. Each build task gets its own worktree at dispatch (Phase 5).

## Phase 1: Scout

Scout with your own runtime's native subagents (read-only explorers), not Orca terminals. Dispatch in parallel, tiered by job (models: `references/routing.md`):

- **Discovery scouts**: project mechanics and inventory. Tooling commands — Install, Build, Test, Lint, Typecheck, and Format in both check and write forms — `.env` presence, the repo's commit-message convention, where the relevant code lives.
- **Comprehension scouts**: blast radius and current behavior of the code being changed, and dependencies on existing code.
- **Test coverage scouts**: existing test coverage that will need adjustments, important gaps in test coverage to address in relation to the implementation goals.

Require `path:line` evidence for claims. Mark every assumption scouting could not confirm; unresolved assumptions go into the plan for the critics and the human.

## Phase 2: Understanding check

Present to the human your understanding of the task: requirements and intended scope as you read them, what is explicitly out, and the scouting findings that shape the approach. Then ask your questions **one at a time** — ambiguities, missing acceptance criteria, conflicts between the source and the code — waiting for each answer before asking the next; a barrage of questions gets shallow answers. When nothing remains open, ask for the go-ahead. Answers are settled facts in the plan; a question you could ask here never becomes an open assumption.

## Phase 3: Plan

**Step 1 - Write**: `<RUNDIR>/plan.md` following `references/plan-template.md` exactly. Key obligations:

- Frontmatter carries the pinned `base_sha`, captured `<RUN-BRANCH>`, a `plan_review_tier`, and `run_complexity: pending` until critique ends.
- The Review Policy snapshots the plan-review cap from `plan_review_tier`. Final code-review depth and QA remain pending until the reviewed plan determines `run_complexity`; both tiers are independent of per-task builder complexity.
- Requirements and acceptance criteria with `AC-n` IDs; every criterion covered by at least one task.
- Task table with explicit deps, complexity, and builder routing. Prefer the smallest viable task set.
- Contracts: pin every interface shared across tasks before dispatch.
- Assumptions split validated (with evidence) vs open (assigned to the task that must verify them).
- Project tooling verbatim, including Build and separate Format check / Format write.
- Verification requirements target behaviour on critical paths; the goal is important behaviours and edge cases covered, not line-by-line coverage.

**Step 2 - Fact check**: dispatch one read-only native subagent (model: `references/routing.md`) to verify every checkable claim in the plan against the repo — file paths, `path:line` evidence, command names, symbols and interfaces cited in contracts. It does not assess reasoning, decomposition, scope, or the run-complexity judgment; it reports mismatches only. Fix every mismatch in the plan before booting the critics.

**Step 3 - Cross-model critique loop**: set `<PLAN_ROUND_CAP>` from the plan's Review Policy and snapshot it with `plan_review_tier` in `run-state.json`. The cap is fixed for this critique loop, even if the plan's risk changes. Boot two critic terminals, Claude `fable` and Codex `gpt-5.6-sol` (recipes: `references/routing.md`), then run rounds 1 through `<PLAN_ROUND_CAP>`:

1. Set `PLAN_CHANGED=false` before dispatch. Record `git -C <WT-PATH> rev-parse HEAD`. Per critic (`<M>` = `claude` | `codex`), create a fresh task and report for this round:

   ```bash
   orca terminal wait --terminal <H_CRITIC_M> --for tui-idle --timeout-ms 120000 --json
   orca orchestration task-create --task-title "plan-critique-<M>-r<ROUND>" \
     --spec "Read <RUNDIR>/plan.md. You are a critic, not an approver: find the strongest reasons this plan fails. Judge decomposition seams, coverage of every requirement, correctness against the requirements, verification adequacy, and sizing in both directions (would fewer tasks beat coordination cost; is any single task too complex to land reliably). Out of scope: implementation detail, style, scope expansion. Each finding: plan section, concrete failure scenario, severity BLOCKING|RISKY|NOTE. End with a verdict: proceed|revise|re-plan. Write your full critique to <RUNDIR>/plan-critique-<M>-r<ROUND>.md. That file is the only file you may write. Then report completion." --json
   orca orchestration dispatch --task <T_CRITIC_M> --to <H_CRITIC_M> --inject --json
   ```
2. Collect both critiques with the bounded-wait loop and correlation rules below. Mark a task `completed` only after confirming its report is non-empty. Mark a failed, overdue, or reportless critic task `failed`, close its terminal, and continue with the surviving lens; note the failure at the plan gate and boot a fresh terminal for that lens before a later round. Both critics failing in one round invokes the abort routine.
3. Evaluate every finding on its merits. Severity labels are evidence, not verdicts. Revise the plan for accepted findings and log discarded findings with reasoning. Leave `PLAN_CHANGED=false` when no plan edit was made. Set it to `true` only after changing the plan; critic verdicts, accepted-but-already-satisfied findings, critique artifacts, timestamps, and discarded findings do not count.
4. Run the read-only collection check, then commit the plan and critique artifacts.
5. If `PLAN_CHANGED=false`, stop immediately. If it is true and the cap is not exhausted, run the next round against the revised plan. At the cap, apply accepted changes without another critique.

Close both critic terminals when the loop stops. Assess canonical `run_complexity` from the reviewed plan; it may be higher or lower than `plan_review_tier`. Fill the downstream Review Policy from `references/routing.md`, then update plan frontmatter and `run-state.json`. Preserve `plan_review_tier`, `<PLAN_ROUND_CAP>`, rounds run, and the stop reason as historical inputs. Commit these updates before Phase 4.

## Phase 4: Plan gate

The human gate is an unlimited approval loop and is not subject to either review cap. Plan critique and fact checking are finished before this phase and never reopen here.

Present the plan, `plan_review_tier`, current `run_complexity` and its review/QA policy, critic outcomes, rounds run, and open assumptions. If this gate is being conducted through Crit, run its documented loop: address every unresolved comment, re-present the live plan, and run the printed next-round command. Crit defines approval when the human finishes a subsequent round with zero comments; a Crit command exiting with feedback is not approval. Otherwise conduct the gate in-session, incorporate requested changes, and re-present until the human explicitly approves by message. Silence, no requested changes, and critic verdicts are never approval.

If feedback suggests changing `run_complexity` in either direction, present the current tier, proposed tier, rationale, and resulting code-review cap/QA policy, then ask for a direct answer on that tier change. General plan approval or a zero-comment Crit round does not approve a complexity change. Update the plan and manifest only after explicit tier approval. Continue at this gate until final plan approval; then commit the approved plan and manifest before Phase 5. An explicit rejection or cancellation invokes the abort routine. After approval, judgment calls are yours, logged in `summary.md`; the human is next involved at the PR.

## Phase 5: Build (parallel where deps allow)

Register the DAG with **thin pointer specs** — the resolved context does not exist yet, and Orca task specs cannot be updated after creation:

```bash
orca orchestration task-create --task-title "{seq}-{slug}" \
  --spec "Run <RUN> assignment {seq}-{slug}. Read your full assignment first: <RUNDIR>/tasks/{seq}-{slug}-assignment.md (absolute path)." \
  --deps '["<dep task id>", ...]' --json
# record every returned task id in run-state.json — the run's owned set
```

**Dispatch loop**: launch every ready task *from the owned set* (never from raw `task-list --ready` — it is runtime-global), up to the concurrency cap (5, `references/routing.md`). Per task:

1. **Create the task worktree**: `orca worktree create --repo <selector> --name "<RUN>-{seq}-{task-slug}" --base-branch <RUN-BRANCH> --parent-worktree id:<WT> --json`. Capture id, path, and actual branch (`git -C <path> branch --show-current`); close the auto-created first terminal; record the starting commit (`git -C <path> rev-parse HEAD`).
2. **Write the assignment file** `<RUNDIR>/tasks/{seq}-{slug}-assignment.md` from `references/assignment-context.md`, now that its contents exist: the worktree path and branch just captured, inputs and sync artifacts from completed dependencies, contracts, tooling verbatim, report path. External content (issue bodies, plan text) goes in this file, never inline into a shell argument.
3. **Boot the routed builder** there (recipes: `references/routing.md`; Codex builders carry `--add-dir "<RUNDIR>"` so they can write their report), `terminal wait --for tui-idle --timeout-ms 120000`, then `orca orchestration dispatch --task <id> --to <handle> --inject --json`. Record the dispatch id; update the manifest.

**Collect loop**: run `orca orchestration check --wait --types worker_done,escalation --timeout-ms 540000 --json` in a loop — never a longer timeout; your shell tool kills long foreground calls, and a killed or empty wait means loop again, not failure. For each message:

- Correlate `payload.taskId` + `payload.dispatchId` against the manifest's **active** dispatches. Messages for other runs' tasks or superseded dispatches: log and ignore. `escalation`: handle it yourself — answer over Orca agent messaging (reply to the escalation), never via files, or adjust the assignment; one you cannot resolve is abort-routine territory, not a human question. It is never a completion.
- On a correlated `worker_done`: run the per-task verify+merge below, then dispatch owned ready tasks up to the cap, then loop.
- Loop until every owned dispatch is terminal. If a worker is overdue (two consecutive empty waits with no new commits on its branch), `orca terminal read` it (stuck, prompting, crashed): stop it, close its terminal, inspect its committed work, boot a fresh terminal on the same branch and worktree, set the task `--status ready`, and re-dispatch with that work as context — record the old dispatch id as superseded; counts toward the cycle limit.

**Per completed task — verify, then merge immediately** (never batch merges):

1. Commits exist past the recorded starting commit (`git log <starting-commit>..<task-branch> --oneline`); worktree clean (`git -C <task-worktree> status --porcelain`). No commits + clean tree is valid only for explicitly no-change outcomes. Uncommitted changes: do not merge; run a fix cycle.
2. Read the report (`<RUNDIR>/tasks/{seq}-{slug}-report.md`) and check its claims: run the checks it says passed — Build first, then Lint, Typecheck, Tests, Format check. Never take the report at face value.
3. Requirements met against the plan. If not: **fix cycle** — append your findings to the assignment file, `orca orchestration task-update --id <task> --status ready --json`, re-dispatch to the same terminal (`dispatch --task <task> --to <handle> --inject`), record the fresh dispatch id and supersede the old one, increment the cycle counter. **Max 3 verify→fix cycles per task**, then the retry protocol.
4. **Merge the task branch into `<RUN-BRANCH>`** in `<WT>`. Trivial textual conflicts (imports, adjacent independent hunks) resolve yourself under the trivial-fix exception; semantic conflicts: abort the merge and register + dispatch a conflict-resolution fix task in `<WT>` (fix-task discipline below), so the resolving commit is attributable. Run integration checks in `<WT>` guided by the scouted blast radius. **Max 3 resolve→verify cycles**, then the retry protocol.
5. `orca orchestration task-update --id <task> --status completed --json` (auto-promotes dependents), close the builder terminal, remove the task worktree (`orca worktree rm --worktree id:<worktree-id> --json`; check `.ok`), delete the merged task branch (`git -C <WT-PATH> branch -d <task-branch>` — `-d`, so git refuses if it is somehow unmerged; already gone after `worktree rm` is fine), update the manifest, dispatch owned ready tasks up to the cap.

**Contract watch**: when two parallel tasks keep reshaping a shared interface to fit their own side, neither is stuck but the work is cycling. Freeze the contract yourself (the plan pinned it) and dispatch explicit conform-to-contract fixes.

**Fix tasks in `<WT>`** (Phase 6 failures, Phase 7 review fixes, Phase 8 QA fixes, conflict resolution): classify the fix itself with the task-complexity rubric and use the matching builder row and fallback from `references/routing.md`. Use the same register + dispatch flow, but no separate worktree and only one fix worker at a time — pause merges and your own `<WT>` commits while it runs. Record `<WT>` HEAD as the starting commit before dispatch. Verify commits and checks as above; the merge, worktree-removal, and branch-deletion steps do not apply. On completion, mark the task completed and close the terminal.

## Phase 6: Whole-run verification

After the last merge, in `<WT>`:

- Full test suite plus Build, Lint, Typecheck, Format check.
- **Browser verification** when the changeset touches UI (components, pages, layouts, styles, templates): spawn one coordinator-native subagent (not an Orca terminal) with `agent-browser` in headless mode (never `--headed`); model per `references/routing.md`. Brief it with: the dev server URL or start command (run from `<WT-PATH>` on a free port), every affected page, the changed feature to interact with, what correct behavior looks like. Screenshots to `<RUNDIR>/screenshots/` as `{description}_{sequence}.png`, required for PASS and FAIL alike; if interaction mutates real data, undo it. Dev server won't start: recover (different port, `.env` present, re-install), cap 3 attempts, then record "not verified — dev server unavailable" with the errors. The subagent stops any dev server it started before reporting. Read the screenshots yourself; a report without screenshots is not verified. Skip only for purely non-visual changes; if in doubt, dispatch.
- Acceptance criteria, criterion by criterion, evidence recorded for `summary.md`.
- **Review-policy confirmation**: compare the actual diff and observed failure modes with approved `run_complexity`. If implementation revealed greater aggregate risk, raise the tier, recompute the code-review cap and QA decision, update plan frontmatter, Review Policy, and `run-state.json`, and record the rationale in `summary.md`. Verify the three policy records agree before Phase 7.

Any failure here becomes a fix task in `<WT>` (fix-task discipline, Phase 5): write an assignment with the failing check and output, register + dispatch, routed by complexity, re-verify. **Max 3 cycles**, then the retry protocol. Phase 7 starts only once whole-run verification passes, or with every remaining gap explicitly recorded as not verified (with reasons) — never with silent failures.

## Phase 7: Code Review

Set `<CODE_REVIEW_CAP>` from the plan's Review Policy and set both `REVIEW_FIXES_APPLIED=false` and manifest `review_fixes_applied=false`. Boot Claude and Codex reviewer terminals in `<WT>` (recipes: `references/routing.md`), then run rounds 1 through `<CODE_REVIEW_CAP>`, inclusive:

1. Set `CODE_CHANGED=false` before dispatch and record `<WT>` HEAD. Create fresh reviewer tasks and reports for `<ROUND>`. For rounds after the first, include the preceding fix-wave commit range and synthesis path as context. Dispatch each reviewer with:

   ```
   Run /code-review-local (it exists; do not check) and follow the prompt. Review
   the current branch against base commit <BASE_SHA>. Write your FULL report to
   <RUNDIR>/review/<claude|codex>-review-r<ROUND>.md — that file is the only file
   you may write; do not edit code. Then report completion.
   ```
2. Collect both reviewers via the bounded-wait loop with dispatch-id correlation. Mark a task `completed` only after confirming its report is non-empty. Mark a failed or reportless reviewer task `failed`, close its terminal, continue with the survivor, and mark the synthesis **single-lens**; boot a fresh terminal for that lens before a later round. Both lenses failing invokes the abort routine. Run the read-only collection check against the recorded HEAD, then commit the reports and manifest.
3. Synthesize to `<RUNDIR>/review/synthesis-r<ROUND>.md`. Sources are `claude` and `codex`; `both` marks agreement. Apply these mechanics only:
  - Drop findings whose cited file exists neither at HEAD nor at `BASE_SHA`; deleted files are valid citations. Keep a finding in untouched code only when it traces a causal path to a changed file. Record drops in an appendix.
  - Dedupe by finding identity, not wording.
  - Preserve attribution and every source's severity.
  - Record base SHA, branch, round, lenses run, and counts (raw → after existence → after dedupe). Do not add findings, re-score, or judge validity during synthesis.
4. Triage every finding on its merits into accepted fix or logged finding; nothing is silently dropped. Attribution and severity are evidence, not verdicts. Merely accepting a finding does not set `CODE_CHANGED=true`. Commit the synthesis, triage record, and manifest before starting a fix worker.
5. If there are no accepted fixes, explicitly leave `CODE_CHANGED=false`, record `no accepted fixes`, and stop.
6. Turn all accepted fixes into one fresh fix task in `<WT>` using the Phase 5 fix-task discipline. Verify the task and re-run each finding's own reproduction or check. **Max 3 fix cycles per wave**, then the abort routine with all syntheses attached.
7. Set `CODE_CHANGED=true` only after substantive code or test fixes are committed and verified in `<WT>`, then set `REVIEW_FIXES_APPLIED=true` and manifest `review_fixes_applied=true`. If the fix wave makes no substantive implementation change, leave `CODE_CHANGED=false`; report/artifact edits and accepted-but-already-satisfied findings do not count. Stop when `CODE_CHANGED=false`.
8. If `<ROUND>` equals `<CODE_REVIEW_CAP>`, stop after the verified fix wave. Record that the cap was reached and the final fixes were not re-reviewed. Otherwise continue to the next round.

Close all reviewer terminals when the loop stops. If `REVIEW_FIXES_APPLIED=true`, rerun Phase 6's full project and applicable browser checks against the post-review HEAD; verification fixes follow Phase 6's fix discipline, are recorded as post-review and unreviewed, and do not reopen code review. Otherwise retain the existing Phase 6 evidence. Once verification is current or every remaining gap is explicitly recorded, set `code_review_complete=true` in `run-state.json`, record the stop reason and persisted `review_fixes_applied`, and commit the final review and verification artifacts.

## Phase 8: Final adversarial QA

Adversarial QA begins only after code review and post-review verification complete. Require `git -C <WT-PATH> status --porcelain` to be empty; QA starts from that exact committed, verified HEAD.

- `low` or `medium`: do not create a QA task, terminal, worktree, dispatch, or findings file. Record `adversarial_qa: skipped` with reason `run complexity policy` in `run-state.json` and `summary.md`, commit the skip record, then continue to Phase 9.
- `high` or `xhigh`: record `QA_HEAD=$(git -C <WT-PATH> rev-parse HEAD)`, then create a disposable worktree from the current `<RUN-BRANCH>` (`orca worktree create --repo <selector> --name "<RUN>-qa" --base-branch <RUN-BRANCH> --parent-worktree id:<WT> --json`). Capture its id, path, and actual QA branch; close the auto terminal; verify its HEAD equals `QA_HEAD`. Boot a Codex `gpt-5.6-sol` `high` worker there (workspace-write recipe with `--add-dir "<RUNDIR>"`) and dispatch:
  ```
  Run /adversarial-review (it exists; do not check) against the current branch
  vs base commit <BASE_SHA>: code-level and browser-based attempts to break the
  implementation. Browser work runs headless. This worktree starts at the latest
  post-review HEAD <QA_HEAD>. Write findings, each with a reproduction (test
  scenario or screenshot), to <RUNDIR>/review/qa-findings.md. That report and
  screenshots under <RUNDIR>/screenshots/ are the only paths you may write
  outside your worktree. Clean up throwaway test files; for tests that produced a FAIL,
  capture the exact scenario in the finding before cleanup. Then report
  completion.
  ```

Collect the QA task with dispatch-id correlation. On success, mark it `completed` and require a non-empty `qa-findings.md`. On failure or a missing report, mark it `failed`, record QA as not verified, clean up its terminal, worktree, and branch, commit the incident, and continue to Phase 9 without triage. No QA branch merges.

After a successful report, close the QA terminal, remove its worktree by recorded id, and delete its branch. Triage concrete findings on their merits. Logged findings go to the PR with attribution and reasoning. Commit the report, triage record, and manifest before starting any fix worker. If there are accepted fixes, create one fresh fix task in `<WT>` against the current integration HEAD, never in the disposable QA worktree. Apply and verify the fixes, re-run every finding's exact reproduction, then rerun Phase 6's full project and applicable browser checks. **Max 3 QA fix cycles**, then the abort routine with `qa-findings.md` attached. QA runs once and code review does not reopen; final QA fixes are verified but not code-reviewed. Commit final QA/fix evidence and manifest updates before Phase 9.

## Phase 9: PR

1. Finalize `<RUNDIR>/summary.md`: start/end datetimes, what shipped, plan-review tier and cap used, final run complexity and downstream review policy, plan/code-review rounds run with stop reasons, QA run/skip result, decisions and judgment calls with reasoning (accumulated throughout the run), acceptance criteria with evidence, incidents (reset reviewer trees, superseded dispatches), open questions.
2. Ensure everything is committed: `git -C <WT-PATH> status --porcelain` must be empty after committing whatever is outstanding (`summary.md`, final `run-state.json`).
3. Push the run branch — the only branch that ever reaches the remote, and only now.
4. Open the PR (the `pr-create` flow) against the base *branch*: summary from `plan.md` and `summary.md`; acceptance criteria with evidence; source issue link when there is one; review appendix with rounds run, fixed findings and re-verification evidence, and logged findings with attribution; QA result only when run, otherwise its policy skip; screenshot references for UI changes; sign-off line:

```markdown
---
:space_invader: Built with Orca
Build: {display names of every model that produced or fixed shipped code, deduped; no effort levels}
Code review: {display names of the reviewer models behind completed lenses, with rounds run; no effort levels}
```

5. Teardown, verified **against the manifest**: close every terminal handle recorded in `run-state.json`, remove any remaining task/QA worktrees by recorded id, confirm each is gone. Never sweep unfiltered `terminal list` / `worktree list` output — the runtime is shared. Only the integration worktree survives, kept until the PR merges (`orca worktree rm` is the human's post-merge step, not yours).
6. Update `run-state.json` (status: shipped, PR URL), commit and push it, then report to the human: PR URL, what shipped, what was fixed vs logged from review, anything unverified.

## Failure handling

- **Retry protocol** (a task exhausts its 3 cycles): reflect — approach or execution? Adjust the assignment or plan, and append a retry briefing to the assignment file: what each cycle attempted, what failed and how (failing checks with output, from the cycle reports), and your diagnosis of why. Then respawn a fresh worker on the same branch and worktree (supersede the old dispatch). If the replacement also exhausts 3 cycles, the task is **permanently failed**: `task-update --id <task> --status failed`, mark owned dependent tasks `failed` (dependency failed), close its terminal, remove its worktree — branch preserved for manual review (verify the branch survives `worktree rm` on first use; if it does not, tag the tip `git tag orca-run/<RUN>/{task-slug} <sha>` before removal, never pushed) — and record attempts and branch name in `summary.md`. Let independent in-flight tasks finish (collect, verify, merge); dispatch nothing new; then run the abort routine.
- **Abort routine** (one idempotent path, used for permanent task failure, plan rejection, both-reviewers failure, and unresolvable critical escalations): mark this run's remaining non-terminal tasks `failed`; close all manifest-owned terminals; remove disposable/task worktrees by recorded id (failure branches preserved; delete the QA branch if one was created); write `summary.md` with `status: failed|blocked`, what was attempted, and what remains; update `run-state.json`; report to the human. The integration worktree and run branch survive for inspection.
- **Infeasibility**: consecutive tasks hitting structurally similar walls, or verification failing on the same criterion regardless of implementation, means the plan or requirements are wrong, not the workers. Stop respawning and run the abort routine, recording what you observed, which assumptions look load-bearing and wrong, and your best read of what is feasible.
- **Coordinator failure** (context limit, unexpected error): attempt recovery; otherwise execute as much of the abort routine's recording as possible. `run-state.json`, the DAG, the run branch, and `<RUNDIR>` survive; a fresh session reconstructs state from the manifest plus live Orca state.
- Orca's dispatch circuit breaker (3 consecutive dispatch failures → task `failed`) is retry-protocol entry, not something to reset and hammer. Never run `orca orchestration reset` — the store is shared with other runs.

## Orca mechanics

- Capture handles, ids, paths, branch names, and dispatch ids at creation into `run-state.json`; none can be recomputed. If Orca restarts mid-run, handles go stale: re-acquire with `terminal list` and reconcile against the manifest before continuing.
- `check --wait` returns one message at a time; run it in ≤ 540000 ms slices in a loop; heartbeats arrive on stderr; a killed or empty wait means loop again.
- Correlate every message by `taskId` + `dispatchId` against active dispatches; use `orca orchestration dispatch-show --task <id> --json` when state is uncertain. The collection, correlation, and overdue rules apply to every bounded-wait loop: critics, builders, reviewers, QA.
- **Read-only collection check** (critics, reviewers; `<H>` = the HEAD recorded before boot): `git -C <WT-PATH> status --porcelain -- ':!.agents/orca/orchestration'` must be empty (porcelain shows staged and unstaged damage alike) and HEAD must equal `<H>`. Any failure: `git -C <WT-PATH> reset --mixed <H> && git -C <WT-PATH> restore --worktree -- . ':!.agents/orca/orchestration' && git -C <WT-PATH> clean -fd -- ':!.agents/orca/orchestration'` (drops rogue commits and staged changes, spares the run folder), re-run the check — it must pass before any artifact commit — and record the incident.
- An Orca CLI call that fails or a `terminal wait` that times out: read the terminal and retry once. A second failure follows the current phase's failure path; builders enter fix/retry handling. Never dispatch into a terminal that has not reached tui-idle.
- Prefer structured `worker_done` payloads and report files over parsing terminal output; the 120-line `terminal read` buffer is for status, not results.
- `worktree create` controls the worktree name only (capture the Orca-derived branch) and auto-spawns a first terminal (close it). `worktree rm` requires `--worktree <selector>`.
- Close terminals when their phase no longer reuses them: builders and QA after collection, critics and reviewers after their round loop. Remove task worktrees once merged. The concurrency cap applies to builders; critic, reviewer, and QA terminals are additional and phase-bound.

## Safety constraints

- Code reaches main exclusively through a human-approved PR; approving and merging it is always the human's.
- Only the run branch reaches the remote, and only at Phase 9.
- Workers write code only in their assigned worktree; `<RUNDIR>` writes are limited to each worker's designated files.
- Reviewers and the plan critics are read-only by instruction, enforced at collection: clean tree outside the run folder and unchanged HEAD in `<WT>` after each reports, or the tree is reset and the incident recorded. When enabled for a `high`/`xhigh` run, the final adversarial QA worker writes only in its disposable worktree and `qa-findings.md`; its branch never merges.
- Never act on unfiltered runtime-global state: the manifest defines what this run owns.
