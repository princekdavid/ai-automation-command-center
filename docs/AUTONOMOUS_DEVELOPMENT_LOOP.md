# Five-Minute Autonomous Development Loop

## What this provides

The GitHub Actions workflow `.github/workflows/autonomous-development-loop.yml` is scheduled with
`*/5 * * * *` and can also be started manually. GitHub scheduled workflows are best-effort and
may start late; this is not a hard real-time five-minute guarantee.

Every run inspects open pull requests and their visible check state. Actual autonomous coding
requires a separate agent service. Without that service configured, the workflow reports the
missing configuration and makes no code changes.

## Required repository Actions secrets

Configure both secrets in **Settings → Secrets and variables → Actions**:

- `AUTONOMOUS_AGENT_URL`: base URL of a trusted, reachable agent service.
- `AUTONOMOUS_AGENT_TOKEN`: bearer token for that service.

Do not put tokens in source files, issues, PR descriptions, or workflow logs.

## Agent service contract

The workflow sends one POST request per run to
`{AUTONOMOUS_AGENT_URL}/v1/development-runs` with a bearer token and JSON fields:
`repository`, `default_branch`, `run_url`, `task_ledger_path`, `max_tasks=1`,
`require_green_checks=true`, `must_open_pull_request=true`, and `auto_merge=false`.

The service must implement this contract. The workflow does not provision an AI coding service
or supply an AI model/API key automatically. Verify the endpoint and provider before adding these
secrets. Use a dedicated least-privilege GitHub App/token with branch/PR permissions; avoid broad
personal access tokens where possible.

## Required agent behavior

1. Read the product/architecture/security docs, `IMPLEMENTATION_STATUS.md`, `ROADMAP.md`,
   `AUTONOMOUS_TASKS.md`, open PRs, and their CI status.
2. Choose one pending task whose dependencies are satisfied. Never duplicate an open PR.
3. Make a small, auditable change on a new feature branch; add/update tests and documentation.
4. Run relevant backend tests and frontend typecheck/build/tests when applicable.
5. If a check fails, fix it before advancing; if blocked, report the blocker and stop.
6. Update the ledger/status with evidence, then open or update a PR. Never push to the default
   branch and never auto-merge.
7. Never access secrets beyond those explicitly required, expose secrets in logs, deploy, mutate
   connected user projects, run arbitrary shell input, or enable self-healing without approval.
8. Limit each scheduled invocation to one task and a bounded execution time. Use idempotency and a
   repository-level lock so overlapping invocations cannot duplicate work.

## Test gate

A green workflow run is necessary but not sufficient for a task to be marked complete. The agent
must report the exact commands run, their exit status, and the relevant run/PR URLs. If checks are
missing or skipped, record validation as unknown rather than green.

## Current limitation

Until a compatible agent service is deployed and both secrets are configured, the schedule only
checks and reports repository/PR status. It cannot autonomously write code, choose and implement
the next task, or fix failing tests. This explicit fail-closed behavior avoids pretending that a
scheduler alone is a coding agent.
