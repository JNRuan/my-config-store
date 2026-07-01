# Codebase intelligence — graphify + codanna

<!--
Three drop-in AGENTS.md / CLAUDE.md sections below. Pick the one matching what's
wired up in the target project — both tools, graphify only, or codanna only —
and delete the other two headings and their content. Each section is
self-contained and guarded ("when ... exists / available") so it degrades
gracefully within its own scope.
-->

## Both — graphify + codanna

This project has two codebase-intelligence layers. Use them **before** grep/find/raw file reads:
graphify is the *map*, codanna is the *precision instrument*, raw files are the *last step*.

- **graphify** — whole-corpus knowledge graph (code **and** docs): architecture, "how does X
  work", how subsystems relate, where a feature lives, cross-cutting or conceptual questions.
  Coarse-grained, includes non-code, edges may be INFERRED.
- **codanna** — code intelligence (MCP tools): semantic *intent* search over code,
  plus exact definitions, who calls what, and blast radius. Fine-grained, code-only, live and accurate.

### Which one to reach for

| You want… | Reach for |
| --- | --- |
| Orientation: architecture, "how does X work", where a feature lives, how subsystems connect, or a concept spanning code *and* docs/specs | **graphify** — `query` / `explain` / `path`, or the wiki |
| The live code behind a behaviour semantically described, e.g., "How does auth work?" | **codanna** — `semantic_search_docs`, then trace with the symbol tools |
| Exact symbol: definition, signature, the real function behind a name | **codanna** — `find_symbol` / `search_symbols` |
| Who calls this / what does it call | **codanna** — `find_callers` / `get_calls` |
| "What breaks if I change this" before a refactor | **codanna** — `analyze_impact` |
| Exact lines to edit or debug | read the file — but orient with the layers above first |

**Tie-breaker:** both run semantic search, but graphify's graph is a snapshot with inferred edges —
once you want the *live, exact* code behind an intent, to trace onward, switch to codanna's
`semantic_search_docs`.

### graphify — when `graphify-out/graph.json` exists

Treat any natural-language question about the codebase as a graph query *first* — these return a
scoped subgraph, usually far smaller than `GRAPH_REPORT.md` or raw grep output:

- `graphify query "<question>"` — scoped subgraph, broad context
- `graphify explain "<concept>"` — plain-language explanation of one node
- `graphify path "<A>" "<B>"` — shortest path between two concepts

If `graphify-out/wiki/index.md` exists, use it for orientation instead of raw source browsing.

Fall back to `graphify-out/GRAPH_REPORT.md` only for a broad architecture review, or when
`query`/`path`/`explain` don't surface enough context — it's the whole-graph dump those scoped
queries exist to avoid.

After modifying code, run `graphify update .` to keep the graph current — AST-only, no API cost.

### codanna — when the Codanna index / MCP is available

- `semantic_search_docs query:"…"` — find code by intent, not keywords; the intent→symbol
  entry point into the tools below
- `search_symbols query:"…" kind:"function"` — find symbols by name/pattern
- `find_symbol name:"…"` — full details on one symbol
- `find_callers symbol:"…"` — upstream callers
- `get_calls symbol:"…"` — downstream calls
- `analyze_impact symbol:"…" depth:N` — blast radius before refactoring shared code

## graphify only

Use graphify **before** grep/find/raw file reads for codebase orientation: architecture, "how does
X work", how subsystems relate, where a feature lives, and cross-cutting or conceptual questions
spanning code **and** docs. Coarse-grained, whole-corpus, edges may be INFERRED.

- `graphify query "<question>"` — scoped subgraph, broad context
- `graphify explain "<concept>"` — plain-language explanation of one node
- `graphify path "<A>" "<B>"` — shortest path between two concepts

If `graphify-out/wiki/index.md` exists, use it for orientation instead of raw source browsing.

Fall back to `graphify-out/GRAPH_REPORT.md` only for a broad architecture review, or when
`query`/`path`/`explain` don't surface enough context — it's the whole-graph dump those scoped
queries exist to avoid.

After modifying code, run `graphify update .` to keep the graph current — AST-only, no API cost.

Read raw files last — only for the exact lines to edit or debug, once graphify has oriented you.

## codanna only

Use codanna's MCP tools **before** grep/find/raw file reads: semantic *intent* search over code,
plus exact definitions, callers/callees, and blast radius. Fine-grained, code-only, live and accurate.

- `semantic_search_docs query:"…"` — find code by intent, not keywords; the intent→symbol
  entry point into the tools below
- `search_symbols query:"…" kind:"function"` — find symbols by name/pattern
- `find_symbol name:"…"` — full details on one symbol
- `find_callers symbol:"…"` — upstream callers
- `get_calls symbol:"…"` — downstream calls
- `analyze_impact symbol:"…" depth:N` — blast radius before refactoring shared code

Read raw files last — only for the exact lines to edit or debug, once the tools above have
oriented you.
