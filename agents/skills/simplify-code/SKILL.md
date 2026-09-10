---
name: simplify-code
description: >-
  Review recently changed code and propose quality cleanups WITHOUT changing
  behaviour: removing duplication, cutting needless complexity, fixing
  inefficiencies, raising fix-altitude (deep fixes over symptom patches), and cutting
  tests that protect nothing. Use when the user wants to simplify, clean up,
  tidy, declutter, refactor for clarity, DRY up / deduplicate, reduce nesting
  or complexity, prune tests, or polish a diff, branch, or PR before
  committing. Also aligns the diff with project convention files
  (CLAUDE.md/AGENTS.md). Proposes edits as diffs in crit; never edits files
  unasked. Quality only: does NOT hunt for correctness bugs; that's the job of
  a code review.
---

# Simplify code

Improve the quality of recently changed code without changing its behaviour.
Review the diff for **reuse, simplification, efficiency, altitude,
conventions, and tests** issues, then propose the fixes as diffs. This is a
quality pass, **not a bug hunt**, and it edits nothing unasked.

## Goal

A review the user can accept or reject hunk by hunk. Each finding carries a
unified diff that preserves behaviour. A summary lists what was proposed and
what was skipped, or confirms the code was already clean.

## Phase 0: Gather the diff

If a PR number, branch name, or file path was passed as an argument, review
that target. Otherwise run `git diff @{upstream}...HEAD`, falling back to
`git diff main...HEAD` or `git diff HEAD~1` when there is no upstream. If the
working tree has uncommitted changes, or the range diff is empty, also run
`git diff HEAD` and include those changes; this pass often runs before the
commit.

Treat this diff as the review scope. Read the enclosing function or file
around each hunk when context is needed. You may search adjacent or shared
code to understand reuse opportunities, but propose edits only within the
reviewed diff and what it directly touches.

## Subagent models

Every subagent spawn uses this table. Choose the column for the harness you are running in.

| Role                      | Claude                                                 | Codex                              | Other harness   |
| ------------------------------------------- | ------------------------------------------------------ | ---------------------------------- | --------------- |
| Angle reviewers, large diffs only (Phase 1) | Fable, high effort; Opus if the Fable limit is reached | gpt-6-astra, high reasoning effort | session default |

If the harness cannot set model or effort per subagent, spawn with defaults. The table is an upgrade, not a requirement. Never fail a pass over it.

Everything else, including the default single pass and Phases 2 and 3, runs in your own context on the session model.

## Phase 1: Review (six angles)

Walk the six angles below yourself, in one pass, in this context. That is the
default.

Fan out only when the diff is large: more than 1000 changed lines or more
than 10 files. Then, if your harness supports subagents, launch two agents at
once on the model from the table above. Give one the diff and the four code
angles, Reuse through Altitude. Give the other the diff and the Conventions
and Tests angles. They read different material. If the harness has no
subagents, walk the angles yourself and say in the summary that a large diff
got a single pass.

For each finding record:

- `file` and `line`;
- a one-line `summary`;
- the cost: what is duplicated, wasted, harder to maintain, or protects nothing;
- a severity of `low`, `med`, or `high` for how much it hurts maintainability;
- the proposed edit as a unified diff with enough context to apply it.

### Reuse

Flag new code that re-implements something the codebase already has. Grep
shared/utility modules and files adjacent to the change, and name the existing
helper to call instead.

### Simplification

Flag unnecessary complexity the diff adds: redundant or derivable state,
copy-paste with slight variation, deep nesting, dead code left behind. Name the
simpler form that does the same job.

### Efficiency

Flag wasted work the diff introduces: redundant computation or repeated I/O,
independent operations run sequentially, blocking work added to startup or hot
paths. Also flag unnecessary memory retention when you can identify the retained
data and explain why it stays alive longer than needed. Name the cheaper alternative.

### Altitude

Check that each change fixes the cause at the right depth, not as a patch on
the symptom. Special cases layered on shared infrastructure are a sign the
fix is not deep enough. Prefer a more general change to the underlying
mechanism over another special case.

### Conventions

Check the changes against the instructions governing this session and the repository
conventions that apply to the changed code.

Only flag a violation when you can quote the exact rule and the exact line
that breaks it: no style preferences, no vague "spirit of the doc"
inferences. In the finding, name the convention file and quote the rule. If no
convention file applies, return nothing for this angle.

### Tests

Scope: every test the diff adds or changes. Do not review tests the diff
leaves alone, and do not propose new tests.

Keep a test only when it catches a failure that reading the code would not
catch and that no other test catches. For each test, name the failure it
guards against. If you cannot, or another test guards the same failure,
propose cutting it.

Keep a test that covers:

- the main path of a public behaviour;
- a failure path with an observable effect: an error, a rejection, a fallback,
  a refusal;
- a boundary or branch: an empty input, a limit, an off-by-one, a comparison,
  a regex;
- a bug this change fixes, so the bug cannot return;
- a contract between modules that a change on either side would break.

Propose cutting a test that:

- repeats another test's path with a different literal, and the literal
  exercises no new branch; propose merging into one parametrised case instead
  of two tests when both inputs matter;
- asserts what the type checker, the compiler, or the framework already
  guarantees;
- tests a trivial unit in isolation: a getter, a constructor setting a field,
  a wrapper that forwards to what it wraps, a constant, a one-line helper
  whose calling path is already tested;
- asserts on the test's own setup: a mock returning what the test told it to
  return, a mock called with the arguments the test passed in;
- pins implementation rather than behaviour: internal call order, private
  state, an exact log message, a snapshot no reader could verify by eye;
- mocks the unit under test, so the code the test names never runs;
- cannot fail: no assertion, an assertion on a constant, or `expect(true)`.

Report each finding with the test name, the verdict `cut` or `merge`, the
failure it was meant to guard, and which kept test already guards it. When a
test file is small and every test in it catches a distinct failure, return
nothing for that file. When in doubt, keep the test and say why.

## Phase 2: Consolidate the findings

Collect all findings, dedup any that point at the same line or mechanism, and
resolve conflicts between angles (see below). Drop any finding you judge a
false positive, and any finding whose fix would change intended behaviour or
require changes well outside the reviewed diff. Record each drop with its
reason.

**Resolving inter-angle conflicts.** Two angles can point at the same code with
different fixes: Reuse says call an existing helper, while Altitude says that
helper is the wrong abstraction and the underlying mechanism needs a more
general change. When this happens, review both against the actual code and
pick the one correct fix. Do not propose both. Note the tension and your reasoning
in the summary.

Do not edit any file, run a formatter, or create a commit. Do not run the
project's tests or checks. Nothing has changed. Name the checks the user
should run after applying the diffs.

## Phase 3: Present in crit

Run the `crit` skill. Post every surviving finding as a line comment on the
file it changes, then open the review so the user can accept or reject each
one in place.

1. Build one JSON entry per finding for `crit comment --json`, with `--author`
   set to your harness name. Anchor it at the finding's `file` and `line`
   range in the file on disk. The body carries, in order: the angle and
   severity on one line, the one-line summary, the cost, and the unified diff
   in a fenced block. For a large edit show the key hunks and describe the
   rest.
2. Add one review-level comment holding the summary: findings by angle,
   skipped findings with reasons, incidental bugs reported without a fix, and
   the checks to run after applying. If nothing survives, this comment says
   the code was already clean and which angles ran.
3. Post the comments in one `crit comment --json` call, then open the review:
   bare `crit` for the branch diff, `crit --pr <n>` when a PR was the target.
4. Wait for the user to finish the round. Read the review file. A finding is
   rejected when the user replies to its comment saying so or resolves it. A
   reply that asks for a change is a revised proposal. Update the comment. Do
   not edit the file.
5. Apply the accepted proposals only when the user says to, after the round.
   Then run the named checks and report the result. Leave the changes
   uncommitted.

### Without crit

When crit is unavailable, write the same content as a Markdown report to
`.agents/simplify-code-reviews/{yyyymmdd-hhmm}-{branch-slug}.md` at the
repository root, creating the directory if needed. Group findings by file,
highest severity first, each with `file:line`, angle, summary, cost, and diff,
followed by the summary sections from step 2. Tell the user the path and
stop.

## Rules

- **Propose, never edit unasked.** The review is the deliverable. Files change
  only when the user says to apply, after the crit round.
- **Quality only.** Do not hunt for correctness bugs; if you notice one
  incidentally, report it in the summary without proposing a fix.
- **Preserve behaviour.** If a cleanup can't be made behaviour-preserving, skip it
  and note why. Cutting a test preserves behaviour. Cutting the only test of a
  behaviour does not, so never propose it.
- **Stay in scope.** Limit proposals to the reviewed diff and what it directly
  touches; don't opportunistically refactor unrelated code.
- **Don't argue with skips.** Record them and move on.
- **Don't touch generated or machine-managed files.** Skip generated code,
  vendored dependencies, lockfiles, and migration snapshots: they aren't meant
  for hand-editing even if they appear in the diff.
