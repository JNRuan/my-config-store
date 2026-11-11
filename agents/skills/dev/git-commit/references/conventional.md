# Conventional Commits

Standard Conventional Commits (conventionalcommits.org):

```
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

- `feat` = MINOR, `fix` = PATCH. Other types (`build`, `chore`, `ci`, `docs`, `refactor`, `perf`, `test`, …) may be used when they have semantic meaning for the codebase; prefer the types already in the project's log.
- Breaking changes = MAJOR: mark with `!` before the colon, or a `BREAKING CHANGE: <description>` footer, or both. When you use `!` without the footer, the description itself must describe the breaking change. `BREAKING-CHANGE` is a synonym footer token.
- Footers follow git-trailer format (`Refs: #123`, `Acked-by: ...`).

## Examples

Breaking change, scoped:

```
feat(api)!: send an email to the customer when a product is shipped
```

With body and footers:

```
fix: prevent racing of requests

A slow response could arrive after a newer request and overwrite its
result. Each request now carries an id, and a response from any
request other than the latest is dismissed.

Remove the timeouts that mitigated the race.

Refs: #123
Ticket: ABC-123
```
