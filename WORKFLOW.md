---
tracker:
  kind: linear
  api_key: $LINEAR_API_KEY
  project_slug: "liev-minecontext-source-research-72f71ab395e3"
  active_states:
    - Todo
    - In Progress
  terminal_states:
    - Done
    - Canceled
    - Cancelled
    - Duplicate
polling:
  interval_ms: 5000
workspace:
  root: ~/code/liev-symphony-workspaces-minecontext
hooks:
  after_create: |
    git clone --depth 1 https://github.com/veil-chow-fyaic/MineContext.git .
    git status --short
agent:
  max_concurrent_agents: 1
  max_turns: 20
codex:
  command: codex --config shell_environment_policy.inherit=all --config 'model="gpt-5.5"' app-server
  approval_policy: never
  thread_sandbox: workspace-write
  turn_sandbox_policy:
    type: workspaceWrite
    networkAccess: true
server:
  port: 4101
---

You are working on a Linear issue for liev's Symphony + Codex MineContext research lane.

Issue:

- Identifier: {{ issue.identifier }}
- Title: {{ issue.title }}
- Current status: {{ issue.state }}
- Labels: {{ issue.labels }}
- URL: {{ issue.url }}

Description:

{% if issue.description %}
{{ issue.description }}
{% else %}
No description provided.
{% endif %}

## Operating rules

- Work only inside the current Symphony workspace.
- This lane is for source-level research and documentation in `veil-chow-fyaic/MineContext`.
- Keep changes minimal and scoped to the Linear issue.
- Prefer adding or updating documentation. Do not change runtime code unless the issue explicitly asks for it.
- Do not read, print, create, or modify secrets.
- Do not start the MineContext desktop recorder or collect live user screenshots.
- Do not call production services.
- Do not merge PRs.
- Do not mark Linear issues Done directly.
- The autonomous closure target is `In Review`, not `Done`.
- Move the Linear issue to `In Review` after opening a PR and reporting proof of work.
- After moving the issue to `In Review`, stop.

## Research task expectations

For source research tasks, produce a durable Markdown document under `docs/`.

The document must include:

- Goal and source issue context.
- Key source paths and classes/functions inspected.
- Desktop capture entry points.
- Capture frequency, scheduling, start/stop behavior, retries, and throttling.
- Data pipeline from capture to processing, storage, and consumption.
- Model call chain for VLM, embedding, and context agent usage.
- Local storage and privacy boundary.
- Backend API, Electron control API, and CLI-Anything control surface.
- At least one Mermaid diagram.
- Engineering risks and recommended next steps.

## Validation

Run this before publishing:

```bash
test -s docs/minecontext-source-research.md
rg -n "ScreenMonitorTask|1733|1734|VLM|embedding|Mermaid|数据流|采集频率|隐私|control API" docs/minecontext-source-research.md
```

If a stronger project-local validation command is relevant and cheap, run it too and report the result.

## GitHub publishing strategy

Primary path:

- Use normal git commands when the workspace `.git` metadata is writable:
  - create a task branch,
  - commit,
  - push,
  - open a PR with `gh pr create`.

Fallback path:

- If local git cannot create refs, index locks, branches, or commits because `.git` is read-only or restricted, do not ask the user for help.
- Use existing `gh` CLI authentication and GitHub Git API calls to publish the same result remotely:
  - read the current `origin/main` SHA,
  - create blobs for changed files,
  - create a tree based on `origin/main`,
  - create a commit,
  - create or update the remote branch,
  - create the PR.
- The PR branch must be named:
  `liev/{{ issue.identifier | downcase }}-short-title`.
- Record in Linear that the GitHub API path was used and why.
- If GitHub API publishing fails, document the exact command/error in Linear and keep the issue in `In Progress` unless a PR exists.

## Expected workflow

1. Inspect the repo before editing.
2. Implement the smallest useful documentation artifact.
3. Run the validation command.
4. Create a task branch named `liev/{{ issue.identifier | downcase }}-short-title`.
5. Commit changes on the task branch, or use the GitHub API fallback when local `.git` writes are blocked.
6. Push the branch with `git push -u origin HEAD`, or create/update the remote branch through GitHub Git API when local git cannot publish.
7. Open a GitHub PR with `gh pr create`, or `gh api repos/:owner/:repo/pulls` when needed.
8. Include in the PR body:
   - Linear issue reference
   - Summary
   - Validation run and result
   - Known limitations or blockers
9. Report the PR and validation result back to Linear.
10. Move the Linear issue to `In Review` when ready for Veil.
11. Stop immediately after the issue is in `In Review`.

## Completion bar

The agent is not allowed to decide final completion. A task is ready for human review when:

- A PR exists.
- Validation passes or a precise blocker is documented.
- The Linear issue has proof of work and the PR link.
- The issue is in `In Review`, which tells Symphony the autonomous run is done.

Final Done requires human acceptance.
