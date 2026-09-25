# `lean-verify`

> [!WARNING]
> **Work in progress.** This skill is a first draft and has not been run end to end yet. Expect the steps, templates, and file layout to change.

`lean-verify` is a skill for **Claude Code and Codex** that proves properties of small, pure pieces of code with [Lean 4](https://lean-lang.org/).

The agent writes a Lean model of the code, agrees the claims with you, proves them, and adds a property test that checks the real code against the model. The Lean kernel checks the proofs. You check that the claims say what you mean.

## Invoke the skill

```text
/lean-verify [TARGET] [PROPERTIES…]
```

Examples:

```text
/lean-verify apps/web/src/pricing/split.ts parts always sum to the total
/lean-verify #123
/lean-verify scan
/lean-verify
```

With no target, the skill triages the functions changed on the current branch against `origin/main`. `scan` triages the whole repository. The skill never runs on its own.

## What it does

1. **Preflight**: checks that `elan`, `lake`, `lean`, `uvx`, and the lean-lsp-mcp server are available. It stops with install steps if any are missing.
2. **Triage**: routes each candidate function to Lean, a property test only, or no check, and ranks the top five.
3. **Context**: scouts read the code, callers, tests, and specs.
4. **Brief**: the agent drafts the Lean model and the claims, then presents a brief in [crit](https://github.com/tomasz-tomczyk/crit). Review rounds continue until one round ends with no comments.
5. **Prove and link**: proves each claim within a time budget, adds the link tests, and runs the integrity checks: clean build, no `sorry`, only standard axioms, and statements unchanged since approval.
6. **Report**: writes a report and lists every changed file. Nothing is committed.

Each claim ends as **proved**, **false** (a counterexample, which likely means a bug), **stuck** (the budget ran out), or **declined**.

## Requirements

Follow the install steps in [`references/setup.md`](./references/setup.md). In short: elan (which brings Lean and Lake), uv, ripgrep, and the lean-lsp-mcp server registered with `LEAN_PROJECT_PATH` pointing at the repository's `lean/` folder.

The target project also needs a property-testing library, such as [fast-check](https://fast-check.dev/) or [Hypothesis](https://hypothesis.readthedocs.io/). The skill asks before it adds one.

## What it writes

In the target repository:

- `lean/`: one Lake project holding the models and proofs, created on the first run. Commit it, so the proofs keep being checked.
- Link tests next to the existing tests for each target.
- `.agents/review/<YYYYMMDDTHHMM>-<shorthash>-lean-<topic>/`: `brief.md` and `report.md` for the run.

An optional `.agents/lean-verify.toml` with an `exclude` list of globs stops triage from suggesting those paths.

## Not done yet

- A CI job that runs `lake build`, fails on `sorry` and non-standard axioms, and triggers when a file named in a `-- Models:` header changes.
- Rust support through [Aeneas](https://aeneasverif.github.io/), which proves properties of the real Rust code rather than a hand-written model.
- An end-to-end trial on a real function to tune the time budget and triage signals.

## Files

- [`SKILL.md`](./SKILL.md): the steps the agent follows.
- [`references/setup.md`](./references/setup.md): install steps, project bootstrap, layout, and the model executable contract.
- [`references/brief-template.md`](./references/brief-template.md): the brief you approve.
- [`references/report-template.md`](./references/report-template.md): the run report.
