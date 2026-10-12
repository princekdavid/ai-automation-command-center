# Evidence Artifact Storage and Retention

Status: implemented in cumulative draft [PR #17](https://github.com/princekdavid/ai-automation-command-center/pull/17). Latest code/test head `4385760f5096c4e9292b0b38710370e98a179d0f` passed backend [workflow #38171267669](https://github.com/princekdavid/ai-automation-command-center/actions/runs/38171267669) and frontend [workflow #38171267630](https://github.com/princekdavid/ai-automation-command-center/actions/runs/38171267630). The artifact tests use the store's closing connection context manager for database updates.

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
- Regression tests cover disabled-by-default behavior, round-trip/digest checks, execution scoping, size rejection, age/budget expiry, tampering, missing files, symlinked leaf files/roots/database, non-regular files, POSIX permissions where supported, connection closure, corrupted storage-key path escape, API scoping, and history migration.

## Security boundaries

- Local, single-user MVP only; there is no API authentication or user identity layer. Keep the API bound to localhost and do not expose it to a LAN/public network without separate authentication and network-control work.
- Evidence may contain customer data or secrets emitted by tests. Enable retention only for trusted projects and deliberately selected evidence.
- No cloud storage, remote uploads, AI processing, multi-user access, encryption-at-rest guarantee, or compliance guarantee.
- Dedicated artifact directory/database permissions are tightened to `0700`/`0600` where supported; history retention remains a follow-up. Same-user processes remain within the trust boundary.
- Local test execution is not a sandbox.

## Review follow-ups

- Continue evaluating concurrent cleanup behavior and filesystem race conditions as part of production hardening.
- Keep API responses restricted to opaque IDs and approved metadata; never expose storage keys or absolute paths.
