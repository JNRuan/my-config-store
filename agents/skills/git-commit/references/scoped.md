# Scoped Commits

A commit message format that puts the most useful information (*what area of the codebase*) at the front, so contributors and incident responders can scan the log fast.

```
<scope>: <description>

[optional body]

[optional trailer(s)]
```

- **scope**: the subsystem, area, or module touched (e.g., `auth`, `net/http`, `i2c: virtio`, `global`, `packages`)
- **trailers**: metadata in this style's forms (`TICKET-123` bare, `Co-authored-by: Name <email>`, `BREAKING: <description>`)

## Identifying the scope

Inspect the diff or files in play:

- One subsystem → use it (`auth`, `compiler`, `cli`)
- Nested path → include parents for clarity: `i2c: virtio: ...` (Linux style)
- Two clear scopes → comma-separated: `cli, config: ...`
- Many areas, no clear primary → `global`
- Pure revert/merge/fixup → freeform, follow project style
- Multi-scope is a last resort: if a unifying general scope exists, use that

## Trailers

Add trailers for non-obvious metadata:

- Ticket refs: in body or as trailer (`TICKET-123`); match project preference
- Co-authors: `Co-authored-by: Name <email>`
- Breaking changes: `BREAKING: <description>` or in body

## Pitfalls

- **Don't pad the description**: "fixed a bug in the authentication system" should be `auth: fix login bug`.
- **Don't over-nest the scope**: two levels is usually enough. `auth: oauth:` is fine; `auth: oauth: google: handlers: login:` is too much. A path scope like `net/http` is a single scope naming a package, not nesting.
- **Defer to the project's existing style** for case, nesting depth, and trailer placement.

## Examples

Single scope:

```
auth: fix race in token refresh
```

Nested:

```
i2c: virtio: mark device ready before registering the adapter
```

Multi-scope:

```
cli, config: align --verbose flag handling
```

With body and trailer:

```
api: rate-limit /v1/login to 5 req/min

- 100 req/min was abused to enumerate credentials
- now 5 req/min per IP for unauthenticated requests
- soft bump to 20 once a valid session exists

TICKET-4821
```

Repo-wide:

```
global: bump minimum Node version to 20
```

Version bump (nixpkgs style):

```
packages: xwayland: 24.1.11 -> 24.1.12
```
