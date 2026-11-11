# Plain Commits

A commit message whose subject is one imperative sentence with no prefix.

```
<description>

[optional body]

[optional trailer(s)]
```

- **description**: starts with a capitalised imperative verb, unless the project's log shows
  otherwise.
- **trailers**: `Co-authored-by: Name <email>`, `BREAKING: <description>`.

## Naming the area

With no prefix, the sentence carries the area. Name the component, page, or command the change
affects when the verb alone leaves it unclear, for example
`Keep long names inside the filter panel` rather than `Fix overflow`.

## Ticket references

Match the log. When its subjects end in a ticket ID, add one the same way, for example
`Stop the list rewriting its URL (ABC-123)`, and count it towards the subject limit. Otherwise
put the ticket in a trailer.

## Examples

Subject only:

```
Make session cleanup idempotent so worktree removal stops crashing
```

With a trailing ticket:

```
Limit concurrent test jobs on build servers (ABC-123)
```

With body and trailer:

```
Deploy amd64 images regardless of the deploying machine

Deployments used the architecture of the machine running them. On an
arm64 machine the task was registered as ARM64, but the base images
are pinned to amd64, so it failed with "exec format error".

Deployments now always register the task as X86_64.

BREAKING: arm64 task definitions are no longer produced
```
