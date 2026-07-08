---
name: pr-create
description: Draft a PR description and open the pull request via `gh`. Use when the user asks to create/open a PR, or to write a PR description or summary. Opens the PR by default; if the user asks for a summary or description *only*, it drafts the text without creating the PR.
---

# PR Create

Draft a pull request description from the current branch's changes and open the PR — unless the user asks for the description only.

By default this skill opens the PR. If the user asks for a "summary only", "description only", or "don't open the PR", stop after producing the text (see [Summary-only mode](#summary-only-mode)).

## How to gather context

### Repository safety check

Before reading commits or diffs, verify the repository in the same execution context/tool that will run the git commands:

1. Run `git rev-parse --show-toplevel && git branch --show-current && git remote -v` in a single call
2. Confirm the repo root, branch, and remote match the user's intended project
3. If any value looks wrong, stop and ask the user before continuing
4. For tools that may run from a different default cwd, run every git command as `git -C <verified-repo-root> ...`

Do not trust the chat/session cwd alone. The command runner's cwd is the source of truth.

### Repository PR template

Before choosing a structure, check whether the repo defines its own PR template:

- `.github/PULL_REQUEST_TEMPLATE.md` or `.github/pull_request_template.md`
- `PULL_REQUEST_TEMPLATE.md` at the repo root or under `docs/`
- multiple templates under `.github/PULL_REQUEST_TEMPLATE/`

If one exists, fill it in and follow its sections instead of the default structure below. If several exist, pick the best fit for the change or ask the user. If none exists, use the default structure.

### Branch diff

1. Determine the base branch from PR metadata/upstream when available; otherwise default to `main`
2. Run `git log <base>..HEAD --oneline` to see all commits
3. Run `git diff <base>...HEAD` to read the actual diff — understand what changed, not just which files. Three dots diffs from the merge-base, matching GitHub's PR view. For large PRs, run with `--stat` first, then read the full diff.
4. Read changed files for additional context if the diff alone doesn't tell the full story
5. Check `git status --short` separately and distinguish uncommitted working-tree changes from the PR branch

If `<base>..HEAD` has no commits or diff, do not invent a PR summary from unrelated working-tree changes. Ask whether the user wants a working-tree summary instead.

## Summary structure

Use this when the repo has no PR template of its own. The PR **title** is separate from the body — it goes in GitHub's title field, so don't repeat it as a heading inside the body.

```
## Summary

<1-3 paragraphs max describing the PURPOSE of the PR — why it exists, what goal it achieves. Prefer one paragraph where possible. This frames the motivation, not the implementation.>

## Impact

<Include only if the change affects existing behaviour: breaking changes — removed/renamed exports, changed API or schema shapes, migrations, behavioural shifts that affect consumers. Lead with the most disruptive item.>

## Changes

<Succinct bullet list of what was done. Each bullet is a single line. Group related changes under sub-headings when the PR spans multiple areas.>

## Test plan

<Checklist of how to verify the changes. Only tick items that were actually run and verified in this session>
```

Treat the structure as flexible, not fixed: include a section only if it helps the reviewer understand or verify the change, and drop any that would be empty or just restate what's already clear (e.g. omit Impact when nothing breaks, omit per-area grouping on a single-area PR).

## PR title guidelines

- Keep under 70 characters
- Use imperative mood ("Add blog navigation" not "Added blog navigation")
- Summarize the whole PR, not just one change
- Don't prefix with type tags like `feat:` — that's for commits, not PR titles

## Writing principles

- Summary paragraphs are about intent — what problem is being solved or what goal is being achieved. "Overhauls the blog to support category browsing and improve discoverability" is good. "Added filters, changed routing, updated SEO" is bad — that's just restating the bullets.
- If the change breaks existing consumers — removed exports, changed API shapes, renamed public interfaces — lead with that in the Impact section, and flag it in the Summary.
- Open directly with what the change does — the PR is already the context.
- Write in plain prose. Let the content carry weight, not decoration.
- Lead with the change, not the file. "Statically generated category routes with client-side filtering via react-query" adds useful context. "Updated `[[...slug]].tsx`" does not.
- Include implementation details only when they help explain the change.
- Prefer one strong sentence over two weak ones. If a bullet needs a second line, the first line wasn't direct enough.

## PR signoff

Append a sign-off as the final lines of the PR body — a divider, then the model identity:

```markdown
---
PR created by {model}
```

**Filling in `{model}` (do this, don't skip):**

- Your exact model name and ID are stated in your own system prompt / environment
  context (e.g. Claude Code's environment block names the model and its ID). Read your
  identity from there, not from memory.
- Format as vendor + human-readable name + version: `Claude Opus 4.8`, `GPT-5.5`,
  `GLM 5.2`. If your context gives the model but not the vendor, prefix the vendor
  yourself. If it gives an internal ID only (e.g. `claude-opus-4-8`), convert it to the
  display name (`Claude Opus 4.8`).
- Resolve as far down this chain as your context allows, and never invent detail beyond it:
  1. Vendor + name + version — `Claude Opus 4.8`
  2. Vendor + family, no version — `Claude Opus`, `GPT-5`
  3. Nothing determinable — use the literal `an AI agent`

Before running `gh pr create`/`gh pr edit`, confirm the body file ends with this sign-off
and that `{model}` has been replaced (no literal `{model}` and no invented version remain).

## Creating the PR

This is the default. Write the body to `/tmp/pr-body-{branch-slug}.md` using the Write tool (e.g. `/tmp/pr-body-fix-auth-flow.md`), then:

1. **Ensure the branch is pushed.** If it has no upstream, push it: `git -C <root> push -u origin HEAD`.
2. **Check for an existing PR** for this branch: `gh pr view --json number,url 2>/dev/null`.
   - **None** → open it: `gh pr create --base <base> --title "<title>" --body-file <body-file>`
   - **Exists** → update its title and body instead of creating a duplicate: `gh pr edit --title "<title>" --body-file <body-file>`
3. Report the PR URL.

If `gh` is not installed or not authenticated, stop and report it, then fall back to Summary-only mode so the work isn't lost.

## Summary-only mode

If the user asked for the description/summary only, run no `gh` create/edit commands. Instead:

- Write the body to `/tmp/pr-body-{branch-slug}.md` using the Write tool.
- Give the user the title, then copy the body to the clipboard with the platform's tool:
  - macOS: `pbcopy < <file>`
  - Linux (Wayland): `wl-copy < <file>`, (X11): `xclip -selection clipboard < <file>`
  - Windows/WSL: `clip.exe < <file>`

If no clipboard tool is available, skip copying and give the user the file path and copy command instead. Copying from the file (not from an inline code block) ensures clean formatting when pasted into GitHub's PR editor.
