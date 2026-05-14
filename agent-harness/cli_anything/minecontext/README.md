# cli-anything-minecontext

CLI-Anything harness for MineContext.

This harness wraps the real MineContext local services and exposes them as an
agent-native CLI. It does not reimplement MineContext internals.

## Install

From a packaged macOS MineContext app:

```bash
/Applications/MineContext.app/Contents/Resources/cli/install-cli.sh
cli-anything-minecontext --json service doctor
cli-anything-minecontext --json service up --record
```

If the app is installed somewhere else:

```bash
export MINECONTEXT_APP_PATH="/path/to/MineContext.app"
/path/to/MineContext.app/Contents/Resources/cli/install-cli.sh
```

From a source checkout:

```bash
pip install -e ".[dev]"
```

## Usage

Prefer `--json` for agent automation.

```bash
cli-anything-minecontext --json service doctor
cli-anything-minecontext --json service up --record
cli-anything-minecontext --json service health
cli-anything-minecontext --json recording start
cli-anything-minecontext --json recording status
cli-anything-minecontext --json recording stop
cli-anything-minecontext --json config get
cli-anything-minecontext --json config validate
cli-anything-minecontext --json config set --provider doubao --base-url https://ark.cn-beijing.volces.com/api/v3 --model doubao-seed-2-0-mini-260428 --api-key "$ARK_API_KEY" --embedding-model doubao-embedding-vision-251215
cli-anything-minecontext --json chat ask "What did I work on recently?"
cli-anything-minecontext --json context types
cli-anything-minecontext --json context search "MineContext CLI" --limit 5
cli-anything-minecontext --json todo list --status 0 --limit 10
cli-anything-minecontext --json todo done 7
cli-anything-minecontext --json todo generate
cli-anything-minecontext --json vault list
cli-anything-minecontext --json activity list --limit 5
cli-anything-minecontext --json tips list --limit 5
cli-anything-minecontext --json report list --limit 5
cli-anything-minecontext --json monitoring overview
cli-anything-minecontext --json monitoring recording-stats
```

Generic passthrough:

```bash
cli-anything-minecontext --json api get /api/debug/todos -p limit=5
cli-anything-minecontext --json control get /recording/status
```

Run without a subcommand to enter the REPL:

```bash
cli-anything-minecontext
```

## Runtime Boundary

This CLI is distributable as a Python package, but it is not a standalone
MineContext runtime. It controls a local MineContext installation. For practical
distribution, ship this harness together with MineContext or ensure the target
machine already has:

- MineContext repository or packaged app
- OpenContext backend available or startable
- Electron control API available or startable
- model settings and OS screen-recording permissions configured

`service up --record` can start a local development checkout when `uv`, `pnpm`,
and `MINECONTEXT_DIR` or `~/Projects/MineContext` are available. On macOS it can
also open `/Applications/MineContext.app` or `MINECONTEXT_APP_PATH` when running
from a packaged distribution.
