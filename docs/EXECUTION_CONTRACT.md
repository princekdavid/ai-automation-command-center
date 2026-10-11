# Execution Contract

## Purpose

Define the framework-neutral boundary between the command center and framework-native execution engines. The contract remains framework-neutral; the current MVP also includes a controlled local pytest executor behind an explicit authorization boundary.

## Request flow

```text
Test Explorer selection
        ↓
ExecutionRequest
        ↓
Capability + authorization validation
        ↓
Framework adapter execution boundary
        ↓
ExecutionResult
        ↓
Evidence / failure analysis
```

## Safety boundary

- Constructing an `ExecutionRequest` never runs a command.
- The caller must explicitly provide the target project and runner.
- `allow_side_effects` defaults to `false` and is created server-side from an explicit execution authorization field; the UI must not silently enable it.
- The execution service verifies adapter capability before invoking a registered executor.
- The pytest executor enforces the requested timeout. Environment overrides remain a future hardening item and are not currently accepted by the API.
- Raw framework output must be normalized before it reaches analysis or dashboard consumers.
- No repository mutation, package installation, deployment, or production action is implied by this contract.

## Request contract

`ExecutionRequest` contains:

- `request_id`: caller-generated correlation identifier.
- `mode`: `single` or `selection`.
- `target`: project path, runner, and normalized test IDs.
- `policy`: side-effect permission, timeout, and environment values.
- `metadata`: extensibility field for future non-breaking additions.

## Result contract

`ExecutionResult` contains:

- request correlation ID
- lifecycle status
- normalized per-test outcomes
- optional start/completion timestamps
- normalized error information
- extensible metadata

`EvidenceReference` intentionally stores a reference rather than embedding large logs, screenshots, videos, or traces in the result object.

## Explicit non-goals

This milestone does not add:

- remote execution
- arbitrary shell command construction
- remote execution
- repository writes
- package installation
- retries
- parallel scheduling
- AI-generated test execution
- self-healing

Remote execution, retries, scheduling, AI-generated execution, and self-healing require separate contracts, capability checks, security decisions, and validation.


## Local execution history

The current API stores a compact local SQLite record after each execution request, including rejected requests. The default database path is `~/.ai-automation-command-center/history.sqlite3`; set `AAC_RUN_DB_PATH` to choose another local path.

- `GET /api/v1/executions?limit=20` lists recent summaries (limit 1–100).
- `GET /api/v1/executions/{request_id}` retrieves one summary.
- The POST execution response includes `history_saved`; if local persistence fails, the immediate execution response is still returned.
- Stored fields include request ID, project path, runner, terminal status, timestamps, per-test outcome/duration, deterministic failure category, matched rule, and evidence count.
- Raw stdout/stderr, raw per-test failure messages, and evidence file contents are intentionally not persisted by this store.
- The local database is not encrypted and has no retention/cleanup policy yet. Keep the file on a trusted machine, restrict filesystem access, and delete it when no longer needed.
- This is synchronous execution history, not a background job queue. Running/rerunning state, cancellation, artifact storage, and multi-user access controls are not implemented.
