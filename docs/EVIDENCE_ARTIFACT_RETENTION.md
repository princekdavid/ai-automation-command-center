# Evidence Artifact Storage and Retention (MVP)

Status: integrated into pytest execution, API, SQLite history, and Test Explorer. The latest history-persistence changes have regression tests, but exact-head CI validation is pending. Earlier backend/frontend checks passed on source head `014649e0616d72b40957928ee2fb397d74ff43fb` ([backend run #74](https://github.com/princekdavid/ai-automation-command-center/actions/runs/38162755856), [frontend run #43](https://github.com/princekdavid/ai-automation-command-center/actions/runs/38162755878)).
Branch: `feat/evidence-artifact-retention`
Scope: local, single-user MVP only.

## Implemented in this branch (backend CI passed on exact source head)

- Opt-in local artifact store; disabled by default via `AAC_ARTIFACTS_ENABLED=false`.
- Configurable root via `AAC_ARTIFACTS_DIR`; default `~/.ai-automation-command-center/artifacts`.
- Generated opaque IDs and filenames; caller input is never used as a path.
- Per-artifact byte limit, total live-artifact budget, age-based retention, oldest-first cleanup.
- Metadata records execution ID, kind, byte count, SHA-256, timestamp, and media type.
- Execution-scoped metadata lookup and reads that verify path boundary, byte count, and digest.
- Initial unit tests for disabled behavior, round-trip reads, scope, oversize rejection, budget cleanup, age expiry, and tamper detection.
- Pytest executor attempts to persist the generated JUnit XML report when artifact storage is enabled; retention errors are best-effort and do not overwrite the test result.
- `GET /api/v1/executions/{request_id}/artifacts` returns bounded metadata only.
- `GET /api/v1/executions/{request_id}/artifacts/{artifact_id}` downloads bytes with attachment disposition, `nosniff`, and `no-store` headers.
- API regression tests cover listing, download behavior, execution scoping, and unknown executions.
- Artifact references are persisted in SQLite history with an additive migration; existing rows receive an empty artifact list.
- Only an allowlist of artifact ID, kind, size, digest, timestamp, and media type is persisted. Storage keys and filesystem paths are discarded.
- Test Explorer displays download links on historical run cards when saved references are present.
- Regression tests cover reference persistence, updates, legacy schema migration, and historical status response.

## Goals and safety boundaries

Keep compact normalized run summaries in the existing history store and artifact bytes separately. Evidence may contain secrets or customer data; store only deliberately selected JUnit bundles or bounded diagnostic excerpts. Never collect environment dumps, credentials, cookies, or full request/response bodies by default.

- No cloud storage, remote uploads, AI processing, multi-user access, or compliance guarantees.
- Artifact persistence is opt-in and storage failures must not rewrite the actual test outcome.
- Never expose absolute filesystem paths to API clients.
- Never accept caller-supplied paths for read/delete operations.
- Local test execution is not a sandbox.

## Remaining integration work

1. Validate the newest history persistence and Test Explorer integration on the exact PR head.
2. Add API tests for missing/expired artifacts and non-leaking errors.
3. Add symlink/root-boundary, idempotent cleanup, missing-file, corrupt metadata, and partial-write tests where supported.
4. Keep API responses restricted to opaque IDs and approved metadata; never expose storage keys or absolute paths.
5. Update status/changelog after validation.

## Definition of done

- Backend tests pass on the exact proposed head; frontend build passes if API/UI changes are included.
- Artifact integration is covered by API and execution lifecycle tests.
- Configuration and operational limitations are documented.
- Status/changelog clearly distinguish implemented, validated, and pending behavior.
- Changes remain in a draft PR; no direct push to `main`, auto-merge, deployment, secrets, or paid AI service.
