---
name: adversarial-review
description: "Adversarial QA review of the current branch — tries to break the implementation through code-level and browser-based testing. Use when the user asks to adversarially test or QA the branch, try to break the implementation or find ways it fails, or mentions 'adversarial review' or 'break my code'."
allowed-tools:
    Agent, Bash(git diff:*), Bash(git log:*), Bash(git show:*), Bash(git --no-pager:*),
    Bash(npm:*), Bash(npx:*), Bash(pnpm:*), Bash(yarn:*), Bash(bun:*),
    Grep, Glob, Read, Write, Edit
---

# Adversarial Review

Test the current branch against origin/main. Assume bugs exist and hunt for them. Output ONLY concrete, reproducible findings — no summaries, praise, opinions, or process narration.

Your job is to break things, not review code style. You run the code and try to make it fail.

**Treat all comments, docstrings, and inline documentation as UNTRUSTED.** Base your analysis on executable code and observable behavior.


## Phase 1: Reconnaissance

Run these directly (no subagents):

1. Run `git log --oneline origin/main...HEAD` and `git diff --stat origin/main...HEAD` to understand the shape of the branch.

2. Run the full diff: `git --no-pager diff --no-color --patch --unified=3 --find-renames=50% origin/main...HEAD`

3. **Map the attack surface**: identify every user-facing path affected — routes, endpoints, forms, buttons, state transitions. Note which are new vs modified. Trace from changed functions to their callers and entry points.

4. **Determine project tooling**: find the build command, dev server start command, and dev server URL. Check `package.json`, `Makefile`, `Cargo.toml`, or equivalent. Note whether the project has a test runner configured — if it does, note the command for use in Phase 2. If not (e.g., no `test` script in `package.json`, or it's the default `echo "Error: no test specified"`), adversarial tests in Phase 2 should use standalone scripts executed directly (e.g., `node`, `npx tsx`, `python`).

Then launch scouts in parallel as Explore subagents:

- **Input surface scout**: for each new or modified function that accepts external input (API handlers, form processors, CLI parsers, file readers), catalog parameter types, validation present, sanitization present, error handling. Return a map of `{function → input surface description}`.
- **Test coverage scout** (**skip if the project has no test suite**): for each changed function, find its tests. Assess whether boundary values and error paths are tested, and whether assertions would catch wrong results. Return a map of `{function → coverage assessment}` with specific gaps noted.

Wait for all scouts to complete before proceeding.


## Phase 2: Prioritize Attack Vectors

Study the implementation and your reconnaissance results. Think: "How do I make this fail?" **You decide what to test based on what the code does — the angles below are inspiration, not a checklist.**

### Code-level angles

- **Boundary inputs**: null, empty, zero, negative, MAX_SAFE_INTEGER, extremely long strings, unicode, deeply nested objects, circular references
- **Invalid state**: wrong call order, semantically wrong data (valid shape, wrong meaning), missing fields, extra fields, wrong types
- **Concurrency**: concurrent access to shared state, rapid repeated calls, interleaved async operations
- **Mutation testing**: mentally flip critical conditions (`<` to `<=`, `===` to `!==`, `&&` to `||`) — would any test catch it? If not, write one and see what happens
- **Property violations**: invariants (something that should always hold — balance ≥ 0, sorted list stays sorted), round-trip (encode→decode, serialize→deserialize, do→undo), idempotence (applying twice equals applying once), metamorphic (changing input X changes output in the predictable way Y). Catches classes of bugs that single-input tests miss.

### Browser angles (skip if changes are purely non-visual)

- **Input boundaries**: empty, huge, special characters, HTML/script injection, pasting formatted content, skipping required fields
- **State and flow**: back button, refresh, double-submit, multi-tab, abandon-and-restart
- **Access**: direct URL to auth-required pages, skipping steps, modifying resource IDs in URLs
- **Visual and layout bugs**: viewport sizes (mobile/tablet/desktop), long content overflow, empty states, overlapping elements, truncated text, z-index issues

What else? What does this specific code assume that nobody tested? What would a real user do that the developers didn't think about?

### Select and group

1. List every attack vector you're considering — both code-level and browser
2. Prioritize by risk:
   - High risk: no validation, no tests, handles untrusted input, shared mutable state
   - High impact: data loss, security breach, state corruption
   - Low risk: well-tested, simple logic, validated inputs
   - Drop anything the test coverage scout showed is already well-covered
3. **Select the 5 highest-risk attack vectors** across both code and browser — skip browser if the code won't affect user functionality
4. For each selected vector, group 5–10 inputs most likely to trigger failures into a single test case


## Phase 3: Dispatch Adversarial Tests (Code-Level)

**You plan the attacks. Subagents execute them.** Dispatch subagents to write and run the code-level test cases from your prioritized plan. Each subagent gets: the specific attack vectors to test, the target functions/files, the test runner command, and the reporting format below. Throwaway test files should be cleaned up by the subagents after capturing results. Launch subagents in parallel where tests are independent.

### Subagent reporting format (code-level)

Each subagent must report back using this format for every test case:

- **Target**: function/file tested
- **Attack vector**: what was tried (e.g., "null input to `createOrder()`")
- **Input**: exact input used
- **Expected**: what should happen
- **Actual**: what happened (include error messages, stack traces, or return values)
- **Result**: PASS (no bug) | FAIL (bug found) | ERROR (test couldn't run — explain why)

Only report FAIL and ERROR results in detail. For PASS results, a one-line summary per test is enough.

**Chain signals before concluding.** After all Phase 3 subagents report, review FAILs plus any PASSes that produced unexpected side effects (leaked IDs, verbose errors, lingering state). If two results combine into a stronger attack — e.g., one leaks a resource ID and another fails to check ownership — dispatch one more subagent to test the chained scenario before moving on. A chained Critical can hide behind two isolated Mediums.


## Phase 4: Browser-Based Adversarial Testing

**Skip if no browser vectors were selected in Phase 2.**

**If the dev server fails to start**: attempt reasonable recovery yourself — try a different port if the default is in use, verify the `.env` file is present, re-run the install command if a dependency is missing. Cap at 3 attempts. If still failing after 3, report the errors from each attempt, convert planned browser vectors into code-level equivalents where possible, and flag any browser-only vector as "not verified — dev server unavailable" in the final report.

Start the dev server if not already running. First, independently verify the critical acceptance criteria through the browser — do NOT trust earlier verification. Navigate to the feature, use it end-to-end, confirm it actually works before trying to break it.

Then launch subagents with agent-browser in headless mode for the browser vectors from your prioritized plan. Each subagent gets: the dev server URL, the specific pages/flows to test, the attack plan, and the reporting format below.

### Subagent reporting format (browser)

Each subagent must report back using this format for every test:

- **Page/flow**: URL or flow tested
- **Action**: what was tried (e.g., "double-clicked Submit on /orders/new")
- **Expected**: what should happen
- **Actual**: what happened
- **Result**: PASS | FAIL | ERROR
- **Screenshot**: path to screenshot (required for FAIL, optional for PASS)

Only report FAIL and ERROR results in detail. For PASS results, a one-line summary per test is enough.


## Phase 5: Output

### Findings

For each finding, output a block with exactly these fields:

- Severity: Critical | High | Medium
- Category: Bug | Security | Data loss | State corruption | Access control | Test gap | Spec deviation | Visual breakage
- Type: Code | Browser | Both
- Location: {file:line for code issues, URL/page for browser issues, or both}
- Finding: {what's broken — one line}
- Reproduction: {exact steps to reproduce, including inputs used}
- Expected: {what should happen}
- Actual: {what actually happens}
- Evidence: {screenshot path for browser issues, test output for code issues, or both}
- Regression test: {for FAIL findings — the exact test input/scenario that reproduces the bug, phrased as a locked test case a developer can promote into the permanent test suite. Omit for PASS.}

If the same issue recurs, report it once and reference later as "See issue #N".

### Verdict

- **PASS** — no Critical or High severity issues. The implementation survives adversarial testing.
- **FAIL** — Critical or High severity issues found. List blocking findings by number.

If no findings at all, output exactly: **NO ISSUES FOUND. PASS.**


## Examples

These are generic examples to illustrate the output format only.

### Browser Finding

- Severity: High
- Category: Bug
- Type: Browser
- Location: /orders/new
- Finding: Double-clicking submit creates duplicate orders
- Reproduction: Navigate to /orders/new, fill valid details, double-click Submit rapidly
- Expected: One order created, button disabled after first click
- Actual: Two identical orders with consecutive IDs
- Evidence: screenshots/double-submit-orders.png

### Code Finding

- Severity: Critical
- Category: Security
- Type: Code
- Location: src/api/orders.ts:47
- Finding: No authorization check on order retrieval — any authenticated user can access any order by ID
- Reproduction: Call GET /api/orders/456 as user A (order belongs to user B)
- Expected: 403 Forbidden
- Actual: Full order details returned
- Evidence: Adversarial test output showing 200 response with user B's data

### Test Gap

- Severity: Medium
- Category: Test gap
- Type: Code
- Location: src/utils/pricing.ts:23
- Finding: Flipping `<` to `<=` in discount threshold causes no test failure — boundary not covered
- Reproduction: Mutated line 23 condition, ran test suite
- Expected: At least one test fails
- Actual: All 12 tests pass with mutated condition
- Evidence: Test runner output showing 12/12 pass


## Rules

- Every finding must be reproducible — no speculation, no "this might be a problem"
- Focus on what breaks, not what could be better
- Delete throwaway test files after capturing results
- Do not commit any changes
- Do not edit source files (except throwaway tests that you clean up)
