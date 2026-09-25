---
name: lean-verify
description: >-
  Prove properties of pure code with Lean 4: triage targets from a path, branch
  diff, or PR, agree the claims with the human in crit, prove them against a
  Lean model, link the model to the real code with a property test, and write
  a report.
disable-model-invocation: true
---
# /lean-verify

You prove claims about small, pure pieces of the user's code. You write a Lean **model** of the code, agree the **claims** with the human, prove each claim against the model, and write a **link test** that checks the real code against the model. The Lean kernel judges the proofs. The human judges the claims.

## Invocation

```text
/lean-verify [TARGET] [PROPERTIES…]
```

`TARGET` is one of:

- a path or symbol: triage that target only;
- a PR number or URL: triage the functions the PR changes;
- `scan`: triage the whole repository;
- omitted: triage the functions changed in `BASE...HEAD`. `BASE` is the base ref the human names, or `origin/main`.

`PROPERTIES` is everything after `TARGET`: plain-English claims, feature specs, tickets, and files the human names. Treat all of it as context for Steps 2 and 3.

## Outcomes

Every claim ends with exactly one outcome:

- **proved**: the proof passes every integrity check in Step 4.
- **false**: you found an input that breaks the claim. Report the input. Keep the claim exactly as approved.
- **stuck**: the time budget ran out. Report the open goal verbatim.
- **declined**: triage routed the target away from Lean.

A claim changes only through the human, in the Step 3 review loop. When a claim resists proof, the claim stays as approved and the outcome is **stuck** or **false**.

## Subagent models

| Role              | Claude          | Codex                  | Other harness   |
| ----------------- | --------------- | ---------------------- | --------------- |
| Scouts (Step 2)   | Sonnet, medium  | gpt-6-luna, xhigh      | session default |

Triage, drafting, proving, and the report stay in your own context on the session model. If the harness cannot set model or effort per subagent, spawn with defaults.

## Step 0: Preflight

1. Check each tool with `command -v`: `elan`, `lake`, `lean`, `uvx`.
2. Call `lean_diagnostic_messages` from lean-lsp-mcp on any `.lean` file in `lean/`. Skip this call when `lean/` does not exist yet.

When a tool is missing, stop. Give the human the steps from `references/setup.md`, section "Install". The human installs tools. You install nothing.

Done when every tool resolves and, if `lean/` exists, the MCP call returns.

## Step 1: Resolve and triage

1. Build the candidate set from `TARGET`:
   - path or symbol: that target;
   - PR: `gh pr diff <N> --name-only`. When HEAD is not the PR head, ask the human to check out the PR branch;
   - `scan`: every source file outside tests, generated code, and vendored code;
   - omitted: `git diff --name-only BASE...HEAD`.
2. Drop every path that matches an `exclude` glob in `.agents/lean-verify.toml`, when that file exists.
3. List what `lean/` already models: `grep -rn "^-- Models:" lean/Proofs`.
4. Route each candidate function to one of:
   - **Lean**: a failure would be costly, the input space is large or unbounded, and a crisp property exists;
   - **property test only**: a crisp property exists and random inputs cover the space well;
   - **none**: reading the code settles correctness, or no crisp property exists.
5. Rank the Lean and property-test candidates on these signals and keep the top five:

   | Raises rank | Lowers rank |
   | --- | --- |
   | Pure and deterministic | I/O, UI, or glue code |
   | Money, permissions, auth, parsing, serialisation, state transitions | Spec still changing |
   | A natural property: round-trip, idempotence, conservation, monotonicity, a state invariant | No property you can state in one sentence |
   | Dense branching or arithmetic | Straight-line code |
   | `fix` commits in `git log` for the file | Rewritten recently with no history |
   | Many callers | One caller |
   | Already modelled in `lean/` and changed since | |

A user-named target skips ranking and takes only a route.

Done when every candidate has a route and a one-line reason. When no candidate routes to Lean or a property test, tell the human how many functions you triaged, why each was routed to none, and stop.

## Step 2: Gather context

Dispatch scouts for each Lean and property-test candidate. Each scout reports, with `path:line` citations:

- the function, its types, and every branch;
- its callers and what they rely on;
- existing tests and their coverage of the branches;
- specs, tickets, comments, and docs that state what the function must do;
- the project's test runner and property-testing library.

Read the human's `PROPERTIES` context yourself.

Done when, for each candidate, you can state its input domain, its output, every branch, and a source for each property you will propose. When the project has no property-testing library, carry that to the brief as a question. Adding a package needs the human's approval.

## Step 3: Draft the model and claims, then brief the human

1. Create the run folder:

   ```bash
   RUNDIR="$(git rev-parse --show-toplevel)/.agents/review/$(date +%Y%m%dT%H%M)-$(git rev-parse --short HEAD)-lean-<topic>"
   mkdir -p "$RUNDIR" && echo "$RUNDIR"
   ```

   `<topic>` is a kebab-case name for the targets, such as `pricing-split`. Record the printed path as `<RUNDIR>`. It carries the start time and cannot be recomputed later.
2. When `lean/` does not exist, create it with `references/setup.md`, section "Bootstrap the Lean project". Then call `lean_diagnostic_messages` on a file in `lean/`. When the call fails, ask the human to reconnect the lean-lsp server (`/mcp` in Claude Code) and retry.
3. For each Lean target, write the model at `lean/Proofs/<App>/<Group>/<Name>.lean` in the layout from `references/setup.md`, section "Project layout". Mirror the source function's branches one for one. Choose Lean types that match the source types: `Int` for a signed integer, not `Nat`.
4. Write each claim as a `theorem` with the proof `sorry`. Put every precondition in a named hypothesis, such as `(h : n > 0)`.
5. Run `lake build` in `lean/`. Fix every error. The only warnings left are `declaration uses 'sorry'`.
6. Write `<RUNDIR>/brief.md` in the shape of `references/brief-template.md`.
7. Present the brief and the model files through the `crit` skill. Run the review loop:
   1. Address every unresolved comment.
   2. Update the brief and the model. Rerun `lake build` after every statement change.
   3. Reopen the brief through `crit` and run the printed next-round command.
   4. Continue until the human completes a round with no comments.

A round with no comments approves the brief. If `crit` is unavailable, run the loop in the conversation and require explicit approval. Silence and an unfinished round are not approval.

## Step 4: Prove and link

### Freeze the claims

The approved brief holds each claim's Lean statement verbatim. From here on, each theorem statement in `lean/` stays identical to the brief, whitespace aside. A needed statement change returns to the Step 3 review loop.

### Prove each claim

1. Record the start time with `date`. The budget is 30 minutes per claim, or the budget the human set.
2. Work the proof through lean-lsp-mcp. Read the goal with `lean_goal` after each tactic and check `lean_diagnostic_messages`. Find lemmas with `lean_local_search`, `lean_loogle`, and `lean_leansearch`. Use tactics the kernel checks: `simp`, `omega`, `decide`, `cases`, `induction`, `exact`. `native_decide` adds an axiom and fails the axioms check.
3. When a goal looks false, hunt for a counterexample: `#eval` the model on boundary values and on inputs the goal suggests. When an input breaks the claim, run the same input through the real code:
   - the real code also breaks the claim: the outcome is **false**. The code likely has a bug;
   - only the model breaks the claim: the model is wrong. Fix the model to match the code and continue.
4. When the budget runs out, the outcome is **stuck**. Copy the open goal from `lean_goal` into your notes.

Leave `sorry` in place for **false** and **stuck** claims. The report names each one.

### Write the link tests

Load the `writing-useful-tests` skill before writing any test.

For each Lean target, whatever its claims' outcomes:

1. Add the model to the `model` executable, following `references/setup.md`, section "Model executable".
2. Write a property test in the project's language and library. It generates inputs inside the preconditions, runs the real function and `lake exe model` on each, and asserts equal outputs. Put it next to the existing tests for that code.
3. Run it. On a mismatch, decide which side is wrong. A wrong model: fix it, then rerun `lake build` and recheck affected proofs. Wrong code: record the input and both outputs for the report. Leave the product code unchanged.

For each property-test-only target, write the property test for its approved claims and run it.

### Run the integrity checks

For every **proved** claim:

1. `lake build` in `lean/` exits 0.
2. The build output has no `declaration uses 'sorry'` warning for the theorem.
3. `#print axioms` lists only `propext`, `Classical.choice`, and `Quot.sound`, or reports no axioms. Run it from a temporary file:

   ```bash
   CHECKDIR="$(mktemp -d)"
   printf 'import Proofs\n#print axioms %s\n' '<Full.Theorem.Name>' > "$CHECKDIR/check.lean"
   (cd lean && lake env lean "$CHECKDIR/check.lean")
   rm -rf "$CHECKDIR"
   ```

4. The theorem statement in `lean/` matches the brief, whitespace aside.

A claim that fails a check is **stuck**, with the failed check as its open goal.

Done when every claim has one outcome with its evidence, and every link test has run.

## Step 5: Report

1. Write `<RUNDIR>/report.md` in the shape of `references/report-template.md`.
2. Give the human, in the conversation: the outcome count per kind, every **false** claim and link-test mismatch with its input, the report path, and every file you created or changed.

Leave all changes uncommitted.
