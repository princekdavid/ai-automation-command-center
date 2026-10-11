# Evidence Artifact Storage and Retention (MVP)

Status: implementation started; local store module and unit tests added, API integration and exact-head validation pending.
Branch: `feat/evidence-artifact-retention`
Scope: local, single-user MVP only.

## Implemented in this branch (not yet validated by CI)

- Opt-in local artifact store; disabled by default via `AAC_ARTIFACTS_ENABLED=false`.
- Configurable root via `AAC_ARTIFACTS_DIR`; default `~/.ai-automation-command-center/artifacts`.
- Generated opaque IDs and filenames; caller input is never used as a path.
- Per-artifact byte limit, total live-artifact budget, age-based retention, oldest-first cleanup.
- Metadata records execution ID, kind, byte count, SHA-256, timestamp, and media type.
- Execution-scoped metadata lookup and reads that verify path boundary, byte count, and digest.
- Initial unit tests for disabled behavior, round-trip reads, scope, oversize rejection, budget cleanup, age expiry, and tamper detection.

The module is not yet wired into the FastAPI execution lifecycle or download/list endpoints. Do not treat evidence artifacts as an available UI/API feature until integration and CI are complete.

## Goals and safety boundaries

Keep compact normalized run summaries in the existing history store and artifact bytes separately. Evidence may contain secrets or customer data; store only deliberately selected JUnit bundles or bounded diagnostic excerpts. Never collect environment dumps, credentials, cookies, or full request/response bodies by default.

- No cloud storage, remote uploads, AI processing, multi-user access, or compliance guarantees.
- Artifact persistence is opt-in and storage failures must not rewrite the actual test outcome.
- Never expose absolute filesystem paths to API clients.
- Never accept caller-supplied paths for read/delete operations.
- Local test execution is not a sandbox.

## Remaining integration work

1. Run backend tests on the exact feature head and fix any failures.
2. Wire artifact persistence into terminal execution results without making it mandatory for test success.
3. Add bounded metadata list and artifact download endpoints scoped to an execution ID; use safe content-disposition and consistent not-found responses.
4. Ensure API responses expose only opaque IDs and metadata, never storage keys or absolute paths.
5. Add API tests for authorization/scope, pagination, missing/expired artifacts, and non-leaking errors.
6. Add symlink/root-boundary, idempotent cleanup, missing-file, corrupt metadata, and partial-write tests where supported.
7. Update README, implementation status, and changelog after validation.

## Definition of done

- Backend tests pass on the exact proposed head; frontend build passes if API/UI changes are included.
- Artifact integration is covered by API and execution lifecycle tests.
- Configuration and operational limitations are documented.
- Status/changelog clearly distinguish implemented, validated, and pending behavior.
- Changes remain in a draft PR; no direct push to `main`, auto-merge, deployment, secrets, or paid AI service.
