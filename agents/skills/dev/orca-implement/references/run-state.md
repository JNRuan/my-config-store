# Run state

`<RUNDIR>/run-state.json` is the durable manifest for one `/orca-implement` run. It records
coordinator decisions, Orca resource ownership, task progress, review progress, and cleanup.

Update it after every state transition and before the next Orca mutation. The checkpoint rule in
SKILL.md commits it at the boundaries it lists.

## Run phases

| Phase | Enter when |
|---|---|
| `setup` | Phase 0 initialises the manifest |
| `scout` | Phase 1 starts |
| `understanding` | Phase 2 starts |
| `plan` | Phase 3 starts |
| `plan_gate` | Phase 4 starts for mandatory human approval of the final plan |
| `build` | Phase 5 starts |
| `verification` | Phase 6 starts |
| `code_review` | Phase 7 starts |
| `qa` | Phase 8 starts, including a policy skip |
| `pr` | Phase 9 starts |

Set `phase` before starting that phase's work.

Fix tasks do not change the phase. A review fix remains in `code_review`; a QA fix remains in `qa`.

On failure or blockage, preserve the phase where the run stopped. Use `status` to record the
outcome.

## Run statuses

| Status | Meaning |
|---|---|
| `active` | The pipeline is still running, including while it awaits workers |
| `awaiting_input` | The run is paused for a human decision recorded in `decisions` |
| `pr` | The PR is open and its URL is recorded |
| `failed` | Setup failed, or no build task merged |
| `blocked` | The human rejected the brief or cancelled the run |

`pr`, `failed`, and `blocked` are terminal pipeline statuses. `awaiting_input` is not; `resume`
continues it.

Do not use `shipped`. The pipeline does not observe merge or deployment.

## Policy values

### Tiers

These fields accept `pending`, `low`, `medium`, `high`, or `xhigh`:

- `plan_review_tier`;
- `run_complexity`.

### Caps

`code_review_cap` accepts `pending`, `1`, `2`, `3`, or `5`.

### QA policy

`qa_policy` accepts:

- `pending`;
- `skip`;
- `run`.

Read final caps and QA policy from `references/routing.md`.

Keep plan metadata, the plan's Review Policy, and these manifest fields synchronised.

## Base and start refs

`base_ref` is the PR target. `start_ref` is the branch the run built on, or null when the run
started from `base_ref`. `base_sha` is `git rev-parse base_ref` when `start_ref` is null or equal to
`base_ref`, and `git merge-base base_ref start_ref` otherwise. `integration_worktree.origin` is
`created` or `adopted`.

## Build-task statuses

Build and fix tasks use:

| Status | Meaning |
|---|---|
| `pending` | Registered, but at least one dependency is not merged |
| `ready` | Every dependency is merged and the task can dispatch |
| `dispatched` | An active dispatch owns the task |
| `completed` | The active attempt reported success with its required report; verification is pending |
| `merged` | Verification passed and the task branch merged |
| `failed` | The task cannot continue |

Allowed transitions:

```text
pending -> ready
ready -> dispatched
dispatched -> completed
completed -> merged
completed -> dispatched  follow-up fix cycle
dispatched -> ready      confirmed recovery before reassignment
pending -> failed        dependency failed
ready -> failed
dispatched -> failed
completed -> failed
```

`merged` and `failed` are terminal task states.

A dependant becomes `ready` only when every dependency is `merged` in the manifest. Orca's completed
status alone is not enough.

A replacement can change the active task, dispatch, and worker identities while the pipeline task
remains `dispatched`. Preserve the original pipeline identity and dependency edges.

## Phase-dispatch statuses

Scout, fact-check, planner, critic, acceptance-check, reviewer, and security-reviewer dispatch
records, and `qa.dispatch_status`, use:

- `pending`;
- `dispatched`;
- `completed`;
- `failed`;
- `superseded`.

A completed phase dispatch requires a successful outcome and its designated report from the active
attempt to exist and be non-empty. Record a QA policy skip in the QA record, not as a fake dispatch.

## Initial manifest

Phase 0 creates the manifest with these top-level fields:

```json
{
  "schema_version": 3,
  "run_name": "<RUN>",
  "orca_run_id": "<ORCA_RUN_ID>",
  "source": "<NORMALISED_SOURCE>",
  "started_at": "<ISO_8601_UTC>",
  "phase": "setup",
  "status": "active",
  "base_ref": "<BASE_REF>",
  "start_ref": null,
  "base_sha": "<BASE_SHA>",
  "plan_review_tier": "pending",
  "run_complexity": "pending",
  "code_review_cap": "pending",
  "qa_policy": "pending",
  "artifacts": {
    "brief": "plan/brief.html",
    "plan": "plan/plan.html",
    "review": "review.html"
  },
  "approvals": {"brief": null, "plan": null},
  "approval_history": [],
  "pr_draft": false,
  "replans": 0,
  "decisions": [],
  "review_fixes_applied": false,
  "code_review_complete": false,
  "plan_review": {
    "rounds": [],
    "rounds_run": 0,
    "stop_reason": null
  },
  "verification": {
    "fix_waves": 0,
    "post_review_fix_waves": 0,
    "evidence": []
  },
  "browser_verification": {
    "policy": "pending",
    "result": null
  },
  "run_page": {
    "title": null,
    "goal": null,
    "outcome": null,
    "constraints": []
  },
  "integration_worktree": {
    "id": "<WT>",
    "path": "<WT-PATH>",
    "branch": "<RUN-BRANCH>",
    "origin": "created"
  },
  "build_owned_task_ids": [],
  "tasks": [],
  "phase_dispatches": {
    "scouts": [],
    "fact_checks": [],
    "acceptance_checks": [],
    "planners": [],
    "critics": [],
    "code_reviewers": [],
    "security_reviewers": []
  },
  "review_rounds": [],
  "qa": {
    "status": "pending",
    "reason": null,
    "dispatch_status": "pending",
    "head": null,
    "task_id": null,
    "active_task_id": null,
    "follow_up_task_ids": [],
    "worker_handle": null,
    "worktree_id": null,
    "worktree_path": null,
    "branch": null,
    "terminal_handle": null,
    "dispatch_id": null,
    "superseded_dispatch_ids": [],
    "report_path": null,
    "review_path": null,
    "fix_waves": 0,
    "accepted_findings": {"critical": 0, "high": 0, "medium": 0}
  },
  "resources": {
    "terminals": [
      {
        "handle": "<HANDLE_RETURNED_BY_WORKTREE_CREATE>",
        "title": "<TITLE>",
        "role": "integration-worktree-startup",
        "worktree_id": "<WT>",
        "status": "open"
      }
    ],
    "worktrees": [
      {
        "id": "<WT>",
        "path": "<WT-PATH>",
        "branch": "<RUN-BRANCH>",
        "kind": "integration",
        "status": "active"
      }
    ]
  },
  "cleanup": {
    "status": "pending",
    "remaining_dispatch_ids": [],
    "remaining_terminal_handles": [],
    "remaining_worktree_ids": []
  },
  "pr_url": null
}
```

Repeat the terminal record for every terminal returned by integration-worktree creation. If creation
returns none, use an empty array. Add every custom sandboxed launch before registering it as a
worker. Update a terminal to `closed` only after confirming it closed.

## Build-task record

Each entry in `tasks` contains:

```json
{
  "seq": "<SEQ>",
  "slug": "<SLUG>",
  "kind": "build",
  "origin_phase": "build",
  "origin_round": null,
  "task_id": "<TASK_ID>",
  "active_task_id": "<TASK_ID>",
  "follow_up_task_ids": [],
  "worker_handle": null,
  "dependency_task_ids": [],
  "worktree_id": null,
  "worktree_path": null,
  "branch": null,
  "starting_commit": null,
  "merge_commit": null,
  "terminal_handle": null,
  "terminal_title": null,
  "model": null,
  "effort": null,
  "active_dispatch_id": null,
  "superseded_dispatch_ids": [],
  "worker_attempt": 1,
  "verify_fix_cycles": 0,
  "resolve_verify_cycles": 0,
  "agent_task_path": null,
  "report_path": null,
  "status": "ready"
}
```

A task with no dependencies starts `ready`. A task with unmerged dependencies starts `pending`.

Keep `task_id`, `dependency_task_ids`, and membership in `build_owned_task_ids` stable for the
pipeline task. Record the current Orca Task in `active_task_id`. Retain every different Task id
returned for this pipeline task in `follow_up_task_ids`, including replacement work when Orca
requires a new Task. Correlate messages with `active_task_id` and `active_dispatch_id`.

Before replacing `active_dispatch_id`, retain its previous value in `superseded_dispatch_ids`.
Reconcile any failure or resource state from an older attempt without treating its report as the
current attempt's result. A failed attempt does not by itself make the pipeline task permanently
`failed` while an authorised recovery or follow-up remains.

Record the worker handle Orca returns. Fill terminal fields only when Orca identifies a terminal.
Use Orca Orchestration to recover worker identity after a restart. Treat terminal titles as metadata,
not proof of identity or ownership.

A fix task uses `"kind": "fix"` and records the phase and round that produced it.

`worker_attempt` is 1 for the original worker and 2 for its single replacement. `verify_fix_cycles`
counts cycles for the current attempt. When moving from attempt 1 to 2, reset `verify_fix_cycles`
to 0. Save both values before starting the replacement. Resuming an attempt preserves both values.

Increment `resolve_verify_cycles` on the original task for each conflict-resolution task registered
for it.

Fill resource, routing, dispatch, and artifact fields when those values become known. Never derive
them later from names. Set `merge_commit` to the merge commit on `<RUN-BRANCH>` when the task is
finalised.

## Phase-dispatch record

Each entry in `phase_dispatches` contains:

```json
{
  "role": "<ROLE>",
  "round": null,
  "start_head": null,
  "task_id": "<TASK_ID>",
  "active_task_id": "<TASK_ID>",
  "follow_up_task_ids": [],
  "worker_handle": "<WORKER_HANDLE>",
  "terminal_handle": null,
  "terminal_title": null,
  "model": "<MODEL>",
  "effort": "<EFFORT>",
  "active_dispatch_id": "<DISPATCH_ID>",
  "superseded_dispatch_ids": [],
  "report_path": "<ABSOLUTE_PATH>",
  "status": "dispatched"
}
```

Use `round` for critic and reviewer rounds. Leave it `null` for unrounded roles. Record a fact
check's `role` as `plan-fact-check-<CHECK>` and an acceptance check's `role` as
`acceptance-check-<PASS>`.

Use the build-task record's identity rules for active tasks, follow-ups, superseded dispatches, and
terminal metadata. Preserve each role and round's report path across its permitted recovery.

For a worker in `<WT>`, save the collection baseline `<H>` as `start_head` before dispatch.
Use the same baseline for every worker and retry in one collection batch.
Preserve it when the coordinator resumes.
Leave `start_head` null for workers outside `<WT>`.

## Artefacts and approvals

`artifacts` holds run-relative paths. Resolve worker `<BRIEF_PATH>` and `<PLAN_PATH>` to absolute
paths from these fields rather than assuming a filename. New or revised human documents use HTML.
Keep authoring templates, task packets, reports, and summaries in Markdown.

`approvals.brief` and `approvals.plan` are null until the human approves the exact document and its
referenced assets. Each receipt has this shape:

```json
{
  "path": "plan/plan.html",
  "document_sha256": "<SHA256>",
  "assets": [
    {"path": "plan/assets/design.png", "sha256": "<SHA256>"}
  ],
  "approved_at": "<ISO_8601_UTC>",
  "review": {
    "method": "<mapped skill name or conversation>",
    "identity": "<returned session or review identity, or explicit approval message reference>",
    "evidence_path": "<review receipt path or null>"
  },
  "brief_receipt_sha256": "<SHA256 of the approved brief receipt, or null for brief approval>"
}
```

Hash the exact file bytes with SHA-256. Inventory each document's local asset dependencies,
including linked design documents that form part of the approval and transitive stylesheet or
image dependencies. Inline content is covered by the document digest. Keep approval material local
and stable, or record an immutable external revision with its provenance. Do not add unrelated
files to the inventory merely because they share `plan/assets/`.

Compute `brief_receipt_sha256` from the approved brief receipt encoded as UTF-8 JSON with sorted
keys and separators `(',', ':')`. This binds plan approval to the brief document and asset revisions.
The mapped human-review skill owns review mechanics and returned identities. Record its actual
receipt, or the explicit conversational approval evidence when unavailable. An unrelated empty
session is not approval. Include any explicitly approved missing-critic coverage in that evidence.

Before editing an approved document or its referenced assets, append its receipt to
`approval_history` with `artifact`, `receipt`, `invalidated_at`, and `reason`, then clear its active
approval. Invalidating the brief also invalidates the plan. Preserve the prior approved version
through its checkpoint or review history; if neither holds it, save a run-owned copy under
`scratch/` before editing. Never update a receipt to claim approval of changed bytes. Store approval
status in the manifest rather than editing an approved page to add an approval badge.

Require current brief and plan receipts before dispatching build or fix work. Recompute digests on
resume and before continuing after a revision. Any changed document or referenced asset needs
renewed human approval. Only material changes require another critic round, as Phase 3 defines.

## Plan-review record

Each entry in `plan_review.rounds` contains:

```json
{
  "round": 1,
  "start_head": "<SHA>",
  "trigger": "<initial plan or reason for revision>",
  "snapshot_path": "scratch/plan-pre-critique-r1.html",
  "input": {"document_sha256": "<SHA256>", "assets": []},
  "output": {"document_sha256": "<SHA256>", "assets": []},
  "critique_reports": [],
  "accepted_findings": {"blocking": 0, "risky": 0, "note": 0},
  "missing_lenses": [],
  "plan_changed": false,
  "material_change": false,
  "change_reason": null
}
```

Set `accepted_findings` at triage to counts by severity and `missing_lenses` when an in-round
retry fails. Record whether features, approach, proposed fixes, contracts, scope, or safety
assumptions changed materially, with the reason. Count fact-check corrections in that assessment.
Use the approval asset-inventory shape for input and output, hashing the actual plan dependencies.
Set output only after triage and fact-checking finish. Compare digests on resume to identify an
unfinished or subsequently changed revision. A snapshot in `scratch/` retains the plan's original
asset-resolution base under `plan/`; resolve asset paths from the actual plan, not the snapshot.

`rounds_run` counts collected rounds across the run, not just the current revision. Continue with
both critics whenever material changes require it, including fixes to previous critics' findings.
`stop_reason` accepts `critique complete`, `all critics failed`, or `awaiting decision`. The last
one pauses a repeated unresolved disagreement and does not complete critique. Preserve the original
tier, prior rounds, stable `PF-n` findings, and their dispositions when resuming critique.

## Verification record

`verification.fix_waves` counts Phase 6 fix waves. `verification.post_review_fix_waves` counts the
post-review verification fix waves in Phase 7. Each has its own limit of three.

Append each check to `verification.evidence` with this shape:

```json
{
  "head": "<code HEAD at the check>",
  "dirty": false,
  "scope": ["AC-1", "C-1"],
  "check": "<command or inspection performed>",
  "result": "<passed, failed, or not verified>",
  "evidence_path": "<report or screenshot path>",
  "recorded_at": "<ISO_8601_UTC>"
}
```

Record implementation HEAD independently of later bookkeeping checkpoints. If implementation files
were dirty, record `dirty=true` with the patch or tree digest identifying the checked contents.
Unverified behaviour needs its reason in the evidence. Carry scoped evidence forward only when its
inputs are unaffected, retaining its original code revision. Use review-round `start_head` for code
actually reviewed. Do not relabel old results as proof of a newer revision. Summarise differences
between approved, delivered, reviewed, and verified revisions in the final human review.

`run_page.title`, `goal`, `outcome`, and `constraints` supply status-page display data independently
of document layout. Set title, goal, and the human-readable constraint list when approving the brief.
Keep goal and outcome under 512 characters. Set outcome when the run ends to explain what the PR
delivers or what failed. The status page is not an approval interface.

`browser_verification.policy` accepts `pending`, `run`, or `not_needed`. Set it in Phase 6.
`browser_verification.result` accepts `null`, `passed`, `failed`, or `not verified`, recorded from
the round 1 browser report or the latest scoped rerun.

## Review-round record

Each entry in `review_rounds` contains:

```json
{
  "round": 1,
  "start_head": "<SHA>",
  "code_reviewer_reports": [],
  "security_reviewer_reports": [],
  "missing_lenses": [],
  "security_lenses_run": true,
  "security_skip_reason": null,
  "browser_result": null,
  "review_path": null,
  "fix_waves": 0,
  "severe_fix_merged": false,
  "accepted_findings": {
    "code": {"critical": 0, "high": 0, "medium": 0},
    "security": {"critical": 0, "high": 0, "medium": 0},
    "browser": 0
  },
  "stop_reason": null
}
```

Set `accepted_findings` at triage to the counts of findings you accepted, by source and severity; a
browser failure counts once. Add a lens to `missing_lenses` when its in-round retry fails. Set
`security_lenses_run=false` with `security_skip_reason` when `run_complexity` is `low`, or when the
Phase 7 security trigger does not fire for a later round. Set `browser_result` in round 1 only.
`stop_reason` accepts `no accepted fixes`, `no severe findings`, or `cap reached`.

`fix_waves` counts the round's review fix waves. Set `review_fixes_applied=true` after any review
fix, Medium included, merges and passes verification. Only a Critical or High fix sets
`severe_fix_merged`.

Set `code_review_complete=true` only after the review loop and any required post-review verification
finish.

## QA record

`qa.status` accepts:

- `pending`;
- `skipped`;
- `completed`;
- `not_verified`.

For a policy skip:

```json
{
  "status": "skipped",
  "reason": "run complexity policy"
}
```

For a QA run, record `head`, task, worktree, branch, worker identity, any terminal metadata, dispatch,
report, review, and fix-wave count as each becomes known. Use the build-task identity rules, with
`qa.dispatch_id` as the active dispatch id. `qa.dispatch_status` uses the phase-dispatch statuses and
tracks the worker dispatch separately from the QA outcome.

Set `completed` only after report collection, triage, accepted fixes, and required verification
finish.

Use `not_verified` when the worker fails or the required report is missing. Record the exact reason.

## Resource records

Worker resources are tracked by the active and superseded dispatch ids in build, phase, and QA
records. Use Orca Orchestration to inspect their live state and release or retain them.

Each terminal resource contains:

```json
{
  "handle": "<HANDLE>",
  "title": "<TITLE>",
  "role": "<ROLE>",
  "worktree_id": "<WORKTREE_ID>",
  "status": "open"
}
```

Terminal status accepts `open` or `closed`.

Each worktree resource contains:

```json
{
  "id": "<WORKTREE_ID>",
  "path": "<ABSOLUTE_PATH>",
  "branch": "<BRANCH>",
  "kind": "integration",
  "status": "active"
}
```

Worktree kind accepts:

- `integration`;
- `task`;
- `qa`.

Worktree status accepts:

- `active`;
- `removed`;
- `retained`.

At PR state, the integration worktree is `retained`. Remove task and QA worktrees only when cleanup
is confirmed safe. Retain any whose worker state or ownership is unresolved and mark cleanup partial.

## Cleanup state

`cleanup.status` accepts:

- `pending`;
- `complete`;
- `partial`.

Set `complete` only when Orca Orchestration confirms no removable run-owned worker resources remain,
every separately recorded run-owned terminal is closed, and every removable worktree is gone. The
retained integration worktree does not make cleanup partial.

Record unresolved worker attempts in `remaining_dispatch_ids`, separate terminals in
`remaining_terminal_handles`, and retained task or QA worktrees in `remaining_worktree_ids`.
Retention or an unknown release result never means a resource closed.

## Decision record

Each entry in `decisions` records one decision required from the human:

```json
{
  "id": "D-1",
  "raised_at": "<ISO_8601_UTC>",
  "source": "<task title, phase, or review round>",
  "question": "<the question as presented>",
  "held_tasks": [],
  "answer": null,
  "answered_at": null
}
```

`held_tasks` lists the build-owned task ids the decision holds. Release them when the answer is
recorded.

## Resume earlier manifests

Leave completed historical runs unchanged. For an active older run, initialise missing `pr_draft`,
`replans`, and `decisions` to their initial values. Recover artefact paths from the actual run,
including existing `plan/brief.md` and `plan/plan.md`. Keep those paths until a document needs
revision, then write its HTML replacement and update `artifacts` and every affected task packet.

Initialise missing approval, history, and verification-evidence fields. Recover approval only when
existing receipts or explicit human approval identify the exact document and asset revision. If
that cannot be proved, return to the appropriate human gate before dispatching more build or fix
work. An old `plan_gate=false` never bypasses approval. Remove that boolean after reconciliation.
Populate run-page display fields from the actual brief once, rather than parsing arbitrary HTML.

When resuming a schema 1 manifest, reconcile its recorded task and dispatch ids through Orca
Orchestration before assigning more work. Initialise missing `active_task_id` from the reconciled
Task, missing follow-up and superseded-id lists as empty, and `remaining_dispatch_ids` as empty.
Recover worker handles from Orca state or receipts rather than copying a terminal title or guessing
a handle. Leave a missing worker handle null and inspect the recorded dispatch through Orca
Orchestration.
Keep terminal records as ownership evidence. If live state or history reveals a follow-up, record
its returned identities before continuing. Set `schema_version` to 3 after resource, artefact, and
approval reconciliation. Retain missing approval as null until the required human gate completes.

## PR state

When Phase 9 starts:

```json
{
  "phase": "pr",
  "status": "active"
}
```

After the PR opens and teardown completes:

```json
{
  "phase": "pr",
  "status": "pr",
  "pr_url": "<URL>",
  "pr_draft": false
}
```

Set `pr_draft` to true whenever the run lists an item under Remaining because a fix-wave limit was
reached, a task failed permanently, or code review could not run. Phase 9 then opens the PR as a
draft.

The integration worktree remains retained until the human removes it after merge.

## Failure and blocker state

On failure or blockage:

1. preserve the current `phase`;
2. set `status` to `failed` or `blocked`;
3. record failed tasks and cleanup results;
4. keep the integration worktree and run branch;
5. write the final manifest to disk;
6. commit the abort checkpoint when no worker can still write, as the checkpoint rule requires.

## Recovery authority

The manifest owns resource identity and coordinator intent. Git and Orca own live execution facts.
Resume a run as SKILL.md describes.
