---
name: conventional-commit
description: "Format git commit messages using the Conventional Commits standard — type prefixes like feat/fix/chore, with optional scope. Use when drafting, rewriting, or suggesting commit messages in projects whose git log uses type prefixes. Counterpart to scoped-commit: if the project's log shows bare scopes with no types, use that skill instead."
---

## Workflow

You need to **Commit exactly what the user staged or asked to commit.** When scope is ambiguous 
(e.g. the user said "commit my changes" with both staged and unstaged work present, or nothing staged), 
ask which to include and wait for an answer.

**Follow these steps:**

1. Run `git status`, `git log --oneline -15`, and `git diff --cached --stat` to inspect what is staged and learn the project's existing commit conventions (types and scopes in use).
2. Read the full staged diff (`git diff --cached`) to draft a succinct and simple commit message.
3. Construct your commit message using the structure described below for conventional commits.
4. Run the commit. Most commits need only the single-line form:

```bash
git commit -m "type(scope): description"
```

Add the optional body/footer(s) only when the subject line can't carry the why — use a heredoc so blank lines and quoting survive:

```bash
git commit -m "$(cat <<'EOF'
type(scope): description

Optional body explaining why, wrapped at ~72 chars.

Refs: #123
EOF
)"
```

5. Verify with `git log -1` — pre-commit hooks can rewrite or reject the message.

## Conventional Commit Structure

The commit message should be structured as follows:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

The commit contains the following structural elements, to communicate intent to the consumers of your library:

1. `fix:` a commit of the type `fix` patches a bug in your codebase (this correlates with PATCH in Semantic Versioning).
2. `feat:` a commit of the type `feat` introduces a new feature to the codebase (this correlates with MINOR in Semantic Versioning).
3. `BREAKING CHANGE:` a commit that has a footer `BREAKING CHANGE:`, or appends a `!` after the type/scope, introduces a breaking API change (correlating with MAJOR in Semantic Versioning). A BREAKING CHANGE can be part of commits of any type.
4. types other than `fix:` and `feat:` are allowed, for example `build:`, `chore:`, `ci:`, `docs:`, `style:`, `refactor:`, `perf:`, `test:`, and others as long as they have semantic meaning for the codebase.
5. footers other than `BREAKING CHANGE:` may be provided and follow a convention similar to git trailer format.

Additional types are not mandated by the Conventional Commits specification, and have no implicit effect in Semantic Versioning (unless they include a BREAKING CHANGE). A scope may be provided to a commit's type, to provide additional contextual information and is contained within parenthesis, e.g., `feat(parser): add ability to parse arrays`.

## Examples

### Commit message with description and breaking change footer

```
feat: allow provided config object to extend other configs

BREAKING CHANGE: `extends` key in config file is now used for extending other config files
```

### Commit message with ! to draw attention to breaking change

```
feat!: send an email to the customer when a product is shipped
```

### Commit message with scope and ! to draw attention to breaking change

```
feat(api)!: send an email to the customer when a product is shipped
```

### Commit message with both ! and BREAKING CHANGE footer

```
feat!: drop support for Node 6

BREAKING CHANGE: use JavaScript features not available in Node 6.
```

### Commit message with no body

```
docs: correct spelling of CHANGELOG
```

### Commit message with scope

```
feat(lang): add Polish language
```

### Commit message with multi-paragraph body and multiple footers

```
fix: prevent racing of requests

Introduce a request id and a reference to latest request. Dismiss
incoming responses other than from latest request.

Remove timeouts which were used to mitigate the racing issue but are
obsolete now.

Refs: #123
Ticket: ABC-123
```

## Formatting rules

Distilled from the Conventional Commits spec — the rules that matter when writing a message.

1. Commits MUST be prefixed with a type, which consists of a noun, `feat`, `fix`, etc., followed by the OPTIONAL scope, OPTIONAL `!`, and REQUIRED terminal colon and space.
2. A scope MAY be provided after a type. A scope MUST consist of a noun describing a section of the codebase surrounded by parenthesis, e.g., `fix(parser):`
3. A description MUST immediately follow the colon and space after the type/scope prefix. The description is a short summary of the code changes, e.g., fix: array parsing issue when multiple spaces were contained in string.
4. A longer commit body MAY be provided after the short description, providing additional contextual information about the code changes. The body MUST begin one blank line after the description.
5. A commit body is free-form and MAY consist of any number of newline separated paragraphs.
6. One or more footers MAY be provided one blank line after the body. Each footer MUST consist of a word token, followed by either a `: ` or ` #` separator, followed by a string value (this is inspired by the git trailer convention).
7. A footer's token MUST use `-` in place of whitespace characters, e.g., `Acked-by` (this helps differentiate the footer section from a multi-paragraph body). An exception is made for `BREAKING CHANGE`, which MAY also be used as a token.
8. Breaking changes MUST be indicated in the type/scope prefix of a commit, or as an entry in the footer.
9. If included as a footer, a breaking change MUST consist of the uppercase text BREAKING CHANGE, followed by a colon, space, and description, e.g., BREAKING CHANGE: environment variables now take precedence over config files.
10. If included in the type/scope prefix, breaking changes MUST be indicated by a `!` immediately before the `:`. If `!` is used, `BREAKING CHANGE:` MAY be omitted from the footer section, and the commit description SHALL be used to describe the breaking change.
