---
description: "Cross-model code + security review: run /code-review-local (Claude Fable + Codex GPT-5.6-Sol) and /security-review-local (Claude Opus 5 + Codex GPT-5.6-Sol) in parallel via Orca, then synthesize and open crit for human comment. For thorough, manually triggered reviews."
---
# Cross-Model Code + Security Review

Run a code review and a security review of the same branch in parallel, each with two models,
using the Orca CLI to spawn and supervise all four workers. Then synthesize the four reports into
one and hand it to **crit** for human comment.

| Stream | Skill | Workers |
| --- | --- | --- |
| code review | `/code-review-local` | Claude (Fable) and Codex (GPT-5.6-Sol) |
| security review | `/security-review-local` | Claude (Opus 5) and Codex (GPT-5.6-Sol) |

Arguments, both optional, in any order; an argument matching an effort level is `<EFFORT>`, any
other argument is `<BASE>`:

- `<BASE>`: the base ref (branch, tag, or SHA). Default `origin/main`.
- `<EFFORT>`: effort level for every worker, one of `low`, `medium`, `high`, `xhigh` (values both
  CLIs accept). Default `high`. Feeds Claude `--effort` and Codex `model_reasoning_effort`.

## Phase 1: Set up the run

Each run gets its own subfolder under `docs/review/`, named time-first so runs sort
chronologically (latest last): `<REVIEWDIR>` = `<repo-root>/docs/review/<datetime>-<short-sha>`
(e.g. `docs/review/20260612T0934-9b73e0e`). Confirm there's a diff worth reviewing, then create it:

```bash
[ -n "$(git diff --name-only <BASE>...HEAD)" ] || { echo "empty diff vs <BASE>: nothing to review"; exit 1; }
git --no-pager diff --stat <BASE>...HEAD     # shape of what's being reviewed
REVIEWDIR="$(git rev-parse --show-toplevel)/docs/review/$(date +%Y%m%dT%H%M)-$(git rev-parse --short HEAD)"
mkdir -p "$REVIEWDIR" && echo "$REVIEWDIR"   # <REVIEWDIR>: substitute this literal path below
```

> `<REVIEWDIR>` carries the review's start time, so each run is unique and the path **cannot** be
> recomputed later: capture the literal path printed above and substitute it into every block
> below, along with the resolved `<BASE>` and `<EFFORT>`. Capture the terminal handles and
> dispatch ids the same way when Phase 2 returns them.

## Phase 2: Spawn the reviewers via Orca

Bind a Run for this review, then boot the four agents **interactively**, each with its model and
effort set at launch, in the current worktree:

```bash
orca orchestration run-create --objective "cross-model code + security review vs <BASE>" --json

orca terminal create --worktree current --title "review:claude-fable" \
  --command "claude --model fable --effort <EFFORT> --permission-mode bypassPermissions" --json

orca terminal create --worktree current --title "review:codex-gpt5.6-sol" \
  --command "codex --model gpt-5.6-sol -c 'model_reasoning_effort=\"<EFFORT>\"' -c 'sandbox_mode=\"workspace-write\"' -c 'sandbox_workspace_write.network_access=true' --ask-for-approval never" --json

orca terminal create --worktree current --title "security:claude-opus5" \
  --command "claude --model claude-opus-5 --effort <EFFORT> --permission-mode bypassPermissions" --json

orca terminal create --worktree current --title "security:codex-gpt5.6-sol" \
  --command "codex --model gpt-5.6-sol -c 'model_reasoning_effort=\"<EFFORT>\"' -c 'sandbox_mode=\"workspace-write\"' -c 'sandbox_workspace_write.network_access=true' --ask-for-approval never" --json
```

Capture the four terminal **handles** from the `--json` responses (`.result.terminal.handle`) as
`<H_CR_CLAUDE>`, `<H_CR_CODEX>`, `<H_SEC_CLAUDE>`, and `<H_SEC_CODEX>`, then wait for each to
finish booting so it can receive a dispatch:

```bash
orca terminal wait --terminal <H_CR_CLAUDE>  --for tui-idle --timeout-ms 120000 --json
orca terminal wait --terminal <H_CR_CODEX>   --for tui-idle --timeout-ms 120000 --json
orca terminal wait --terminal <H_SEC_CLAUDE> --for tui-idle --timeout-ms 120000 --json
orca terminal wait --terminal <H_SEC_CODEX>  --for tui-idle --timeout-ms 120000 --json
```

Create one task per worker, then dispatch each into its terminal with `--inject` (Orca injects the
spec plus a preamble teaching the agent to report back via `orca orchestration send --type
worker_done`). The four specs are identical except for the skill and the report file:

```bash
orca orchestration task-create --task-title "cross-review: claude" \
  --spec "Run the /code-review-local skill and follow it. The skill exists; do not verify it first. Review the current branch against base ref <BASE>. When done, write your FULL report to <REVIEWDIR>/claude-review.md. That report is the only file you may write; do not edit any code. Then report completion." --json
# → task id <T_CR_CLAUDE>
orca orchestration task-create --task-title "cross-review: codex" \
  --spec "Run the /code-review-local skill and follow it. The skill exists; do not verify it first. Review the current branch against base ref <BASE>. When done, write your FULL report to <REVIEWDIR>/codex-review.md. That report is the only file you may write; do not edit any code. Then report completion." --json
# → task id <T_CR_CODEX>
orca orchestration task-create --task-title "security-review: claude" \
  --spec "Run the /security-review-local skill and follow it. The skill exists; do not verify it first. Review the current branch against base ref <BASE>. When done, write your FULL report to <REVIEWDIR>/claude-security.md. That report is the only file you may write; do not edit any code. Then report completion." --json
# → task id <T_SEC_CLAUDE>
orca orchestration task-create --task-title "security-review: codex" \
  --spec "Run the /security-review-local skill and follow it. The skill exists; do not verify it first. Review the current branch against base ref <BASE>. When done, write your FULL report to <REVIEWDIR>/codex-security.md. That report is the only file you may write; do not edit any code. Then report completion." --json
# → task id <T_SEC_CODEX>

orca orchestration dispatch --task <T_CR_CLAUDE>  --to <H_CR_CLAUDE>  --inject --json
orca orchestration dispatch --task <T_CR_CODEX>   --to <H_CR_CODEX>   --inject --json
orca orchestration dispatch --task <T_SEC_CLAUDE> --to <H_SEC_CLAUDE> --inject --json
orca orchestration dispatch --task <T_SEC_CODEX>  --to <H_SEC_CODEX>  --inject --json
# → capture each dispatch id as <D_CR_CLAUDE> / <D_CR_CODEX> / <D_SEC_CLAUDE> / <D_SEC_CODEX>;
#   Phase 3 cleanup needs them
```

> All four agents run in **visible, interactive tabs** in the **current** worktree against the
> same `<BASE>`, so they review identical code and you can watch them.

## Phase 3: Wait + collect

Block until all four workers report. `check --wait` returns the Run's oldest unacknowledged
Delivery (a batch of up to 50 messages) and replays that same batch until acknowledged with
`--ack`, so the reports may arrive in one batch or across several. Loop: wait, handle every
message in the batch, acknowledge, wait again, until all four dispatches have settled. A
30-minute window covers a full review; `--json` keeps results on stdout, and `--wait` prints
keepalive JSON lines to stderr:

```bash
orca orchestration check --wait --types worker_done,escalation,question --timeout-ms 1800000 --json
# handle the batch, then acknowledge it and wait for the rest:
orca orchestration check --ack <delivery_id> --wait --types worker_done,escalation,question --timeout-ms 1800000 --json
# after the last expected message, acknowledge the final batch:
orca orchestration check --ack <delivery_id> --json
```

Handle each message:

- `worker_done`: Orca marks the task and dispatch completed automatically; do not run
  `task-update`. Confirm the worker's report file under `<REVIEWDIR>` exists and is non-empty,
  then release the worker so no review agents linger:
  `orca orchestration worker-release --dispatch <its dispatch id> --json`. Release after a
  failed report too; never substitute `orca terminal close`.
- `question`: answer it with `orca orchestration reply --id <msg_id> --body "<answer>" --json`,
  then keep waiting.
- `escalation`, a timed-out `check`, or a missing/empty report: `orca terminal read --terminal
  <handle> --json` to see what the tab is doing (stuck, prompting, crashed). A worker that is
  still producing output just needs more time; keep waiting. If it is dead, stop it with
  `orca orchestration worker-stop --dispatch <its dispatch id> --json`.

Record which lenses completed. A stream that lost one worker continues **single-lens**: the
cross-model signal for that stream is gone, and the synthesis must say so. A stream that lost
both workers is reported as missing, never fabricated. If all four workers failed, stop and
report the errors.

Synthesis reads the report files, not the tabs, so releasing the workers now is safe.

## Phase 4: Synthesize

You are **not** judging validity; that is the human's job in crit. Your synthesis does exactly
three mechanical things per stream, then writes one markdown file. Read the four reports:
`<REVIEWDIR>/claude-review.md`, `<REVIEWDIR>/codex-review.md`, `<REVIEWDIR>/claude-security.md`,
and `<REVIEWDIR>/codex-security.md`. Synthesize each stream separately; never merge a code-review
finding with a security finding. If the same issue appears in both streams, keep both entries.

1. **Existence check (file-level).** For each finding, confirm its cited file is real (`test -f`)
   and was touched by this branch (appears in `git --no-pager diff --name-only <BASE>...HEAD`).
   This catches fabricated or untouched *paths*, not fabricated *line numbers* within a real
   file, which it cannot see. Drop findings that fail it; the existence check is the only ground
   for removal.
2. **Dedupe by identity, not wording, within a stream.** Merge findings from the stream's two
   models that refer to the **same underlying issue** (same file, overlapping or adjacent lines,
   same root cause) even when the two models phrase or rate them differently. This is an
   identity judgment, not a validity one: do not drop the weaker-sounding one; merge them.
3. **Preserve attribution.** Tag every surviving finding `both` | `claude` | `codex`. When you
   merge across models, keep **both** severity labels (e.g. `Claude: High / Codex: Medium`)
   rather than picking one. `both` is the cheap confidence cue the human will weigh first.

**Single-lens stream** (one worker failed): steps 2-3 collapse to pass-through for that stream.
There is nothing to dedupe, and attribution is just the surviving model. Don't fabricate the
missing lens.

Write `<REVIEWDIR>/synthesis.md`:

- Header: base ref, branch, effort, which lenses ran, and per-stream counts (raw per model →
  after existence filter → after dedupe).
- Two sections, **Code review** and **Security review**. In each, findings ordered by
  attribution (`both` first), then by the higher of the two severities. Each finding keeps the
  original fields from its source report(s), plus the attribution tag and both severity labels.
- A short **Dropped (non-existent reference)** appendix listing what the existence check removed,
  from which stream and model, so the filtering is visible rather than silent.

Do not add findings of your own, re-score confidence, or decide which are "real."

## Phase 5: Human gate via crit

Invoke the **/crit** skill on `<REVIEWDIR>/synthesis.md` and follow it: it opens the synthesis in
the browser, blocks until the human clicks Finish Review, then names the review output file. Read
that file and report the unresolved comments. That is the human's verdict on the cross-model
findings.

## PR Signoff

When you're instructed to post comments on a PR, end each one with a divider followed by the
sign-off line:

```markdown
---
:space_invader: Code Review by Claude Fable 5 & GPT-5.6-Sol, Security Review by Claude Opus 5 & GPT-5.6-Sol; with Orca
```

## Rules

- This command coordinates; it does not review. Never substitute a read of the diff for a
  worker's report: the four spawned workers are the only reviewers.
- All workers get the **same** `<BASE>` and run in the **same** worktree: identical input is
  what makes the reports comparable.
- Synthesis removes only on the existence check. Never drop a finding for being wrong, weak, or
  one-model-only; surface it with its attribution and let the human rule.
- Report honestly: if a worker failed, a lens is missing, or auth blocked Codex, say so. A
  single-lens stream is not a cross-model stream.
- Read-only end to end. The only writes are the report/synthesis files under `<REVIEWDIR>`.
