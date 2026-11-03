---
name: code-review-orca
description: >-
  Cross-model code and security review of the current branch through Orca:
  Claude and Codex each run code-review-local and security-review-local in
  parallel, the coordinator combines the four reports mechanically, crit
  collects the human verdict, and the coordinator fixes the confirmed findings.
disable-model-invocation: true
---
# /code-review-orca

You coordinate. Four Orca workers review; you do not. Never substitute your own read of the
diff for a worker's report.

`/code-review-orca [BASE] [EFFORT]`, both optional, in any order. An argument that is an
effort level (`low`, `medium`, `high`, `xhigh`) is `<EFFORT>`, default `high`. Any other
argument is `<BASE>`, a branch, tag, or SHA, default `origin/main`.

## Orca contract

Use Orca Orchestration to register and manage supervised workers. Load the `orchestration` skill
and follow its instructions for assignment, messages, follow-ups, recovery, and cleanup. Load
`orca-cli` for separately created terminals and other Orca resources. This skill owns workflow,
model routing, sandbox requirements, resource ownership, and safety.

Record every run, task, dispatch, and worker identity when Orca returns it, including follow-up ids.
Keep the original task identity for each lens and correlate messages with its current task and
dispatch. Record separately created terminals before assignment. Orca is shared with other runs:
act only on resources this review created. Recover worker identities through Orca Orchestration,
not terminal-title matching.

## Workers

| Stream          | Skill                   | Claude | Codex         | Fallback                                                         |
| --------------- | ----------------------- | ------ | ------------- | ---------------------------------------------------------------- |
| code review     | `code-review-local`     | `opus` | `gpt-6-astra` | Claude `fable` for `opus`; Codex `gpt-6.1-sol` for `gpt-6-astra` |
| security review | `security-review-local` | `opus` | `gpt-6-astra` | Claude `fable` for `opus`; Codex `gpt-6.1-sol` for `gpt-6-astra` |

All four run at `<EFFORT>`, interactively, in the current worktree, against the same `<BASE>`.
Identical input is what makes the reports comparable.

Launch every worker through the sandbox commands below in a terminal titled `<stream>:<model>`.
Register it and assign its task through Orca Orchestration. The `nclaude` and `ncodex` aliases run
the worker inside its nono sandbox profile. Preserve those profiles and filesystem grants. Do not
substitute Orca's normal agent launch or an agent's built-in sandbox for these commands:

```bash
nclaude --model <opus|fable> --effort <EFFORT> --permission-mode bypassPermissions
ncodex --model <gpt-6-astra|gpt-6.1-sol> -c 'model_reasoning_effort="<EFFORT>"' --sandbox danger-full-access --ask-for-approval never
```

Apply the same sandbox requirement to processes started for follow-ups, retries, or resume.
Continue an existing worker only through operations that preserve its sandbox. If an operation can
automatically reopen a worker outside nono, assign the work to a terminal launched through these
commands instead. A liveness check alone does not make automatic reopening safe. Resolve uncertain
liveness through Orca Orchestration before launching a replacement. Use the task and prior reports
as context if safe conversation resume is unavailable.

## Phase 1: Set up

Confirm there is a diff, then create the review folder. Folders are named time-first so runs
sort with the latest last.

```bash
[ -n "$(git diff --name-only <BASE>...HEAD)" ] || { echo "empty diff vs <BASE>: nothing to review"; exit 1; }
git --no-pager diff --stat <BASE>...HEAD
REVIEWDIR="$(git rev-parse --show-toplevel)/.agents/review/$(date +%Y%m%dT%H%M)-$(git rev-parse --short HEAD)"
mkdir -p "$REVIEWDIR" && echo "$REVIEWDIR"
```

Record the printed path as `<REVIEWDIR>`. It carries the start time and cannot be recomputed
later. Substitute it, `<BASE>`, and `<EFFORT>` literally in everything below.

## Phase 2: Dispatch

1. Create an Orca run with objective `cross-model code + security review vs <BASE>`.
2. Launch the four sandboxed workers from the Workers table and record their run-owned terminals.
3. Register and assign them through Orca Orchestration, using the task template below. Record the
   returned run, task, dispatch, and worker identities for each lens and its report path.
4. Follow Orca Orchestration's startup and recovery instructions. Resolve uncertain startup before
   attempting another launch or delivering the task again.

Task template. `<SKILL>` is the stream's skill. `<REPORT>` is `claude-review.md`,
`codex-review.md`, `claude-security.md`, or `codex-security.md`:

```text
Run /<SKILL> and follow its instructions. The skill exists. Do not check for it. Review the current branch against base ref <BASE>. Write the full report to <REVIEWDIR>/<REPORT>. That report is the only file you may write. Do not edit code. Then report completion.
```

## Phase 3: Collect

Use Orca Orchestration to collect results, answer questions, and handle escalations. Save the review's
worker identities and report paths before yielding. Correlate messages with this review's current
task and dispatch ids. Keep the review active while workers remain unsettled.

Require a successful completion outcome and a non-empty report from the active attempt for each
completed lens. A settled dispatch with a failed outcome or missing report permits one retry, subject
to Orca Orchestration's recovery requirements. Preserve the original review input and report path.
Use the fallback model in a fresh sandboxed terminal when a worker must be replaced. Retry execution
failures on the same Orca Task; record any new identities returned for follow-up work.

Follow Orca Orchestration for startup uncertainty, stopped workers, retry eligibility, and cleanup.
Respect its recovery limits even when the review still has a retry available. A question or
permission prompt requires resolution, not automatic replacement. Answer within the approved review
scope or ask the human when their decision or authorisation is required. Silence or a timeout alone
does not prove failure or exit.

Record which lenses completed. A stream that lost one worker continues single-lens, and the
synthesis says so. A stream that lost both is reported missing, never fabricated. If all four
failed, stop and report the errors.

Synthesis reads the report files. Resolve worker resources through Orca Orchestration before
synthesis. Use `orca-cli` to clean up separately recorded run-owned terminals only after confirming
their identity and that no worker still uses them. Respect retention and ownership refusals. Record
retained or unresolved resources rather than treating them as closed.

## Phase 4: Synthesise

You are not judging validity; the human does that in crit. Read the four reports under
`<REVIEWDIR>` and treat each stream separately. Never merge a code-review finding with a
security finding. An issue that appears in both streams keeps both entries.

Per stream, three mechanical steps:

1. **Reference and scope check.** Drop a finding when its cited file exists neither at HEAD
   nor at `<BASE>`. A deleted file remains a valid citation. Keep a finding in untouched code
   only when its report traces a causal path to a changed file. These checks do not establish
   that the line numbers or the finding are correct, and failing them is the only ground for
   removal.
2. **Dedupe by identity, not wording.** Merge findings from the stream's two models that
   refer to the same underlying issue (same file, overlapping or adjacent lines, same root
   cause) even when they are phrased or rated differently. Merge; never drop the weaker one.
3. **Preserve attribution.** Tag every surviving finding `both`, `claude`, or `codex`. A
   merged finding keeps both severity labels, for example `Claude: High / Codex: Medium`.

A single-lens stream skips steps 2 and 3: nothing to dedupe, and attribution is the surviving
model.

Write `<REVIEWDIR>/synthesis.md`:

- Header: base ref, branch, effort, which lenses ran, and per-stream counts (raw per model,
  after the reference and scope check, after dedupe).
- Two sections, **Code review** and **Security review**. Order findings by attribution, `both`
  first, then by the higher severity. Each finding keeps the original fields from its source
  report, plus the attribution tag and both severity labels.
- A **Dropped (reference or scope)** appendix listing what step 1 removed, with stream and
  model, so the filtering is visible.

Add no findings of your own. Do not re-score confidence or decide which are real.

## Phase 5: Human gate

Invoke `/crit` on `<REVIEWDIR>/synthesis.md` and follow it. Each comment is the human's ruling
on a finding. Record the ruling in `synthesis.md` and reply to the comment. `synthesis.md` is
the only file you revise during crit rounds.

Finish Review ends a round. Approve ends the review. Run rounds until the human clicks Approve
and crit reports the review approved. The review is then final.

The approved `synthesis.md` is the verdict:

- A code finding with no comment is confirmed for fixing.
- A finding that recommends a change to a document or artifact, such as docs, specs, READMEs,
  or generated pages, is confirmed only when a comment confirms it.
- A commented finding stands as its thread settled it: confirmed, changed, or rejected.

## Phase 6: Fix

Fix every confirmed finding in the current worktree. Where a comment changed a finding, fix it
as the comment says.

## PR sign-off

When instructed to post comments on a PR, end each one with a divider and the sign-off line:

```markdown
---
:space_invader: Code Review by {display names of the code-review models that completed}, Security Review by {display names of the security-review models that completed}; with Orca
```

## Rules

- All workers get the same `<BASE>` and run in the same worktree.
- Synthesis removes only on the reference and scope check. Never drop a finding for being
  wrong, weak, or one-model-only. Surface it with its attribution and let the human rule.
- Report what happened. A failed worker, a missing lens, or a Codex auth failure is stated
  as such. A single-lens stream is not a cross-model stream.
- Read-only until the human approves the review in crit. Until then, the only writes are the
  report and synthesis files under `<REVIEWDIR>`.
