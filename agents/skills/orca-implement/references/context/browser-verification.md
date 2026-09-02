# Browser-verification context

## Load when

Read this file in Phase 6 when the integrated diff needs browser verification.

## Required values

Resolve:

- `{browser-skill}` from `references/skill-map.md`;
- `<WT-PATH>`;
- `<DEV_SERVER_URL_OR_COMMAND>` and `<PORT>` from the plan's Project Tooling;
- `<AFFECTED_PAGES>`;
- `<INTERACTIONS>`;
- `<EXPECTED_RESULTS>`;
- `<RUNDIR>`.

## Context rules

Run headlessly. Require screenshots for passing and failing checks. Undo interactions that change real data. Stop every dev server started during verification.

If the dev server does not start, try at most three times. Use another port, confirm that `.env` exists, and run the project's recorded install command when needed. After the third failure, report `not verified: dev server unavailable` with every startup error.

## Dispatch template

```text
Use /{browser-skill} in headless mode to verify the integrated UI from <WT-PATH>.

Dev server: <DEV_SERVER_URL_OR_COMMAND>
Port: <PORT>
Affected pages: <AFFECTED_PAGES>
Interactions: <INTERACTIONS>
Expected results: <EXPECTED_RESULTS>

Save screenshots to <RUNDIR>/screenshots/ as {description}_{sequence}.png. Capture screenshots for passing and failing checks. Undo any interaction that changes real data. Stop every dev server you start. Report the checks performed, actual results, screenshot paths, and any unverified behaviour.
```
