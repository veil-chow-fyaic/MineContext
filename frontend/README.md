# MineContext

## Project Setup

### Local Prerequisites

- Python 3.10+ with `uv`
- Node.js 20+
- pnpm 10+
- macOS is the primary supported development and packaging target
- Optional: `tmux` for long-running local backend/frontend sessions

Install the backend dependencies from the repository root:

```bash
cd ..
uv sync
```

If your environment uses a SOCKS proxy and `httpx` reports that `socksio` is missing:

```bash
cd ..
uv pip install socksio
```

### Model Environment

Create a local `.env` file in the repository root. Do not commit this file.

```bash
cd ..
cat > .env <<'EOF'
LLM_PROVIDER=doubao
LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
LLM_MODEL=doubao-seed-2-0-mini-260428
LLM_API_KEY=your-ark-api-key

EMBEDDING_PROVIDER=doubao
EMBEDDING_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
EMBEDDING_MODEL=doubao-embedding-vision-251215
EMBEDDING_API_KEY=your-ark-api-key
EOF
chmod 600 .env
```

For Doubao/Ark, make sure the API key has access to both configured models in the Beijing region.

### Install Frontend

```bash
cd frontend
pnpm install
```

If native dependency rebuilding fails with `No module named 'distutils'`, retry with macOS system Python:

```bash
PYTHON="/usr/bin/python3" npm_config_python="/usr/bin/python3" pnpm install
```

### Development

Start the backend from the repository root:

```bash
set -a
source .env
set +a
uv run opencontext start --port 1733
```

Start the Electron frontend:

```bash
cd frontend
pnpm dev
```

Backend debug UI: `http://localhost:1733`
Renderer dev server: `http://localhost:5173`
Recording control API: `http://127.0.0.1:1734`

Start recording without clicking the UI button:

```bash
curl -X POST http://127.0.0.1:1734/recording/start \
  -H 'Content-Type: application/json' \
  -d '{}'
```

Check or stop recording:

```bash
curl http://127.0.0.1:1734/recording/status
curl -X POST http://127.0.0.1:1734/recording/stop
```

The default start API selects the first visible screen and applies the default screen settings. Override settings with:

```bash
curl -X POST http://127.0.0.1:1734/recording/start \
  -H 'Content-Type: application/json' \
  -d '{"config":{"recordInterval":10,"enableRecordingHours":false}}'
```

### CLI Bundle

MineContext ships the CLI-Anything harness from the repository root `agent-harness/`.
The CLI is a control surface for a local MineContext runtime; it can be packaged
as Python, but it does not replace the backend or Electron app.

Install from source:

```bash
cd ..
python3 -m pip install -e ./agent-harness
cli-anything-minecontext --json service doctor
```

Install from a packaged macOS app:

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

Useful commands:

```bash
cli-anything-minecontext --json service up --record
cli-anything-minecontext --json recording status
cli-anything-minecontext --json recording stop
cli-anything-minecontext --json config validate
cli-anything-minecontext --json chat ask "What did I work on recently?"
cli-anything-minecontext --json todo list --status 0
cli-anything-minecontext --json api get /api/debug/todos -p limit=5
cli-anything-minecontext --json control get /recording/status
```

For agent automation, prefer `--json`. `service up --record` reuses running
services, starts a source checkout when `uv` and `pnpm` are available, or opens
the packaged macOS app from `/Applications/MineContext.app` or
`MINECONTEXT_APP_PATH`.

Optional tmux workflow from the repository root:

```bash
tmux new-session -d -s minecontext-backend -c "$(pwd)" \
  'set -a; source .env; set +a; uv run opencontext start --port 1733'

tmux new-session -d -s minecontext-frontend -c "$(pwd)/frontend" \
  'PYTHON="/usr/bin/python3" npm_config_python="/usr/bin/python3" pnpm dev'
```

Stop the sessions:

```bash
tmux kill-session -t minecontext-backend
tmux kill-session -t minecontext-frontend
```

### Using The App

1. Open the Electron app started by `pnpm dev`.
2. Confirm model settings in Settings.
3. Grant screen recording permissions in macOS System Settings.
4. Select the capture area in Screen Monitor and click Start Recording, or call `http://127.0.0.1:1734/recording/start` to auto-select the first visible screen.
5. Let the backend generate activities, todos, tips, and reports.

### Build APP

```bash
# For macOS
pnpm build:mac
# Data Path
# ～/Library/Application\ Support/MineContext
```

The app bundle includes the CLI harness under `Contents/Resources/cli/agent-harness` and the CLI installer under `Contents/Resources/cli/install-cli.sh`.

### Data Path

～/Library/Application\ Support/MineContext
