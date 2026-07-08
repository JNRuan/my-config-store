---
name: conventional-commit
description: "Format git commit messages using the Conventional Commits standard — type prefixes like feat/fix/chore, with optional scope. Use when drafting, rewriting, or suggesting commit messages in projects whose git log uses type prefixes. Counterpart to scoped-commit: if the project's log shows bare scopes with no types, use that skill instead."
---

## Workflow

You need to **commit exactly what the user staged or asked to commit.** When scope is ambiguous
(e.g. the user said "commit my changes" with both staged and unstaged work present, or nothing staged),
ask which to include and wait for an answer.

**Follow these steps:**

1. Run `git status`, `git log --oneline -15`, and `git diff --cached --stat` to inspect what is staged and learn the project's existing commit conventions (types and scopes in use).
2. Read the full staged diff (`git diff --cached`) to draft a succinct and simple commit message.
3. Construct the message using the structure below.
4. Run the commit. Most commits need only the single-line form:

```bash
git commit -m "type(scope): description"
```

Add the optional body/footer(s) only when the subject line can't carry the why — use a heredoc so blank lines and quoting survive:

```bash
git commit -m "$(cat <<'EOF'
type(scope): description

- why this change, in bullets (lines wrap at ~72; body ≤500 chars)
- another distinct point if needed

Refs: #123
EOF
)"
```

5. Verify with `git log -1` — pre-commit hooks can rewrite or reject the message.

## Structure

Standard Conventional Commits (conventionalcommits.org):

```
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

- `feat` = MINOR, `fix` = PATCH; other types (`build`, `chore`, `ci`, `docs`, `refactor`, `perf`, `test`, …) as long as they have semantic meaning for the codebase — prefer the types already in the project's log.
- Breaking changes = MAJOR: mark with `!` before the colon, or a `BREAKING CHANGE: <description>` footer, or both.
- Footers follow git-trailer format (`Refs: #123`, `Acked-by: ...`).

## Length and body style (house rules)

Keep messages scannable — no huge subjects, no sprawling bodies.

- **Subject ≤72 chars total** (type + scope + `!` + description). If it won't fit, the commit is probably doing too much — split it.
- **Body ≤500 chars total** — a hard ceiling. If you're over, cut detail the diff already shows or move it to the PR/ticket.
- **Body is bullet points only — no prose paragraphs.** The spec allows free-form paragraphs; we don't. Add a body only when the subject can't carry the why.
- **Group bullets under topic subheadings where useful** (e.g. `Behaviour:` / `Cleanup:`); a flat list is fine when there's one topic.
- **Wrap lines at ~72 chars** — this is line width only; a single bullet may span several wrapped lines.
- Skip the body entirely when the subject says it all.

## Examples

Breaking change, scoped:

```
feat(api)!: send an email to the customer when a product is shipped
```

Body grouped under subheadings, with footers:

```
fix: prevent racing of requests

Behaviour:
- add request id + reference to the latest request
- dismiss incoming responses other than from the latest request

Cleanup:
- remove timeouts that mitigated the race but are now obsolete

Refs: #123
Ticket: ABC-123
```
