# Setup

## Install

Give the human these steps when preflight finds a tool missing. The human runs them.

Documentation:

- [Lean install guide](https://lean-lang.org/install/): the official installer and editor setup.
- [Manual install with elan](https://lean-lang.org/install/manual/): elan, the Lean version manager. It installs `lean` and `lake` and picks the Lean version from each project's `lean-toolchain` file.
- [uv install guide](https://docs.astral.sh/uv/getting-started/installation/): runs the MCP server through `uvx`.
- [lean-lsp-mcp](https://github.com/oOo0oOo/lean-lsp-mcp): the MCP server that gives the agent goal states, diagnostics, and theorem search.
- [ripgrep](https://github.com/BurntSushi/ripgrep#installation): the MCP server's `lean_local_search` tool needs it.

Steps:

1. Install elan, then load it into the current shell:

   ```bash
   curl https://elan.lean-lang.org/elan-init.sh -sSf | sh
   source "$HOME/.elan/env"
   ```

   Accept the default option when prompted.
2. Install uv:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Install ripgrep if `command -v rg` finds nothing:

   ```bash
   brew install ripgrep
   ```

4. Build the repository's Lean project once, so the MCP server does not time out on a cold build. Skip this step when `lean/` does not exist yet; the skill builds it at bootstrap.

   ```bash
   (cd lean && lake build)
   ```

5. Register lean-lsp-mcp for this repository. `LEAN_PROJECT_PATH` points the server at `lean/`, because the Lake project is not the repository root. Use the absolute path, and keep the registration local to your machine.

   Claude Code, from the repository root:

   ```bash
   claude mcp add lean-lsp -s local -e LEAN_PROJECT_PATH="$(pwd)/lean" -- uvx lean-lsp-mcp
   ```

   Codex, in `~/.codex/config.toml`:

   ```toml
   [mcp_servers.lean-lsp]
   command = "uvx"
   args = ["lean-lsp-mcp"]
   env = { LEAN_PROJECT_PATH = "/absolute/path/to/repo/lean" }
   ```

6. Restart the agent session so it loads the MCP server.

## Bootstrap the Lean project

Run these when `lean/` does not exist:

```bash
mkdir lean && cd lean
lake init Proofs .toml
```

`lake init` writes `lean-toolchain`, `lakefile.toml`, and starter files. Then:

1. Replace `lakefile.toml` with:

   ```toml
   name = "proofs"
   defaultTargets = ["Proofs"]

   [[lean_lib]]
   name = "Proofs"

   [[lean_exe]]
   name = "model"
   root = "Model"
   ```

2. Delete the starter files `lake init` created under `Proofs/`, and any `Main.lean`.
3. Write `Proofs.lean` with one `import` line per model module.
4. Add `lean/.lake/` to the repository's `.gitignore`.
5. Run `lake build`.

Leave `lean-toolchain` as `lake init` wrote it. It pins the Lean version for everyone.

Add Mathlib only when a proof needs it, because it makes the first build much larger. Follow the Mathlib instructions in the [Lake README](https://github.com/leanprover/lean4/blob/master/src/lake/README.md), then run `lake exe cache get` to fetch prebuilt files.

## Project layout

One Lake project per repository, at `lean/`:

```text
lean/
  lakefile.toml
  lean-toolchain
  lake-manifest.json
  Proofs.lean              # imports every model module
  Model.lean               # the model executable
  Proofs/
    <App>/                 # one folder per app; omit in a single-app repo
      <Group>/             # a domain area, such as Pricing or Auth
        <Name>.lean        # one model and its claims
```

Folder and file names are `CapitalCase`, because they become module names (`Proofs.Web.Pricing.Split`). Each module's namespace matches its path.

Start every model file with a header naming each source it models:

```lean
-- Models: apps/web/src/pricing/split.ts#splitEvenly
```

Triage reads these headers to find what is already modelled.

## Model executable

`Model.lean` exposes every model to link tests through `lake exe model`.

Contract:

- Input: one JSON object per line on stdin, `{"fn": "<Full.Lean.Name>", "input": <JSON>}`.
- Output: one JSON value per line on stdout, the model's result for that input, in input order.
- An unknown `fn` or malformed input writes `{"error": "<message>"}` for that line.

Parse and render JSON with `Lean.Json` (`import Lean.Data.Json`). Give each model a `FromJson` instance for its input and a `ToJson` instance for its output. Dispatch on `fn` with a `match` that lists every model.

A link test starts one `lake exe model` process per run and streams all generated inputs through it. Build the executable first with `lake build model`.
