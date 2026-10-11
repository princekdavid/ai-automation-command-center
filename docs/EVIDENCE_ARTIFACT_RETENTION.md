# Evidence Artifact Storage and Retention

Status: implemented in cumulative draft [PR #17](https://github.com/princekdavid/ai-automation-command-center/pull/17). Backend and frontend CI passed on reviewed code head `cc9e8aebb3b8a6f608100fe66ca733d613096488`: [backend workflow](https://github.com/princekdavid/ai-automation-command-center/actions/runs/38164557651), [frontend workflow](https://github.com/princekdavid/ai-automation-command-center/actions/runs/38164557644). Any subsequent code/test change requires fresh CI validation.

## Implemented

- Opt-in local artifact store, disabled by default via `AAC_ARTIFACTS_ENABLED=false`.
- Configurable root via `AAC_ARTIFACTS_DIR`; default `~/.ai-automation-command-center/artifacts`.
- Generated opaque IDs and filenames; caller input is not used as a storage path.
- Per-artifact byte limit, total live-artifact budget, age-based retention, and oldest-first cleanup.
- Metadata includes execution ID, kind, byte count, SHA-256, timestamp, and media type.
- Execution-scoped metadata lookup and reads verify the resolved path boundary, byte count, and digest.
- Pytest executor attempts to retain generated JUnit XML when storage is enabled; storage errors do not rewrite the test outcome.
- `GET /api/v1/executions/{request_id}/artifacts` returns bounded metadata.
- `GET /api/v1/executions/{request_id}/artifacts/{artifact_id}` downloads bytes with attachment disposition, `nosniff`, and `no-store` headers.
- Artifact references are persisted in SQLite history using an additive migration and an allowlist that excludes storage keys and absolute paths.
- Test Explorer displays links for retained evidence on historical runs.
- Regression tests cover disabled-by-default behavior, round-trip/digest checks, execution scoping, size rejection, age/budget expiry, tampering, missing files, symlinked leaf files, connection closure, API scoping, and history migration.

## Security boundaries

- Local, single-user MVP only; there is no API authentication or user identity layer. Keep the API bound to localhost and do not expose it to a LAN/public network without separate authentication and network-control work.
- Evidence may contain customer data or secrets emitted by tests. Enable retention only for trusted projects and deliberately selected evidence.
- No cloud storage, remote uploads, AI processing, multi-user access, encryption-at-rest guarantee, or compliance guarantee.
- Artifact and history files rely on host filesystem permissions. Pre-existing directory/database permission hardening and history retention are follow-up items.
- Local test execution is not a sandbox.

## Review follow-ups

- Added explicit regression coverage for a symlinked artifact root and a corrupted storage key attempting to escape the root; validate these tests on the updated PR head.
- Continue evaluating concurrent cleanup behavior and filesystem race conditions as part of production hardening.
- Keep API responses restricted to opaque IDs and approved metadata; never expose storage keys or absolute paths.
