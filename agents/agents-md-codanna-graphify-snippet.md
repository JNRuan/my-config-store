# Codebase intelligence: graphify + codanna

<!--
Three drop-in AGENTS.md / CLAUDE.md sections below. Pick the one matching what's
wired up in the target project (both tools, graphify only, or codanna only)
and delete the other two headings and their content. Each section is
self-contained and guarded ("when ... exists / available") so it degrades
gracefully within its own scope.
-->

## Both: graphify + codanna

This project has two codebase-intelligence layers. Use them **before** grep/find/raw file reads.
graphify is the *map*: a whole-corpus knowledge graph over code and docs, with some edges marked
INFERRED. codanna is the *precision instrument*: exact symbols and relationships from the code
index. Raw files come last. Both are agent skills, not shell commands: **graphify** (invoked as
`/graphify …`, active when `graphify-out/graph.json` exists) and **codanna-codebase-intelligence**
(Codanna MCP tools, active when the Codanna MCP is available).

### Which one to reach for

| You want… | Reach for |
| --- | --- |
| Orientation: architecture, "how does X work", where a feature lives, how subsystems connect, or a concept spanning code and docs/specs | **graphify**: `/graphify query "<question>"` (scoped subgraph), `/graphify explain "<concept>"` (plain-language explanation of one node), `/graphify path "<A>" "<B>"` (shortest path between two concepts) |
| Find code by intent, with callers/callees/impact in one shot | **codanna**: `semantic_search_with_context query:"…"`, the default entry point; `semantic_search_docs query:"…"` for a lighter matches-only pass |
| Exact symbol: definition, signature, the real function behind a name | **codanna**: `find_symbol name:"…"` for full details on one symbol; `search_symbols query:"…" kind:"function"` to find by name/pattern |
| Who calls this / what does it call (actual `()` calls only) | **codanna**: `find_callers function_name:"…"` upstream, `get_calls function_name:"…"` downstream |
| "What breaks if I change this": calls plus type usage and composition/rendering | **codanna**: `analyze_impact symbol_name:"…" max_depth:N`, blast radius before refactoring shared code |
| Exact lines to edit or debug | read the file, but orient with the layers above first |

**Tie-breaker:** both run semantic search, but graphify's graph is a snapshot with inferred edges.
When you need the exact code behind an intent, switch to codanna's `semantic_search_with_context`.

### graphify notes

- Treat any natural-language question about the codebase as a `/graphify query` first.
- If `graphify-out/wiki/index.md` exists, use it for orientation instead of raw source browsing.
- Fall back to `graphify-out/GRAPH_REPORT.md` (the whole-graph dump) only for a broad architecture
  review, or when the scoped queries don't surface enough context.
- After modifying code, run `/graphify . --update` to re-extract only changed files (code is
  AST-only, no LLM cost; changed docs/images trigger an LLM re-pass). If `graphify-out/wiki/`
  exists, add `--wiki`; only that flag regenerates the wiki, and it goes stale otherwise.

## graphify only

Use graphify **before** grep/find/raw file reads for codebase orientation: architecture, "how does
X work", how subsystems relate, where a feature lives, and cross-cutting or conceptual questions
spanning code and docs. It is coarse-grained and whole-corpus, and some edges are marked INFERRED.
These are invocations of the **graphify** skill, not shell commands:

- `/graphify query "<question>"`: scoped subgraph, broad context
- `/graphify explain "<concept>"`: plain-language explanation of one node
- `/graphify path "<A>" "<B>"`: shortest path between two concepts

If `graphify-out/wiki/index.md` exists, use it for orientation instead of raw source browsing.

Fall back to `graphify-out/GRAPH_REPORT.md` (the whole-graph dump) only for a broad architecture
review, or when the scoped queries above don't surface enough context.

After modifying code, run `/graphify . --update` to re-extract only changed files (code is
AST-only, no LLM cost; changed docs/images trigger an LLM re-pass). If `graphify-out/wiki/`
exists, add `--wiki`; only that flag regenerates the wiki, and it goes stale otherwise.

Read raw files last: only for the exact lines to edit or debug, once graphify has oriented you.

## codanna only

Use codanna's MCP tools (via the **codanna-codebase-intelligence** skill) **before** grep/find/raw
file reads: semantic intent search over code, plus exact definitions, callers/callees, and blast
radius. Fine-grained, code-only, exact.

- `semantic_search_with_context query:"…"`: the default entry point. Finds code by intent;
  returns matches with docs, callers, callees, and impact in one call
- `semantic_search_docs query:"…"`: lighter intent search, matches only (no relationship context)
- `search_symbols query:"…" kind:"function"`: find symbols by name/pattern
- `find_symbol name:"…"`: full details on one symbol
- `find_callers function_name:"…"`: upstream callers
- `get_calls function_name:"…"`: downstream calls
- `analyze_impact symbol_name:"…" max_depth:N`: blast radius before refactoring shared code;
  unlike the call tools, also covers type usage and composition/rendering

Read raw files last: only for the exact lines to edit or debug, once the tools above have
oriented you.
