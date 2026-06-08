---
name: pr-summary
description: Generate concise PR summaries. Use when the user asks for a PR summary, PR description, wants to create a PR, or says things like "give me a pr summary", "summarize changes", "write a PR description", or "create a PR". Also trigger when the user asks to commit and push with a PR.
---

# PR Summary

Generate a concise pull request summary by analyzing the current branch's changes against the base branch.

## How to gather context

### Repository safety check

Before reading commits or diffs, verify the repository in the same execution context/tool that will run the git commands:

1. Run `pwd`, `git rev-parse --show-toplevel`, `git rev-parse --abbrev-ref HEAD`, and `git remote -v`
2. Confirm the repo root, branch, and remote match the user's intended project
3. If any value looks wrong, stop and ask the user before generating a summary
4. For tools that may run from a different default cwd, prefix every git command with `cd <verified-repo-root> && ...`

Do not trust the chat/session cwd alone. The command runner's cwd is the source of truth.

### Branch diff

1. Determine the base branch from PR metadata/upstream when available; otherwise default to `main`
2. Run `git log <base>..HEAD --oneline` to see all commits
3. Run `git diff <base>..HEAD` to read the actual diff — understand what changed, not just which files
4. Read changed files for additional context if the diff alone doesn't tell the full story
5. Check `git status --short` separately and distinguish uncommitted working-tree changes from the PR branch

If `<base>..HEAD` has no commits or diff, do not invent a PR summary from unrelated working-tree changes. Ask whether the user wants a working-tree summary instead.

## Summary structure

```
# <PR title — short, under 70 characters, imperative mood>

## Summary

<1-3 paragraphs max describing the PURPOSE of the PR — why it exists, what goal it achieves. Prefer one paragraph where possible. This frames the motivation, not the implementation.>

## Changes

<Succinct bullet list of what was done. Each bullet is a single line. Group related changes under sub-headings when the PR spans multiple areas.>

## Test plan

<Checklist of how to verify the changes, tick any already done if known>
```

## PR title guidelines

- Keep under 70 characters
- Use imperative mood ("Add blog navigation" not "Added blog navigation")
- Summarize the whole PR, not just one change
- Don't prefix with type tags like `feat:` — that's for commits, not PR titles

## Writing principles

- Summary paragraphs are about intent — what problem is being solved or what goal is being achieved. "Overhauls the blog to support category browsing and improve discoverability" is good. "Added filters, changed routing, updated SEO" is bad — that's just restating the bullets.
- If the change breaks existing consumers — removed exports, changed API shapes, renamed public interfaces — lead with that in the Summary.
- Open directly with what the change does — the PR is already the context.
- Write in plain prose. Let the content carry weight, not decoration.
- Lead with the change, not the file. "Statically generated category routes with client-side filtering via react-query" adds useful context. "Updated `[[...slug]].tsx`" does not.
- Include implementation details only when they help explain the change.
- Prefer one strong sentence over two weak ones. If a bullet needs a second line, the first line wasn't direct enough.
- Prefer concise sentences or bullet points only, verbosity makes it hard to quickly understand the PR.

## Output format

Always write the summary to `/tmp/pr-summary-{branch-slug}.md` using the Write tool (e.g. `/tmp/pr-summary-fix-auth-flow.md`). Then tell the user to copy it with `pbcopy < /tmp/pr-summary-{branch-slug}.md`. This ensures clean formatting when pasted into GitHub's PR editor, which breaks when copying from inline code blocks.
