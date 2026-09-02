# Builder context

## Load when

Read this file in Phase 5 before registering build tasks or writing an assignment. Reuse it for every build and fix task.

## Required values

Resolve:

- `<RUN>`;
- `<RUNDIR>`;
- `{seq}` and `{slug}`;
- the task worktree's absolute path and captured branch;
- dependency outputs;
- the approved plan and pinned contracts;
- project commands and commit style;
- verification requirements;
- the absolute report path.

## Orca task spec

The Orca task spec contains only a stable pointer to the assignment file:

```text
Run <RUN> assignment {seq}-{slug}. Read your full assignment first:
<RUNDIR>/tasks/{seq}-{slug}-assignment.md (absolute path).
```

## Create the assignment

Create `<RUNDIR>/tasks/{seq}-{slug}-assignment.md` immediately before dispatch. Wait until the task worktree exists and every dependency output is known.

Resolve every value before writing:

- absolute worktree and report paths;
- captured branch names;
- dependency outputs;
- pinned contracts;
- project commands.

Do not leave a placeholder that the worker must infer.

## Fix cycles

Append each verify-to-fix cycle to the task's existing assignment file. The worker rereads the file on every dispatch.

Create a new assignment file for a new fix task. A task's Fix cycles section contains only its own redispatch history.

## Fix-task substitutions

Phase 6 fixes, review fixes, QA fixes, and conflict-resolution tasks use the same template with these changes:

1. **Objective and scope** lists each finding, reproduction, or failing check with its output.
2. **The plan** contains only excerpts relevant to the fix. Omit the task table.
3. **Verification requirements** contain each finding's reproduction and the applicable project checks.

For conflict resolution, name the branch to merge and require a real `git merge` with a merge commit. Do not rebase, cherry-pick, or reimplement the conflicting changes.

## Assignment template

```markdown
# Assignment: {seq}-{slug}

## Objective & scope

What this task delivers and where its edges are. What is explicitly out of
scope for this task.

## The plan

{The plan.md content with the coordinator-only Orchestration section omitted,
and this task's section clearly marked as yours. Everything else is context:
read it, do not build it.}

## Inputs from completed tasks

{Outputs, decisions, or sync artifacts from dependency tasks that feed this
one. "None" if the task has no deps.}

## Contracts

{The pinned interfaces this task must obey or produce, verbatim from the
plan. Do not reshape a contract to fit your implementation; if a contract
cannot work as pinned, stop and escalate.}

## Assumptions

- Validated: {assumptions scouting confirmed, with evidence}
- Open, yours to verify: {assumptions this task must confirm against the
  actual code before implementing on them}

## Verification requirements

1. Existing coverage to run (must stay green): {...}
2. Tests to add or update: {...}
3. Edge cases that must be covered: {...}
4. Manual/visual checks: {... or "none"}

## Project tooling

Install:       {command}
Build:         {command or "none"}
Test:          {command}
Lint:          {command or "none"}
Typecheck:     {command or "none"}
Format check:  {command or "none"}
Format write:  {command or "none"}
Dev server:    {command and port, or "none"}
Commit style:  {the repo's commit-message convention, from the plan}

## Worktree & branch

Worktree (absolute): {captured task worktree path}
Branch: {captured task branch name}

All work happens in this worktree. Anchor every shell command and file
operation to the absolute worktree path. A `cd` in one command does not move
your session.

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

{Absent initially. Each verify-to-fix cycle appends a dated subsection here:
the coordinator's findings, the failing checks with output, and what must
change. On re-dispatch, address the latest cycle's findings first.}
```
