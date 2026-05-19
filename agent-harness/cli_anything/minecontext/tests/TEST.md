# MineContext CLI-Anything Harness Test Plan

## Inventory Plan

- `test_core.py`: unit coverage for client URL/query/body behavior and session state.
- `test_full_e2e.py`: CLI subprocess-style tests through Click runner with mocked client behavior.

## Unit Test Plan

- `MineContextClient.request`
  - normalizes paths
  - encodes query parameters
  - serializes JSON request bodies
  - accepts object and array JSON responses
- `Session`
  - records history and last result

## E2E Test Plan

- Verify `--json service health`
- Verify `--json service smoke` as the install/distribution quality gate,
  including Electron renderer readiness instead of only backend health
- Verify stale daily report detection when activities exist but the report says
  no activity is available
- Verify `service up --restart-frontend --user-data-dir` for clean-room startup
  and stale Electron recovery
- Verify `recording start --interval`
- Verify `api get` passthrough
- Verify semantic commands such as `todo done`, `summary day`, and `report read --date`

## Results

```text
.....................                                                    [100%]
21 passed in 0.10s
```

Additional live checks against the local MineContext instance passed:

- `cli-anything-minecontext --json service health`
- `cli-anything-minecontext --json window ui-status`
- `cli-anything-minecontext --json service smoke --date 2026-05-17`
- `cli-anything-minecontext --json service smoke --skip-summary --skip-chat --require-recording`
- `cli-anything-minecontext --json recording status`
- `cli-anything-minecontext --json summary day 2026-05-17`
- `cli-anything-minecontext --json report read --date 2026-05-17`
- `cli-anything-minecontext --json chat ask "只回答 cli-chat-ok"`
- `cli-anything-minecontext --json todo list --status 0 --limit 1`
- `cli-anything-minecontext --json context types`
- `cli-anything-minecontext --json service doctor`
- `cli-anything-minecontext --json service up --record --wait 5`
- `cli-anything-minecontext --json service up --record --restart-frontend --user-data-dir /tmp/minecontext-clean --wait 45`
