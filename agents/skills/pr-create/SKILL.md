---
name: pr-create
description: Draft a PR description or create/update a pull request via `gh`. Use when the user asks to create, open, or update a PR, or to write a PR description or summary. Writing requests produce a draft; create, open, or update requests authorise publication.
---

# PR Create

Draft a pull request description from the current branch's changes. Requests for wording use
[Summary-only mode](#summary-only-mode). Requests to create, open, or update a PR authorise
publication. Earlier authorisation to publish remains sufficient.

## Delegation

Do not draft the PR in the session model: dispatch one subagent to run the whole skill, and relay its result. Set model and effort per this table, choosing the column for the harness you are running in:


| Role                         | Claude                | Codex                                 | Other harness                                               |
| ---------------------------- | --------------------- | ------------------------------------- | ----------------------------------------------------------- |
| PR worker (everything below) | Sonnet, medium effort | gpt-5.6-luna, medium reasoning effort | gpt-5.6-luna, medium reasoning effort; else session default |


- Give the subagent the user's parameters (base ref if given, create or summary-only mode) and any intent from the session the description should reflect.
- The subagent follows the selected mode. It reports the PR URL, or the title and body file path in summary-only mode.
- Where a step below says stop and ask the user, the subagent reports back instead; resolve with the user and dispatch again.
- If the harness can't spawn subagents or set model and effort per call, run the steps below yourself. The table is an upgrade, not a requirement; never fail the task over it.

## How to gather context

### Repository safety check

Before reading commits or diffs, verify the repository from the same tool that will run the git commands:

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

1. Determine the base branch: use the user's specified base first; otherwise an existing PR's base
(`gh pr view --json baseRefName`); otherwise the remote's default branch
(`gh repo view --json defaultBranchRef` or `git symbolic-ref refs/remotes/origin/HEAD`);
otherwise `main`.
2. If the current branch is the base branch, stop and ask which branch the PR should be created from
3. Run `git log <base>..HEAD --oneline` to see all commits
4. Run `git diff <base>...HEAD` to read the actual diff: understand what changed, not just which files. Three dots diffs from the merge-base, matching GitHub's PR view. For large PRs, run with `--stat` first, then read the full diff.
5. Read changed files for additional context if the diff alone doesn't tell the full story
6. Check `git status --short` separately and distinguish uncommitted working-tree changes from the PR branch

If `<base>...HEAD` has no commits or diff, do not invent a PR summary from unrelated working-tree changes. Ask whether the user wants a working-tree summary instead.

## Summary structure

Use this when the repo has no PR template of its own. The PR **title** is separate from the body: it goes in GitHub's title field, so don't repeat it as a heading inside the body.

```
## Summary

<1-3 paragraphs max describing the PURPOSE of the PR: why it exists, what goal it achieves. Prefer one paragraph where possible. This frames the motivation, not the implementation.>

## Impact

<Include only if the change affects existing behaviour: breaking changes such as removed/renamed exports, changed API or schema shapes, migrations, behavioural shifts that affect consumers. Lead with the most disruptive item.>

## Changes

<Short bullet list of what was done. Each bullet is a single line. Group related changes under sub-headings when the PR spans multiple areas.>

## Test plan

<Checklist of how to verify the changes. Only tick items that were actually run and verified in this session.>
```

Treat the structure as flexible, not fixed: include a section only if it helps the reviewer understand or verify the change, and drop any that would be empty or just restate what's already clear (e.g. omit Impact when nothing breaks, omit per-area grouping on a single-area PR).

## PR title guidelines

- Keep under 70 characters
- Use imperative mood ("Add blog navigation" not "Added blog navigation")
- Summarize the whole PR, not just one change
- Don't prefix with type tags like `feat:` by default; that's for commits. But follow the project's convention when its PR titles use them (e.g. squash-merge repos where the PR title becomes the commit subject); check recent merged PRs (`gh pr list --state merged --limit 10`).

## Writing principles

- Summary paragraphs are about intent: what problem is being solved or what goal is being achieved. "Overhauls the blog to support category browsing and improve discoverability" is good. "Added filters, changed routing, updated SEO" is bad; that's just restating the bullets.
- If the change breaks existing consumers (removed exports, changed API shapes, renamed public interfaces), lead with that in the Impact section, and flag it in the Summary.
- Open directly with what the change does: the PR is already the context.
- Write in plain prose; don't decorate with bold, emoji, or badges.
- Lead with the change, not the file. "Statically generated category routes with client-side filtering via react-query" adds useful context. "Updated `[[...slug]].tsx`" does not.
- Include implementation details only when they help explain the change.
- Prefer one strong sentence over two weak ones.

## PR signoff

Append this sign-off as the final lines of the PR body:

```markdown
---
:space_invader: PR created by Agent
```

## Creating the PR

For create mode, write the body to `/tmp/pr-body-{branch-slug}.md` using the Write tool (e.g. `/tmp/pr-body-fix-auth-flow.md`), then:

1. **Ensure the branch is pushed.** If it has no upstream, push it: `git -C <root> push -u origin HEAD`.
2. **Check for an existing open PR** for this branch: `gh pr view --json number,url,state,body 2>/dev/null`. `gh pr view` also resolves closed and merged PRs, so check `state`:
   - **No PR, or state is not `OPEN`** → open one: `gh pr create --base <base> --title "<title>" --body-file <body-file>`
   - **State is `OPEN`** → retain relevant decisions, issue links and validation notes from the
     existing body in the draft, then update its title and body: `gh pr edit --title "<title>" --body-file <body-file>`
3. Report the PR URL.

If `gh` is not installed or not authenticated, report it and fall back to Summary-only mode so the work isn't lost.

## Summary-only mode

In summary-only mode, run no push or `gh` create/edit commands. Instead:

- Write the body to `/tmp/pr-body-{branch-slug}.md` using the Write tool.
- Give the user the title, then copy the body to the clipboard with the platform's tool:
  - macOS: `pbcopy < <file>`
  - Linux (Wayland): `wl-copy < <file>`, (X11): `xclip -selection clipboard < <file>`
  - Windows/WSL: `clip.exe < <file>`

If no clipboard tool is available, skip copying and give the user the file path and copy command instead. Copying from the file (not from an inline code block) ensures clean formatting when pasted into GitHub's PR editor.
