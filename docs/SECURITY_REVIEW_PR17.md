# PR #17 Security and Quality Review

Review target: cumulative integration candidate `integration/evidence-retention-on-current-stack`. Latest code/test head reviewed: `4385760f5096c4e9292b0b38710370e98a179d0f`. Backend workflow [#38171267669](https://github.com/princekdavid/ai-automation-command-center/actions/runs/38171267669) and frontend workflow [#38171267630](https://github.com/princekdavid/ai-automation-command-center/actions/runs/38171267630) both passed on this exact head.

## Review summary

A focused review identified a filesystem time-of-check/time-of-use risk in artifact reads: a leaf path could theoretically be swapped for a symlink after path validation but before `read_bytes()`. The current change opens the artifact with `O_NOFOLLOW` where the platform supports it, validates the opened descriptor is a regular file, and bounds the read to the configured per-artifact limit. A regression test also verifies that a directory cannot be returned as an artifact. This narrows the local filesystem race surface but is not a complete defense against a hostile process with the same OS user or platforms lacking `O_NOFOLLOW`. Existing controls include generated artifact filenames, parameterized SQL, execution-scoped lookups, SHA-256 and byte-size verification, bounded retention, and connection-closing context managers.

Validation: backend workflow [#38171267669](https://github.com/princekdavid/ai-automation-command-center/actions/runs/38171267669) and frontend workflow [#38171267630](https://github.com/princekdavid/ai-automation-command-center/actions/runs/38171267630) both passed on code/test head `4385760f5096c4e9292b0b38710370e98a179d0f`.

This is not a security certification. The product remains a local-only developer tool.

## Findings and follow-ups

### Deployment blocker — API has no authentication

Execution, history, status, and artifact endpoints do not enforce a user identity or access-control policy. The execution authorization checkbox only expresses UI intent; it is not authentication and does not protect the API from direct requests. Keep Uvicorn bound to `127.0.0.1`. Do not expose the API to another host, LAN, or public network until authentication and network controls are designed and tested. CORS alone is not a security boundary.

### Filesystem permissions and database symlinks

The latest change rejects a symlinked artifact root or SQLite database path before connecting, reapplies mode `0700` to the dedicated artifact directory and `0600` to the SQLite database where supported, and adds regression tests for database-symlink rejection and POSIX permissions. Unsupported filesystems/platforms may not honor POSIX modes. These controls do not defend against a hostile process running as the same OS user. History remains local and unencrypted.

### Scope checks

- Artifact storage remains disabled by default.
- New regression tests reject a symlink used as the configured artifact root and a corrupted database storage key resolving outside that root.
- No secrets, paid services, cloud uploads, deployment, auto-merge, or changes to `main` are introduced.
- Original feature PRs and integration PRs remain open and unmerged.
