---
name: git-commit
description: "Create git commits: stage what was asked, detect the repository's commit style from its history, and draft the message in that style (Conventional Commits, Scoped Commits, or Plain Commits; scoped is the default when unclear). Use when asked to commit, stage and commit, or draft, rewrite, or suggest a commit message."
---
## Message drafts

For a message draft, read the requested diff, sample the repository's commit style, and
follow Style detection and Shared message rules below, including the matching style reference.
Return the message without staging or committing. Use the Workflow below only when asked to commit.

## Workflow

Existing authorisation to commit remains sufficient.

**Commit exactly what the user staged or asked to commit.** When scope is ambiguous
(e.g. the user said "commit my changes" with both staged and unstaged work present, or nothing staged),
ask which to include and wait for an answer. Stage anything the user asked to commit that is not yet staged.

1. Run `git status`, `git log -30 --no-merges --pretty=%s`, and `git diff --cached --stat` to inspect what is staged and sample the repository's existing commit style.
2. Classify the style with **Style detection** below, then read the matching reference: [`references/conventional.md`](references/conventional.md), [`references/scoped.md`](references/scoped.md), or [`references/plain.md`](references/plain.md).
3. Read the full diff of the selected changes and draft the message in the detected grammar,
following the shared rules below.
4. Commit only the selected changes. Preserve unrelated changes and their staging state,
including partial staging. Use the command below only when the index contains exactly the
selected changes:

```bash
git commit -m "<subject>"
```

When the message needs a body or trailers, use a heredoc so blank lines and quoting survive:

```bash
git commit -m "$(cat <<'EOF'
<subject>

<body>

<trailers>
EOF
)"
```

5. Verify with `git log -1`: pre-commit hooks can rewrite or reject the message.

## Style detection

Decide which grammar the repository uses, in this order:

1. **The user names a style**: use it.
2. **The repo declares one** (CONTRIBUTING.md, commitlint or semantic-release config): read and follow it.
3. **Infer from the sampled subjects**:
   - a clear majority start with a Conventional type prefix — `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `revert` — optionally with `(scope)` and/or `!` before the colon → conventional;
   - a clear majority start with any other `<scope>:` prefix → scoped;
   - a clear majority have no prefix → plain.
4. **Empty history, mixed signals, or anything genuinely unclear** → scoped. Scoped is the default; it takes this role only when no better evidence exists.

## Shared message rules

- **Write for a reader who knows the codebase and never saw the session.** Use the names the
  code and the log already use. Refer to work by what it changes. Phase, step, task, and
  iteration labels from the session stay out of the message.
- **Subject ≤72 chars total**, imperative mood ("add", not "added"), lowercase first letter unless the style reference or the project's log shows otherwise, no trailing period.
- **The description completes "This commit will …"** and states the change in behaviour, for
  example `stop the list rewriting its URL on every render` rather than
  `add a ref guard to the URL effect`.
- **Default to a subject only.** Before adding a body, ask whether it provides important context
  the subject cannot convey. If not, omit it. Keep any body within 500 characters total, wrapped
  at ~72 characters per line. The limit is a ceiling, not a target.
- **A body states the cause, then the change.** First what was wrong or missing, with the
  concrete symptom such as the error text or the triggering condition. Then what the code does
  now. Leave what the diff shows to the diff.
- **Trailers** for non-obvious metadata (tickets, co-authors); their exact form is style-specific — see the reference.
- **Mark breaking changes**; the marking mechanism differs per style — see the reference.

