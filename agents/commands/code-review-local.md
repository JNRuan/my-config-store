---
description: Actionable code review of the current branch — scout, review, verify, report
---
# Code Review

Review the current branch against `origin/main` — unless the user specifies a different base ref (e.g. `origin/develop`, a tag, a commit SHA, or a comparison range), in which case use that. Output **only actionable issues**. No summaries, praise, opinions, or process narration. Think about how code *breaks*, not just how it works — challenge assumptions ("what if this isn't true?").

## Phase 1: Gather context

Run directly (no subagents):

Let `BASE` = the user-specified base ref, or `origin/main` if none was given.

1. `git log --oneline $BASE...HEAD` and `git diff --stat $BASE...HEAD` for shape and intent.
2. Fetch the full diff:

   `git --no-pager diff --no-color --patch -U3 --find-renames=50% $BASE...HEAD`

   Keep it in context — you'll pass it inline to the category review subagents in Phase 2.

Then launch these **Explore subagents in parallel** to scout:

- **Blast radius** — for each function/type/export modified or removed, find upstream callers and dependents. Return `{changed symbol → callers}`.
- **Pattern consistency** — for new code, find similar implementations elsewhere in the codebase. Return how the new code diverges or aligns.
- **Test coverage** — for each changed symbol, find existing tests and gaps. Return `{symbol → test files, what they cover, gaps}`.

Wait for all scouts. Note the highest-risk areas where blast radius × pattern divergence × test gaps overlap — this is for your verify pass, not for fanning to subagents.

## Phase 2: Spawn category review subagents

Spawn one subagent per category in parallel. Always spawn Correctness, Security, Reliability, Patterns. Spawn Tests **only if** the diff contains test files.

> **Tool degradation**: if your agentic tool can't spawn parallel subagents, apply the 5 lenses sequentially in your own context using the framing below, then proceed to Phase 3.

### Spawn package

Each subagent receives:

- **Role framing**: "You are a specialist code reviewer focused on {category}. Apply the {category} lens to this diff. The 'What to look for' items are starting points; flag concrete issues you find, on or off the list. The main reviewer will verify, score, and consolidate your output — propose draft Severity from your lens; don't worry about cross-finding normalization."
- **Full diff** (inline) and the **base ref** (for any re-runs the subagent wants).
- **All 3 scout outputs** (inline).
- **Their category's "What to look for" section** (inline — see below).
- **Path to project conventions** if present: `CLAUDE.md`, `AGENTS.md`, `.claude/rules/`. Read if relevant to your lens (Patterns subagent strictly needs these).
- **Output format spec** (below).

### Subagent output

Each subagent returns findings with these fields:

- Severity (draft): Critical | High | Medium | Low
- Category: Bug | Security | Data | Performance | Reliability | API/Contract | Pattern violation | Test gap | UX/Design
- File: `path:line(s)`
- Finding: concise statement
- Why: impact; cite CWE/OWASP if security
- Evidence: what was checked (call sites, scout output, conventions, files re-read)
- Fix: specific change; minimal snippet if useful

If no concrete issues, return exactly `NO FINDINGS.` Do not pad.

### Subagent failure

Restart the subagent once with the same package. If the second attempt also fails, note the gap in the report and proceed with what came back.

### What to look for

Use these as starting points per category, not as exhaustive checklists. The goal is real issues, not bullet coverage. Flag anything concrete you find, on or off the list.

**Correctness**

- Logic errors, edge cases (null/empty, off-by-one, time zones, leap boundaries), unhandled errors
- Implicit assumptions (ordering, idempotency, availability); invalid state transitions
- Concurrency: races, deadlocks, check-then-act, shared mutable state escaping sync boundaries
- Data integrity: partial writes, missing rollbacks, silent truncation, items dropped in transformation
- Breaking changes: signature/export/API/schema shifts — cross-check against the blast-radius map
- Hallucinated APIs: fabricated option keys, invented config values, behavior that doesn't match the pinned library version
- Misleading names: `getX()` that mutates, `validateX()` that writes, `isX()` with side effects
- Stale comments, docstrings, or doc references that no longer match the code after this change
- Comment hygiene: flag comments that restate what the code already says or explain "what" instead of "why". Missing comments on self-evident code are NOT a finding.

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
- Dependencies: known CVEs, typosquats, unpinned versions
- Agentic (only if PR touches agents/skills/tools/memory/prompts): prompt injection from user-controlled content, unbounded tool allow-lists, memory poisoning, vague agent instructions — reference OWASP Agentic Top 10
- Cite CWE/OWASP IDs when relevant

**Reliability**

- Perf antipatterns with measurable impact: N+1, O(n²), unbounded I/O/memory, missing pagination/indexes, long transactions wrapping slow I/O
- Resource lifecycle: file handles, connections, streams released on **all** paths — verify error paths, not just happy path
- Caching: stale data, invalidation races
- Silent error swallowing; over-broad catches masking specific failure modes
- Missing timeouts/retries/circuit breakers on external calls
- Migrations: reversible, zero-downtime-safe — no NOT NULL without default on large tables, no dropping columns still referenced, no locking backfills
- Destructive ops without rollback path or explicit "accepted loss" note
- Feature flags: safe default to ship; clean up dead branches on removal
- Observability: if similar paths emit structured logs/metrics/traces, new paths should match — don't prescribe where no pattern exists

**Patterns**

- Read project conventions: `CLAUDE.md`, `AGENTS.md`, `.claude/rules/`, `` or equivalent
- Search the codebase for utilities the PR could have reused; flag duplication of an already-solved problem
- Architecture fit: new global mutable state where scoped alternatives exist, layering bypass (UI → persistence), logic in the wrong module, circular deps introduced by the diff

Wait for all spawned subagents to complete before Phase 3.

## Phase 3: Verify + Consolidate

You hold all category subagent findings, the full diff, all scout output, and project conventions. Apply the protocol:

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
6. **Drop low severity** - drop any you confirm is Low severity.
7. **Drop anything below 75** - unless your judgment overrides due to functionality, maintainability, or security.  
8. **Drop nits** - drop any findings that are nits unless they hinder functionality or maintainability.

Subagents proposed; you rule.

## Phase 4: Output

### Tests review

Always include this subsection.

- Tests subagent ran with findings: `Tests review — see findings above.`
- Tests subagent ran with no findings: `Tests review — no issues found.`
- Tests subagent skipped (no test files in diff), new logic without coverage exists:
  > **Tests review** — Skipped (no test files in diff). New production logic added without coverage: `{symbols from Test coverage scout}`. Review recommended.
- Tests subagent skipped, no new logic either: `Tests review — Skipped (no test files in diff, no new production logic).`

### Code Issues

For each surviving finding you must report:

```
**Severity**: Critical | High | Medium
**Confidence**: {score}/100
**Category**: eg., Bug | Security | Data | Performance | Reliability | API/Contract | Pattern violation | Test gap | UX/Design
**File**: `path:line(s)`
**Finding**: concise statement of what's wrong
**Why**: impact/consequence; cite CWE/OWASP for security
**Evidence**: what you verified — call sites checked, context read, scenario articulated; include what you tried to disprove and couldn't
**Fix**: specific change; include a minimal snippet if useful
```

Recurring issue → report once, reference later as "See issue #N".
Formatting → ensure that there is an empty line between each finding for readability.

If none survive: **NO CODE ISSUES.**

### Documentation &amp; Artifact Recommendations

Advisory only — these are recommendations, **not** Code Issues. Cover:

- Public-facing surface changes (API, CLI, config keys, breaking behavior) that may warrant README, CHANGELOG, or external doc updates
- Stale references, renamed paths, removed APIs, or non-obvious patterns worth capturing in `CLAUDE.md`, `AGENTS.md`, `.claude/rules/`, skills, or equivalent agent artifacts

For each:

- **File**: path to doc or artifact (or "new file" if proposing one)
- **Recommendation**: what to add/change
- **Reason**: why it helps future readers or agent sessions

If none: **NO RECOMMENDATIONS.**

### Verdict

One line: **Ready to merge** | **Needs work** (medium issues only) | **Blocked** (any critical/high).

## Example finding

- **Severity**: High
- **Confidence**: 91/100
- **Category**: Bug
- **File**: `lib/auth/session.ts:34`
- **Finding**: Token refresh race — concurrent requests both read the expired token before either writes the new one
- **Why**: Intermittent 401s under concurrent API calls
- **Evidence**: Callers in `api-client.ts:89` and `middleware.ts:42` invoke without a dedup guard; no mutex or pending-promise pattern in scope. Tried to disprove by searching axios interceptors and middleware for an existing dedup — none found.
- **Fix**: Share one in-flight refresh:
  ```ts
  let pending: Promise<Token> | null = null
  async function refreshToken() {
    if (!pending) pending = doRefresh().finally(() => { pending = null })
    return pending
  }
  ```

## Rules

- Assume tests pass and code compiles — skip running them
- Read-only review — no file edits
- Report only confirmed issues — silently drop investigated-and-dismissed
- Precision over recall — a short report with real issues beats a long noisy one
- If you can't articulate a concrete trigger, drop the finding
- No praise, summaries, opinions, or process narration in the output

