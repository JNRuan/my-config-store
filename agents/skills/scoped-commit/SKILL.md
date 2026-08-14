---
name: scoped-commit
description: "Format git commit messages using the Scoped Commits standard. Use when drafting, rewriting, or suggesting commit messages. Deliberately NOT Conventional Commits: no type prefixes (feat/fix/chore). Counterpart to conventional-commit: if the project's log uses type prefixes, use that skill instead."
---
# Scoped Commits

A commit message format that puts the most useful information (*what area of the codebase*) at the front, so contributors and incident responders can scan the log fast.

## Delegation

Do not write the commit in the session model: dispatch one subagent to run the whole skill, and relay its result. Set model and effort per this table, choosing the column for the harness you are running in:


| Role                             | Claude                | Codex                                 | Other harness                                               |
| -------------------------------- | --------------------- | ------------------------------------- | ----------------------------------------------------------- |
| Commit worker (everything below) | Sonnet, medium effort | gpt-5.6-luna, medium reasoning effort | gpt-5.6-luna, medium reasoning effort; else session default |


- Resolve commit-scope ambiguity with the user before dispatching. Give the subagent exactly what to stage and commit, plus any intent from the session the message should carry.
- The subagent runs every step below, including staging and the commit. It reports the final message from `git log -1`.
- If the harness can't spawn subagents or set model and effort per call, run the steps below yourself. The table is an upgrade, not a requirement; never fail the task over it.

## Workflow

**Commit exactly what the user staged or asked to commit.** When scope is ambiguous (e.g. the user said "commit my changes" with both staged and unstaged work present, or nothing staged), ask which to include and wait for an answer. Stage anything the user asked to commit that is not yet staged.

**Follow these steps:**

1. Run `git status`, `git log --oneline -15`, and `git diff --cached --stat` to inspect what is staged and learn the project's existing scope names and style.
2. Read the full staged diff (`git diff --cached`) to draft a short commit message.
3. Construct your commit message as per conventions described for scoped commits.
4. Run the commit. Most commits need only the single-line form:

```bash
git commit -m "scope: description"
```

Add the optional body/trailer(s) only when the subject line can't carry the why; use a heredoc so blank lines and quoting survive:

```bash
git commit -m "$(cat <<'EOF'
scope: description

- why this change, in bullets
- another distinct point if needed

TICKET-123
EOF
)"
```

5. Verify with `git log -1`: pre-commit hooks can rewrite or reject the message.

## Format

```
<scope>: <description>

[optional body]

[optional trailer(s)]
```

- **scope**: the subsystem, area, or module touched (e.g., `auth`, `net/http`, `i2c: virtio`, `global`, `packages`)
- **description**: short, clear summary of the change; subject ≤72 chars total
- **body**: *why* this change, not *what*; bullet points only, ≤500 chars total, grouped under topic subheadings where useful, lines wrapped at ~72 (width only; a bullet may span several wrapped lines)
- **trailers**: metadata (`TICKET-123`, `Co-authored-by`, `BREAKING:`, etc.)

## Procedure

1. **Identify the scope** by inspecting the diff or files in play:
  - One subsystem → use it (`auth`, `compiler`, `cli`)
  - Nested path → include parents for clarity: `i2c: virtio: ...` (Linux style)
  - Two clear scopes → comma-separated: `cli, config: ...`
  - Many areas, no clear primary → `global`
  - Pure revert/merge/fixup → freeform, follow project style
2. **Write the description**:
  - Imperative mood ("add", not "added")
  - Lowercase first letter unless project style says otherwise
  - No trailing period
3. **Add a body only when it earns its place**: the *why* and trade-offs the subject can't carry, following the body rules in Format above. If you're over the ceiling, cut detail the diff shows or move it to the PR/ticket. Skip the body entirely when the subject says it all.
4. **Add trailers** for non-obvious metadata:
  - Ticket refs: in body or as trailer (`TICKET-123`); match project preference
  - Co-authors: `Co-authored-by: Name <email>`
  - Breaking changes: `BREAKING: <description>` or in body
5. **When in doubt, check the project's recent log**: the existing convention beats any rule.

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

## Pitfalls

- **Don't use Conventional Commits types** (`feat:`, `fix:`, `chore:`, `refactor:`). Scoped Commits deliberately omits them: the scope is the only prefix.
- **Don't make the body a rephrasing of the subject**: body is for *why* and context.
- **Don't over-nest the scope**: two levels is usually enough. `auth: oauth:` is fine; `auth: oauth: google: handlers: login:` is too much. A path scope like `net/http` is a single scope naming a package, not nesting.
- **Don't pad the description**: "fixed a bug in the authentication system" should be `auth: fix login bug`.
- **Don't auto-derive a changelog from the log**: different audiences, different formats.
- **Multi-scope is a last resort**: if you can find a unifying general scope, use that.
- **Defer to the project's existing style** for case, nesting depth, and trailer placement.
