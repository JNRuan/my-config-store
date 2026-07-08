---
name: simplify-code
description: >-
  Review recently changed code and apply quality cleanups WITHOUT changing
  behavior — removing duplication, cutting needless complexity, fixing
  inefficiencies, and raising fix-altitude (deep fixes over band-aids). Use
  when the user wants to simplify, clean up, tidy, declutter, refactor for
  clarity, DRY up / deduplicate, reduce nesting or complexity, or polish a
  diff, branch, or PR before committing. Trigger phrases: "simplify this",
  "clean up the code", "tidy this up", "make it cleaner / simpler", "refactor
  for readability", "reduce complexity", "DRY this up", "polish the diff".
  Quality only - does NOT hunt for correctness bugs as that is for code
  reviews only.
---

# Simplify Code

`gather diff → four angles → apply fixes`

Improve the quality of recently changed code without changing its behavior.
Review the diff for **reuse, simplification, efficiency, and altitude** issues,
then fix what you find. This is a quality pass, **not a bug hunt** — behavior
must be identical before and after.

## Inputs

- `$target` (optional): a PR number, branch name, commit range, or file path to
  review. If omitted, review the current uncommitted + branch changes.

## Goal

A cleaner diff — duplication, needless complexity, wasted work, and band-aid
fixes removed — plus a short summary of what was changed and what was
deliberately left alone.

**Done when:** every accepted finding is fixed, behavior is unchanged, and the
final summary lists what was fixed and what was skipped (or confirms the code
was already clean).

## Phase 0 — Gather the diff

Get the unified diff under review:

- Run `git diff @{upstream}...HEAD` — or `git diff main...HEAD` / `git diff HEAD~1`
  if there is no upstream.
- If there are uncommitted changes, or the range diff is empty, also run
  `git diff HEAD` and include the working-tree changes in scope — this skill
  often runs before the commit.
- If a `$target` (PR number, branch, commit range, or path) was passed, review
  that instead.

Treat this diff as the review scope. Read the enclosing function/file around each
hunk when context is needed. You may search adjacent/shared code to understand
reuse opportunities, but limit edits to the reviewed diff and what it directly
touches.

## Phase 1 — Review (four angles)

Work through the four angles below. **If your harness supports subagents or
parallel tasks, launch one agent per angle concurrently**, each given the diff
and a single angle — this isolates context and is faster. **Otherwise, walk the
four angles sequentially** in a single pass; both should land on the same
findings.

For each finding, record: `file`, `line`, a one-line `summary`, the concrete
**cost** (what is duplicated, wasted, or harder to maintain), and a **severity**
(`low` / `med` / `high`) reflecting how much the issue hurts maintainability —
use this to prioritize when there are many findings.

### Reuse

Flag new code that re-implements something the codebase already has. Grep shared
/utility modules and files adjacent to the change, and name the existing helper
to call instead.

### Simplification

Flag unnecessary complexity the diff adds: redundant or derivable state,
copy-paste with slight variation, deep nesting, dead code left behind. Name the
simpler form that does the same job.

### Efficiency

Flag wasted work the diff introduces: redundant computation or repeated I/O,
independent operations run sequentially, blocking work added to startup or hot
paths. Name the cheaper alternative.

### Altitude

Check that each change is implemented at the right depth, not as a fragile
band-aid. Special cases layered on shared infrastructure are a sign the fix isn't
deep enough — prefer generalizing the underlying mechanism over adding special
cases.

## Phase 2 — Apply the fixes

Collect all findings, dedup any that point at the same line or mechanism, and
resolve conflicts between angles (see below) before fixing. Fix each remaining
one directly. **Skip** any finding whose fix would:

- change intended behavior,
- require changes well outside the reviewed diff, or
- that you judge to be a false positive.

Note the skip rather than arguing with it.

**Resolving inter-angle conflicts.** Two angles can point at the same code with
different fixes — e.g. Reuse says call an existing helper, Altitude says that
helper is the wrong abstraction and the underlying mechanism should be
generalized. When this happens, review both against the actual code and pick the
single most correct fix; do not apply both. Note the tension and your reasoning
in the summary.

After applying the fixes, if the project has fast tests, a type-check, or lint
covering the touched code, run them to confirm behavior is preserved. If none
exist, say so in the summary rather than claiming verification you didn't do.
Finally, inspect the resulting `git diff` and confirm the patch contains only
behavior-preserving simplifications within scope.

Leave changes uncommitted for the user to review — do not amend, commit, or
push automatically unless explicitly told to.

Finish with a brief summary of what was fixed and what was skipped (or confirm
the code was already clean).

## Rules

- **Quality only.** Do not hunt for or fix correctness bugs here — route those to
  a code-review skill.
- **Preserve behavior.** If a cleanup can't be made behavior-preserving, skip it
  and note why.
- **Stay in scope.** Limit changes to the reviewed diff and what it directly
  touches; don't opportunistically refactor unrelated code.
- **Don't argue with skips.** Record them and move on.
- **Don't touch generated or machine-managed files.** Skip generated code,
  vendored dependencies, lockfiles, and migration snapshots — they aren't meant
  for hand-editing even if they appear in the diff.
