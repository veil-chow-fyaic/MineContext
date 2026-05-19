# MineContext Community Issue Triage - 2026-05-19

## Repository Baseline

- Upstream repository: `volcengine/MineContext`
- Upstream branch checked: `origin/main`
- Upstream commit used as fork baseline: `171c7a9 fix(security): sandbox vikingdb:// protocol to userData directory (#363)`
- Fork repository: `veil-chow-fyaic/MineContext`
- Fork branch: `fix/local-stability-bugs`
- Fork fix head after local stability work: `6baced4`

The fork branch is based on the latest upstream `main`; `origin/main` is an ancestor of the fork branch.

## Already Covered By Local Fixes

| Issue | Status | Notes |
| --- | --- | --- |
| [#166](https://github.com/volcengine/MineContext/issues/166) Summary name deviates from actual time | Covered | Daily report title now uses the report start date instead of generation date. |
| [#174](https://github.com/volcengine/MineContext/issues/174) Abnormal close leaves multiple backends | Partially covered | Electron single-instance lock is enabled; reused backend ownership is tracked so a reused backend is not killed by a second app instance. |
| [#221](https://github.com/volcengine/MineContext/issues/221) Multiple app instances duplicate timeline/token use | Covered for app process | Electron now activates the existing window on second launch instead of starting another app instance. |
| [#231](https://github.com/volcengine/MineContext/issues/231) Screenshot interval differs from settings | Covered for observed unit bug | Screen monitor cache refresh interval was corrected from milliseconds-like value to seconds. |
| [#246](https://github.com/volcengine/MineContext/issues/246) Daily report not visible / data path mismatch | Partially covered | Dev SQLite now uses a stable app data path; report upsert is deterministic. Packaged Windows migration still needs validation. |
| [#253](https://github.com/volcengine/MineContext/issues/253) Daily report generated but not visible | Partially covered | Same path/report changes as #246. Needs packaged Windows verification. |
| [#313](https://github.com/volcengine/MineContext/issues/313) GetStarted spinner / no feedback | Partially covered | Local startup bypass and dev updater fixes reduce false blocking. Provider validation UX is separate. |
| [#318](https://github.com/volcengine/MineContext/issues/318) Dev startup stuck at 99% / port conflict | Partially covered | Existing healthy backend on port 1733 is reused; frontend no longer treats EADDRINUSE as fatal. Windows backend binary checks need separate validation. |
| [#338](https://github.com/volcengine/MineContext/issues/338) Startup progress too slow | Partially covered | Avoiding repeated backend start/update failure reduces local startup delay. More startup profiling is still needed. |

## Newly Added After Community Review

| Issue | Status | Fix |
| --- | --- | --- |
| [#365](https://github.com/volcengine/MineContext/issues/365) Prompt file save fails due permission/path | Fixed locally | `user_prompts_*.yaml` now writes next to `user_setting_path` instead of the bundled prompt directory. |
| [#350](https://github.com/volcengine/MineContext/issues/350) `ExtractedData.summary` validation fails when LLM returns a list | Fixed locally | `ExtractedData` now coerces `title`, `summary`, `keywords`, and `entities` into stable string/list shapes before validation. |
| [#342](https://github.com/volcengine/MineContext/issues/342) Missing `screenshot_analyze` prompt after upgrade | Fixed locally | `processing.extraction.screenshot_analyze` now falls back to the legacy `screenshot_contextual_batch` prompt name. |

## Candidate Issues For Next Fix Pass

| Issue | Priority | Reason |
| --- | --- | --- |
| [#326](https://github.com/volcengine/MineContext/issues/326) `'list' object has no attribute get` from provider-specific response shape | High | Related to weak LLM response normalization. The new `ExtractedData` coercion helps but does not cover malformed merge items. |
| [#124](https://github.com/volcengine/MineContext/issues/124) Recording stops silently | High | Directly affects unattended capture reliability. Need watchdog/heartbeat and recovery logging. |
| [#50](https://github.com/volcengine/MineContext/issues/50) High token use without visible output | High | Important for distribution. Needs budget guardrails, per-task token telemetry, and duplicate-process prevention validation. |
| [#228](https://github.com/volcengine/MineContext/issues/228) Window capture selection lost when minimized | Medium | Real UX gap, but some behavior is OS-limited. Need explicit fallback/disable behavior rather than pretending minimized windows are capturable. |
| [#198](https://github.com/volcengine/MineContext/issues/198) Summary only covers afternoon | Medium | Likely tied to report schedule/time range settings. Current date-title fix does not prove full-day coverage. |
| [#182](https://github.com/volcengine/MineContext/issues/182) No available port on Windows/Hyper-V | Low for our macOS suite, High for Windows distribution | Community workaround exists via dynamic port range. App should distinguish `EACCES` from "port used" and show an actionable message. |

## Not Accepted As Immediate Fix Scope

| Issue | Reason |
| --- | --- |
| [#298](https://github.com/volcengine/MineContext/issues/298) HDR screenshots overexposed | Platform/rendering specific; needs reproduction on HDR display. |
| [#267](https://github.com/volcengine/MineContext/issues/267) Apple Silicon numpy import error | Packaging/native dependency issue. Needs release artifact validation, not source-only patching. |
| [#293](https://github.com/volcengine/MineContext/issues/293) Linux compile question | Distribution scope, not a runtime blocker for current macOS CLI suite. |

## Open PRs To Avoid Duplicating

- [#349](https://github.com/volcengine/MineContext/pull/349) background AI generation/session isolation: compare before proposing chat/session fixes.
- [#357](https://github.com/volcengine/MineContext/pull/357) lightweight CLI `--version`: separate from our full CLI suite.
- [#362](https://github.com/volcengine/MineContext/pull/362) PIL image handle leak: relevant to long-running stability; review before adding screenshot resource fixes.
- [#361](https://github.com/volcengine/MineContext/pull/361) document upload path validation: security fix, not overlapping with current local bugs.

## Next Engineering Pass

1. Split fork fixes into small upstreamable PRs.
2. Add migration/fallback for missing `processing.extraction.screenshot_analyze` prompt.
3. Harden screenshot merge response parsing so malformed LLM JSON skips bad items instead of breaking the whole batch.
4. Add screen-recording watchdog and token budget observability before broader distribution.
5. Keep the CLI suite pinned to the fork branch/tag that includes these fixes.
