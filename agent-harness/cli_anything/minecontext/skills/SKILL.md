---
name: cli-anything-minecontext
description: Use to control MineContext through a CLI-Anything harness, including recording, chat, context search, vault documents, todos, activities, reports, tips, monitoring, and raw API passthrough.
---

# CLI-Anything MineContext

Always prefer JSON output:

```bash
cli-anything-minecontext --json service health
cli-anything-minecontext --json service doctor
cli-anything-minecontext --json service smoke --date 2026-05-17
cli-anything-minecontext --json service up --record
cli-anything-minecontext --json service up --record --show-ui
cli-anything-minecontext --json recording start
cli-anything-minecontext --json window ui-status
cli-anything-minecontext --json window show
cli-anything-minecontext --json window hide
cli-anything-minecontext --json chat ask "What did I work on recently?"
cli-anything-minecontext --json summary day 2026-05-17
cli-anything-minecontext --json report read --date 2026-05-17
cli-anything-minecontext --json context search "MineContext CLI" --limit 5
cli-anything-minecontext --json todo list --status 0
cli-anything-minecontext --json api get /api/debug/todos -p limit=5
```

Use `api` for backend passthrough and `control` for Electron control passthrough.

This CLI requires a local MineContext runtime. It can be distributed separately,
but it is useful only when MineContext backend/Electron control services are
installed or startable on the same machine.

`service up` defaults to background no-UI startup. Use `--show-ui` or
`window show` when a visible main window is needed.

Treat `service smoke` as the readiness gate for agents. It includes an Electron
renderer readiness check, so it fails if MineContext is still stuck on the 99%
bootstrap loading screen.
