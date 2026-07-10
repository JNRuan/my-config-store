---
description: Cross-model code review — run /code-review-local in parallel on Claude (Fable) and Codex (GPT-5.6-Sol) via Orca, then synthesize and open crit for human comment. Used for more thorough manually run code reviews.
---
# Cross-Model Code Review

Runs a code review with two different models in parallel: **Claude (Fable, high effort)**, **Codex (GPT-5.6-Sol, high reasoning effort)** — using **Orca** cli too spawn and supervise both. Then synthesize the two reports into one and hand it to **crit** for human comment.

`<BASE>` is the ref passed to this command (branch, tag, or SHA), or `origin/main` .

## Phase 1: Set up the run

Each run gets its own subfolder under `docs/review/`, named time-first so runs sort chronologically (latest last): `<REVIEWDIR>` = `<repo-root>/docs/review/<datetime>-<short-sha>` (e.g. `docs/review/20260612T0934-9b73e0e`). Create it and confirm there's a diff worth reviewing:

```bash
REVIEWDIR="$(git rev-parse --show-toplevel)/docs/review/$(date +%Y%m%dT%H%M)-$(git rev-parse --short HEAD)"
mkdir -p "$REVIEWDIR" && echo "$REVIEWDIR"   # <REVIEWDIR> — substitute this literal path below
git --no-pager diff --stat <BASE>...HEAD     # shape of what's being reviewed
[ -n "$(git diff --name-only <BASE>...HEAD)" ] || { echo "empty diff vs <BASE> — nothing to review"; exit 1; }
```

> `<REVIEWDIR>` carries the review's start time, so each run is unique and the path **cannot** be recomputed later — capture the literal path printed above and substitute it into every block below, along with the resolved `<BASE>` (the command argument, or `origin/main` if none). The two terminal handles likewise need capturing once Phase 2 returns them. Every run leaves its own folder under `docs/review/`.

## Phase 2: Spawn both reviewers via Orca

Boot each agent **interactively** with its model set at launch, in the current worktree:

```bash
orca terminal create --worktree current --title "review:claude-fable" \
  --command "claude --model fable --effort high --permission-mode bypassPermissions" --json

orca terminal create --worktree current --title "review:codex-gpt5.6-sol" \
  --command "codex --model gpt-5.6-sol -c 'model_reasoning_effort=\"high\"' -c 'sandbox_mode=\"workspace-write\"' -c 'sandbox_workspace_write.network_access=true' --ask-for-approval never" --json
```

Capture each terminal **handle** from the `--json` response (`.result.terminal.handle`) as `<H_CLAUDE>` and `<H_CODEX>`, then wait for both to finish booting so they can receive a dispatch:

```bash
orca terminal wait --terminal <H_CLAUDE> --for tui-idle --timeout-ms 120000 --json
orca terminal wait --terminal <H_CODEX>  --for tui-idle --timeout-ms 120000 --json
```

Create one task per worker, then dispatch each into its terminal with `--inject` (Orca injects the spec **plus** a preamble teaching the agent to report back via `orca orchestration send --type worker_done`):

```bash
orca orchestration task-create --task-title "cross-review: claude" \
  --spec "Run /code-review-local skill (it exists and you do not have to check) and follow the prompt, you are reviewing the current branch against base ref <BASE>. When done, write your FULL report to <REVIEWDIR>/claude-review.md — that report file is the only file you may write; do not edit any code. Then report completion." --json
# → task id <T_CLAUDE>
orca orchestration task-create --task-title "cross-review: codex" \
  --spec "Run /code-review-local skill (it exists and you do not have to check) and follow the prompt, you are reviewing the current branch against base ref <BASE>. When done, write your FULL report to <REVIEWDIR>/codex-review.md — that report file is the only file you may write; do not edit any code. Then report completion." --json
# → task id <T_CODEX>

orca orchestration dispatch --task <T_CLAUDE> --to <H_CLAUDE> --inject --json
orca orchestration dispatch --task <T_CODEX>  --to <H_CODEX>  --inject --json
```

> Both agents run in **visible, interactive tabs** in the **current** worktree against the same `<BASE>`, so they review identical code and you can watch them.

## Phase 3: Wait + collect

Block until each worker signals completion. `check --wait` returns one message at a time, so call it **once per worker** (two workers → twice); a 30-minute timeout covers a full review. Heartbeat lines go to stderr — `--json` keeps results on stdout:

```bash
orca orchestration check --wait --types worker_done,escalation --timeout-ms 1800000 --json
orca orchestration check --wait --types worker_done,escalation --timeout-ms 1800000 --json
```

For each `worker_done`, mark its task complete (`orca orchestration task-update --id <task> --status completed --json`). Then confirm each produced a non-empty report (`<REVIEWDIR>/claude-review.md`, `<REVIEWDIR>/codex-review.md`):

- If a worker sent `escalation`, a `check` timed out, or its report file is missing/empty, `orca terminal read --terminal <handle>` to see what its tab is doing (stuck, prompting, crashed). Record which lens completed.
- If **one** worker failed, continue with the survivor but mark the synthesis **single-lens** — the cross-model signal is gone; say so explicitly.
- If **both** failed, stop and report the errors. Do not fabricate a synthesis.

Once each worker's output is collected — report file in hand, or tab read for context if it failed — shut its terminal down so no review agents linger:

```bash
orca terminal close --terminal <H_CLAUDE> --json
orca terminal close --terminal <H_CODEX>  --json
```

Synthesis reads the report files, not the tabs, so closing them now is safe.

## Phase 4: Synthesize

You are **not** judging validity — that's the human's job in crit. Your synthesis does exactly three mechanical things, then writes one markdown file. Read `<REVIEWDIR>/claude-review.md` and `<REVIEWDIR>/codex-review.md`.

1. **Existence check (file-level).** For each finding, confirm its cited file is real (`test -f`) **and** was touched by this branch (appears in `git --no-pager diff --name-only <BASE>...HEAD`). This catches fabricated or untouched *paths* — not fabricated *line numbers* within a real file, which it can't see. Drop findings that fail it; this is the only thing you're allowed to remove on.
2. **Dedupe by identity, not wording.** Merge findings that refer to the **same underlying issue** — same file, overlapping or adjacent lines, same root cause — even when the two models phrase or rate them differently. This is an identity judgment, not a validity one: do not drop the weaker-sounding one, merge them.
3. **Preserve attribution.** Tag every surviving finding `both` | `claude` | `codex`. When you merge across models, keep **both** severity labels (e.g. `Claude: High / Codex: Medium`) rather than picking one. `both` is the cheap confidence cue the human will weigh first.

**Single-lens run** (one worker failed): steps 2–3 collapse to pass-through — nothing to dedupe, and attribution is just the surviving model. Don't fabricate the missing lens.

Write `<REVIEWDIR>/synthesis.md`:

- Header: base ref, branch, which lenses ran, counts (raw per model → after existence filter → after dedupe).
- Findings ordered by attribution (`both` first), then by the higher of the two severities. Each keeps the original `File`, `Finding`, `Why`, `Evidence`, `Fix` fields from the source report(s), plus the attribution tag and both severity labels.
- A short **Dropped (non-existent reference)** appendix listing what the existence check removed and from which model — so the filtering is visible, not silent.

Do not add findings of your own, re-score confidence, or decide which are "real."

## Phase 5: Human gate via crit

Open the synthesis for inline human comment:

```bash
/crit <REVIEWDIR>/synthesis.md
```

crit auto-detects file mode and waits for the human to leave inline comments in the browser. After they finish, read the review file back and report the unresolved comments — that's the human's verdict on the cross-model findings.

## PR Signoff

When you're instructed to post comments on a PR, end each one with a divider followed by the sign-off line:

```markdown
---
Reviewed by Claude Fable 5 and GPT-5.6-Sol with Orca
```

## Rules

- This command coordinates; it does not review. Never substitute a read of the diff for a worker's report — the two spawned workers are the only reviewers.
- Both workers get the **same** `<BASE>` and run in the **same** worktree — identical input is what makes the two reports comparable.
- Synthesis removes only on the existence check. Never drop a finding for being wrong, weak, or one-model-only — surface it with its attribution and let the human rule.
- Report honestly: if a worker failed, if a lens is missing, if auth blocked Codex — say so. A single-lens run is not a cross-model run.
- Read-only end to end. The only writes are the report/synthesis files under `<REVIEWDIR>`.

