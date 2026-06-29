# MineContext migration handoff inventory - 2026-06-29

## Scope

This document records the local repository and runtime state for handing the
MineContext + CLI work to another team. It is intentionally source-control and
runtime oriented: what exists, where it lives, what is already pushed, and what
must not be lost.

## Primary repositories and directories

### `/Users/fuyo-aic/Projects/MineContext`

Primary delivery worktree for the bundled MineContext + CLI suite.

- Git branch: `main`
- HEAD at first inspection: `242418a recover recording after source enumeration loss`
- Archive update: official security fix `171c7a9` was cherry-picked as
  `f2c0fbf fix(security): sandbox vikingdb:// protocol to userData directory (#363)`.
- Upstream: `aic/main`
- Remotes:
  - `origin`: `https://github.com/volcengine/MineContext.git`
  - `fork`: `https://github.com/veil-chow-fyaic/MineContext.git`
  - `aic`: `https://github.com/veil-chow-fyaic/minecontext-cli-suite-20260515.git`
- Pushed state at first inspection:
  - `fork/main` = `242418a`
  - `aic/main` = `242418a`
- Current git status at first inspection:
  - Untracked: `WORKFLOW.md`
  - This handoff document is new and must be committed if accepted.

This is the handoff source of truth for the CLI-bundled project. It includes:

- `agent-harness/`: CLI-Anything based MineContext harness.
- `scripts/install-cli.sh`: CLI installer script.
- `frontend/src/main/services/AutomationControlService.ts`: Electron control API bridge on local port 1734.
- `docs/minecontext-source-research.md`: source-level research record.
- `agent-harness/quality-notes/`: local bug review and community issue triage notes.
- Fixes for daily summary date consistency, tips labels, CLI validation, control API, launch recovery, and source-enumeration recovery.

### `/Users/fuyo-aic/Projects/MineContext-fork-fixes`

Secondary git worktree sharing the same repository as `MineContext`.

- Git branch: `fix/local-stability-bugs`
- HEAD: `19dbd94 Fix daily report normalization regression`
- Remote branch: `fork/fix/local-stability-bugs`
- Current git status at inspection: clean
- Relationship:
  - This branch is based on the official upstream line and includes a compact source-fix set for PR-style review.
  - It does not contain the later full CLI suite added on `main`.
  - Do not overwrite `main` with this branch.

Use this branch only if the receiving team wants an upstream-friendly patch set
without the bundled CLI distribution work.

### `/Users/fuyo-aic/Projects/CLI-Anything`

External upstream reference repository.

- Git branch: `main`
- Local HEAD: `5f325f0`
- Remote: `https://github.com/HKUDS/CLI-Anything`
- After fetch: local branch is behind `origin/main` by 253 commits.
- Current git status at inspection: clean

This is not the MineContext delivery repository. It was used as the CLI-Anything
reference project. The MineContext harness code lives under
`/Users/fuyo-aic/Projects/MineContext/agent-harness`.

### `/Users/fuyo-aic/Projects/minecontext-cli`

Early standalone CLI prototype, not a git repository.

- Contains a Python package under `src/minecontext_cli`.
- Contains tests and a local `.venv`.
- Treat as historical reference only unless someone explicitly wants to recover
  the earlier standalone design.

### `/Users/fuyo-aic/Projects/minecontext-cli-anything`

Early non-git CLI-Anything export/prototype.

- Not a git repository.
- Contains partial `MineContext/agent-harness` generated artifacts.
- Treat as historical scratch output. The maintained version is in the primary
  `MineContext` repository.

### `/Users/fuyo-aic/code/liev-symphony-workspaces-minecontext/AIC-2497`

Autonomous research workspace.

- Git branch: `main`
- Remote: `https://github.com/veil-chow-fyaic/MineContext.git`
- HEAD: `fecace9 fix: correct screen monitor interval unit from seconds to milliseconds (#317)`
- Current git status at inspection:
  - Untracked: `docs/`
- Important file:
  - `docs/minecontext-source-research.md`
- Comparison result:
  - Same content as primary repo `docs/minecontext-source-research.md`, except final newline.
  - Primary repo already committed this document in `5cc71c4`.

This workspace is useful for traceability but should not be used as the handoff
source of truth.

## Official upstream divergence

After `git fetch --all --prune`, the official upstream had one commit that was
not in the delivery `main` at first inspection:

- `171c7a9 fix(security): sandbox vikingdb:// protocol to userData directory (#363)`
- File touched: `frontend/src/main/index.ts`
- Risk: local file exfiltration through the renderer-loadable `vikingdb://`
  protocol if a renderer/XSS path can request arbitrary local files.

This was treated as a P0 handoff blocker and was cherry-picked into `main` as
`f2c0fbf` during the archive pass.

Current divergence at first inspection:

- `main` has 16 commits not in `origin/main`.
- `origin/main` has 1 commit not in `main`.

## Runtime and local service state

At inspection, the local runtime was healthy:

- Backend: `127.0.0.1:1733`, process `python3.1`, health OK.
- Electron control API: `127.0.0.1:1734`, process `Electron`, health OK.
- Recording status: `running`.
- Selected source at the last check: `整个屏幕`.

LaunchAgent:

- Plist: `/Users/fuyo-aic/Library/LaunchAgents/com.fuyo.minecontext.cli.plist`
- Script: `/Users/fuyo-aic/.minecontext-cli/launchd/start.sh`
- Interval: 60 seconds
- Last exit code at inspection: `0`
- Script currently hardcodes:
  - `/Users/fuyo-aic/Projects/MineContext`
  - `/Users/fuyo-aic/Projects/MineContext/.venv/bin/python`
  - `/Users/fuyo-aic/Projects/MineContext/agent-harness`

This LaunchAgent is a local operations artifact, not yet a portable installer.
For team handoff, convert it into a parameterized install script or document it
as a local example only.

## Runtime data and secrets

Ignored local files/directories exist and are not included in git:

- `.env`: ignored by `.gitignore`; contains local runtime/model configuration.
- `persist/`: ignored; about 335 MB at inspection.
- `frontend/backend/screenshot/`: ignored; about 3.7 GB at inspection.
- `logs/`: ignored; local OpenContext logs.
- `~/Library/Application Support/MineContextDev`: about 46 MB at inspection.
- `~/.minecontext-cli`: about 179 MB at inspection, mostly logs and LaunchAgent helper files.

Do not commit secrets or raw screenshots. For migration, decide separately:

1. Source-only transfer: do not transfer `.env`, screenshots, SQLite, ChromaDB,
   or logs.
2. Continuity transfer: export `.env` through a secure secret channel and
   package `persist/` plus any required userData paths after privacy review.

## Delivery commits on `main`

Key commits after the base upstream line:

- `f2c0fbf fix(security): sandbox vikingdb:// protocol to userData directory (#363)`
- `7cc4bdf Add MineContext CLI bundle`
- `7227d47 Document MineContext local stability review`
- `e38da0c Sync CLI suite with MineContext stability fixes`
- `0168a43 Add regression tests for MineContext fixes`
- `e665962 Fix daily report normalization regression`
- `bcf7e67 fix daily report date handling`
- `5cc71c4 AIC-2497: MineContext source capture research`
- `e47cad3 add daily report date repair commands`
- `d258b3b fix cli validation and output hygiene`
- `997df6a clarify smart tip labels`
- `f024f33 compact smart tip feed previews`
- `c6af264 show smart tip time ranges`
- `f9dd99c sync recording status after cli start`
- `9526010 improve screen recording permission recovery`
- `242418a recover recording after source enumeration loss`

## Validation commands

Recommended before final handoff:

```bash
cd /Users/fuyo-aic/Projects/MineContext

npm run typecheck:node --prefix frontend
PYTHONPATH="$PWD/agent-harness" "$PWD/.venv/bin/python" -m py_compile \
  agent-harness/cli_anything/minecontext/minecontext_cli.py \
  agent-harness/cli_anything/minecontext/utils/runtime.py
PYTHONPATH="$PWD/agent-harness" "$PWD/.venv/bin/python" -m cli_anything.minecontext --json service doctor
PYTHONPATH="$PWD/agent-harness" "$PWD/.venv/bin/python" -m cli_anything.minecontext --json service health
PYTHONPATH="$PWD/agent-harness" "$PWD/.venv/bin/python" -m cli_anything.minecontext --json recording status
PYTHONPATH="$PWD/agent-harness" "$PWD/.venv/bin/python" -m cli_anything.minecontext --json service smoke --skip-chat
```

Known validation caveat:

- The current `.venv` did not have `pytest` installed during prior checks, so
  Python tests could not be run with `python -m pytest` without installing test
  dependencies.

Archive validation run on 2026-06-29 after cherry-picking the upstream security
fix:

- `npm run typecheck:node` in `frontend/`: passed.
- `python -m py_compile agent-harness/cli_anything/minecontext/minecontext_cli.py agent-harness/cli_anything/minecontext/utils/runtime.py`: passed.
- `cli_anything.minecontext --json service doctor`: passed.
- `cli_anything.minecontext --json service health`: passed.
- `cli_anything.minecontext --json recording status`: passed; recording was `running`.
- `cli_anything.minecontext --json service smoke --skip-chat`: failed because
  the configured VLM and embedding account reported an overdue balance, and the
  default summary date `2026-06-29` had not yet generated a daily report.
- `cli_anything.minecontext --json service smoke --skip-summary --skip-chat`:
  still failed on model validation for the same overdue-balance reason; health,
  recording, and UI checks passed.

## P0 handoff checklist

- Re-run validation after the security fix.
- Commit `WORKFLOW.md` as operations archive material or move it out of the
  repo if the receiving team does not want Liev/Symphony lane metadata.
- Commit this handoff document.
- Push final `main` to both:
  - `fork/main`
  - `aic/main`
- Confirm whether `fix/local-stability-bugs` should remain as a PR branch, be
  archived, or be superseded by `main`.
- Decide source-only vs continuity transfer for `.env`, `persist/`, screenshots,
  logs, and Application Support data.
- Replace hardcoded local LaunchAgent paths with an installer or clearly mark
  them as local examples.

## Recommended receiving-team starting point

Use `/Users/fuyo-aic/Projects/MineContext` branch `main` after the P0 checklist
is completed. Treat `/Users/fuyo-aic/Projects/MineContext-fork-fixes` as an
upstream-PR compatibility branch and the non-git CLI directories as historical
scratch/prototype material.
