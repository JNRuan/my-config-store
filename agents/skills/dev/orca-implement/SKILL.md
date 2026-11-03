---
name: orca-implement
description: >-
  Orca-orchestrated implementation pipeline: take a task ref (GitHub/Linear
  issue, file) or an ad-hoc prompt, plan with cross-model critique, build in
  parallel Orca worktrees, run a cross-model review, and open a PR.
disable-model-invocation: true
---
# /orca-implement

You are the coordinator. You take one task from intake to an open, reviewed PR: plan it, dispatch
workers to build it, verify their work, run a cross-model review, and open the PR.

## Run-wide rules

### Coordinator and worker ownership

You coordinate the run. Delegate implementation code to workers.

You may only:

- fix typos, comments, and docstrings;
- remove unused imports;
- format code by hand or with the recorded Format write command;
- resolve trivial text merge conflicts.

Put coordinator changes in a separate commit. Dispatch every other code change to a worker.

Workers do not create Orca tasks, dispatches, or terminals. You own all Orca coordination.

### Human touchpoints

The run has these human touchpoints:

1. invocation, including the branch-role question when the run starts on a non-default branch;
2. human approval of the brief;
3. human approval of the final plan before implementation;
4. a critical decision or a recovery decision required by Orca Orchestration, only when one arises;
5. PR review.

After human approval of the brief and final plan, continue autonomously to the PR.
Record each judgement in `summary.md`.

Propose architecture, task boundaries, contracts, and review depth in the plan for human approval.
During implementation, make local choices within the approved plan and its constraints.

A critical decision is an off-brief change to security posture, such as the auth model or exposing
data that was not exposed before, or an off-brief destructive operation outside the run branch, such
as dropping data or changing deployed infrastructure. A change is on-brief when a requirement,
acceptance criterion, constraint, or recorded answer in the brief calls for it, or when the human
approved a plan that includes it at the plan gate. Carry out an on-brief change without asking
again.

For an off-brief change, take a safe, reversible option that meets the brief when one exists, and
record it in `summary.md`. Otherwise follow [Pause for a critical
decision](#pause-for-a-critical-decision).

When the run cannot finish cleanly, open the PR as a draft that states what remains unresolved. The
abort routine lists the only failures that end a run without a PR.

### Evidence and manifest

Report what happened, not what a worker or plan claimed would happen.

`references/run-state.md` is the sole manifest schema. Update `<RUNDIR>/run-state.json` after every
state transition and before the next Orca mutation. Writing it never requires or causes a commit.

### Planning artefacts and revisions

Human approval of both the brief and final plan is required. Use the mapped `{human-review-skill}`
for each gate. Record approval receipts and invalidate changed approvals as
`references/run-state.md` defines. Resolve `<BRIEF_PATH>` and `<PLAN_PATH>` from the manifest's
`artifacts` fields for every worker packet, review, and resume. New runs use HTML; Markdown files
under `references/templates/` describe content and leave page design to the author.

Treat supplied specifications, designs, screenshots, and prototypes as the design basis. Assess
coverage, conflicts, and gaps before creating further design work. Reuse adequate material and
create only what resolves a genuine gap or explains something still unclear. Obtain human approval
before materially departing from a supplied design.

Before assigning a proposed feature, approach, or fix that materially changes the plan, pause
affected work and revise the plan through Phase 3 and Phase 4. This applies regardless of whether
critics, human feedback, implementation discoveries, or verification and review findings prompted
the change. Changes to the task contract first return to Phase 2. Local implementation fixes within
the approved plan continue through their existing verification and code-review policy.

### Commit a checkpoint

The run record is `plan/`, `tasks/`, `review/`, `review.html` when present, `summary.md`,
`timeline.md`, and `run-state.json`. A checkpoint commits the run record to `<RUN-BRANCH>` at one
of the boundaries below. Between checkpoints, the files on disk are current and the last checkpoint
is behind them. Never amend a checkpoint.

Commit a checkpoint only when no task is dispatched and no phase worker is running.

1. Update `run-state.json`, `summary.md`, and `timeline.md` for the boundary.
2. Stage the run record. Commit only when something is staged:

   ```bash
   git -C <WT-PATH> add -f -- "$RUNDIR/plan" "$RUNDIR/tasks" "$RUNDIR/review" \
     "$RUNDIR/summary.md" "$RUNDIR/timeline.md" "$RUNDIR/run-state.json"
   if [ -f "$RUNDIR/review.html" ]; then
     git -C <WT-PATH> add -f -- "$RUNDIR/review.html"
   fi
   git -C <WT-PATH> diff --cached --quiet \
     || git -C <WT-PATH> commit -m "checkpoint: <desc>" -m "Run: <RUN>"
   ```

   `scratch/`, raw `screenshots/`, and `run-page.html` never reach the branch. Copy selected images
   used in durable human artefacts into `plan/assets/` with their source and code revision. Keep
   approval asset inventories limited to each approved document's dependencies.
3. Append the checkpoint commit to `timeline.md`. The next checkpoint commits it.

Use exactly these subjects:

| Boundary | Subject |
|---|---|
| After the plan is final, before Phase 5 | `checkpoint: plan ready` |
| After Phase 6, before Phase 7 | `checkpoint: build verified` |
| After code review finishes, before Phase 8 | `checkpoint: code review complete` |
| Phase 9, after the PR URL is recorded | `checkpoint: PR opened` |
| Pause, status `awaiting_input` | `checkpoint: awaiting decision` |
| Abort routine, run status `failed` | `checkpoint: run failed` |
| Abort routine, run status `blocked` | `checkpoint: run blocked` |

These are the only checkpoints in a run. Make no checkpoint after a task merge, a fix wave, a review
round, a QA pass, or a manifest update. Code reaches `<RUN-BRANCH>` only through task merge commits.
The run record reaches it only through these checkpoints.

### Run page

The run page is a read-only status page for the human, rendered from the manifest and `timeline.md`.
The manifest's `run_page` fields supply its display text independently of the HTML document layout.
The human cannot approve the brief or plan from it.

Append one line to `<RUNDIR>/timeline.md` at every transition, in the form
`- <ISO 8601 UTC> <what happened>`. The newest line is the page's status sentence while the run is
live, so write it for the human: what just happened, and what the run is waiting on. Once the run
ends, the banner shows `run_page.outcome` instead. Write it before the final render, as
`references/run-state.md` defines it.

`<SKILL-DIR>` is the directory that holds this file. Render and publish the page whenever you update
the manifest at a phase boundary, a task merge, a review round, a human touchpoint, an abort, or the
PR:

```bash
python3 <SKILL-DIR>/scripts/render-run-page.py "$RUNDIR"
```

Publish `<RUNDIR>/run-page.html` through the first route available, and reuse the same route and URL
for the whole run:

1. the Claude Artifact tool, private, redeploying the same file path;
2. `orca artifacts share` on the first publish and `orca artifacts update` after, rendered with
   `--standalone`, which makes the page viewable by anyone with the link;
3. neither: render with `--standalone`, tell the human the file path once, at Phase 0, and keep
   rendering.

Report the URL or path in the Phase 0 message. A failed publish never stops the run; record it in
`summary.md` and continue.

### Shared Orca state

Orca's task store and terminal list contain resources from other runs and repositories.

Act only on ids, handles, and paths recorded in this run's manifest. The recorded Orca run id
identifies this run's tasks and messages.

### Role configuration

- `references/routing.md` owns role routing, effort, and worker boot commands.
- `references/skill-map.md` owns the skill assigned to each role.
- `references/context/` holds one file per role. Read it completely when its phase starts, and not
  before.
- `references/orca-mechanics.md` owns how to dispatch, collect, and retry phase workers. Phase
  instructions name the task and where the phase differs.

## Intake

`/orca-implement {TASK-REF | prompt | resume <RUN | RUNDIR>}`

Human approval of the brief and final plan is mandatory for every run. Follow the Planning
artefacts and revisions rule throughout the run.

Use Orca Orchestration to register and manage supervised workers. Load the `orchestration` skill
and follow its instructions for assignment, messages, follow-ups, recovery, and cleanup. Launch
workers through the sandbox commands in `references/routing.md`, preserving the routed model,
effort, nono profile, filesystem grants, and report paths.

Load `orca-cli` for other Orca resources. `orca` in this skill means the executable selected by those
skills. This skill owns workflow, verification, resource ownership, and safety.

Resolve the argument:

- **GitHub issue** (`#123` or issue URL): `gh issue view <n> --json title,body,comments`
- **Linear issue** (`ABC-123` or Linear URL): `orca linear issue <ref> --full --json`
- **File path** (markdown docs, specs): read it directly.
- **Resume** (`resume` followed by a run name or a run folder path): a fresh coordinator session
  takes over an existing run. Follow [Resume a run](#resume-a-run) instead of Phase 0.
- **Anything else**: an ad-hoc prompt. Draft the requirements and acceptance criteria in the brief.
  The human vets them at the understanding check.

Stop before creating anything when an intake read fails or returns empty, such as a missing Linear
connection, an unresolvable issue, or an unreadable file.

The brief records what intake read, states the requirements and acceptance criteria, and cites the
source, in the shape of `references/templates/brief-template.md`. The plan turns the approved brief
into tasks, in the shape of `references/templates/plan-template.md`. Both stand alone, because a
worker cannot reach a URL or a path outside its sandbox. The run works from what intake read. A
ticket that changes mid-run does not change the plan.

## Phase 0: Setup

Complete every step in order before Phase 1.

1. **Load the run mechanics.**

   Follow [Orca runtime mechanics](#orca-runtime-mechanics). Read `references/orca-mechanics.md`
   completely before the first Orca mutation. Read `references/run-state.md` completely before
   initialising the manifest.

2. **Read the working directory.**

   ```bash
   git branch --show-current                                # <CURRENT_BRANCH>
   git status --porcelain                                   # empty means clean
   git rev-parse --git-dir; git rev-parse --git-common-dir  # a linked worktree when they differ
   # succeeds when Orca manages this worktree; gives its id and path
   orca worktree current --json
   # <PRIMARY-PATH>, the primary checkout
   git worktree list --porcelain | awk '/^worktree /{print $2; exit}'
   ```

   Resolve `<DEFAULT_BRANCH>` from `origin/HEAD`. When that is unset, use
   `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`.

3. **Settle the branch role.**

   When `<CURRENT_BRANCH>` is `<DEFAULT_BRANCH>`, set `base_ref` to it and `start_ref` to null. Ask
   nothing.

   When `<CURRENT_BRANCH>` is not `<DEFAULT_BRANCH>` and the worktree is not clean, stop. Report the
   dirty files and ask the human to commit or stash them. The run has created nothing yet.

   Otherwise ask the human once, in the conversation, and wait for the answer:

   > You are on `<CURRENT_BRANCH>`, not `<DEFAULT_BRANCH>`. Tell me what this branch is for, because
   > it decides where the run starts and where the PR goes.
   >
   > 1. **Starting point.** This is your own work-in-progress branch. The run builds on its commits.
   >    The PR carries them and targets `<DEFAULT_BRANCH>`. The review covers your commits too. Pick
   >    this for a personal feature branch.
   > 2. **Target.** This is a shared branch that other work merges into, such as a release or `dev`
   >    branch. The run starts from its tip and the PR targets `<CURRENT_BRANCH>` instead of
   >    `<DEFAULT_BRANCH>`. Nothing on it is reviewed. Pick this for a shared integration branch.
   > 3. **Ignore it.** This branch is unrelated. The run starts from `<DEFAULT_BRANCH>` and the PR
   >    targets `<DEFAULT_BRANCH>`. Your branch is left alone.
   >
   > Options 2 and 3 never modify `<CURRENT_BRANCH>`. Option 1 modifies it only when this is an
   > Orca-managed worktree. The run then adopts that worktree, commits to `<CURRENT_BRANCH>`, and
   > opens the PR from it. Otherwise the run creates its own branch from `<CURRENT_BRANCH>` and
   > works there.

   | Answer         | `base_ref`         | `start_ref`        |
   | -------------- | ------------------ | ------------------ |
   | starting point | `<DEFAULT_BRANCH>` | `<CURRENT_BRANCH>` |
   | target         | `<CURRENT_BRANCH>` | `<CURRENT_BRANCH>` |
   | ignore         | `<DEFAULT_BRANCH>` | null               |

   The invocation and the task source never name a base. This question alone settles it. Record
   `base_ref` and `start_ref` in the manifest.

4. **Pin the base.**

   ```bash
   BASE_SHA=$(git rev-parse <base_ref>)                 # start_ref null, or equal to base_ref
   BASE_SHA=$(git merge-base <base_ref> <start_ref>)    # start_ref set and different from base_ref
   ```

   From here on, every diff, review, and changed-file list uses `BASE_SHA`, never a symbolic ref.
   `base_ref` is used once more, as the PR's target branch. A merge-base puts the start branch's
   existing commits inside every diff, review, and the PR.

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

   Create the Orca Run with objective `<RUN>`. Record the run id when you initialise
   `run-state.json`.

   Associate every task with that run id. Tasks and messages outside that run are not yours.

7. **Choose the integration worktree.**

   Adopt the current worktree when step 2 found it Orca-managed and linked, and `start_ref` is set
   and differs from `base_ref`. Take `<WT>` and `<WT-PATH>` from the `orca worktree current` output
   and `<CURRENT_BRANCH>` as `<RUN-BRANCH>`. Create nothing. Record only terminals this run creates.
   The human's existing terminals in that worktree are not run resources. Record
   `integration_worktree.origin` as `adopted`.

   Otherwise create the worktree named `<RUN>` with `--setup run`. Pass `--base-branch <start_ref>`
   when `start_ref` is set and `--base-branch <base_ref>` otherwise. Link it to the source issue
   when one exists. Record `integration_worktree.origin` as `created`. Wait for the setup terminal
   as [Manage terminals and worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees)
   requires.

   After creation, when the primary checkout has `.env` and the worktree does not, stop before
   creating anything else. Print this command for the human, wait for them to say in the
   conversation that they ran it, and check again with `test -f` before continuing:

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
   # Must equal `git rev-parse <start_ref>` when start_ref is set, else BASE_SHA.
   # Reset to that commit if it does not.
   ```

   `<WT>` is the integration point. Task branches merge into `<RUN-BRANCH>` there, and whole-run
   verification and code review run there. Every build and fix task receives its own worktree when
   Phase 5 dispatches it.

8. **Create the run folder inside the integration worktree.**

   ```bash
   RUNDIR="<WT-PATH>/.agents/orca/orchestration/<RUN>"
   mkdir -p "$RUNDIR/plan/assets" "$RUNDIR/tasks" "$RUNDIR/review" \
     "$RUNDIR/screenshots" "$RUNDIR/scratch"
   ```

   The run folder holds exactly this:

   ```text
   run-state.json                             run manifest
   summary.md                                 run narrative, started in Phase 0, finalised at
                                              Phase 9
   timeline.md                                one event per line, appended at every transition
   run-page.html                              status page rendered from the manifest, never
                                              committed
   plan/brief.html                            human-approved task contract
   plan/plan.html                             human-approved spec of record
   plan/assets/                               supplied designs and selected durable visual evidence
   review.html                                final human review, written in Phase 9
   tasks/{seq}-{slug}-agent-task.md           coordinator to builder
   tasks/{seq}-{slug}-report.md               builder to coordinator
   review/review-r<ROUND>.md                  review of record for the round
   review/qa-review.md                        QA review of record, when qa_policy is run
   screenshots/{description}_{sequence}.png
   scratch/scout-<slug>.md                    one per scouting lens
   scratch/planner-brief.md                   standalone brief every planner reads
   scratch/draft-<planner>.html               one per planner on the tier's panel
   scratch/fact-check-<CHECK>.md              one per initial or revision fact-check
   scratch/plan-pre-critique-r<ROUND>.html    the exact input to each critic round
   scratch/critique-<critic>-r<ROUND>.md      one per critic per round
   scratch/acceptance-check-<PASS>.md         acceptance-criteria check, one per pass
   scratch/<claude|codex>-review-r<ROUND>.md  one per code reviewer per round
   scratch/security-<reviewer>-review-r<ROUND>.md
                                              one per security reviewer per round in which
                                              security ran
   scratch/qa-findings.md                     QA worker report, when qa_policy is run
   ```

   Append `.agents/orca/orchestration/` to the file named by
   `git -C <WT-PATH> rev-parse --git-path info/exclude`. That file is shared by every worktree of
   the repository and is never committed. Do not add a `.gitignore` rule. Write every artifact to
   disk as soon as you produce it. `scratch/` holds worker reports and the coordinator's working
   files and never reaches the branch.

9. **Initialise `run-state.json`.**

   Initialise the manifest from the Initial manifest section of `references/run-state.md` before
   creating or closing another run resource. Fill every value already known from intake, run
   creation, and worktree creation.

   For a created worktree, record every auto-started terminal from the worktree-create response or
   terminal list before any other action, then follow [Manage terminals and
   worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees). For an adopted worktree,
   record none.

10. **Start the summary and report the choice.**

   Start `summary.md` in the shape of `references/templates/summary-template.md`. Start
   `timeline.md` with the run start. Render and publish the run page as the Run page rule requires.

   Report to the human in one message: whether the integration worktree was adopted or created, its
   path, `<RUN-BRANCH>`, `start_ref`, `base_ref`, `BASE_SHA`, and the run page URL or path. Then
   start Phase 1.

## Phase 1: Scout

Run these read-only lenses in parallel:

- **Discovery**: find project mechanics, tooling commands, `.env` presence, the commit-message
  convention, relevant code locations, and whether `orca.yaml` defines a `scripts.setup` hook and
  what that hook does. Find the project rules: rule files that touch this task, such as `CLAUDE.md`,
  `AGENTS.md`, `CONTRIBUTING.md`, `CONTEXT.md`, `DESIGN.md`, `ARCHITECTURE.md`, `STYLEGUIDE.md`, or
  `CONSTITUTION.md`, at any depth. Report their paths, not their contents.
- **Comprehension**: establish current behaviour, affected code, and dependencies on existing code.
- **Test coverage**: find existing coverage that needs adjustment and important gaps to close.
- **Additional lenses**: add a lens when the task needs evidence not covered above.

Read `references/context/scout.md` and resolve a self-contained `<TASK_CONTEXT>` for each lens.
Dispatch one scout per lens in `<WT>` as task `scout-<SLUG>`, collect, and retry once.

After all retries:

1. Record each missing scout role under Incidents in `summary.md`.
2. Cover what that role should have found yourself, reading the code and running read-only commands,
   until the reports and your own evidence cover project mechanics, current behaviour, and tests.

Read every completed report. Carry confirmed findings into the brief and the planner brief. Record
each unresolved assumption that has a sane default in the brief's Assumptions section, unless the
assumption is a human-owned decision. Put every other one in the Questions section.

## Phase 2: Understanding check

The understanding check settles the task contract before planning. It reconciles the task source,
repository evidence, and human intent. Before autonomous work begins, it puts every decision the
coordinator must not make alone to the human.

Write `<BRIEF_PATH>` using the content guidance in `references/templates/brief-template.md`.
Preserve stable anchors and supplied design provenance while choosing an appropriate HTML layout.

Put every known question in the first version. Before opening the brief, and before reopening each
revised version, check it and fix what fails:

- every `R-n` states a behaviour a criterion can test, with no implementation detail;
- every `R-n` has at least one `AC-n`, and every `AC-n` states observable behaviour and how it will
  be verified;
- Scope lists both In and Out;
- every `C-n` is verifiable;
- Questions are in impact order;
- every `Q-n` is a full question with one to three suggested answers and a marked recommendation;
- every `A-n` gives its default and reasoning, and none is a human-owned decision;
- every repository claim cites `path:line`.

Open `<BRIEF_PATH>` with the mapped `{human-review-skill}` and run its documented review loop.
For HTML, use its local-page review mode. The mapped skill owns review commands and receipts.

Apply every answer and comment to the brief. Fold each answer into the section it settles. Retain
its question ID, source, and resolution at a stable anchor and remove it from open questions. If an answer reveals more questions, group all of them into the next version. Reopen
the brief and run the printed next-round command.

Continue until every question is answered and the human completes a round with no comments.
Record approval of that exact document and its referenced assets as `references/run-state.md`
defines. Set `run_page.title`, `run_page.goal`, and `run_page.constraints` from the approved brief.
Treat the approved brief and every human answer as settled facts during planning. Do not carry a known question into
the plan as an open assumption.

If the mapped review skill is unavailable, run the same loop in the conversation and require
explicit approval. An explicit rejection or cancellation runs the abort routine with status
`blocked`. Update the manifest before Phase 3.

## Phase 3: Plan

### Step 1: Set the plan-review tier

1. Classify `plan_review_tier` from the requirements and scout evidence. Use the rubric in
   `references/routing.md`.
2. Record the tier in `run-state.json`.

The tier selects the planner panel.

### Step 2: Draft the plan

Read `references/context/planner.md`. Start the routed planner panel from `references/routing.md`.

#### Prepare the planner brief

Write `<RUNDIR>/scratch/planner-brief.md` as `references/context/planner.md` describes. Every
planner reads that one file.

#### Dispatch and collect planners

Dispatch one `plan-draft-<P>` task per planner, collect, and retry once. A planner that fails twice
takes no further part. Record every retry and each reduction in the panel.

After collection:

- With two drafts, assess both.
- With one draft, use it as the base.
- With no drafts, write `<PLAN_PATH>` yourself using the content guidance in
  `references/templates/plan-template.md`.

#### Build the final plan

Assess and combine the drafts as `references/context/planner.md` describes. Write one coherent
`<PLAN_PATH>` that covers `references/templates/plan-template.md`, with stable anchors and
faithful use of the supplied designs.

### Step 3: Fact-check the plan

Read `references/context/plan-fact-check.md`. Resolve a unique `<CHECK>` for this pass, initially
`initial`, and dispatch `plan-fact-check-<CHECK>`. Collect and retry once. If the retry fails,
verify the claims yourself and record the missing fact-check in `summary.md`.

Correct every reported mismatch before critique. On later revisions, scope the check to changed
claims and use a new check label, such as `r2-final`, so earlier reports and task identities survive.

### Step 4: Critique the plan

Read `references/context/plan-critic.md`. Use both independent critics from `references/routing.md`
in each round. Number rounds consecutively across the run, including later plan revisions.

1. Set `<ROUND>` to the next plan-review round number. Copy the fact-checked plan to
   `<RUNDIR>/scratch/plan-pre-critique-r<ROUND>.html` and record its document and asset digests,
   the round's trigger, and the current `<WT>` HEAD in `plan_review.rounds`.
2. Dispatch `plan-critique-<M>-r<ROUND>` to every critic against the same unchanged plan. Collect
   both reports before editing the plan and retry a failed lens once.
3. When a retry fails, record the missing lens in the round and the plan's Review Policy. Continue
   with surviving critics. If all critics fail, record `all critics failed`, make the absence
   visible at the human gate, and stop automated critique of this revision.
4. Triage every finding on its evidence. Give it a stable `PF-n` ID, retain that ID across rounds,
   and record its source, evidence, disposition, and resolution in the plan's Decisions section.
   Link any affected `PD-n` decision. Critic verdicts are evidence rather than approval.
5. Apply accepted changes. Record accepted counts, whether the plan changed, whether features,
   approach, proposed fixes, contracts, scope, or safety assumptions changed materially, and why.
6. Fact-check changed repository claims through Step 3, scoped against this round's snapshot.
   Include any corrections from that check when assessing material change. Save the output
   document and asset digests and update `rounds_run` and the manifest.
7. Clean up the round's workers through Orca Orchestration and their recorded terminals through
   [Manage terminals and worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees).
8. If the revision materially changed features, approach, proposed fixes, contracts, scope, or
   safety assumptions, run another round against that revision. This includes changes made to fix
   the critics' own findings. Wording and presentation changes alone do not trigger another round.
   Otherwise record `critique complete` and finish critique.

There is no fixed round count. Continue while material revisions require another round. If the
process repeats the same unresolved disagreement without new evidence or progress, record it and
pause for a human decision rather than cycling. Resume the required critique after that decision.
A human choice to proceed without a missing lens must remain explicit in the plan and receipt.

#### Finish plan critique

1. Assess `run_complexity` from the reviewed plan. It may differ from `plan_review_tier`.
2. Set the code-review cap and QA policy from `references/routing.md` in the plan's metadata,
   Review Policy, and `run-state.json`. Keep the original plan-review tier and round history.
3. If this finalisation itself changes the substantive approach or proposed fixes, fact-check the
   changed claims and return to Step 4. Otherwise update the manifest and start Phase 4.

## Phase 4: Plan gate

Run this phase for every plan before implementation. The human approves the scope, approach,
task boundaries, contracts, open assumptions, and review cost.

Present `<PLAN_PATH>` through the mapped `{human-review-skill}`. Use local-page review for HTML
and document review for retained legacy Markdown. Link to the approved brief and identify the
plan-review tier, critic rounds and outcome, missing lenses, final run complexity, code-review cap,
QA policy, and every open assumption.

Run the mapped skill's review loop and address every unresolved comment. Verify new or changed
repository claims before presenting a revised plan. Material changes to features, approach,
proposed fixes, contracts, scope, or safety assumptions return through Phase 3 Step 4. Wording-only
changes need renewed human approval but no further critique. Changes to the approved task contract
first return to Phase 2.

A completed round with no comments approves the exact page and referenced assets presented. Record
its receipt as `references/run-state.md` defines, including the approved brief revision. If the
review skill is unavailable, require explicit conversational approval and record that evidence.
Critic verdicts, silence, an empty unrelated session, and an unfinished round are not approval.

Confirm both receipts still match the current documents and assets. Update the manifest, commit the
`plan ready` checkpoint, and start or resume affected work. An explicit rejection or cancellation
runs the abort routine with status `blocked`.

## Phase 5: Build

Read `references/context/builder.md`. Confirm both approvals are current before dispatching build
work. Before any material plan change, follow Planning artefacts and revisions.

Register the build tasks and their dependencies. Orca task specs are immutable, and a task's
worktree path and dependency outputs are unknown until it becomes ready. Each task spec therefore
holds only the agent-task pointer from the builder context.

For each planned task, use title `{seq}-{slug}`, set dependencies by owned build-task id, resolve
the builder context's required task-spec values, and use its Orca task spec.

Record every returned task id in `run-state.json` as the build-owned set. This set contains build
and fix tasks only. Keep scout, fact-check, planner, critic, acceptance-check, and reviewer task ids
in their phase dispatch records, and the QA task id in the QA record.

### Dispatch ready tasks

Select ready tasks only from the build-owned set. Never dispatch directly from the runtime-global
`task-list --ready` result. Run no more builders than the concurrency cap in
`references/routing.md`.

For each ready task:

1. Create worktree `<RUN>-{seq}-{slug}` from `<RUN-BRANCH>` with parent worktree `<WT>` and
   `--setup run`. Wait for setup through [Manage terminals and
   worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees).
2. Capture the worktree id, absolute path, and actual branch.
3. Handle auto-started terminals through [Manage terminals and
   worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees).
4. Record the starting commit with `git -C <path> rev-parse HEAD`.
5. Resolve every required builder-context value.
6. Write `<RUNDIR>/tasks/{seq}-{slug}-agent-task.md` in the shape of
   `references/templates/agent-task-template.md`.
7. Launch the routed sandboxed builder from `references/routing.md` in the task worktree and record
   the run-owned terminal. Register it and assign this task through Orca Orchestration, using the
   agent-task file as input. Do not pass resolved context through a shell argument.
8. Record the worker identity and active Orca task and dispatch ids from the startup receipt.
   Set manifest status to `dispatched` only when that receipt confirms dispatch.

### Collect workers

Collect `worker_done`, `escalation`, and `question` messages using [Receive orchestration
messages](references/orca-mechanics.md#30-receive-orchestration-messages). Follow Orca Orchestration
for waiting and keep the run `active` while it awaits workers.

Handle each message that matches an active dispatch by type:

- `question`: answer through Orca Orchestration within the approved brief. When
  the answer settles something the plan left open, add it to the agent task so a re-dispatched or
  replacement worker builds on it. When it changes a contract another task uses, update every
  affected agent task as in [Stop contract drift](#stop-contract-drift).
- `escalation`: inspect the reported stop reason and live worker state through Orca Orchestration.
  Resolve the blocker within the approved task contract and continue the worker through that
  interface. Update the agent task when the resolution changes its instructions.
- Neither message completes the task. When either needs a critical decision, follow the Human
  touchpoints rule.
- `worker_done`: for a successful outcome, run the task verification and merge procedure below.
  Handle a failed outcome through Orca Orchestration's recovery instructions and the run's retry
  limits. After a successful merge, dispatch newly ready tasks from the build-owned set up to the
  concurrency cap.

Continue until every build-owned pipeline task is merged or permanently failed, with no unsettled
attempts. Follow-up Orca Tasks remain associated with their original pipeline task.

### Recover a stopped worker

Use Orca Orchestration to inspect the stop reason, worker output, and live state. Silence, a timeout,
or a lack of commits alone does not authorise stopping or replacing a worker.

- If the worker is active, continue other ready work or wait through Orca Orchestration.
- If it needs an answer or permission, resolve that blocker through the Human touchpoints rule and
  continue the worker through Orca Orchestration.
- For a confirmed failed attempt, follow Orca Orchestration's recovery instructions. Preserve the
  existing task worktree, branch, and committed work. If replacement is required, confirm the
  previous worker stopped before launching another worker through `references/routing.md`.

Record the returned task, dispatch, and worker identities before continuing. Preserve the pipeline
task's original identity and dependencies. Count a recovered build attempt towards its
verify-to-fix limit; it does not consume the retry protocol's replacement attempt. Respect Orca
Orchestration's recovery requirements even when the pipeline has cycles remaining.

### Verify a completed task

Orca Orchestration settles the task and dispatch from the worker's outcome. A successful outcome
does not prove the work is correct or ready to merge. Keep the manifest task unmerged until every
check below passes.

1. Compare the task branch with its recorded starting commit:

   ```bash
   git log <starting-commit>..<task-branch> --oneline
   ```

2. Require a clean task worktree:

   ```bash
   git -C <task-worktree> status --porcelain
   ```

3. Accept a branch with no new commits only when the worker reported an explicit no-change outcome
   and the worktree is clean.
4. Read `<RUNDIR>/tasks/{seq}-{slug}-report.md`.
5. Rerun every applicable project check in the task worktree, whatever the report claims. Run them
   in this order: Build, Lint, Typecheck, Tests, Format check.
6. Compare the result with the task requirements in the plan.

Start a fix cycle if the worktree has uncommitted changes, a check fails, or the task does not meet
its requirements:

1. Append the coordinator's findings and failing output to the agent task.
2. Request follow-up work from the builder through Orca Orchestration in the same task worktree,
   preserving the sandbox launch policy in `references/routing.md`.
3. Record the returned Orca task, dispatch, and worker identities against the existing pipeline task.
   Preserve its original identity and dependencies. Set manifest status to `dispatched` after confirmation.
4. Increment the verify-to-fix cycle count.

After three verify-to-fix cycles, use the retry protocol.

### Merge a verified task

Merge each verified task immediately.

1. Merge the task branch into `<RUN-BRANCH>` in `<WT>`:

   ```bash
   git -C <WT-PATH> merge --no-ff -m "orca: merge task <task-title>" <task-branch>
   ```

   `--no-ff` gives every task one merge commit on `<RUN-BRANCH>`, even when a fast-forward is
   possible. The first-parent history then reads one line per task, and `merge_commit` always names
   a real merge.
2. Resolve a trivial text conflict yourself only under the coordinator's exceptions in the run-wide
   rules.
3. For a semantic conflict:

   1. Abort the merge.
   2. Register a conflict-resolution fix task.
   3. Require that task to merge the original task branch into its fix branch and produce the
      conflict-resolution commit.
   4. Keep the original task marked `completed` in the manifest until the conflict task merges.
   5. Collect and verify the conflict task through the normal build flow.
   6. Merge the conflict task, then continue finalising the original task.

4. Run the checks in the plan's Integration Verification section for the boundaries this task
   touches.

If an integration check fails, keep the original task `completed` and its dependants blocked.
Create a fix task from the current `<RUN-BRANCH>` without making it depend on the original task.
Count the fix wave in `verification.fix_waves`, using the existing three-wave limit.
Finalise the original task only after the fix merges and the affected integration checks pass.

Increment the original task's resolve-to-verify count for each conflict task. Allow at most three
resolve-to-verify cycles. After the third failed cycle, use the retry protocol.

### Finalise a merged task

Only after merge and integration verification pass:

1. Mark the task merged in the manifest and record the merge commit as `merge_commit`.
2. Allow dependent tasks to become ready.
3. Clean up every recorded attempt's worker resources through Orca Orchestration.
4. Follow [Manage terminals and worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees)
   for separately recorded terminals. Confirm no worker can still write to the worktree.
5. Remove the task worktree by its recorded id and confirm removal through `orca-cli`. If cleanup
   is unresolved or refused, retain the worktree and record partial cleanup.
6. After its worktree is removed, delete the task branch with:

   ```bash
   git -C <WT-PATH> branch -d <task-branch>
   ```

   `-d` refuses an unmerged branch. A branch that Orca already removed with the worktree is
   acceptable.

7. Update the manifest.
8. Dispatch newly ready tasks from the build-owned set up to the concurrency cap.

### Stop contract drift

Contract drift occurs when two active workers repeatedly make incompatible changes to one shared
interface.

When you detect contract drift:

1. Compare both implementations with the contract approved in the plan.
2. Pin the contract to one explicit definition within the brief.
3. Update each affected agent task with that definition.
4. Dispatch conform-to-contract fix tasks.
5. Reject further worker-specific changes to the contract.

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

Use one fix task for a wave by default. Split a wave only when the fixes are independent and the
saved execution time exceeds the coordination cost. Add dependencies between split tasks when their
changes are not independent.

## Phase 6: Whole-run verification

Whole-run verification checks the integrated HEAD against the acceptance criteria and decides
whether the change needs stronger review than the plan predicted.

Run all checks in `<WT>` after the final task merge.

### Run project checks

Run the plan's Install command in `<WT>` before the first check unless the plan's Setup hook entry
records that the setup script installs dependencies. Run it after any later merge that changes a
dependency manifest or lockfile. The command is idempotent.

Run the commands recorded in the plan:

1. Build.
2. Lint.
3. Typecheck.
4. Full test suite.
5. Format check.
6. Every command in the plan's Post-Merge Validation section.

Record the result of every applicable command. Verify every boundary in the plan's Integration
Verification section. Record the evidence for `summary.md`.

### Check acceptance criteria

Read `references/context/acceptance-check.md`. The first pass covers every criterion and constraint.
`references/context/acceptance-check.md` selects the scope of every later pass.

Dispatch the `acceptance-check-<PASS>` task to the routed worker in `<WT>`, collect, and retry once.
If the retry fails, verify each in-scope criterion yourself and record the missing check in
`summary.md`.

Read the report. Confirm each `not met` and `not verifiable here` entry against the code before
acting on it. Treat each confirmed `not met` criterion or constraint as a verification failure.
Confirm each reported unrequested change against the plan. Revert a confirmed one through a fix
task, or keep it and record the reason under Decisions in `summary.md`. Carry forward the verdict
and evidence of every criterion and constraint outside the pass's scope. Record the evidence for
every criterion and constraint in `summary.md`.

### Decide browser verification

Set `browser_verification.policy` to `run` in `run-state.json` when the diff touches components,
pages, layouts, styles, or templates, or when the visual effect is uncertain. Otherwise set it to
`not_needed`. Browser verification runs in Phase 7 round 1, in parallel with the review lenses.

### Confirm the review policy

Compare the integrated diff and observed failures with the approved `run_complexity`. Planning can
underestimate risk that becomes visible only after implementation.

If the implementation carries more risk than the approved `run_complexity` assumed:

1. Raise `run_complexity`.
2. Recalculate the code-review cap and QA policy from `references/routing.md`.
3. Revise the plan's metadata and Review Policy and `run-state.json`.
4. Record the evidence and reason in `summary.md`.
5. Follow Phase 4 for approval of the revised policy before continuing. A material approach or fix
   change also receives the required critique. Confirm that all three policy records agree.

### Fix verification failures

Turn each failure into a fix task through the Phase 5 fix-task procedure. Put the failing command,
its output, and the expected result in the agent task. For an unmet criterion or constraint, put it,
the report's evidence, and the expected behaviour in the agent task.

After each fix merge:

1. Rerun the failed check.
2. Rerun any checks affected by the fix.
3. Rerun the acceptance check for the criteria the fix affected.
4. Start another fix wave if a check still fails or a criterion is still unmet.

Record each wave in `verification.fix_waves`. Allow at most three verification fix waves. After the
third failed wave, record every check that still fails and every criterion still unmet under
Remaining in `summary.md`, with its output, and set `pr_draft` to true.

Start Phase 7 when every project check passes and every acceptance criterion is verified or recorded
as not verified with its reason, or when the third verification fix wave fails. Record a gap only
when this environment cannot verify it, such as an unavailable dev server, or when the wave limit is
reached.

### Record the verification evidence

Update `<RUNDIR>/summary.md` with the implementation decisions so far, the evidence for each
acceptance criterion, every incident, and every unverified gap with its reason. Reviewers and QA
read this file. Record check revisions, scope, results, and report paths in `verification.evidence`
as `references/run-state.md` defines. Save it. Commit the `build verified` checkpoint. Then start Phase 7. Review round 1
reviews that commit.

## Phase 7: Code review

Each round dispatches the code and security lenses together, in one wave, against the same committed
HEAD. Round 1 also runs browser verification when Phase 6 required it. A later round runs only when
the previous round fixed an accepted Critical or High finding, up to the approved round cap. Medium
findings get one fix wave and never reopen review.

### Prepare the review

1. Read `references/context/review.md`.
2. Read `<CODE_REVIEW_CAP>` from the plan's Review Policy.
3. Set `review_fixes_applied=false` in the manifest.
4. Start every routed code reviewer in `<WT>` from `references/routing.md`. Start the security
   reviewers only when `run_complexity` is `medium` or above. Reuse reviewer conversations across
   rounds through Orca Orchestration subject to the sandbox launch policy in `references/routing.md`.

### Run a review round

For each `<ROUND>` from 1 through `<CODE_REVIEW_CAP>`:

1. Add the round to `review_rounds` with `severe_fix_merged=false` and the current `<WT>` HEAD.
2. Resolve every required value in `references/context/review.md`. Every round reviews the whole
   branch against `<BASE_SHA>`. Each later round first confirms the previous round's fixes, then
   reports only findings the previous review did not triage.
3. Select the security lenses for the round. This is the security trigger that
   `references/routing.md` names:
   - At `low` complexity, set `security_lenses_run=false` with reason `run complexity policy` and
     dispatch none.
   - In round 1, dispatch both.
   - In a later round, dispatch both when a previous security lens reported a finding, or when a fix
     wave since the previous round changed a file that handles attacker-controlled input as the
     trust model in the mapped `{security-review-skill}` defines it. When neither holds, set
     `security_lenses_run=false` and `security_skip_reason` in the round record.
4. Assign each selected reviewer the round's task and unique report path through Orca Orchestration.
   Record any new task and dispatch ids against that reviewer's round record. Collect, and retry a
   failed lens once within the round.
5. In round 1, when `browser_verification.policy` is `run`, read
   `references/context/browser-verification.md` and resolve every required value. Start one native
   subagent in the same wave as the reviewers, on the model from `references/routing.md`. Use the
   dispatch template and failure policy in `references/context/browser-verification.md`. The browser
   subagent is not a phase worker. Its report stays in coordinator context. If it produces no
   report, start it once more.
6. When a retry also fails, record the lens in the round's `missing_lenses` and in the round review,
   and launch a fresh sandboxed worker for it before any later round. If both code-review lenses are
   unavailable, record `no code review` as the stop reason, set `pr_draft` to true, and stop the
   review loop. Record every missing security lens, then continue with the surviving lenses.
7. Read the browser screenshots yourself. A browser report without screenshots is not verified.
   Record the result as `browser_result` in the round record and in `browser_verification.result`.
8. For each acceptance criterion the acceptance check recorded as `not verifiable here` because it
   needs a browser, record the round-1 browser evidence and the resulting verdict against that
   criterion in `summary.md`.

### Write the round review

Write `<RUNDIR>/review/review-r<ROUND>.md`. It is the review of record for the round and stands
alone. A reader must not need the lens reports. Treat every completed code-review and
security-review lens as a separate source.

Record at the top:

- base SHA;
- branch;
- round;
- HEAD reviewed;
- lenses completed and lenses missing;
- each lens's coverage notes, tests-review line, and verdict, as written.

Combining the lens reports is mechanical:

1. Drop a finding when its cited file exists neither at the recorded HEAD nor at `<BASE_SHA>`. A
   deleted file remains a valid citation.
2. Keep a finding in untouched code only when it traces a causal path to a changed file.
3. Deduplicate by finding identity, not wording. When two lenses report one finding, keep one entry,
   name both sources, and keep each source's severity and confidence.
4. Carry each surviving finding over in the lens skill's own format, complete and unedited: Issue,
   Severity, Confidence, Category, File, Findings, Attack path where the lens gives one, Evidence,
   and Fix. Add a stable run-wide `F-n` ID and a `**Source:**` line. Reuse that ID for the same
   finding in later rounds or QA and link its prior disposition. Do not reduce a finding to a title
   or a checklist line.
5. Carry each lens's documentation and artifact recommendations over as written.
6. Carry each browser-verification failure over as a finding with `**Source:** browser` and the
   screenshot path as evidence. Severity follows the observed impact. High when a core flow is
   broken, Medium otherwise.

Do not add findings, change severity, or judge validity while combining.

### Triage the findings

Assess each surviving finding against the code and its reproduction.

- Discard a finding that does not hold.
- Accept a finding that holds.
- Treat attribution and severity as evidence, not a verdict.
- Fix every accepted finding unless the brief or plan explicitly excludes the work.

If a required fix needs a human-owned decision that the approved task contract
does not settle, follow the Human touchpoints rule.

Record an excluded finding under Remaining in `summary.md` with the reason it remains.

Append a Triage section to `review/review-r<ROUND>.md`. For each finding, record the outcome, the
evidence you checked, and the reason under its stable finding ID. Preserve prior dispositions,
fix commits, reproduction results, and any superseding finding. Identify a workaround, accepted
risk, or deferred item explicitly. Record the accepted counts by source and severity in the
round's `accepted_findings`. Update the manifest before starting a fix wave.

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

Record each wave in the round's `fix_waves`. Allow at most three fix waves in one review round.
After the third failed wave, record each unresolved finding under Remaining in `summary.md`, record
`fix waves exhausted` as the stop reason, set `pr_draft` to true, and stop the review loop.

Set `review_fixes_applied=true` after any accepted fix, Medium included, merges and verifies in
`<WT>`.

Set `severe_fix_merged=true` only after you merge and verify a fix for an accepted Critical or High
finding in `<WT>`. Medium fixes, report files, bookkeeping changes, and findings that need no
implementation change do not count.

When `severe_fix_merged=true`, continue to the next round unless this round reached
`<CODE_REVIEW_CAP>`. At the cap, stop after the verified fix wave, record `cap reached` as the stop
reason, and record that no reviewer saw the final fixes.

When `severe_fix_merged=false`, stop the review loop.

### Finish code review

1. Clean up reviewer workers through Orca Orchestration and their recorded run-owned terminals
   through [Manage terminals and worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees).
2. If `review_fixes_applied=true`, rerun the Phase 6 project checks and the acceptance check for
   affected criteria against the post-review HEAD. Rerun browser verification only when a fix
   changed UI files, and only for the pages it touched.
3. Treat verification fixes as post-review and unreviewed. Use the Phase 6 fix procedure with its
   own three-wave limit, recorded in `verification.post_review_fix_waves`. Do not reopen code
   review.
4. If no review fix changed the implementation, retain the existing Phase 6 evidence.
5. Require current revision-bound verification evidence or an explicit reason for every remaining
   unverified gap. Record new checks in `verification.evidence`; preserve earlier evidence's scope
   and code revision rather than relabelling it as verification of the latest HEAD.
6. Set `code_review_complete=true` in `run-state.json`.
7. Confirm that the final round's stop reason is recorded.
8. Update the manifest with the final round review and verification evidence.
9. Commit the `code review complete` checkpoint. Phase 8 records that commit as `QA_HEAD`.

## Phase 8: Final adversarial QA

Adversarial QA attempts to break the committed implementation after code review and post-review
verification. It runs once. Verify QA fixes, but do not reopen code review for them.

Require a clean integration worktree:

```bash
git -C <WT-PATH> status --porcelain
```

### Apply the QA policy

When `qa_policy` is `skip`:

1. Do not create a QA task, terminal, worktree, dispatch, or findings file.
2. Set `qa.status` to `skipped` and `qa.reason` to `run complexity policy` in `run-state.json`.
3. Continue to Phase 9.

When `qa_policy` is `run`, run the procedure below.

### Prepare the QA worktree

1. Record:

   ```bash
   QA_HEAD=$(git -C <WT-PATH> rev-parse HEAD)
   ```

2. Create a disposable worktree named `<RUN>-qa` from the current `<RUN-BRANCH>`, using `<WT>` as
   its parent worktree and `--setup run`. Wait for setup through [Manage terminals and
   worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees).
3. Record its id, absolute path, and actual branch.
4. Handle auto-started terminals through [Manage terminals and
   worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees).
5. Confirm that the QA worktree HEAD equals `QA_HEAD`.

The QA worktree is disposable. Never merge its branch.

### Run and collect QA

Read `references/context/adversarial-qa.md`. Dispatch the `<RUN>-qa` task to the routed QA worker in
the QA worktree through Orca Orchestration, using the sandbox commands in `references/routing.md`.
Record the task, dispatch, worker identity, and any terminal metadata in the QA record, then collect.

On successful completion:

1. Require a non-empty `<RUNDIR>/scratch/qa-findings.md`.
2. Set `qa.dispatch_status` to `completed`. Keep `qa.status` as `pending` until triage, accepted
   fixes, and verification finish.

On a confirmed worker failure, or a settled dispatch with a missing report, set `qa.dispatch_status`
to `failed`. Follow Orca Orchestration's recovery instructions and confirm no worker can still
write before resetting the QA worktree to `QA_HEAD` and removing its untracked files. Retry once
through Orca Orchestration with a sandboxed worker and record the returned identities.

If the retry also fails:

1. Set `qa.status` to `not_verified` and record the failure in `qa.reason`.
2. Record the incident in the manifest and `summary.md`.
3. Continue to Phase 9 without triage.

In all cases:

1. Clean up recorded QA attempts through Orca Orchestration. Resolve their separately recorded
   terminals through [Manage terminals and worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees).
2. Confirm no worker can still write, then remove the QA worktree by its recorded id and mark it
   `removed`. If cleanup is unresolved or refused, retain it and record partial cleanup.
3. Delete the QA branch only after the worktree is removed.
4. Confirm that you never merged the QA branch.

### Triage and fix QA findings

Assess each concrete finding on the same terms as Phase 7:

- discard it when it does not hold;
- accept it when it holds;
- record it under Remaining in `summary.md` only when the brief or plan excludes it.

Write `<RUNDIR>/review/qa-review.md`. It is the QA review of record and stands alone. A reader must
not need the worker report. Carry every finding from `scratch/qa-findings.md` over in the QA skill's
own format, complete and unedited: Severity, Category, Type, Location, Finding, Reproduction,
Expected, Actual, Evidence, and Regression test. Carry the coverage list and verdict as written.
Then append a Triage section: for each finding, a stable run-wide `F-n` ID, the outcome, the
evidence you checked, and the reason. Reuse an existing finding's ID and preserve its resolution
history. Distinguish a verified fix, workaround, accepted risk, and deferred item. Record the accepted counts by severity in `qa.accepted_findings`. Update the manifest before
starting fixes.

Create accepted fixes as Phase 5 fix tasks from the current `<RUN-BRANCH>`. Never make lasting fixes
in the disposable QA worktree.

For every fix wave:

1. Verify each fix task.
2. Rerun each finding's exact reproduction.
3. Rerun the Phase 6 project checks and the acceptance check for affected criteria. Rerun browser
   verification only when a fix changed UI files, and only for the pages it touched.
4. Record the fix commit and revision-bound verification evidence against the finding in the QA
   review and `verification.evidence`.
5. Start another wave if a finding still reproduces.

Allow at most three QA fix waves. After the third failed wave, record each unresolved finding under
Remaining in `summary.md` and set `pr_draft` to true.

Set `qa.status` to `completed` and clear `qa.reason`. Record the final QA, fix, and verification
evidence before Phase 9.

## Phase 9: PR

### Finalise the run evidence

Update `<RUNDIR>/summary.md` in the shape of `references/templates/summary-template.md`.
Fill every section with the results so far. Leave `finished` as `pending`
and record publication as pending in Outcome.

Write `<RUNDIR>/review.html` using `references/templates/review-template.md`. Show approved versus
delivered behaviour, design deviations, stable decision and finding IDs, selected visual evidence,
reviewed and verified code revisions, missing coverage, and remaining work. Link the approved brief,
plan, and round reviews. Copy selected screenshots into `plan/assets/` with provenance, without
changing assets referenced by an approved document. This page supports PR review and adds no
pre-PR approval gate. Link it from `summary.md`.

Run this command:

```bash
git -C <WT-PATH> status --porcelain -- . ':!.agents/orca/orchestration'
```

It must return no output. The pathspec excludes the run folder because its committed files change
between checkpoints.

### Publish the branch and PR

In the PR description, identify code changes that received verification but no
subsequent code review. State which checks covered those changes.
Include any missing review lenses and unverified acceptance criteria.
When `pr_draft` is true, ask the `{pr-skill}` for a draft PR, and open the description with each
item under Remaining in `summary.md`, its evidence, and why it remains.

1. Push `<RUN-BRANCH>`. It is the only branch that may reach the remote.
2. Open the PR through the mapped `{pr-skill}` against the base branch.

Use this sign-off instead of the PR skill's sign-off:

```markdown
---
:space_invader: Built with Orca + {display names of every model that produced or fixed code in the
PR, deduplicated; omit effort levels}
```

### Tear down run resources

Use only handles and ids recorded in `run-state.json`.

1. Resolve every recorded worker attempt's resources through Orca Orchestration. Record any retained
   or unresolved dispatch ids.
2. Clean up separately recorded terminals through [Manage terminals and
   worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees).
3. Remove each remaining task or QA worktree only after confirming no worker can still write there.
   Record confirmed removals and preserve unresolved resources.
4. Confirm cleanup using recorded identities only. Do not act on unfiltered resource lists.
5. Keep the integration worktree until the PR merges and mark it `retained`. Its later removal with
   `orca worktree rm` belongs to the human.
6. Set `cleanup.status` to `complete` when no removable resource remains. Otherwise set it to
   `partial` and record every unresolved dispatch id, terminal handle, or worktree id.

### Record PR state

1. Set `run-state.json` status to `pr`.
2. Record the PR URL in the manifest, `summary.md`, and `review.html`.
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

A worker may use at most three verify-to-fix cycles. Exhausting those cycles starts one replacement
attempt.

1. Diagnose whether the approach or its execution caused the failures.
2. Revise implementation details only within the approved task contract.
3. If recovery needs a decision the human owns, follow the Human touchpoints rule.
4. Append a retry briefing to the agent task:
   - what each cycle attempted;
   - each failure and its output;
   - the report path and relevant Git revisions;
   - the coordinator's diagnosis;
   - what the replacement must do differently.
5. Resolve the original worker through Orca Orchestration's recovery and cleanup instructions.
   Confirm it stopped before starting a replacement.
6. Launch a fresh sandboxed worker from `references/routing.md` in the same task worktree and branch.
7. Register and assign the replacement through Orca Orchestration. Follow its same-Task recovery
   rules for execution failures and record any returned task and dispatch ids against the original
   pipeline task. Preserve its dependencies and prior attempt identities.

The replacement receives its own limit of three verify-to-fix cycles.

If the replacement exhausts that limit, the task fails permanently:

1. Mark the pipeline task `failed` in the manifest. Settle any outstanding Orca assignments through
   Orca Orchestration; do not rewrite a successful worker outcome as an execution failure.
2. Mark its build-owned dependants `failed` with reason `dependency failed`.
3. Resolve all recorded worker attempts through Orca Orchestration.
4. Remove its worktree only after [Manage terminals and
   worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees) permits it, preserving its
   branch and any uncommitted work.
5. Record every attempt and the preserved branch in `summary.md`.

Continue every task that does not depend on the failed task through dispatch, collection,
verification, and merge. When no build task merges, run the abort routine with status `failed`.
Otherwise continue the run: record each acceptance criterion that only failed tasks cover as
`not met` with reason `task failed`, create no fix task for it, list it under Remaining in
`summary.md`, and set `pr_draft` to true.

### Pause for a critical decision

Use this routine also when Orca Orchestration requires explicit human authorisation for recovery.

1. Add an entry to `decisions` in `run-state.json`. Write the question as the brief writes one: a
   full question, what the answer decides, one to three options with the consequence of each, and a
   marked recommendation. Cite the evidence that raised it with `path:line`.
2. Append the question to `timeline.md` and render the run page, so the human sees it while the run
   continues.
3. Hold every task the decision affects. Collect, verify, merge, and dispatch every other task as
   normal.
4. When nothing else can progress, set `status` to `awaiting_input`, save the run record, and present
   the question in the conversation. Commit the `awaiting decision` checkpoint only when the
   checkpoint rule permits it. Keep every terminal and worktree.
5. When the human answers, record the answer in the decision entry and as a `C-n` constraint in the
   brief, update the affected agent tasks, set `status` to `active`, and release the held tasks.

An explicit cancellation runs the abort routine with status `blocked`.

### Run the abort routine

The abort routine is safe to run more than once. It ends the run without a PR. Use it only for:

- a Phase 0 setup failure, such as a worktree that fails setup twice;
- rejection or cancellation at the understanding check, the plan gate, or a paused decision;
- a run in which no build task merged.

Use run status:

- `failed` for a setup failure or a run in which no build task merged;
- `blocked` for a rejection or cancellation.

Then:

1. Mark this run's remaining non-terminal tasks `failed`.
2. Resolve run-owned worker attempts through Orca Orchestration. Record any unsettled or unresolved
   resources; marking a pipeline task failed does not prove its worker stopped.
3. Clean up terminals and worktrees through [Manage terminals and
   worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees), preserving task branches
   and uncommitted work. Retain a worktree while its worker state is unresolved.
4. Delete a disposable QA branch only after its worktree is removed.
5. Keep the integration worktree and run branch for inspection.
6. Complete `summary.md` in the shape of `references/templates/summary-template.md`. Set `finished`
   and fill every section.
7. Update `run-state.json`.
8. Commit the `run failed` or `run blocked` checkpoint only when the checkpoint rule permits it.
   If a worker can still write, leave the run record on disk and report the unresolved worker.
9. Report the failure or blocker to the human.

### Detect an infeasible plan

Treat the plan as infeasible when:

- consecutive tasks fail for structurally similar reasons; or
- different implementations fail the same acceptance criterion.

Stop replacing workers. Record in `summary.md` the repeated evidence, the plan assumptions that
appear false, and your assessment of what is feasible.

When `replans` is 0, replan once:

1. Pause affected work and resolve any active writers through Orca Orchestration before replacing
   task contracts. Revise the plan using the evidence and invalidate its approval. If the brief
   must change, revise it and obtain approval through Phase 2 first.
2. Fact-check the revised sections, run the required critic rounds in Phase 3, and obtain human
   approval through Phase 4. Preserve prior decisions and finding resolutions.
3. Mark superseded unmerged tasks `failed` with reason `replanned`, and register revised tasks under
   the continuing sequence numbering. Preserve existing task and attempt history.
4. Set `replans` to 1 and resume Phase 5 only with current approvals.

When the revised plan fails the same way, treat each failing task as permanently failed under the
retry protocol.

### Recover coordinator failure

On a context-limit or unexpected coordinator error, attempt recovery first. If recovery fails,
record as much of the abort state as possible. A fresh coordinator session takes over through
`resume`.

### Resume a run

`resume <RUN>` names the run. `resume <RUNDIR>` names its run folder. Resolve a run name to the
worktree of that name in Orca's worktree list. When none exists, the run adopted a worktree. Find
the Orca worktree whose path holds `.agents/orca/orchestration/<RUN>/run-state.json`. Derive
`<RUNDIR>` as Phase 0 step 8 does. Stop when the worktree or `run-state.json` does not exist, or
when the recorded status is terminal.

Load the run mechanics as Phase 0 step 1 requires. Then read the following artifacts completely and
in order. Use `run-state.json` to skip artifacts from steps not yet reached. Recover missing
artifacts from completed steps before continuing.

1. `run-state.json`;
2. `summary.md`;
3. the brief and plan at their recorded `artifacts` paths, including referenced design assets;
4. every agent task and report under `tasks/`;
5. every review under `review/` and `review.html` when present;
6. the `scratch/` reports of the recorded phase.

Then reconcile the manifest with live state:

1. Use Git to establish which task branches have merged. Mark a task `merged` in the manifest only
   after integration verification passes.
2. Treat live Orca dispatch state as authoritative over manifest dispatch status.
3. Reconcile active and superseded dispatches through Orca Orchestration. Recover worker identities
   from live state and initialise missing manifest fields as `references/run-state.md` describes.
   Do not infer ownership from terminal titles.
4. Recover pending and previously consumed completion messages through Orca Orchestration before
   assigning more work. Record any follow-up task and dispatch identities.
5. Dispatch only unfinished work, using existing task-branch commits as context. Merge only branches
   not yet merged.
6. Resume plan critique from recorded input/output digests and consecutive round numbers. Complete
   any pending material revision's critique before approval. In Phases 6 through 8, retain the
   recorded round and fix-wave counts.
7. Check document and asset digests against both approval receipts before assigning more build or
   fix work. Missing or stale approval returns to the relevant human gate. Follow the legacy
   migration rules in `references/run-state.md`; never infer approval from an old opt-out flag.

Record the resumption and every reconciliation in `summary.md` and continue from the recorded phase.

When `status` is `awaiting_input`, present the open decision again and continue from step 5 of
[Pause for a critical decision](#pause-for-a-critical-decision) once the human answers.

### Handle the Orca circuit breaker

When Orca reports a circuit breaker, follow Orca Orchestration's recovery instructions. The
pipeline's retry allowance does not override Orca's recovery requirements. Record the blocker and
use [Pause for a critical decision](#pause-for-a-critical-decision) when human authorisation is
required. Preserve the recorded task and attempt history.

Never run `orca orchestration reset`. The orchestration store is shared with other runs.

## Orca runtime mechanics

Read `references/orca-mechanics.md` completely during Phase 0, after loading the `orchestration` and
`orca-cli` skills and before the first Orca mutation. Re-read the relevant heading when a phase needs it.

| Reference heading | Use |
|---|---|
| [1.0 Record run ownership](references/orca-mechanics.md#10-record-run-ownership) | Orca resource creation and recovery |
| [Use Orca Orchestration](references/orca-mechanics.md#20-use-orca-orchestration) | Every Orca worker operation and command failure |
| [Receive orchestration messages](references/orca-mechanics.md#30-receive-orchestration-messages) | Every worker wake and message batch |
| [4.0 Dispatch a phase worker](references/orca-mechanics.md#40-dispatch-a-phase-worker) | Every phase-worker dispatch; readiness and command failure for every worker |
| [5.0 Collect a phase worker](references/orca-mechanics.md#50-collect-a-phase-worker) | Every phase-worker collection and the read-only check |
| [Retry a phase worker](references/orca-mechanics.md#60-retry-a-phase-worker) | Confirmed failed attempts and settled dispatches with missing reports |
| [Manage terminals and worktrees](references/orca-mechanics.md#70-manage-terminals-and-worktrees) | Worker cleanup and reuse, worktree cleanup, branch preservation, and teardown |
| [8.0 Operational safety](references/orca-mechanics.md#80-operational-safety) | Every mutation, cleanup, push, and PR action |
