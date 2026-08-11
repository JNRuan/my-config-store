# Assignment file

Written by the coordinator to `<RUNDIR>/tasks/{seq}-{slug}-assignment.md` immediately before dispatch, once its contents exist (worktree created, dependency outputs known). The Orca task spec is only a pointer to this file. Fill every section; give fully resolved absolute paths, captured branch names, and verbatim commands, never placeholders the worker must guess.

Fix cycles append to this file (see the final section); the worker re-reads it on every dispatch. A new fix task gets a new assignment file; the Fix cycles section covers only a task's own verify→fix re-dispatches.

Fix tasks (Phase 6 failures, review fixes, QA fixes, conflict resolution) use the same template with three substitutions: Objective & scope states the findings to fix, each with its reproduction or failing check output; The plan carries only the excerpts relevant to the fix (a fix task has no task-table section); Verification requirements are each finding's own reproduction plus the applicable project checks. A conflict-resolution objective names the branch to merge and requires a true `git merge` producing a merge commit; never rebase, cherry-pick, or reimplement.

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
Commit style:  {the repo's commit-message convention, from the plan}

## Worktree & branch

Worktree (absolute): {captured task worktree path}
Branch: {captured task branch name}

All work happens in this worktree. Anchor every shell command and file
operation to the absolute worktree path; `cd` in one command does not move
your session.

## Reporting

Commit all work in the commit style above. Write your full report to:

<RUNDIR>/tasks/{seq}-{slug}-report.md   (absolute path)

The report must include: commits (hashes and messages), files changed,
checks run with actual results, assumptions you resolved and how, and
anything incomplete or concerning. Report what actually happened, not what
was supposed to happen. That report file is the only file you may write
outside your worktree. Then report completion. If blocked, send an
escalation instead of improvising around the blocker.

## Fix cycles

{Absent initially. Each verify→fix cycle appends a dated subsection here:
the coordinator's findings, the failing checks with output, and what must
change. On re-dispatch, address the latest cycle's findings first.}
```
