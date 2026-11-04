# Brief template

Write `<RUNDIR>/plan/brief.html`. This Markdown template describes required content, not a fixed
HTML layout. The brief is the task contract the human approves before planning starts.

Choose the layout, typography, diagrams, and disclosure that suit the task. Use semantic HTML,
readable contrast, and stable section and requirement anchors for review comments. Keep substantive
content readable without scripts. Link to the plan when it exists. Keep assets under
`<RUNDIR>/plan/assets/` and use relative links.

## Metadata and decision request

Identify the title, run, intake source, creation time, and modification time. Summarise the problem,
recommended scope, and what the human is being asked to approve. Approval receipts belong in the
manifest, as `references/run-state.md` defines them.

## Request and supplied material

For an issue or a file, cite it and quote only the text that carries a requirement or constraint.
For an ad-hoc prompt, record the prompt verbatim except for secrets and private data. Replace those
values with `[REDACTED]` before writing the brief.

Identify supplied specifications, designs, screenshots, and prototypes, their source and status,
and which requirements they settle. Assess coverage, conflicts, and gaps before deciding whether
further design work is needed. Reuse adequate material. Create designs only to resolve genuine gaps.
Seek human approval before materially departing from supplied designs.

## Goal, problem, and visuals

Explain what is wrong or missing today, for whom, and the intended outcome. Use the source's terms.
Show a concrete current-to-intended example when it helps the human assess the change.

Use diagrams when they make the change easier to understand than prose alone. Where useful,
compare the current situation with the intended outcome for a journey, process, system context,
or scope. Use paired views or one annotated view, with clear labels and consistent names.
For a new capability, show what is missing today rather than inventing a current implementation.

Reuse supplied diagrams and design screenshots where adequate. Add missing visual explanations
only when useful. Label supplied designs, observed screenshots, and proposed mockups distinctly,
with their provenance. A mockup is not evidence of running behaviour.

## Requirements and acceptance criteria

Number requirements `R-1`, `R-2`, and so on. Each states behaviour an acceptance criterion can test
without reopening the source. Show how the request and subsequent human steering map to them.

Number acceptance criteria `AC-1`, `AC-2`, and so on. Each states observable behaviour, cites the
`R-n` it proves, and names how it will be verified, such as a test, command, or browser check.

## Scope and constraints

State what is in and out of scope. Number constraints `C-1`, `C-2`, and so on, and make each
verifiable. Include security, data handling, architecture, compatibility, and process limits.
Fold human answers into the requirements or constraints they settle while preserving their source.

## Repository findings and assumptions

Cite repository claims with `path:line`. Include findings that affect the approach: current
behaviour, affected code, coverage, and tooling. Distinguish observed facts from recommendations.

Number assumptions `A-1`, `A-2`, and so on. Give each default, its reasoning, the evidence or check
that could confirm it, and the consequence if it is false. A human-owned decision belongs in
Questions rather than Assumptions.

## Questions

Number questions `Q-1`, `Q-2`, and so on. Include ambiguities, missing acceptance criteria, and
source/repository conflicts no reasonable default settles. Order by impact: scope, security and
data handling, user-facing behaviour, then technical detail.

Write each as a full question ending in `?`, followed by what the answer decides. Give one to three
suggested answers and mark the recommended one with its reason. After the answer, retain the ID
and resolution at a stable anchor, link to the section it settled, and remove it from open questions.
