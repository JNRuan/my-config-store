# Setup

## Install

Give the human these steps when preflight finds a tool missing. The human runs them.

Documentation:

- [Lean install guide](https://lean-lang.org/install/): the official installer and editor setup.
- [Manual install with elan](https://lean-lang.org/install/manual/): elan, the Lean version
  manager. It installs `lean` and `lake` and picks the Lean version from each project's
  `lean-toolchain` file.
- [uv install guide](https://docs.astral.sh/uv/getting-started/installation/): runs the MCP server
  through `uvx`.
- [lean-lsp-mcp](https://github.com/oOo0oOo/lean-lsp-mcp): the MCP server that gives the agent goal
  states, diagnostics, and theorem search.
- [ripgrep](https://github.com/BurntSushi/ripgrep#installation): the MCP server's
  `lean_local_search` tool needs it.

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

4. Build the repository's Lean project once, so the MCP server does not time out on a cold build.
   Skip this step when `lean/` does not exist yet; the skill builds it at bootstrap.

   ```bash
   (cd lean && lake build)
   ```

5. Register lean-lsp-mcp for this repository. `LEAN_PROJECT_PATH` points the server at `lean/`,
   because the Lake project is not the repository root. Use the absolute path, and keep the
   registration local to your machine.

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

## PATH

The agent's shell and the MCP server run without an interactive profile, so a tool that works in the
terminal can be missing from both. The symptoms: `command -v lake` fails while `~/.elan/bin/lake`
exists, or the MCP server reports `No such file or directory: 'lake'`.

Give the human this fix: add the line below to `~/.zshenv`, unless it is already there. zsh reads
`.zshenv` for every shell, while `.zshrc` and `.zprofile` serve interactive logins only.

```zsh
. "$HOME/.elan/env"
```

When `lean_local_search` cannot find ripgrep although `command -v rg` resolves, the MCP server's
PATH lacks the directory that holds `rg`. Tell the human which directory that is, and leave the fix
to them.

The fix needs a session restart. A restart ends any open crit round, so apply it before the brief
opens.

## Bootstrap the Lean project

Run these when `lean/` does not exist:

```bash
mkdir lean && cd lean
lake init Proofs .toml
```

When elan has no default toolchain installed, the first `lake` call downloads one. Tell the human
before the call: it is the one download the skill triggers.

`lake init` writes `lean-toolchain`, `lakefile.toml`, `.gitignore`, `README.md`, `Main.lean`,
`Proofs.lean`, `Proofs/Basic.lean`, and a CI workflow under `.github/`. Then:

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

2. Delete `.github/`, `README.md`, `Main.lean`, and `Proofs/Basic.lean`. Keep `.gitignore`, which
   ignores `/.lake`.
3. Write `Proofs.lean` with one `import` line per model module, replacing the `Proofs.Basic` import.
4. Run `lake build`.

Leave `lean-toolchain` as `lake init` wrote it. It pins the Lean version for everyone.

Add Mathlib only when a proof needs it, because it makes the first build much larger. Follow the
Mathlib instructions in the [Lake
README](https://github.com/leanprover/lean4/blob/master/src/lake/README.md), then run
`lake exe cache get` to fetch prebuilt files.

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
  reports/
    <YYYYMMDDTHHMM>-<shorthash>-<topic>/
      brief.md             # the approved claims and model notes
      report.md            # outcomes, evidence, and coverage gaps
```

Folder and file names are `CapitalCase`, because they become module names
(`Proofs.Web.Pricing.Split`). Each module's namespace matches its path.

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
- A modelled function that fails writes `{"throws": "<message>"}`, where the message is the text
  the source throws for that input. Model failure as `Except <Error> α`, with one constructor per
  message the source can throw and a `message` function that rebuilds the source's text.
- Output JSON mirrors the source's shapes: the same discriminant fields, and `null` where the
  source has no value, so a link test can compare by deep equality.

Parse and render JSON with `Lean.Json` (`import Lean.Data.Json`). Give each model a `FromJson`
instance for its input and a `ToJson` instance for its output. Dispatch on `fn` with a `match` that
lists every model.

`lake build model` writes the binary to `lean/.lake/build/bin/model`. Build it once before the test
run, in the runner's global setup or by hand, because test workers that each run `lake build` in
parallel race. Each link-test file starts one `model` process by its path and streams every
generated input through it.
