# `orca-implement`

`orca-implement` is a skill for **Claude Code and Codex** that orchestrates implementation work
through [Orca's CLI](https://github.com/stablyai/orca).

It takes a GitHub issue, Linear issue, specification, or prompt through planning, implementation,
verification, review, and optional adversarial QA, then opens a pull request.

This repository contains the skill. [Orca](https://github.com/stablyai/orca) is the external
orchestration runtime and CLI it uses.

## Invoke the skill

Invoke the skill with:

```text
/orca-implement {TASK-REF | prompt | resume <RUN | RUNDIR>}
```

Examples:

```text
/orca-implement #123
/orca-implement ABC-123
/orca-implement .orchestrator/specs/SPEC-APP-AUTH/001-authentication.md
/orca-implement Add CSV export to the reports page
/orca-implement resume 20260720-0003-spec-0-5-0
```

A general request to implement, fix, or build something does **not** trigger the skill. Use
`/orca-implement` when you want this full Orca-backed pipeline. `resume` hands an existing run to a
fresh coordinator session, which reads the manifest and every run artifact before it acts.

## What it does

[`references/routing.md`](./references/routing.md) is the only source for model and effort
assignments. This README describes roles and phases without repeating them.

1. **Intake**: loads the Orca guides and reads the task source.
2. **Setup**: settles the role of the current branch, pins the base, adopts the current Orca
   worktree or creates one, and initialises the manifest.
3. **Scout**: sends routed read-only workers to inspect the affected code and project practices.
4. **Brief approval**: presents `plan/brief.html` and all known questions through the mapped human
   review interface, then records approval of the exact document and referenced assets.
5. **Plan**: drafts and fact-checks `plan/plan.html`, then runs two independent critics per round.
   Material changes to features, approach, proposed fixes, contracts, scope, or safety assumptions
   trigger another round, including changes addressing the critics' own findings. Fact-check changed
   claims after revisions. Wording changes alone do not trigger another round.
6. **Plan approval**: resolves human feedback and obtains approval of the final plan and referenced
   assets before implementation. Material revisions return through critique before approval.
7. **Build**: registers the build tasks and their dependencies, then dispatches workers as
   dependencies merge.
8. **Verify and integrate**: checks, fixes, and merges each task before releasing its dependants.
   After the last merge, a `medium`-or-above run sends one Claude worker to run the built-in
   `/simplify` over the integrated branch, through the same verify-and-merge flow.
9. **Whole-run verification**: runs the project checks, sends a routed read-only worker to verify
   every acceptance criterion, turns unmet criteria into fix tasks, and records any remaining gaps.
   Later passes re-check only the criteria a fix affected.
10. **Review**: runs the routed code and security review lenses, with browser verification in
    parallel in the first round. A later round runs only after a Critical or High fix, up to the
    approved cap. It confirms the previous round's fixes and reports only new findings.
11. **Final adversarial QA**: runs once when the routing policy requires it, then verifies accepted
    fixes.
12. **PR**: pushes only the run branch, opens a PR, then commits the final checkpoint.

The human approves both the brief and final plan, then the coordinator runs autonomously to the PR.
Material changes to the approved plan return through critique and human approval before affected
work proceeds. It also pauses for critical decisions or recovery authorisation required by Orca
Orchestration. A run that cannot finish cleanly ends in a draft PR that states what remains.

Supplied specifications and designs are the design basis. The coordinator assesses coverage and gaps,
reuses adequate diagrams and screenshots, and creates further design work only where needed. Both
HTML authoring templates call for useful visuals and preserve supplied-design provenance. Their
Markdown files describe required content while leaving page layout to the author. Worker tasks and
reports stay in Markdown. There is no separate `proposal.html`.

Approval receipts identify the exact documents and asset revisions. Changed artefacts need renewed
approval; verification and review records identify the code actually checked. Stable decision and
finding IDs preserve reasoning and resolutions across rounds.

## Requirements

Run `/orca-implement` inside Orca.

The environment must provide:

- every worker and coordinator skill mapped in
  [`references/skill-map.md`](./references/skill-map.md);
- the worker runtimes, sandbox profiles, and launch commands required by
  [`references/routing.md`](./references/routing.md);
- GitHub tooling for GitHub intake and PR creation;
- a working Linear connection for Linear intake.

Install Orca from its [official repository](https://github.com/stablyai/orca). The upstream project
documents desktop downloads and package-manager installation, including:

```bash
brew install --cask stablyai/orca/orca
```

## Orca CLI contract

The coordinator uses Orca Orchestration through the `orchestration` skill for supervised workers,
including assignment, messages, follow-ups, recovery, and cleanup. It uses `orca-cli` for other Orca
resources. These skills own CLI mechanics; this pipeline owns workflow and verification policy.
Workers launch through the nono sandbox commands in `references/routing.md` before registration
with Orca Orchestration.

This README does not duplicate CLI syntax. See
[`references/orca-mechanics.md`](./references/orca-mechanics.md) for the pipeline's ownership,
dispatch, collection, and cleanup rules.

## Run artifacts

Each run keeps its artifacts inside the integration worktree at:

```text
<WT-PATH>/.agents/orca/orchestration/<RUN>/
```

The run record reaches the branch through checkpoint commits when the plan is ready, at build
verification, code-review completion, a paused decision, the PR, and abort. Each checkpoint holds
the brief, plan, agent tasks and reports, reviews, summary, and manifest at that HEAD. The run makes
no other record commits. Worker reports and the coordinator's working files go under `scratch/`,
which never reaches the branch.

The artifact set is closed. A run writes these and nothing else:

- `run-state.json`, the run manifest for state transitions and recovery
- `plan/brief.html` and `plan/plan.html`, the approved task contract and specification of record
- `plan/assets/`, supplied designs and selected durable visual evidence with provenance
- `review.html`, approved versus delivered behaviour, review coverage, evidence, and remaining work
- `tasks/`, worker agent tasks and reports
- `review/`, the review of record for every round run, and the QA review when QA runs
- `summary.md`, the run narrative: what happened, acceptance evidence, incidents, lessons for later
  runs, and what remains
- `timeline.md`, one event per line, and `run-page.html`, a status page rendered from it and the
  manifest by `scripts/render-run-page.py` and published for the human when an artifact route is
  available
- `screenshots/`, browser-verification evidence when applicable
- `scratch/`, scout, fact-check, planner, critic, acceptance-check, review-lens, and QA reports

Browser verification stores raw screenshots when applicable. Its report stays in coordinator
context. Selected images used by durable human documents are copied into `plan/assets/` and included
in checkpoint commits. Raw screenshots, scratch files, and the status page remain uncommitted.
The final `review.html` supports PR review without adding a pre-PR approval gate.

The integration worktree and run branch survive until the PR merges. The coordinator removes task
and QA worktrees using only the ids recorded in the manifest.

## References

- [`SKILL.md`](./SKILL.md), the complete pipeline and safety rules
- [`references/routing.md`](./references/routing.md), model routing, complexity tiers, and worker
  boot recipes
- [`references/skill-map.md`](./references/skill-map.md), the skill each role invokes
- [`references/templates/`](./references/templates/), HTML authoring guidance for the brief, plan,
  and final review, plus Markdown agent-task and summary formats
- [`references/context/`](./references/context/), role contexts and dispatch templates loaded by
  phase
- [`references/run-state.md`](./references/run-state.md), the manifest schema and lifecycle states
- [`references/orca-mechanics.md`](./references/orca-mechanics.md), shared Orca dispatch,
  collection, recovery, and resource rules
- [Orca on GitHub](https://github.com/stablyai/orca), the external CLI and runtime
