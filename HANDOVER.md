# Handover: remaining `orca-implement` work

## Continuation constraints

- Do not change model or effort values in `agents/skills/orca-implement/references/routing.md`. The user adjusts them manually.
- Keep the `Fable unavailable fallback` column and its Fable-specific fallback rule.
- Do not repeat model or effort assignments in the README or main skill. `routing.md` is the source of truth. The concrete builder examples in `references/plan-template.md` are an approved exception.
- Leave the existing worktree-created terminal handling in Phase 0, Phase 5, Phase 8, and `references/orca-mechanics.md` unchanged.
- Do not use `ask_user_question`. Present one proposed change at a time with its effect and recommendation.
- Do not start another broad review or scouting pass. Apply the known items below, validate, and stop.

## Pending edit 1: Phase 3 drafting and fact checking

The proposed rewrite was approved for discussion but has not been applied.

In `agents/skills/orca-implement/SKILL.md`, restructure Phase 3 Steps 1 through 3 without changing the existing planner prompt, retry limits, draft selection, synthesis rules, or fact-check prompt.

Use this structure:

### Step 1: Set the plan-review tier

1. Classify `plan_review_tier` from requirements and scout evidence.
2. Read its cap from `references/routing.md`.
3. Record both in `run-state.json`.
4. State that the tier remains fixed through plan critique.

### Step 2: Draft the plan

Split the procedure into:

- **Prepare the planner brief**: approved brief, scout evidence, open assumptions, project tooling verbatim, and the structure from `references/plan-template.md`. The brief must stand alone and be identical for each planner.
- **Dispatch planners**: record `<WT>` HEAD, start routed planners, wait for readiness, create `plan-draft-<P>`, dispatch the existing prompt, and record task and dispatch ids.
- Keep the existing collection, one-retry-per-planner, zero/one/two-draft outcomes, read-only check, synthesis, and cleanup instructions.

### Step 3: Fact-check the plan

Split the procedure into:

1. record `<WT>` HEAD;
2. create `plan-fact-check`;
3. start the routed worker;
4. wait for readiness;
5. dispatch the existing prompt;
6. collect through the bounded-wait rules and require a non-empty report;
7. retry one failed, overdue, or reportless run on a fresh routed terminal with the same task;
8. abort if the retry fails, without substituting another model;
9. run the read-only collection check;
10. commit the report and manifest;
11. close the terminal;
12. correct every reported mismatch before starting critique.

## Pending edit 2: README setup wording

Phase 0 no longer performs the old runtime, terminal-handle, repository-registration, or base-cleanliness checks. The README still claims that it does.

In `agents/skills/orca-implement/README.md`:

```diff
-2. **Preflight**: checks the Orca runtime, terminal, repository, and base.
+2. **Setup**: loads the Orca guidance, pins the base, creates the run and
+   integration worktree, and initialises the manifest.
```

Simplify `## Requirements` so it does not prescribe the removed checks. Keep these requirements:

- run the skill inside Orca;
- mapped worker and coordinator skills are available;
- worker runtimes, sandbox profiles, and launch commands from `routing.md` are available;
- GitHub tooling is available when needed;
- Linear connectivity is available when needed.

Remove the bullets requiring an explicit `orca status` check, `$ORCA_TERMINAL_HANDLE` check, `orca repo list` check, and clean base checkout.

## Pending consistency checks

After the two edits above:

1. Confirm every `run-state.json` field and status used by `SKILL.md` matches `references/run-state.md`.
2. Confirm Phase 8 uses `qa.status`, `qa.reason`, and canonical QA states.
3. Confirm Phase 9 uses run status `pr`, never `shipped`.
4. Confirm task records distinguish `pending`, `ready`, `dispatched`, `completed`, `merged`, and `failed`.
5. Explicitly inspect the new untracked references:
   - `agents/skills/orca-implement/references/orca-mechanics.md`
   - `agents/skills/orca-implement/references/run-state.md`
6. Confirm no unrelated files are included.

## Final validation

Run:

```bash
git diff --check
```

Validate every fenced JSON example in `references/run-state.md` with `json.loads`.

Check that every relative Markdown file link resolves.

Search for stale terms:

```text
plan-gate-skill
understanding-check-skill
understanding.md
status: shipped
shipped result
shipped PR
adversarial_qa:
Luna/
Fable and Sol
draft-<fable
critique-<fable
```

Run one final advisor review after validation. Apply only confirmed corrections, then report the changed files and remaining risks.
