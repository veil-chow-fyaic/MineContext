# MineContext Local Bug Review - 2026-05-19

## Purpose

This note records the bugs observed while packaging and operating MineContext
through an agent-driven CLI workflow. The goal is to distinguish project quality
issues from incorrect local usage, and to preserve evidence for future internal
tracking, upstream issues, or pull requests.

## Repository Context

- Upstream repository: `origin` -> `https://github.com/volcengine/MineContext.git`
- Internal repository: `aic` -> `https://github.com/veil-chow-fyaic/minecontext-cli-suite-20260515.git`
- Local checkout: `/Users/fuyo-aic/Projects/MineContext`
- Local branch: `main`, tracking `aic/main`
- Upstream baseline observed locally: `origin/main` at `e782408 Create SECURITY.md (#364)`
- Internal baseline observed locally: `7cc4bdf Add MineContext CLI bundle`

## Assessment Summary

The defects below are assessed as MineContext project quality issues rather than
incorrect user operation. They were reproduced after the required model settings,
API key, backend service, Electron frontend, screen recording permission, and
recording source were configured. Several issues are caused by implementation
details visible in source code, such as using wall-clock time instead of the
report time window, sharing a global streaming agent queue, forcing dev updater
downloads, or showing raw event titles in notifications.

Some local symptoms are amplified by historical bad SQLite records. Those
records explain why the current UI can still show incorrect historical summaries
after code fixes, but they do not explain how the bad records were created. The
creation path is a source-level bug.

## Confirmed Project Quality Issues

### 1. Daily Report Date Mismatch

Observed symptom:
- The UI showed `Daily Report - 2026-05-19`, but the report body started with
  `# 日报 - 2026年05月18日`.
- The report list also contained duplicated `Daily Report - 2026-05-18` records,
  including a stale "No activity data available" report.

Why this is not user misuse:
- The user had already configured the model and enabled recording.
- The backend health check was green.
- The incorrect date was persisted in the application's own SQLite vault data.
- Source inspection showed the report generator named stored reports with
  `datetime.now()` while generating content from the requested `start_time` and
  `end_time` window. A cross-day generation window can therefore store yesterday's
  content under today's title.

Local fix applied:
- Use `start_time` as the report date for the stored title.
- Upsert by daily report title instead of inserting duplicates.
- Normalize the Markdown body and enforce the first heading date.

Candidate upstream PR:
- `fix: correct daily report date, upsert daily report, and normalize markdown`

### 2. Daily Report Markdown Format Instability

Observed symptom:
- Some generated reports were wrapped in a top-level ```markdown fence, while
  others were plain Markdown.

Why this is not user misuse:
- The report body comes directly from LLM generation and is stored as-is by the
  application.
- Users cannot control whether the model wraps the whole response in a fenced
  block from the normal UI flow.

Local fix applied:
- Strip a top-level Markdown fence during report storage.
- Normalize the first daily report heading.

Candidate upstream PR:
- Can be included with the daily report date fix.

### 3. Chat With AI Streaming Isolation Risk

Observed symptom:
- `chat with ai` felt stuck or unsuccessful in the UI.
- Non-streaming CLI requests could take a long time, and streaming requests
  emitted events slowly while collecting large local context sets.

Why this is not user misuse:
- Model settings validated successfully.
- Backend health and control API were healthy.
- Both `/api/agent/chat` and `/api/agent/chat/stream` used a shared global
  `ContextAgent` instance configured for streaming.
- A shared streaming manager queue creates cross-request contamination and hang
  risk when multiple chat requests overlap or when a previous stream is not fully
  drained.

Local fix applied:
- Create an isolated `ContextAgent` for each `/chat` and `/chat/stream` request.

Remaining product concern:
- Chat can still be slow because context collection may run multiple retrieval
  rounds and gather many context items. That is a performance/UX issue, separate
  from the shared-queue correctness issue.

Candidate upstream PR:
- `fix: isolate context agent instances for chat requests`

### 4. Smart Tip Notification Has Unclear Title/Body

Observed symptom:
- macOS occasionally showed a notification from `Electron` with content like
  `intelligence reminder`.

Why this is not user misuse:
- Source code hard-coded the smart tip event title as `intelligence reminder`.
- The frontend converted events into notifications using `event.data.title`,
  not the generated tip content.
- In development mode, Electron can appear as the app name unless explicitly set.

Local fix applied:
- Use `智能提醒` as the backend smart tip title.
- Use real tip content as the notification message, with Markdown stripped and
  text truncated for notification display.
- Set the Electron app name to `MineContext`.

Candidate upstream PR:
- `fix: improve smart tip notification title and body`

### 5. Development Mode SQLite Path Mismatch

Observed symptom:
- Frontend-visible vaults and backend-generated data could diverge.
- UI features such as summary loading appeared broken even while backend health
  checks passed.

Why this is not user misuse:
- The app used different path resolution rules in development mode for frontend
  Electron services and backend storage.
- A healthy backend can still write to one SQLite path while the Electron UI reads
  another.

Local fix applied:
- Centralize SQLite path resolution for main-process database services.
- Support `MINECONTEXT_USER_DATA_DIR` for clean-room validation.

Candidate upstream PR:
- `fix: unify dev SQLite path resolution`

### 6. Development Updater Attempts Broken GitHub Release Download

Observed symptom:
- The app attempted to download a GitHub release asset during dev runs and hit
  `404`, producing an unhandled rejection-style error in logs.

Why this is not user misuse:
- Update checks are automatically started by application code.
- Dev users should not need to disable update checks manually to avoid a broken
  release download path.

Local fix applied:
- Skip update checks in development mode.
- Catch `downloadUpdate` failures instead of letting them surface noisily.

Candidate upstream PR:
- `fix: skip auto updater in development and catch download failures`

### 7. Screen Monitor Visible Source Cache Can Be Empty at Task Start

Observed symptom:
- Logs included `screen monitor visibleSources is empty`.
- Recording could still be marked running, but capture behavior depended on a
  cache being ready.

Why this is not user misuse:
- The screen source cache is internal application state.
- The task accessed cached data immediately and did not always recover when the
  cache had not yet produced values.
- Source inspection also showed an interval unit mismatch in the cache
  configuration.

Local fix applied:
- Correct cache interval units.
- Re-fetch visible sources when the cache is empty.

Candidate upstream PR:
- `fix: make screen monitor source cache robust at startup`

### 8. Backend Ownership During Electron Shutdown

Observed symptom:
- The Electron frontend can reuse an already running backend on port `1733`.
- Without ownership tracking, shutdown logic can attempt to stop a backend it did
  not start.

Why this is not user misuse:
- Reusing an existing backend is an internal app behavior.
- Process ownership must be tracked by the app, not by the user.

Local fix applied:
- Track whether the backend process is owned by the current Electron process.
- Skip stop logic for reused external backend services.

Candidate upstream PR:
- `fix: avoid stopping externally managed backend process`

### 9. React Development Warnings

Observed symptom:
- React warned about missing list keys in `ModelRadio`.
- React warned that `clip-path` should be `clipPath`.

Why this is not user misuse:
- These are static frontend code issues.

Local fix applied:
- Add a stable key to `ModelRadio` items.
- Rename SVG `clip-path` attributes to `clipPath`.

Candidate upstream PR:
- `fix: resolve React key and SVG prop warnings`

## Internal CLI And Distribution Enhancements

The following changes are useful for our internal distribution workflow but are
larger than simple upstream bug fixes:

- CLI harness under `agent-harness/`.
- `service up`, `service smoke`, `window ui-status`, `summary day`, and `chat ask`
  commands.
- No-UI startup support via `MINECONTEXT_NO_UI`.
- Automation control API endpoints for recording and window state.
- Packaged CLI installer script.

These changes are best kept in the internal `aic` repository unless upstream is
explicitly interested in adopting an agent/CLI distribution workflow.

## Evidence From Local Verification

Verification commands that passed after local fixes:

```bash
pnpm typecheck
uv run pytest "agent-harness/cli_anything/minecontext/tests"
uv run python -m py_compile \
  "opencontext/context_consumption/generation/generation_report.py" \
  "opencontext/context_consumption/generation/smart_tip_generator.py" \
  "opencontext/server/routes/agent_chat.py"
uv run cli-anything-minecontext --json --timeout 180 service smoke --skip-summary --skip-ui
```

Known remaining local data issue:
- Existing SQLite records still contain historical bad daily reports, such as a
  `2026-05-19` title whose body is for `2026-05-18`.
- This requires a local data backup and repair step. It is not solved by code
  changes alone.

## Recommended PR Strategy

Do not submit one large PR. Split into focused PRs:

1. Daily report date/upsert/format normalization.
2. Chat agent request isolation.
3. Smart tip notification clarity.
4. Dev runtime stability: SQLite path, updater, screen monitor cache, backend
   ownership.
5. Small React warning cleanup.

Each PR should include a minimal reproduction, the observed source-level cause,
and a small validation note.
