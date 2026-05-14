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
- Verify `recording start --interval`
- Verify `api get` passthrough
- Verify semantic commands such as `todo done` and `vault create`

## Results

```text
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: <MineContext>/agent-harness
collected 12 items

cli_anything/minecontext/tests/test_core.py ....                         [ 50%]
cli_anything/minecontext/tests/test_full_e2e.py ......                   [ 83%]
cli_anything/minecontext/tests/test_runtime.py ..                        [100%]

============================== 12 passed in 0.18s ===============================
```

Additional live checks against the local MineContext instance passed:

- `cli-anything-minecontext --json service health`
- `cli-anything-minecontext --json recording status`
- `cli-anything-minecontext --json todo list --status 0 --limit 1`
- `cli-anything-minecontext --json context types`
- `cli-anything-minecontext --json service doctor`
- `cli-anything-minecontext --json service up --record --wait 5`
