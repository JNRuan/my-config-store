# Final-review template

Write `<RUNDIR>/review.html` in Phase 9. This Markdown template describes required content, not a
fixed HTML layout. Choose a layout that helps the human assess delivery and the resulting PR.
Use stable anchors, semantic HTML, readable contrast, and relative links. Keep substantive content
readable without scripts. Link to the approved brief, plan, and technical reviews.

## Outcome and approved intent

Identify the run, source, branch, implementation HEAD, and PR when available. State what was
delivered and what remains. Map the approved requirements and human steering to delivered behaviour
and acceptance results. Identify the approved brief and plan revisions from their receipts.

## Design and delivery

For significant planned changes and `PD-n` decisions, show whether they were built as approved,
changed with approval, or omitted, with reasons and evidence. Identify defaults and human decisions
that affect the result. Distinguish verified fixes from workarounds and accepted risks.

Use before/after examples and selected screenshots where they help assess the change. Reuse supplied
designs for comparison. Copy selected evidence into `plan/assets/` for durable relative links.
Label design mockups and observed behaviour distinctly, with source and code revision.

## Verification and review coverage

Report each criterion and constraint's result, check, evidence path, and tested code revision.
Distinguish planned behaviour, static inspection, executed checks, and unverified behaviour. State
the HEADs actually reviewed and verified, and identify later changes each check does not cover.

Summarise which planner, critic, code-review, security, browser, and QA roles completed or were
missing. Link to the reports rather than duplicating their full contents. Preserve stable finding
IDs, dispositions, fix commits, and reproduction results.

## Remaining work and human action

Show unresolved and deferred findings, accepted risks, workarounds, and verification gaps with their
reason and effect. State whether the PR is a draft and why. Point the human to PR review. This page
adds no separate pre-PR approval gate. PR description format remains owned by `{pr-skill}`.
