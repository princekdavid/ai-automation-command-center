# Execution Contract

## Purpose

Define the framework-neutral boundary between the command center and future framework-native execution engines. This document defines contracts only; it does **not** authorize or implement test execution.

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
- `allow_side_effects` defaults to `false`.
- A future executor must verify adapter capability before execution.
- A future executor must enforce the requested timeout and environment policy.
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

- subprocess execution
- shell command construction
- remote execution
- repository writes
- package installation
- retries
- parallel scheduling
- AI-generated test execution
- self-healing

Those behaviors require separate contracts, capability checks, security decisions, and validation.
