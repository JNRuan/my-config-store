# Scout context

## Load when

Read this file in Phase 1 after selecting scout lenses and before composing scout tasks.

## Required values

Resolve:

- `<LENS>`: the lens name and scope;
- `<TASK_CONTEXT>`: the task's requirements, self-contained, from intake;
- `<RUNDIR>`;
- `<SLUG>`: the stable lens slug used by the task and report.

## Dispatch template

```text
Read-only scouting lens: <LENS>.

<TASK_CONTEXT>

Investigate the repository without changing implementation files. Cite path:line evidence for every repository claim. List every assumption you could not confirm, each with the resolution you would recommend and why. Write your full findings to <RUNDIR>/scratch/scout-<SLUG>.md. That report is the only file you may write. Then report completion.
```
