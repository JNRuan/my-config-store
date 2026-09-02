# Run state

`<RUNDIR>/run-state.json` is the durable manifest for one `/orca-implement` run. It records coordinator decisions, Orca resource ownership, task progress, review progress, and cleanup.

Update it after every state transition and before the next Orca mutation. Commit it at each phase boundary.

## Run phases

| Phase | Enter when |
|---|---|
| `setup` | The manifest is initialised in Phase 0 |
| `scout` | Phase 1 starts |
| `understanding` | Phase 2 starts |
| `plan` | Phase 3 starts |
| `plan_gate` | Phase 4 starts |
| `build` | Phase 5 starts |
| `verification` | Phase 6 starts |
| `code_review` | Phase 7 starts |
| `qa` | Phase 8 starts, including a policy skip |
| `pr` | Phase 9 starts |

Set `phase` before starting that phase's work.

Fix tasks do not change the phase. A review fix remains in `code_review`; a QA fix remains in `qa`.

On failure or blockage, preserve the phase where the run stopped. Use `status` to record the outcome.

## Run statuses

| Status | Meaning |
|---|---|
| `active` | The pipeline is still running |
| `pr` | The PR is open and its URL is recorded |
| `failed` | Implementation or verification could not complete |
| `blocked` | Progress needs a human-owned decision or external prerequisite |

`pr`, `failed`, and `blocked` are terminal pipeline statuses.

Do not use `shipped`. The pipeline does not observe merge or deployment.

## Policy values

### Tiers

These fields accept `pending`, `low`, `medium`, `high`, or `xhigh`:

- `plan_review_tier`;
- `run_complexity`.

### Caps

These fields accept `pending`, `1`, `2`, `3`, or `5`:

- `plan_review_cap`;
- `code_review_cap`.

### QA policy

`qa_policy` accepts:

- `pending`;
- `skip`;
- `run`.

Read final caps and QA policy from `references/routing.md`.

Keep plan frontmatter, the plan's Review Policy, and these manifest fields synchronised.

## Build-task statuses

Build and fix tasks use:

| Status | Meaning |
|---|---|
| `pending` | Registered, but at least one dependency is not merged |
| `ready` | Every dependency is merged and the task can dispatch |
| `dispatched` | An active dispatch owns the task |
| `completed` | `worker_done` was accepted; coordinator verification is pending |
| `merged` | Verification passed and the task branch merged |
| `failed` | The task cannot continue |

Allowed transitions:

```text
pending -> ready
ready -> dispatched
dispatched -> completed
completed -> merged
completed -> ready       fix cycle
dispatched -> ready      recovered or replaced worker
pending -> failed        dependency failed
ready -> failed
dispatched -> failed
completed -> failed
```

`merged` and `failed` are terminal task states.

A dependant becomes `ready` only when every dependency is `merged` in the manifest. Orca's completed status alone is not enough.

## Phase-dispatch statuses

Scout, fact-check, planner, critic, reviewer, and security-reviewer dispatch records, and `qa.dispatch_status`, use:

- `pending`;
- `dispatched`;
- `completed`;
- `failed`;
- `superseded`.

A completed phase dispatch requires its designated report to exist and be non-empty. QA policy skips are recorded in the QA record, not as fake dispatches.

## Initial manifest

Phase 0 creates the manifest with these top-level fields:

```json
{
  "schema_version": 1,
  "run_name": "<RUN>",
  "orca_run_id": "<ORCA_RUN_ID>",
  "source": "<NORMALISED_SOURCE>",
  "started_at": "<ISO_8601_UTC>",
  "phase": "setup",
  "status": "active",
  "base_ref": "<BASE_REF>",
  "base_sha": "<BASE_SHA>",
  "plan_review_tier": "pending",
  "plan_review_cap": "pending",
  "run_complexity": "pending",
  "code_review_cap": "pending",
  "qa_policy": "pending",
  "review_fixes_applied": false,
  "code_review_complete": false,
  "plan_review": {
    "rounds": [],
    "rounds_run": 0,
    "stop_reason": null
  },
  "verification": {
    "fix_waves": 0,
    "post_review_fix_waves": 0
  },
  "integration_worktree": {
    "id": "<WT>",
    "path": "<WT_PATH>",
    "branch": "<RUN_BRANCH>"
  },
  "build_owned_task_ids": [],
  "tasks": [],
  "phase_dispatches": {
    "scouts": [],
    "fact_checks": [],
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
    "worktree_id": null,
    "worktree_path": null,
    "branch": null,
    "terminal_handle": null,
    "dispatch_id": null,
    "report_path": null,
    "fix_waves": 0
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
        "path": "<WT_PATH>",
        "branch": "<RUN_BRANCH>",
        "kind": "integration",
        "status": "active"
      }
    ]
  },
  "cleanup": {
    "status": "pending",
    "remaining_terminal_handles": [],
    "remaining_worktree_ids": []
  },
  "pr_url": null
}
```

Repeat the terminal record for every terminal returned by integration-worktree creation. If creation returns none, use an empty array. Update a terminal to `closed` after closing it.

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
  "dependency_task_ids": [],
  "worktree_id": null,
  "worktree_path": null,
  "branch": null,
  "starting_commit": null,
  "terminal_handle": null,
  "terminal_title": null,
  "model": null,
  "effort": null,
  "active_dispatch_id": null,
  "superseded_dispatch_ids": [],
  "verify_fix_cycles": 0,
  "resolve_verify_cycles": 0,
  "assignment_path": null,
  "report_path": null,
  "status": "ready"
}
```

A task with no dependencies starts `ready`. A task with unmerged dependencies starts `pending`.

A fix task uses `"kind": "fix"` and records the phase and round that produced it.

Increment `resolve_verify_cycles` on the original task for each conflict-resolution task registered for it.

Fill resource, routing, dispatch, and artifact fields when those values become known. Never derive them later from names.

## Phase-dispatch record

Each entry in `phase_dispatches` contains:

```json
{
  "role": "<ROLE>",
  "round": null,
  "task_id": "<TASK_ID>",
  "terminal_handle": "<HANDLE>",
  "terminal_title": "<TITLE>",
  "model": "<MODEL>",
  "effort": "<EFFORT>",
  "active_dispatch_id": "<DISPATCH_ID>",
  "superseded_dispatch_ids": [],
  "report_path": "<ABSOLUTE_PATH>",
  "status": "dispatched"
}
```

Use `round` for critic and reviewer rounds. Leave it `null` for unrounded roles.

## Plan-review record

Each entry in `plan_review.rounds` contains:

```json
{
  "round": 1,
  "start_head": "<SHA>",
  "critique_reports": [],
  "missing_lenses": [],
  "plan_changed": false
}
```

Add a lens to `missing_lenses` when its in-round retry fails. Set `rounds_run` and `stop_reason` when the critique loop stops. `stop_reason` accepts `no plan change`, `cap reached`, or `all critics failed`.

## Verification record

`verification.fix_waves` counts Phase 6 fix waves. `verification.post_review_fix_waves` counts the post-review verification fix waves in Phase 7. Each has its own limit of three.

## Review-round record

Each entry in `review_rounds` contains:

```json
{
  "round": 1,
  "start_head": "<SHA>",
  "code_reviewer_reports": [],
  "security_reviewer_reports": [],
  "missing_lenses": [],
  "synthesis_path": null,
  "fix_waves": 0,
  "code_changed": false,
  "stop_reason": null
}
```

Add a lens to `missing_lenses` when its in-round retry fails.

Set `review_fixes_applied=true` after any substantive review code or test fix merges and passes verification.

Set `code_review_complete=true` only after the review loop and any required post-review verification finish.

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

For a QA run, record `head`, task, worktree, branch, terminal, dispatch, report, and fix-wave count as each becomes known. `qa.dispatch_status` uses the phase-dispatch statuses and tracks the worker dispatch separately from the QA outcome.

Set `completed` only after report collection, triage, accepted fixes, and required verification finish.

Use `not_verified` when the worker fails or the required report is missing. Record the exact reason.

## Resource records

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

At PR state, the integration worktree is `retained`. Task and QA worktrees must be `removed`.

## Cleanup state

`cleanup.status` accepts:

- `pending`;
- `complete`;
- `partial`.

Set `complete` when every run-owned terminal is closed and every removable worktree is gone. The retained integration worktree does not make cleanup partial.

Record unresolved terminal handles or worktree ids when cleanup is partial.

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
  "pr_url": "<URL>"
}
```

The integration worktree remains retained until the human removes it after merge.

## Failure and blocker state

On failure or blockage:

1. preserve the current `phase`;
2. set `status` to `failed` or `blocked`;
3. record failed tasks and cleanup results;
4. keep the integration worktree and run branch;
5. commit the final manifest when possible.

## Recovery authority

The manifest owns resource identity and coordinator intent. Git and Orca own live execution facts.

During recovery:

- merge commits and task branches override stale task status;
- live Orca dispatch state overrides stale dispatch status;
- recorded round and fix-wave counts preserve spent limits;
- pending `worker_done` deliveries must be collected before new dispatches;
- work already committed or merged must not run again.
