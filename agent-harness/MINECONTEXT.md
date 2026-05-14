# MineContext CLI-Anything Harness SOP

## Target

MineContext is an Electron + React desktop application backed by the OpenContext
FastAPI service. The GUI is useful for humans, while agents need a stable
command-line control surface.

## Backend Engine

- Backend: OpenContext FastAPI service, usually `http://127.0.0.1:1733`
- Electron control API: local HTTP bridge, usually `http://127.0.0.1:1734`
- Desktop capture and recording still live in Electron main process
- Context processing, chat, vaults, todos, reports, tips, monitoring, and model
  settings live in the FastAPI backend

## Data Model

- Captured context is persisted by OpenContext storage
- User documents live in the vaults table/API
- Todos, activities, reports, and tips are exposed by debug/consumption APIs
- Recording state is held by the Electron screen monitor task

## CLI Architecture

The harness wraps the real MineContext services. It does not reimplement
recording, OCR, embedding, vector search, chat, or context processing logic.

Command groups:

- `service`: health and startup checks; `service up --record` supports source
  checkouts and packaged macOS apps
- `recording`: start, stop, status
- `config`: get and validate model settings
- `chat`: ask questions through the Context Agent
- `context`: list types and vector search
- `vault`: document CRUD
- `todo`: list, complete, reopen, generate
- `activity`: list and generate summaries
- `tips`: list and generate tips
- `report`: list and generate reports
- `monitoring`: overview and recording stats
- `api`: backend API passthrough
- `control`: Electron control API passthrough

## Agent Contract

- Always prefer `--json`
- Use semantic commands first
- Use `api` and `control` passthrough commands for missing coverage
- Non-zero exits indicate unavailable services or invalid requests

## Known Limitations

- macOS screen-recording permission still requires OS-level user authorization
- Full Electron IPC coverage requires more control API endpoints in MineContext
- Streaming chat is not wrapped yet; use backend passthrough if needed
- The CLI package is distributable by itself, but operational use requires a
  local MineContext runtime. Standard product distribution should bundle the CLI
  with MineContext or provide an installer that installs both.
- Packaged macOS usage expects MineContext at `/Applications/MineContext.app` or
  `MINECONTEXT_APP_PATH`.
