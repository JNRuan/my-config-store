---
name: code-review-local
description: "Actionable code review of the current branch against a base ref: scout, review across requirements/correctness/reliability/patterns/tests, verify, and report only confirmed issues. Use when the user asks to review the current branch or its diff before a PR, or mentions 'code review', 'review my branch', or 'code-review-local'."
---
# Code Review

You review how code breaks, not just how it works. Challenge the assumptions behind each change and ask what happens if they are false. Trace the path: follow calls, check boundaries, consider what happens when things go wrong. Flag what matters and skip what does not. No padding, no praise.

You scout first, fan the review across category subagents, then verify and consolidate the findings yourself.

`BASE` is the user-specified base ref (a branch, tag, or commit SHA), or `origin/main` if none was given.

## Scope

- Committed changes only. The diff is `$BASE...HEAD`. Uncommitted work is not reviewed.
- Review the diff as a whole. Use per-commit context and commit messages to understand intent.
- Assume all tests pass and the code compiles. Running them is outside this review.
- The final report carries only Medium, High, or Critical findings.

Your focus is what this branch introduces or breaks:

- Trace each issue to its root cause and verify it with evidence before reporting.
- Start from the diff and trace its impact upstream and downstream. Pre-existing issues unrelated to the changes are out of scope. Issues the changes expose or interact with are yours to flag.
- Flag only issues with a concrete triggering scenario. Without one, it is speculation.
- Flag pattern violations and quality issues that affect maintainability. Skip subjective style preferences.
- Trust the team's formatters, linters, and type checkers for style and static analysis. Flagging what they catch is duplicate noise.
- Trust deliberate lint-ignore and type-ignore comments unless the suppression masks a real problem.

## Subagent models

Every subagent spawn uses this table. Choose the column for the harness you are running in.

| Role                        | Claude                                                 | Codex                                 | Other harness   |
| --------------------------- | ------------------------------------------------------ | ------------------------------------- | --------------- |
| Scouts (Step 1)             | Sonnet, medium effort                                  | gpt-5.6-luna, medium reasoning effort | session default |
| Category reviewers (Step 2) | Fable, high effort; Opus if the Fable limit is reached | gpt-5.6-sol, high reasoning effort    | session default |

If the harness cannot set model or effort per subagent, spawn with defaults. The table is an upgrade, not a requirement. Never fail a review over it.

The verify and consolidate pass (Step 3) stays in your own context on the session model.

## Step 1: Gather context

Run these yourself:

1. `git log --oneline $BASE..HEAD` and `git diff --stat $BASE...HEAD` for shape and intent.
2. The full diff: `git --no-pager diff --no-color --patch -U3 --find-renames=50% $BASE...HEAD`
3. Resolve the intent source, what this branch is meant to accomplish, in priority order:
   1. Context you already hold: a spec, task, or plan file the user pointed to, requirements the user stated when invoking the review, or the request that drove an implementation made in this session.
   2. A spec, task, or plan file the branch references, in commit messages or a tasks or specs directory.
   3. The PR or issue description, if the branch has one. Run `gh pr view` and skip quietly if there is no PR.

Keep the diff in context. You pass it to the category subagents in Step 2.

Then launch scouts in parallel as read-only general-purpose subagents. Do not use a locate-only explorer, because the scouts assess code rather than find it.

- **Blast radius**: for each function, type, or export the diff modified or removed, identify upstream callers and dependents. Return a map from changed symbol to callers and dependents.
- **Pattern consistency**: report project conventions from `CLAUDE.md`, `AGENTS.md`, or equivalent rules files. For new or substantially changed code, find similar implementations in the codebase. Return the similar patterns and how they differ from the new code.
- **Test coverage**: for each changed function or module, find its tests, the scenarios they cover, and the edge cases they miss. Return a map from changed symbol to test files, coverage, and gaps.
- **Additional scouts**: launch any others the diff needs, on the same terms.

Wait for all scouts. Note where blast radius, pattern divergence, and test gaps overlap. Those are the highest-risk areas for your verify pass. Do not pass them to subagents.

## Step 2: Spawn category reviewers

Spawn one subagent per category in parallel. Always spawn Correctness, Reliability, and Patterns. Spawn Requirements only when Step 1 resolved an intent source, and pass it or its path in the package. Spawn Tests only when the diff contains test files.

If your harness cannot spawn parallel subagents, apply the category lenses one at a time in your own context using the same package, then continue to Step 3.

### Spawn package

Each subagent receives:

```
**Role**
You are a code reviewer focused on {category}. Apply the {category} lens to this diff.
- The category items are starting points, not a checklist. Flag concrete issues you find, on or off the list.
- The main reviewer verifies, scores, and consolidates your output. Propose a draft Severity from your lens. Do not normalise across findings.
- This is a read-only task. Do not modify code.

**Base ref**
{base ref}

**Full diff**
{the diff from Step 1, or the diff command when the diff exceeds about 500 lines}

**Scout outputs**
{scout reports from Step 1}

**Review category**
{this subagent's section from "What to look for" below}

**Project conventions**
{paths to CLAUDE.md, AGENTS.md, or equivalent}

**Output format**
{the Subagent output format below}

If there are no concrete issues, return exactly `NO FINDINGS.` Do not pad.

**Additional information** (optional)
{anything else this subagent needs, briefly}
```

### Subagent output

Each finding has these fields:

```
**Issue 1** - Short name of issue
**Severity (draft):** Critical | High | Medium | Low
**Category:** Bug | Data | Performance | Reliability | API/Contract | Pattern violation | Test gap | Requirements gap
**File:** `path:line(s)`
**Findings:**
- Concise statement and list of findings

**Evidence:**
- Concise list of evidence, such as call sites, scout output, conventions, files re-read, and checks done

**Fix:**
- Specific changes and approaches, with a minimal snippet if useful
```

### Subagent failure

If a subagent fails or returns garbage, restart it with the same package, up to three failed attempts in total. After the third failure, report it in the Coverage note in Step 4 and continue with what came back.

### What to look for

Starting points, not checklists.

**Requirements**

- The intent source from Step 1 is the spec. Derive acceptance criteria, constraints, and non-goals from it.
  - Missing: acceptance criteria not delivered, or only partly delivered.
  - Unasked: behaviour the spec never asked for, such as extra features, options, config, endpoints, or speculative abstractions.
  - Wrong: criteria that look implemented but do not hold. Trace each acceptance criterion to the code that satisfies it and confirm the behaviour matches.
- Cite the spec line alongside the code reference for each finding.

**Correctness**

- Logic errors, edge cases (null or empty, off-by-one, time zones, leap boundaries), unhandled errors.
- Implicit assumptions (ordering, idempotency, availability) and invalid state transitions.
- Concurrency: races, deadlocks, check-then-act, shared mutable state escaping sync boundaries.
- Logical data integrity: silent truncation, items dropped in transformation, partial writes leaving inconsistent state. Operational data safety (migrations, destructive ops, rollback paths) belongs to Reliability.
- Breaking changes: signature, export, API, or schema shifts. Cross-check against the blast-radius map.
- Hallucinated APIs: fabricated option keys, invented config values, behaviour that does not match the pinned library version.

**Tests**

- Behaviour over implementation: tests assert outcomes users care about, not internal state or private methods.
- Regression coverage: a bug-fix branch ships a test that fails before the fix and passes after.
- Meaningful assertions: no `expect(x).toBeTruthy()` on a never-null object, no snapshots without semantic intent.
- Brittleness: no hard sleeps, order-dependent state, fragile selectors, or live network calls in unit tests.
- Mocking discipline: do not mock the system under test. Do not mock dependencies where integration coverage is required, such as databases, migrations, and message queues. Over-mocking hides real bugs.
- Coverage gaps: flag only when you can name a realistic input or flow that hits the uncovered path.
- Test code quality: held to the same bar as production code. Extract repeated setup and parameterise similar tests.

**Reliability**

- Performance antipatterns with measurable impact: N+1, O(n²), unbounded I/O or memory, missing pagination or indexes, long transactions wrapping slow I/O.
- Resource lifecycle: file handles, connections, and streams released on every path. Verify error paths, not just the happy path.
- Caching: stale data, invalidation races.
- Silent error swallowing and over-broad catches masking specific failure modes.
- Missing timeouts, retries, or circuit breakers on external calls.
- Migrations: reversible and zero-downtime safe. No NOT NULL without a default on large tables, no dropping columns still referenced, no locking backfills.
- Destructive operations without a rollback path or an explicit "accepted loss" note. Logical data loss inside transformations belongs to Correctness.
- Observability: if similar paths emit structured logs, metrics, or traces, new paths should match. Do not prescribe where no pattern exists.

**Patterns**

- Apply the project conventions in the spawn package.
- Search the codebase for utilities the change could have reused. Flag duplication of an already-solved problem.
- Architecture fit: new global mutable state where scoped alternatives exist, layering bypass such as UI reaching persistence, logic in the wrong module, circular dependencies introduced by the diff.
- Misleading names: `getX()` that mutates, `validateX()` that writes, `isX()` with side effects.
- Comment hygiene: flag comments or docstrings that are stale or restate the code instead of explaining why. Missing comments on self-evident code are not a finding.
- Smell baseline. These are judgement calls, never hard violations, and a documented repo standard overrides them:
  - Duplicated code: the same logic shape in more than one hunk. Extract the shared shape.
  - Data clumps: the same few fields or parameters travelling together. Bundle them into one type.
  - Primitive obsession: a primitive or string standing in for a domain concept. Give the concept its own type.
  - Repeated switches: the same switch or if-cascade on the same type recurring across the change. Use polymorphism or one shared map.
  - Shotgun surgery: one logical change forcing scattered edits across many files. Gather what changes together into one module.
  - Speculative generality: abstraction, parameters, or hooks for needs the task does not have. Delete them and inline until a real need appears.

Wait for every subagent before Step 3.

## Step 3: Verify and consolidate

You hold every category finding, the full diff, all scout output, the intent source, and the project conventions.

For each finding:

1. Try to disprove it. Search the codebase for handling that prevents it. Trace call sites, check consumers of changed interfaces, and look for guards or control flow that make the bug unreachable.
2. State the exact trigger: inputs, state, sequence. If no concrete trigger survives, drop the finding as speculation.
3. Score confidence from 0 to 100:
   - 75 to 100: likely real or verified. Concrete trigger, no handling found, checked against call sites.
   - 50 to 74: plausible but uncertain. The trigger needs assumptions you could not confirm.
   - below 50: speculative. No trigger survived, handling probably prevents it, or the cited code does not exist.

Across all surviving findings:

4. Consolidate. Merge findings with the same root cause and refer to duplicates as "See issue #N". Cross-reference related findings.
5. Normalise severity across the full set.
6. Drop Low severity findings, nits, anything below 75 confidence, and anything in code the diff neither changed nor exposed.

Subagents propose. You rule.

## Step 4: Output

### Tests review

Always include this subsection.

- Tests subagent ran with findings: `Tests review: see findings above.`
- Tests subagent ran with no findings: `Tests review: no issues found.`
- Tests subagent skipped and new logic lacks coverage:
  > **Tests review**: Skipped (no test files in diff). New production logic added without coverage: `{symbols from the test coverage scout}`. Review recommended.
- Tests subagent skipped and no new logic either: `Tests review: Skipped (no test files in diff, no new production logic).`

### Coverage note

Include only when a category subagent failed every attempt:

> **Coverage note**: {Category} lens did not complete. This report does not cover {category} concerns.

### Code issues

Report each surviving finding in the Subagent output format, with Severity limited to Critical, High, or Medium and a `**Confidence:** {score}/100` line after it.

Report a recurring issue once and refer to it later as "See issue #N". Leave an empty line between findings.

If none survive: **NO CODE ISSUES.**

### Documentation and artifact recommendations

Advisory only. These are not code issues. Cover:

- public-facing surface changes (API, CLI, config keys, breaking behaviour) that may need README, CHANGELOG, or external doc updates;
- stale references, renamed paths, removed APIs, or non-obvious patterns worth capturing in `CLAUDE.md`, `AGENTS.md`, codebase rules, skills, or equivalent agent artifacts.

For each:

- **File**: path to the doc or artifact, or "new file" when proposing one
- **Recommendation**: what to add or change
- **Reason**: why it helps future readers or agent sessions

If none: **NO RECOMMENDATIONS.**

### Verdict

One line: **Ready to merge**, **Needs work** (Medium issues only), or **Blocked** (any Critical or High).

## Example finding

This generic example shows the format only. Base your findings on the code reviewed, not on this example.

**Issue 1** - Token refresh race condition
**Severity:** High
**Confidence:** 94/100
**Category:** Bug
**File:** lib/auth/session.ts:34
**Findings:**

- Token refresh race condition: concurrent requests can both read an expired token before either writes the new one
- Users get intermittent 401s under concurrent API calls

**Evidence:**

- Traced `refreshToken()` callers in `api-client.ts:89` and `middleware.ts:42`. Both invoke without a dedup guard. No mutex or pending-promise pattern in scope.

**Fix:**

- Wrap the refresh call in a dedup guard so concurrent callers share one in-flight refresh:

```ts
let pending: Promise<Token> | null = null
async function refreshToken() {
  if (!pending) pending = doRefresh().finally(() => { pending = null })
  return pending
}
```

## Rules

- Precision over recall. A shorter report with only real issues beats a longer one with noise.
- Defend findings with evidence when challenged, and withdraw when the evidence is not there.
- Report fixable issues only. Skip micro-optimisations, general quality commentary, and PR summaries.
- Do not explain findings you investigated and dropped.

## Safety

Your only output is the review report. Read source code. Do not change it.
