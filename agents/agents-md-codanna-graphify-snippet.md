# Codebase intelligence — graphify + codanna

<!--
Drop-in AGENTS.md / CLAUDE.md section for projects that have both tools wired up.
Keep whichever layers are actually present; delete the rest. Both layers are
guarded ("when ... exists / available") so the snippet degrades gracefully.
-->

This project has two codebase-intelligence layers. Use them **before** grep/find/raw file reads:
graphify is the *map*, codanna is the *precision instrument*, raw files are the *last step*.

- **graphify** — whole-corpus knowledge graph (code **and** docs): architecture, "how does X
  work", how subsystems relate, where a feature lives, cross-cutting or conceptual questions.
  Coarse-grained, includes non-code, edges may be INFERRED.
- **codanna** — code intelligence (MCP tools): semantic *intent* search over code, 
  plus exact definitions, who calls what, and blast radius. Fine-grained, code-only, live and accurate.

## Which one to reach for

| You want… | Reach for |
| --- | --- |
| Orientation: architecture, "how does X work", where a feature lives, how subsystems connect | **graphify** — `query` / `explain` / `path`, or the wiki |
| A concept that spans code *and* docs/specs | **graphify** |
| The live code behind a behaviour semantically described, e.g., "How does auth work?" | **codanna** — `semantic_search_docs`, then trace with the symbol tools |
| Exact symbol: definition, signature, the real function behind a name | **codanna** — `find_symbol` / `search_symbols` |
| Who calls this / what does it call | **codanna** — `find_callers` / `get_calls` |
| "What breaks if I change this" before a refactor | **codanna** — `analyze_impact` |
| Exact lines to edit or debug | read the file — but orient with the layers above first |

**Tie-breaker when both could answer.** Both run semantic search, but not the same search:

- *Find by intent:* use **graphify** while you're orienting — conceptual, architectural, or
  doc-spanning questions where you don't yet know where the code lives. Switch to **codanna
  `semantic_search_docs`** once you want the *actual current code* behind an intent and will
  trace it onward; it lands on live, exact symbols, whereas graphify's graph is a snapshot
  with inferred edges.
- *Caller / impact* ("what calls Y", "what breaks"): trust **codanna** — symbol-exact and live.
- *The why / conceptual flow:* **graphify**.

## graphify — when `graphify-out/graph.json` exists

Treat any natural-language question about the codebase as a graph query *first* — these return a
scoped subgraph, usually far smaller than `GRAPH_REPORT.md` or raw grep output:

- `graphify query "<question>"` — scoped subgraph, broad context
- `graphify explain "<concept>"` — plain-language explanation of one node
- `graphify path "<A>" "<B>"` — shortest path between two concepts

For orientation, start at `graphify-out/wiki/index.md` — community and god-node summaries, each
linking to a per-topic article with `source_file` pointers. The wiki is a snapshot; `graph.json` /
the CLI stays the live source of truth.

Fall back to `graphify-out/GRAPH_REPORT.md` only for a broad architecture review, or when
`query`/`path`/`explain` don't surface enough context — it's the whole-graph dump those scoped
queries exist to avoid.

After modifying code, run `graphify update .` to keep the graph current — AST-only, no API cost.

## codanna — when the Codanna index / MCP is available

- `semantic_search_docs query:"…"` — find code by intent, not keywords; the intent→symbol
  entry point into the tools below
- `search_symbols query:"…" kind:"function"` — find symbols by name/pattern
- `find_symbol name:"…"` — full details on one symbol
- `find_callers symbol:"…"` — upstream callers
- `get_calls symbol:"…"` — downstream calls
- `analyze_impact symbol:"…" depth:N` — blast radius before refactoring shared code

## Order of operations

1. **Orient** with graphify (or its wiki) — get the map: which subsystems exist, where they live,
   how they connect.
2. **Pinpoint** with codanna — if you don't know the symbol's name, start with
   `semantic_search_docs` (intent → symbol), then trace its callers and impact at the spot
   you're about to change.
3. **Read raw files last** — only for the exact lines to edit or debug, once steps 1–2 have
   oriented you.
