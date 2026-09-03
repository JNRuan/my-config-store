# Agent-task template

Write `<RUNDIR>/tasks/{seq}-{slug}-agent-task.md` in exactly this shape. The agent task is the worker's complete instruction for one task. The worker rereads it on every dispatch.

Braces mark what the coordinator fills. Text outside braces stays as written.

```markdown
---
run: {RUN}
task: {seq}-{slug}
kind: {build | fix}
origin: {plan | verification | review r<ROUND> | qa | conflict}
created: {ISO 8601 UTC}
modified: {ISO 8601 UTC}
---

# Agent task: {seq}-{slug}

## Objective & scope

{What this task must deliver, in one paragraph. Then its edges: what it must not touch, and what neighbouring tasks own.}

{For a fix task: each finding, failing check, or conflict this task resolves, with the failing command, its output, and the reproduction.}

{For conflict resolution: the branch to merge, and the instruction to merge it with a real `git merge` and a merge commit, never a rebase, cherry-pick, or reimplementation.}

## Plan excerpt

{The `### {seq}-{slug}` section of `plan/plan.md`, copied verbatim: What, Why, Deps / Inputs, Contracts, Constraints & Context, Relevant existing code, Verification requirements, Covers. Nothing else from the plan: no task table, no other task's section, no Orchestration section.}

{For a fix task: the plan material the fix touches, copied verbatim. The original task's section when fixing that task's code. The acceptance criterion a verification failure traced to.}

The full plan is at `<RUNDIR>/plan/plan.md` and the approved brief at `<RUNDIR>/plan/brief.md`. Read them for context. Build only this task.

## Inputs from completed tasks

{For each dependency task, what it produced that this task uses, taken from its report after merge: exported names, file paths, schema changes, decisions it made within its contracts. `None` when the task has no dependencies.}

## Contracts

{The pinned interfaces this task obeys or produces, copied verbatim from the plan's Contracts section: signatures, schemas, routes, types. Only the contracts this task's plan section names.}

Build against these as written. Do not reshape a contract to fit your implementation. If a contract cannot work as pinned, stop and escalate.

## Assumptions

- Validated: {each assumption scouting or a merged task confirmed, with its `path:line` evidence}
- Open, yours to verify: {each assumption the plan's Assumptions section names this task to verify. Confirm it against the code before building on it.}

## Verification requirements

{From this task's plan section, plus every Integration Verification boundary in the plan's Orchestration section that this task touches.}

1. Existing coverage to run (must stay green): {test files or commands}
2. Tests to add or update: {behaviours and scenarios, not test code}
3. Edge cases that must be covered: {behaviours}
4. Manual/visual checks: {steps, or `none`}

{For a fix task: replace the four items with each finding's exact reproduction, then the applicable project checks.}

## Project tooling

{Every command copied verbatim from the plan's Project Tooling section.}

Install:       {command}
Build:         {command or `none`}
Test:          {command}
Lint:          {command or `none`}
Typecheck:     {command or `none`}
Format check:  {command or `none`}
Format write:  {command or `none`}
Dev server:    {command and port, or `none`}
Commit style:  {the repository's commit-message convention, from the plan}

## Worktree & branch

Worktree (absolute): {task worktree path from the worktree-create response}
Branch: {task branch name captured from that worktree}

All work happens in this worktree. Anchor every shell command and file operation to the absolute worktree path. A `cd` in one command does not move your session.

## Reporting

Commit all work using the recorded commit style.

Write the full report to this absolute path:

<RUNDIR>/tasks/{seq}-{slug}-report.md

Include:

- commit hashes and messages;
- files changed;
- checks run and their actual results;
- assumptions resolved and the supporting evidence;
- incomplete or concerning work.

Report what happened, not what was expected.

The report is the only file you may write outside the task worktree. Then report completion. If blocked, send an escalation instead of working around the blocker.

## Fix cycles

{Absent until the first verify-to-fix cycle.}

On re-dispatch, address the latest cycle first.

### Cycle {n}: {ISO 8601 UTC}

- Findings: {what failed verification or fell short of the requirements}
- Output: {the failing command and its output}
- Required change: {what must change before the next report}

### Retry briefing: {ISO 8601 UTC}

{Present only when a replacement worker takes over.}

- What each cycle attempted: {...}
- Each failure and its output: {...}
- Cycle report paths: {...}
- Coordinator's diagnosis: {...}
- What the replacement must do differently: {...}
```

Append each verify-to-fix cycle under Fix cycles and update `modified`. The worker rereads the file on every dispatch.

A fix task gets its own agent task. Its Fix cycles section holds only its own redispatch history.
