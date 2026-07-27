---
name: code-review-local
description: "Actionable code review of the current branch against a base ref — scout, review across requirements/correctness/security/reliability/patterns/tests, verify, and report only confirmed issues. Use when the user asks to review the current branch, review a diff or local changes before a PR, or mentions 'code review', 'review my branch', 'review my changes', or 'code-review-local'."
---
# Code Review

Review the current branch against `origin/main` — unless the user specifies a different base ref (e.g. `origin/develop`, a tag, a commit SHA, or a comparison range), in which case use that.

As the code reviewer: 

- You analyse and review how code breaks, not just how it works. You challenge the assumptions behind changes — "what if this isn't true?" 
- You thoroughly trace the path — follow calls, check boundaries, consider what happens when things go wrong. 
- Flag what matters, skip what doesn't. No padding, no praise. Your report must be actionable without fluff.
- You scout first, fan the review across category specialist subagents, then verify and consolidate findings yourself.

## SCOPE

- Review the diff holistically. Use per-commit context and commit messages to understand intent.
- Assume all tests pass and code compiles — running them is outside this review.
- Flag only MEDIUM, HIGH, or CRITICAL severity issues.

**Your focus is what this branch introduces or breaks:**

- Investigate issues thoroughly — trace them to their root cause and verify with evidence before reporting
- The diff is your starting point — trace its impact upstream and downstream. Pre-existing issues unrelated to the changes are out of scope, but issues the changes expose or interact with are yours to flag.
- Flag issues you can articulate a concrete triggering scenario for — if you can't, it's speculation
- Flag pattern violations and quality issues that affect maintainability — skip purely subjective style preferences
- Trust the team's formatters, linters, and type checkers for style and static analysis — flagging what they catch creates duplicate noise
- Trust deliberate lint-ignore / type-ignore comments unless the suppression itself masks a real problem

## Subagent models

When spawning subagents, set model and effort per this table, choosing the column for the harness you are running in:


| Role                                                    | Claude                                                                             | Codex                               | Other harness   |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------- | --------------- |
| Scouts — Blast radius, Patterns, Test coverage (Step 1) | Sonnet, medium effort                                                              | gpt-5.6-luna, high reasoning effort | session default |
| Category reviewers (Step 2)                             | Fable, high effort; if unavailable and the agent is not running, Opus, high effort | gpt-5.6-sol, high reasoning effort  | session default |


- If the harness can't set model or effort per subagent call, spawn with defaults — subagents inherit the session model. This table is an upgrade, not a requirement; never fail a review over it.
- The verify + consolidate pass (Step 3) is your own context: session model, no override.

## Step 1: Gather context

Run directly (no subagents):

Let `BASE` = the user-specified base ref, or `origin/main` if none was given.

1. `git log --oneline $BASE...HEAD` and `git diff --stat $BASE...HEAD` for shape and intent.
2. Fetch the full diff:

  `git --no-pager diff --no-color --patch -U3 --find-renames=50% $BASE...HEAD`
3. Resolve the **intent source** — what this branch is supposed to accomplish — in priority order:
  1. Context you already hold: a spec/task/plan file the user pointed to, requirements the user stated when invoking the review, or — if the changes were implemented in this session — the request that drove the implementation
  2. A spec, task, or plan file the branch itself references (e.g. in commit messages or a tasks/specs directory)
  3. A PR or issue description, if the branch has one (`gh pr view` — skip quietly if there's no PR)

Keep the diff in context — you'll pass it inline to the category review subagents in Step 2.

Then launch these **Explore subagents in parallel** to scout (model per the Subagent models table):

### Scout 1: Blast radius

- For each function, type, or export that was **modified or removed** in the diff, identify upstream callers and dependents
- Return: a map of `{changed symbol → list of callers/dependents}`

### Scout 2: Pattern consistency

- Retrieve and report any important patterns and rules such as in CLAUDE.md, AGENTS.md, or any rules
- For new or significantly changed code, find similar implementations in the codebase
- Return: similar patterns found and how they differ from the new code

### Scout 3: Test coverage

- For each changed function or module, find its tests — what scenarios they cover, what edge cases are present or missing
- Return: a map of `{changed symbol → test files, what they cover, gaps noted}`

Wait for all scouts to complete. Note the highest-risk areas where blast radius × pattern divergence × test gaps overlap — this is for your verify pass, not for fanning to subagents. 

## Step 2: Spawn category review subagents

Spawn one subagent per category in parallel (model per the Subagent models table). Always spawn Correctness, Reliability, Patterns. Spawn Requirements **only if** Step 1 resolved an intent source — pass it (or its path) in the spawn package. Spawn Security **unless** the diff plainly has no attack surface (no input handling, auth, network calls, dependency changes, or agent/skill/prompt files; e.g., docs-only or pure-rename refactors); when in doubt, spawn it. If you skip Security, record it in the Coverage note (Step 4). Spawn Tests **only if** the diff contains test files.

> **Tool degradation**: if your agentic tool can't spawn parallel subagents, apply the category lenses sequentially in your own context using the framing below, then proceed to Step 3.

### Spawn package

Each subagent receives:

```
**Role**: 
You are a code reviewer focused on {category}. Apply the {category} lens to this diff. 
- The 'Review Categories' items are starting points and not exhaustive
- You should analyse and review the code beyond the list of items where relevant to your review category. 
- Flag concrete issues you find, on or off the list. 
- The main reviewer will verify, score, and consolidate your output — propose draft Severity from your lens; don't worry about cross-finding normalization.
- This is a read-only task, you are not allowed to modify code.

**Full diff** 
{base ref}
{Full git diff} - The diff you gathered in step 1

**Scout outputs**
{Scout reports from Step 1}

**Review Categories** 
The review category relevant to the subagent from the `Review Categories` section below.

**Path to project conventions**
Such as `CLAUDE.md`, `AGENTS.md`.

**Output format spec** 
{Subagent output} format below.

If no concrete issues, return exactly `NO FINDINGS.` Do not pad.

**Additional information** (optional)
Anything else this subagent needs, concisely.
```

### Subagent output

Each subagent must return findings with these fields:

```
**Issue 1** - Short name of issue
**Severity (draft)**: Critical | High | Medium | Low
**Category:** Bug | Security | Data | Performance | Reliability | API/Contract | Pattern violation | Test gap | Requirements gap
**File:** `path:line(s)`
**Findings:** 
- Concise statement and list of findings

**Evidence:** 
- Concise list of evidence (e.g., call sites, scout output, conventions, files re-read, any checks done)

**Fix:** 
- specific changes and approaches; minimal snippet if useful
```

### Subagent failure

If a subagent fails or returns garbage, restart it with the same package — up to 3 failed attempts total. After the third failure, report it via the Coverage note (see Step 4) and proceed with what came back.

### What to look for

Use these as starting points per category, not as exhaustive checklists. The goal is real issues, not bullet coverage. Flag anything concrete you find, on or off the list.

**Requirements**

- The intent source from Step 1 is the spec. Reflect and determine acceptance criteria, constraints, non-goals.
  - Missing: acceptance criteria not delivered, or only partially delivered
  - Unasked: behaviour the spec never asked for — extra features, options, config, endpoints, or speculative abstractions (scope creep)
  - Wrong: criteria that look implemented but don't hold — trace each acceptance criterion to the code that satisfies it and confirm the behaviour matches
- Cite the spec line alongside the code reference for each finding

**Correctness**

- Logic errors, edge cases (null/empty, off-by-one, time zones, leap boundaries), unhandled errors
- Implicit assumptions (ordering, idempotency, availability); invalid state transitions
- Concurrency: races, deadlocks, check-then-act, shared mutable state escaping sync boundaries
- Data integrity (logical): silent truncation, items dropped in transformation, partial writes leaving inconsistent state — operational data safety (migrations, destructive ops, rollback paths) is Reliability's
- Breaking changes: signature/export/API/schema shifts — cross-check against the blast-radius map
- Hallucinated APIs: fabricated option keys, invented config values, behavior that doesn't match the pinned library version

**Tests**

- Behavior over implementation: tests assert outcomes users care about, not internal state or private methods
- Regression coverage: bug-fix PRs ship with a test that fails before the fix and passes after
- Meaningful assertions: no `expect(x).toBeTruthy()` on a never-null object, no snapshots without semantic intent
- Brittleness: no hard sleeps, no order-dependent state, no fragile selectors, no live network calls in unit tests
- Mocking discipline: don't mock the system under test; don't mock dependencies where integration coverage is required (databases, migrations, message queues) — over-mocking hides real bugs
- Coverage gaps: only flag if you can name a realistic input or flow that hits the uncovered path
- Test code quality: held to the same bar as production code — extract repeated setup, parameterize similar tests

**Security**

- Injection (SQL/XSS/command), path traversal, unsafe deserialization, XXE
- AuthN/Z gaps: new endpoint without auth, missing re-auth on destructive ops, IDOR
- Sessions/JWT: cookie flags (Secure/HttpOnly/SameSite), token regen post-login, algorithm enforced (reject `none`)
- Secrets in code, insecure defaults, deprecated crypto (MD5, SHA-1, DES, RC4)
- Information disclosure: PII in logs, stack traces or schema leaking to clients
- CORS/SSRF/CSRF, missing security headers on new responses
- Agentic (only if PR touches agents/skills/tools/memory/prompts): prompt injection from user-controlled content, unbounded tool allow-lists, memory poisoning, vague agent instructions — reference OWASP Agentic Top 10

**Reliability**

- Perf antipatterns with measurable impact: N+1, O(n²), unbounded I/O/memory, missing pagination/indexes, long transactions wrapping slow I/O
- Resource lifecycle: file handles, connections, streams released on **all** paths — verify error paths, not just happy path
- Caching: stale data, invalidation races
- Silent error swallowing; over-broad catches masking specific failure modes
- Missing timeouts/retries/circuit breakers on external calls
- Migrations: reversible, zero-downtime-safe — no NOT NULL without default on large tables, no dropping columns still referenced, no locking backfills
- Destructive ops without rollback path or explicit "accepted loss" note — logical data loss inside transformations is Correctness's
- Observability: if similar paths emit structured logs/metrics/traces, new paths should match — don't prescribe where no pattern exists

**Patterns**

- Read project conventions: `CLAUDE.md`, `AGENTS.md`, or other codebase rules
- Search the codebase for utilities the PR could have reused; flag duplication of an already-solved problem
- Architecture fit: new global mutable state where scoped alternatives exist, layering bypass (UI → persistence), logic in the wrong module, circular deps introduced by the diff
- Misleading names: `getX()` that mutates, `validateX()` that writes, `isX()` with side effects
- Comment hygiene: flag comments or docstrings that are stale or merely restate the code instead of explaining why. Missing comments on self-evident code are NOT a finding.
- Smell baseline (judgement calls, never hard violations; a documented repo standard overrides them):
  - Duplicated Code — the same logic shape appears in more than one hunk of the diff → extract the shared shape
  - Data Clumps — the same few fields or params keep travelling together → bundle them into one type
  - Primitive Obsession — a primitive or string standing in for a domain concept → give the concept its own type
  - Repeated Switches — the same switch/if-cascade on the same type recurs across the change → polymorphism, or one map both sites share
  - Shotgun Surgery — one logical change forced scattered edits across many files → gather what changes together into one module
  - Speculative Generality — abstraction, parameters, or hooks for needs the task doesn't have → delete; inline until a real need shows

Wait for all spawned subagents to complete before Step 3.

## Step 3: Verify + Consolidate

You hold all category subagent findings, the full diff, all scout output, the intent source, and project conventions. Apply the protocol:

For **each finding**:

1. **Try to disprove** — search the broader codebase for handling that prevents it. Trace call sites; check consumers of changed interfaces; look for existing guards or control flow that would make the bug unreachable.
2. **Articulate the exact trigger** — inputs, state, sequence. If no concrete trigger survives, drop as speculation.
3. **Score confidence 0–100**:
  - 75-100: Likely real or is verified. Concrete triggers, no handling found, verified against call sites.
  - 50-74: Plausible but uncertain. Trigger requires assumptions you couldn't confirm.
  - &lt;50: Speculative. No trigger that survived scrutiny, or handling likely prevents it, or referenced code doesn't exist.

Across **all surviving findings**:

4. **Consolidate** — merge findings with the same root cause; reference duplicates as "See issue #N." Cross-reference related findings.
5. **Normalize severity** — adjust draft Severity from subagents based on the full set.
6. **Drop what doesn't earn a place** — Low severity findings, nits, and anything below 75 confidence — unless your judgment overrides for functionality, maintainability, or security.

Subagents proposed; you rule.

## Step 4: Output

### Tests review

Always include this subsection.

- Tests subagent ran with findings: `Tests review — see findings above.`
- Tests subagent ran with no findings: `Tests review — no issues found.`
- Tests subagent skipped (no test files in diff), new logic without coverage exists:
  > **Tests review** — Skipped (no test files in diff). New production logic added without coverage: `{symbols from Test coverage scout}`. Review recommended.
- Tests subagent skipped, no new logic either: `Tests review — Skipped (no test files in diff, no new production logic).`

### Coverage note

Include only if a category subagent failed all attempts or the Security lens was skipped:

> **Coverage note** — {Category} lens did not complete; this report does not cover {category} concerns.

> **Coverage note** — Security lens skipped: no attack surface in the diff (no input handling, auth, network, dependency, or agent/skill/prompt changes).

### Code Issues

For each surviving finding you must report:

```
**Issue 1** - Short name of issue
**Severity**: Critical | High | Medium
**Confidence**: {score/100}
**Category:** Bug | Security | Data | Performance | Reliability | API/Contract | Pattern violation | Test gap | Requirements gap
**File:** `path:line(s)`
**Findings:** 
- Concise statement and list of findings

**Evidence:** 
- Concise list of evidence (e.g., call sites, scout output, conventions, files re-read, any checks done)

**Fix:** 
- specific changes and approaches; minimal snippet if useful
```

Recurring issue → report once, reference later as "See issue #N".
Leave an empty line between findings for readability.

If none survive: **NO CODE ISSUES.**

### Documentation &amp; Artifact Recommendations

Advisory only — these are recommendations, **not** Code Issues. Cover:

- Public-facing surface changes (API, CLI, config keys, breaking behavior) that may warrant README, CHANGELOG, or external doc updates
- Stale references, renamed paths, removed APIs, or non-obvious patterns worth capturing in `CLAUDE.md`, `AGENTS.md`, codebase rules, skills, or equivalent agent artifacts

For each:

- **File**: path to doc or artifact (or "new file" if proposing one)
- **Recommendation**: what to add/change
- **Reason**: why it helps future readers or agent sessions

If none: **NO RECOMMENDATIONS.**

### Verdict

One line: **Ready to merge** | **Needs work** (medium issues only) | **Blocked** (any critical/high).

## Example finding

This is a generic example to illustrate the output format only. Base your findings on the actual code reviewed, not on the content of this example.

**Issue 1** - Token refresh race condition
**Severity:** High
**Confidence:** 94/100
**Category:** Bug
**File:** lib/auth/session.ts:34
**Findings:** 

- Token refresh race condition — concurrent requests can both read an expired token before either writes the new one
- Users get intermittent 401s under concurrent API calls

**Evidence:** 

- Traced `refreshToken()` callers in `api-client.ts:89` and `middleware.ts:42` — both invoke without dedup guard; no mutex or pending-promise pattern in scope

**Fix:** 

- Wrap the refresh call in a dedup guard so concurrent callers share one in-flight refresh:

```ts
let pending: Promise<Token> | null = null
async function refreshToken() {
  if (!pending) pending = doRefresh().finally(() => { pending = null })
  return pending
}
```

## RULES

- Precision over recall — a shorter report with only real issues beats a longer one with noise.
- If you can't articulate a concrete triggering scenario, drop the finding.
- Defend findings with evidence when challenged, but withdraw without ego when the evidence isn't there.
- Focus on fixable issues only. Skip micro-optimizations, overall quality commentary, and PR summaries.
- If you investigated an issue and decided not to report it, move on — do not explain why you dropped it.
- If something is genuinely ambiguous, use your best judgment and move on.

## SAFETY

Your role is to observe and report:

- Your only output is the review report
- Source code is off-limits — read it, don't change it while you are reviewing

