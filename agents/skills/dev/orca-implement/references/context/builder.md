# Builder context

## Load when

Read this file in Phase 5 before registering build tasks or writing an agent task. Reuse it for every build and fix task.

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

The Orca task spec contains only a stable pointer to the agent task:

```text
Run <RUN> task {seq}-{slug}. Read your full agent task first:
<RUNDIR>/tasks/{seq}-{slug}-agent-task.md (absolute path).
```

## Create the agent task

Create `<RUNDIR>/tasks/{seq}-{slug}-agent-task.md` in the shape of `references/templates/agent-task-template.md` immediately before dispatch. Wait until the task worktree exists and every dependency output is known.

Resolve every value before writing:

- absolute worktree and report paths;
- captured branch names;
- dependency outputs;
- pinned contracts;
- project commands.

Do not leave a placeholder that the worker must infer.
