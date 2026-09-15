---
name: code-review-orca
description: >-
  Cross-model code and security review of the current branch through Orca:
  Claude and Codex each run code-review-local and security-review-local in
  parallel, the coordinator combines the four reports mechanically, and crit
  collects the human verdict.
disable-model-invocation: true
---
# /code-review-orca

You coordinate. Four Orca workers review; you do not. Never substitute your own read of the
diff for a worker's report.

`/code-review-orca [BASE] [EFFORT]`, both optional, in any order. An argument that is an
effort level (`low`, `medium`, `high`, `xhigh`) is `<EFFORT>`, default `medium`. Any other
argument is `<BASE>`, a branch, tag, or SHA, default `origin/main`.

## Orca contract

Load the `orchestration` skill. Resolve the Orca executable and load the guides it serves for
`orchestration` and `orca-cli`. The guides own command names, flags, response fields, and
recovery commands. This skill owns the workflow, resource ownership, and safety. Do not guess
syntax or repeat a mutation from memory.

Record every run id, terminal handle, task id, and dispatch id when Orca returns it. Orca is
shared with other runs: act only on resources this review created.

## Workers

| Stream          | Skill                   | Claude  | Codex         | Fallback                               |
| --------------- | ----------------------- | ------- | ------------- | -------------------------------------- |
| code review     | `code-review-local`     | `fable` | `gpt-6-astra` | Codex `gpt-5.6-sol` or Claude `opus`   |
| security review | `security-review-local` | `fable` | `gpt-6-astra` | Codex `gpt-5.6-sol` or Claude `opus`   |

All four run at `<EFFORT>`, interactively, in the current worktree, against the same `<BASE>`.
Identical input is what makes the reports comparable.

Boot each with `terminal create` and an explicit `--command`, titled `<stream>:<model>`. The
`nclaude` and `ncodex` aliases run the worker inside its nono sandbox profile:

```bash
nclaude --model <fable|opus> --effort <EFFORT> --permission-mode bypassPermissions
ncodex --model <gpt-6-astra|gpt-5.6-sol> -c 'model_reasoning_effort="<EFFORT>"' --sandbox danger-full-access --ask-for-approval never
```

## Phase 1: Set up

Confirm there is a diff, then create the review folder. Folders are named time-first so runs
sort with the latest last.

```bash
[ -n "$(git diff --name-only <BASE>...HEAD)" ] || { echo "empty diff vs <BASE>: nothing to review"; exit 1; }
git --no-pager diff --stat <BASE>...HEAD
REVIEWDIR="$(git rev-parse --show-toplevel)/docs/review/$(date +%Y%m%dT%H%M)-$(git rev-parse --short HEAD)"
mkdir -p "$REVIEWDIR" && echo "$REVIEWDIR"
```

Record the printed path as `<REVIEWDIR>`. It carries the start time and cannot be recomputed
later. Substitute it, `<BASE>`, and `<EFFORT>` literally in everything below.

## Phase 2: Dispatch

1. Create an Orca run with objective `cross-model code + security review vs <BASE>`.
2. Boot the four terminals from the Workers table. Wait for each to reach `tui-idle`. A
   terminal still starting drops injected input.
3. Create one task per worker from the template below and dispatch it into its terminal with
   inject. Record each dispatch id.
4. Confirm the prompt landed in each terminal. If it left no trace, wait for readiness and
   inject once more.

Task template. `<SKILL>` is the stream's skill. `<REPORT>` is `claude-review.md`,
`codex-review.md`, `claude-security.md`, or `codex-security.md`:

```text
Run /<SKILL> and follow its instructions. The skill exists. Do not check for it. Review the current branch against base ref <BASE>. Write the full report to <REVIEWDIR>/<REPORT>. That report is the only file you may write. Do not edit code. Then report completion.
```

## Phase 3: Collect

Wait with `check --wait` for `worker_done`, `escalation`, and `question` messages, in slices
of at most 540000 ms, or shorter when your command timeout is lower. A delivery repeats until
acknowledged: handle every message in it, acknowledge it, then wait again until all four
dispatches are terminal. A timeout or empty delivery is a checkpoint, not a failure.

- `worker_done`: Orca completes the task and dispatch itself; do not update them by hand.
  Confirm the report file exists and is non-empty. Then release the worker and close its tab,
  in that order. Release settles the ledger and archives the worker's output; the tab came
  from `terminal create`, so an explicit `terminal close --tab` removes it. Do the same after
  a failed report.
- `question`: reply, then keep waiting.
- `escalation`, two consecutive slices with no message from a worker, or a missing or empty
  report: read its terminal. A worker still producing output needs more time. A dead one:
  stop it, release it, close its tab, then retry it once in a fresh terminal on the fallback
  model with the same task text.

Record which lenses completed. A stream that lost one worker continues single-lens, and the
synthesis says so. A stream that lost both is reported missing, never fabricated. If all four
failed, stop and report the errors.

Synthesis reads the report files, not the tabs. Close every tab before it.

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

Invoke `/crit` on `<REVIEWDIR>/synthesis.md` and follow it. It opens the synthesis in the
browser, blocks until the human finishes the review, then names the review output file. Read
that file and report the unresolved comments. That is the human's verdict.

## PR sign-off

When instructed to post comments on a PR, end each one with a divider and the sign-off line:

```markdown
---
:space_invader: Code Review by Claude Fable 5 & GPT-6 Astra, Security Review by Claude Fable 5 & GPT-6 Astra; with Orca
```

## Rules

- All workers get the same `<BASE>` and run in the same worktree.
- Synthesis removes only on the reference and scope check. Never drop a finding for being
  wrong, weak, or one-model-only. Surface it with its attribution and let the human rule.
- Report what happened. A failed worker, a missing lens, or a Codex auth failure is stated
  as such. A single-lens stream is not a cross-model stream.
- Read-only end to end. The only writes are the report and synthesis files under
  `<REVIEWDIR>`.
