<!--
Paste the section below into a project's AGENTS.md / CLAUDE.md. Delete the
bullet for any tool the project does not use.
-->

## Codebase intelligence

Orient with these tools before grep, find, or raw file reads. Read raw files for the exact lines
to edit or debug.

- **graphify**, when `graphify-out/graph.json` exists, is the map: a whole-corpus graph of code
  and docs, with some edges INFERRED. Use it for architecture, how subsystems connect, where a
  feature lives, and concepts that span code and docs. Run `graphify query "<question>"`,
  `graphify explain "<concept>"`, or `graphify path "<A>" "<B>"`. The matcher takes words
  literally, so phrase questions in the names the code and docs use. Start from
  `graphify-out/wiki/index.md` when it exists. Read `graphify-out/GRAPH_REPORT.md` only for a
  broad architecture review or when the queries come up short.
  - After changing code, run `graphify update .` (AST only, no LLM cost). After changing docs,
    run `/graphify . --update`. When `graphify-out/wiki/` exists, run
    `/graphify . --update --wiki` after any change, since only that flag refreshes the wiki.
- **codanna**, when its MCP tools are available, gives exact symbols, callers, callees, and
  impact from the code index. Start with `semantic_search_with_context`. When graphify names a
  concept and you need the code behind it, switch to codanna.
