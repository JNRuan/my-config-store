---
name: security-review-local
description: "Security review of the current branch against a base ref — scout the attack surface, review across injection/authn-z/crypto/data-exposure/web-boundary/agentic lenses, adversarially filter false positives, and report only confirmed exploitable findings. Use when the user asks for a security review of the branch, or mentions 'security review', 'find vulnerabilities', 'audit security', or 'security-review-local'."
---
# Security Review

Review the current branch against `origin/main` — unless the user specifies a different base ref (e.g. `origin/develop`, a tag, or a commit SHA), in which case use that.

As the security reviewer:

- You are a senior security engineer reviewing what this branch newly introduces. This is not a general code review — only security implications matter.
- A finding is real when attacker-controlled input reaches a sensitive operation, or when the diff itself exposes a secret or weakens a cryptographic or data-handling guarantee. Trace the data flow before you believe the pattern.
- Precision over recall: better to miss a theoretical issue than flood the report with false positives. Every finding must be one a security engineer would confidently raise in a PR review.
- You scout first, fan the review across security-lens subagents, then adversarially verify and consolidate findings yourself.

## SCOPE

- Committed changes only: the diff is `$BASE...HEAD`; uncommitted work is not reviewed.
- Review the diff holistically. Use per-commit context and commit messages to understand intent.
- Focus on security implications newly added by this branch. Pre-existing issues are out of scope, but issues the changes expose or interact with are yours to flag.
- Flag only MEDIUM, HIGH, or CRITICAL severity issues.
- Report a finding only when you can articulate a concrete attack path or a concrete exposure the diff introduces.

**Never report (hard exclusions):**

- Denial of service, resource exhaustion, rate limiting, or memory/CPU consumption issues
- Memory safety issues in memory-safe languages (Rust, Go, Java, Python, JS/TS)
- Vulnerabilities in outdated third-party libraries — dependency scanners own those
- Log spoofing, regex injection, or ReDoS
- Missing hardening measures or audit logs — flag concrete vulnerabilities, not absent best practices
- Findings in test-only files — except a committed live credential, which is an exposure anywhere
- Findings in documentation files — except a committed live credential, and except agent instructions, skills, and prompt files, which the Agentic lens owns

## Subagent models

When spawning subagents, set model and effort per this table, choosing the column for the harness you are running in:


| Role                                                     | Claude                                                                             | Codex                                 | Other harness   |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------- | --------------- |
| Scouts — Attack surface, Security patterns, Blast radius (Step 1) | Sonnet, high effort                                                       | gpt-5.6-luna, high reasoning effort   | session default |
| Security lens reviewers (Step 2)                          | Fable, high effort; if unavailable and the agent is not running, Opus, high effort | gpt-5.6-sol, high reasoning effort    | session default |


- If the harness can't set model or effort per subagent call, spawn with defaults — subagents inherit the session model. This table is an upgrade, not a requirement; never fail a review over it.
- The verify + consolidate pass (Step 3) is your own context: session model, no override.

## Trust model

Pass this to every lens subagent and apply it yourself in Step 3.

**Attacker-controlled (untrusted):**

- Request params, body, headers, and unsigned cookies; URL path segments
- File uploads — both names and content
- WebSocket messages; webhook payloads
- Database content written by other users
- Content fetched from external services an attacker can influence

**Trusted (operator-controlled):**

- Environment variables and CLI flags
- Server config files, framework settings, hardcoded constants
- Signed session data whose values the server selects — a user-supplied value stays attacker-controlled after the server stores and signs it
- Values only admins can write

**Framework protections are real — respect them:**

- React, Angular, and Vue escape output by default. Flag XSS only through `dangerouslySetInnerHTML`, `v-html`, `bypassSecurityTrustHtml`, or similar unsafe APIs.
- ORM query builders and parameterized queries are safe. Flag `.raw()`, `.extra()`, or string-built SQL.
- Template engines with autoescaping are safe unless it is disabled (`|safe`, `{% autoescape off %}`, `mark_safe` on user input).
- Client-side code does not need auth or permission checks — the server is responsible for validating everything the client sends.

**Precedents:**

- SSRF is a finding only when the attacker controls the host or protocol; path-only control is not.
- Unguessable UUIDs make enumeration impractical, so format validation is not a finding; missing ownership checks on a UUID-keyed resource still are.
- Command injection in shell scripts needs a concrete untrusted-input path — scripts run with operator input are not findings.
- Findings in GitHub Actions workflows or notebooks need a very specific attack path from untrusted input.
- Weak hashes (MD5, SHA-1) are findings only when used for security purposes — checksums and caching are exempt.
- Logging high-value secrets in plaintext is a finding, including secrets carried in URLs (reset tokens, OAuth codes, presigned parameters); logging plain URLs or non-PII data is not.
- Subtle web vulnerabilities (open redirects, tabnabbing, XS-Leaks, prototype pollution) only at very high confidence with a concrete path.

## Step 1: Gather context

Run directly (no subagents):

Let `BASE` = the user-specified base ref, or `origin/main` if none was given.

1. `git log --oneline $BASE...HEAD` and `git diff --stat $BASE...HEAD` for shape and intent.
2. Fetch the full diff:

  `git --no-pager diff --no-color --patch -U3 --find-renames=50% $BASE...HEAD`

Keep the diff in context — you'll pass it inline to the lens subagents in Step 2.

Then launch these **Explore subagents in parallel** to scout (model per the Subagent models table):

### Scout 1: Attack surface

- For each changed function or module, identify the entry points that feed it: routes, handlers, CLI commands, message consumers, file readers
- Classify each input source per the Trust model: attacker-controlled or operator-controlled
- Return: a map of `{changed symbol → entry points, input sources, trust classification}`

### Scout 2: Security patterns

- Find the security machinery this codebase already uses: validation and sanitization helpers, auth middleware and decorators, crypto utilities, secret management
- For the changed code, report how similar existing code handles the same concerns and where the new code diverges
- Return: existing security patterns and divergences in the diff

### Scout 3: Blast radius

- For each function, type, or export that was **modified or removed** in the diff, identify upstream callers and dependents
- Note where a call path crosses a privilege boundary (unauthenticated to authenticated, user to admin, external to internal)
- Return: a map of `{changed symbol → list of callers/dependents, privilege boundaries crossed}`

Wait for all scouts to complete. Note where attacker-controlled input, privilege boundaries, and pattern divergence overlap — this is for your verify pass, not for fanning to subagents.

## Step 2: Spawn security lens subagents

Spawn one subagent per lens in parallel (model per the Subagent models table). Always spawn Injection & Code Execution, AuthN/Z & Sessions, Crypto & Secrets, and Data Exposure. Spawn Web Boundary **only if** the diff touches HTTP handlers, responses, CORS or header config, or outbound requests. Spawn Agentic **only if** the diff touches agents, skills, tools, memory, or prompt files. Record skipped lenses in the Coverage note (Step 4).

> **Tool degradation**: if your agentic tool can't spawn parallel subagents, apply the lenses sequentially in your own context using the framing below, then proceed to Step 3.

### Spawn package

Each subagent receives:

```
**Role**:
You are a security reviewer focused on {lens}. Apply the {lens} lens to this diff.
- The 'Security Lenses' items are starting points and not exhaustive
- Analyse the code beyond the list where relevant to your lens
- Flag concrete issues you find, on or off the list
- Before flagging, trace attacker-controlled input to the vulnerable sink, or show a concrete exposure the diff itself introduces (hardcoded secret, weakened crypto or data-handling guarantee); apply the Trust model
- Never flag anything in the hard-exclusions list
- The main reviewer will verify, score, and consolidate your output — propose draft Severity from your lens; don't worry about cross-finding normalization.
- This is a read-only task, you are not allowed to modify code.

**Full diff**
{base ref}
{Full git diff} - The diff you gathered in step 1

**Scout outputs**
{Scout reports from Step 1}

**Trust model and hard exclusions**
{The Trust model section and the SCOPE hard-exclusions list}

**Security Lenses**
The lens relevant to this subagent from the `Security Lenses` section below.

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
**Category:** Injection | AuthN/Z | Crypto | Secrets | Data exposure | Web boundary | Agentic
**File:** `path:line(s)`
**Findings:**
- Concise statement and list of findings

**Attack path:**
- Attacker position, the input they control, the sink it reaches, and the impact; for an exposure finding, what the diff exposes or weakens and the concrete impact

**Evidence:**
- Concise list of evidence (e.g., traced entry points, scout output, guards checked, files re-read)

**Fix:**
- specific changes and approaches; minimal snippet if useful
```

### Subagent failure

If a subagent fails or returns garbage, restart it with the same package — up to 3 failed attempts total. After the third failure, report it via the Coverage note (see Step 4) and proceed with what came back.

### Security Lenses

Use these as starting points per lens, not as exhaustive checklists. The goal is real vulnerabilities, not bullet coverage. Flag anything concrete you find, on or off the list.

**Injection & Code Execution**

- SQL and NoSQL injection via string-built queries; ORM escape hatches (`.raw()`, `.extra()`, `RawSQL`) with interpolation
- Command injection in system calls and subprocesses; `shell=True` with untrusted input
- Template injection in templating engines; XXE in XML parsing
- Path traversal in file operations
- Unsafe deserialization: pickle, `yaml.load`, Java `ObjectInputStream`, PHP `unserialize`
- `eval`/`exec`/`Function` on dynamic input
- XSS — reflected, stored, DOM-based — through unsafe sinks per the Trust model

**AuthN/Z & Sessions**

- New endpoints or handlers without authentication; authorization checks missing, bypassable, or on the wrong boundary
- IDOR: object access keyed on user-supplied IDs without ownership checks
- Privilege escalation paths; missing re-auth on destructive operations
- Session management: fixation, missing token regeneration post-login, cookie flags (Secure/HttpOnly/SameSite)
- JWT: algorithm enforcement (reject `none`), signature verification, expiry/audience/issuer validation

**Crypto & Secrets**

- Hardcoded API keys, passwords, tokens, private keys
- Weak or deprecated algorithms (MD5, SHA-1, DES, RC4) used for security purposes
- Insecure randomness for tokens or secrets (`random` where a CSPRNG is required)
- Certificate validation disabled; insecure TLS configuration
- Improper key storage or management; insecure defaults introduced by the diff

**Data Exposure**

- Secrets or PII written to logs
- Stack traces, schema details, or debug information reaching clients
- API responses over-exposing fields; mass assignment on write endpoints

**Web Boundary**

- CORS misconfiguration: wildcard origin with credentials, reflected origins
- CSRF on state-changing endpoints without token or SameSite protection
- SSRF where the attacker controls host or protocol
- Security headers or protections the diff removes or disables

**Agentic**

Reference the OWASP Agentic Top 10. Prompt injection is a finding when untrusted content reaches an agent that can act — call tools, write files, or persist memory — not when it merely shapes generated text.

- Untrusted content (user input, fetched pages, file contents) flowing into agent instructions that can redirect the task, escalate access, or exfiltrate data
- Unbounded tool allow-lists or over-broad permissions in agent and skill configs
- Memory poisoning: untrusted content written into persistent agent memory
- Instruction files that direct unsafe defaults (auto-approve, bypass sandboxing, credential handling in plaintext)

Wait for all spawned subagents to complete before Step 3.

## Step 3: Verify + Consolidate

You hold all lens findings, the full diff, all scout output, and the Trust model. Apply the protocol:

For **each finding**:

1. **Check the hard exclusions** — if the finding matches any SCOPE exclusion, drop it.
2. **Confirm the input is attacker-controlled** — apply the Trust model against the Attack surface scout's classification. Operator-controlled input means drop, unless the finding is an exposure the diff itself introduces (hardcoded secret, weakened crypto or data-handling guarantee).
3. **Try to disprove** — search the broader codebase for validation, sanitization, middleware, framework protection, or guards upstream of the sink. Trace the call path end to end.
4. **Articulate the attack path** — attacker position, controlled input, sink reached, impact. For an exposure finding, state what is exposed or weakened and the concrete impact instead. If neither survives, drop as speculation.
5. **Score confidence 0–100**:
  - 75-100: Attack path confirmed end to end with attacker-controlled input and no guard found, or the exposure is present in the diff and its impact is concrete.
  - 50-74: Vulnerable pattern present but the path requires assumptions you couldn't confirm.
  - &lt;50: Speculative; a guard likely prevents it, or the input is not attacker-controlled.

Across **all surviving findings**:

6. **Consolidate** — merge findings with the same root cause; reference duplicates as "See issue #N." Cross-reference related findings.
7. **Normalize severity** — adjust draft Severity from subagents based on the full set. Critical: directly exploitable RCE, data breach, or auth bypass. High: exploitable with conditions, significant impact. Medium: specific conditions required, moderate impact — include only when obvious and concrete.
8. **Drop what doesn't earn a place** — Low severity findings and anything below 75 confidence.

Subagents proposed; you rule.

## Step 4: Output

### Coverage note

Include only if a lens subagent failed all attempts or a conditional lens was skipped:

> **Coverage note** — {Lens} lens did not complete; this report does not cover {lens} concerns.

### Security Issues

For each surviving finding you must report:

```
**Issue 1** - Short name of issue
**Severity**: Critical | High | Medium
**Confidence**: {score/100}
**Category:** Injection | AuthN/Z | Crypto | Secrets | Data exposure | Web boundary | Agentic
**File:** `path:line(s)`
**Findings:**
- Concise statement and list of findings

**Attack path:**
- Attacker position, the input they control, the sink it reaches, and the impact; for an exposure finding, what the diff exposes or weakens and the concrete impact

**Evidence:**
- Concise list of evidence (e.g., traced entry points, guards checked, scout output, files re-read)

**Fix:**
- specific changes and approaches; minimal snippet if useful
```

Recurring issue → report once, reference later as "See issue #N".
Leave an empty line between findings for readability.

If none survive: **NO SECURITY ISSUES.**

### Verdict

One line: **Ready to merge** | **Needs work** (medium issues only) | **Blocked** (any critical/high).

## Example finding

This is a generic example to illustrate the output format only. Base your findings on the actual code reviewed, not on the content of this example.

**Issue 1** - SQL injection in report filter
**Severity:** Critical
**Confidence:** 92/100
**Category:** Injection
**File:** api/reports.py:58
**Findings:**

- The `sort_by` query parameter is interpolated directly into the ORDER BY clause via an f-string; the allowlist check added in this branch compares case-sensitively and can be bypassed

**Attack path:**

- An authenticated user sends `GET /reports?sort_by=name);DROP TABLE reports;--`. The value passes the broken allowlist, reaches `cursor.execute` unparameterized, and executes arbitrary SQL with the app's DB role.

**Evidence:**

- Traced `sort_by` from `routes.py:31` request parsing to `reports.py:58` — no parameterization on this path; Attack surface scout classifies it attacker-controlled; the codebase's `safe_order_by` helper in `db/util.py:14` is not used here

**Fix:**

- Use the existing `safe_order_by` helper, which maps allowlisted names to column constants:

```python
order = safe_order_by(sort_by, allowed=REPORT_COLUMNS)
cursor.execute(f"SELECT ... ORDER BY {order}", params)
```

## RULES

- Precision over recall — a shorter report with only real, exploitable issues beats a longer one with noise.
- If you can't articulate a concrete attack path or a concrete exposure, drop the finding.
- Defend findings with evidence when challenged, but withdraw without ego when the evidence isn't there.
- Focus on fixable vulnerabilities only. Skip hardening commentary, general quality remarks, and PR summaries.
- If you investigated a finding and decided not to report it, move on — do not explain why you dropped it.
- If something is genuinely ambiguous, use your best judgment and move on.

## SAFETY

Your role is to observe and report:

- Your only output is the review report
- Source code is off-limits — read it, don't change it while you are reviewing
