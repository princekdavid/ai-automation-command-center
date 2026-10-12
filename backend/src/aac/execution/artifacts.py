"""Opt-in local evidence artifact store with bounded size and retention.

This module is intentionally separate from normalized execution history. Callers
must explicitly enable it; artifacts may contain sensitive test output.
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
import stat
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator


class ArtifactNotFoundError(LookupError):
    """Artifact does not exist, expired, or is outside the configured store."""


class ArtifactStoreError(RuntimeError):
    """Artifact storage failed without implying that the test itself failed."""


class LocalEvidenceArtifactStore:
    """Store bounded bytes under a private local root and expire old artifacts.

    The store is disabled by default. The API should expose only opaque artifact
    IDs and metadata, never storage paths. Do not pass arbitrary user paths here.
    """

    def __init__(
        self,
        root: str | Path | None = None,
        *,
        enabled: bool | None = None,
        max_artifact_bytes: int = 2_000_000,
        max_total_bytes: int = 50_000_000,
        retention_days: int = 14,
    ) -> None:
        self.enabled = (
            os.getenv("AAC_ARTIFACTS_ENABLED", "false").lower() == "true"
            if enabled is None else enabled
        )
        if max_artifact_bytes < 1 or max_total_bytes < 1 or retention_days < 1:
            raise ValueError("artifact limits and retention must be positive")
        if max_artifact_bytes > max_total_bytes:
            raise ValueError("max_artifact_bytes cannot exceed max_total_bytes")
        configured = root or os.getenv("AAC_ARTIFACTS_DIR")
        self.root = Path(configured).expanduser() if configured else (
            Path.home() / ".ai-automation-command-center" / "artifacts"
        )
        self.max_artifact_bytes = max_artifact_bytes
        self.max_total_bytes = max_total_bytes
        self.retention_days = retention_days
        self.database_path = self.root / "artifacts.sqlite3"

    def _prepare(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        resolved_root = self.root.resolve(strict=True)
        if self.root.is_symlink():
            raise ArtifactStoreError("artifact root must not be a symlink")
        try:
            resolved_root.relative_to(self.root.absolute().parent.resolve())
        except ValueError as exc:
            raise ArtifactStoreError("invalid artifact root") from exc
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    storage_key TEXT NOT NULL UNIQUE,
                    byte_size INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    expired INTEGER NOT NULL DEFAULT 0
                )
                """
            )
        return resolved_root

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Commit/rollback transactions and always close SQLite connections."""
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _connect(self) -> sqlite3.Connection:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Never let SQLite follow a pre-existing symlink for either the store
        # directory or database. These checks are defense in depth for a
        # dedicated local store; they do not protect against a hostile process
        # running as the same OS user.
        if self.root.is_symlink() or self.database_path.is_symlink():
            raise ArtifactStoreError("artifact root and database must not be symlinks")
        try:
            os.chmod(self.root, 0o700)
        except OSError:
            # Some platforms/filesystems do not support POSIX permission bits.
            pass
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            os.chmod(self.database_path, 0o600)
        except OSError:
            # Keep the store usable where chmod is unsupported; document the
            # host filesystem as part of the local trust boundary.
            pass
        return connection

    def save(
        self,
        execution_id: str,
        kind: str,
        content: bytes,
        media_type: str = "application/octet-stream",
    ) -> dict:
        if not self.enabled:
            raise ArtifactStoreError("artifact persistence is disabled")
        if not execution_id.strip() or not kind.strip() or not media_type.strip():
            raise ValueError("execution_id, kind, and media_type are required")
        if not isinstance(content, bytes):
            raise TypeError("content must be bytes")
        if len(content) > self.max_artifact_bytes:
            raise ValueError("artifact exceeds configured per-artifact size limit")

        root = self._prepare()
        self.cleanup()
        artifact_id = uuid.uuid4().hex
        storage_key = f"{artifact_id}.bin"
        target = root / storage_key
        resolved_target = target.resolve(strict=False)
        if resolved_target.parent != root or target.is_symlink():
            raise ArtifactStoreError("artifact path escaped storage root")
        now = datetime.now(timezone.utc)
        digest = hashlib.sha256(content).hexdigest()
        try:
            # Exclusive creation prevents replacing an existing file or following
            # a pre-existing leaf symlink.
            with target.open("xb") as stream:
                try:
                    os.chmod(target, 0o600)
                except OSError:
                    pass
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            with self._connection() as connection:
                connection.execute(
                    """INSERT INTO artifacts
                    (artifact_id, execution_id, kind, storage_key, byte_size,
                     sha256, created_at, media_type, expired)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                    (artifact_id, execution_id, kind, storage_key, len(content),
                     digest, now.isoformat(), media_type),
                )
            self.cleanup()
            metadata = self.get_metadata(execution_id, artifact_id)
            if metadata is None:
                raise ArtifactStoreError("artifact was removed by retention policy")
            return metadata
        except Exception as exc:
            try:
                target.unlink(missing_ok=True)
            except OSError:
                pass
            if isinstance(exc, (ValueError, TypeError, ArtifactStoreError)):
                raise
            raise ArtifactStoreError("unable to persist evidence artifact") from exc

    def list_metadata(self, execution_id: str, limit: int = 50) -> list[dict]:
        if not self.enabled:
            return []
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        self._prepare()
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT artifact_id, execution_id, kind, byte_size, sha256,
                          created_at, media_type
                   FROM artifacts WHERE execution_id = ? AND expired = 0
                   ORDER BY created_at DESC, artifact_id DESC LIMIT ?""",
                (execution_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_metadata(self, execution_id: str, artifact_id: str) -> dict | None:
        if not self.enabled:
            return None
        self._prepare()
        with self._connection() as connection:
            row = connection.execute(
                """SELECT artifact_id, execution_id, kind, byte_size, sha256,
                          created_at, media_type
                   FROM artifacts
                   WHERE execution_id = ? AND artifact_id = ? AND expired = 0""",
                (execution_id, artifact_id),
            ).fetchone()
        return dict(row) if row else None

    def read(self, execution_id: str, artifact_id: str) -> tuple[dict, bytes]:
        metadata = self.get_metadata(execution_id, artifact_id)
        if metadata is None:
            raise ArtifactNotFoundError("artifact not found")
        root = self.root.resolve(strict=True)
        with self._connection() as connection:
            row = connection.execute(
                """SELECT storage_key FROM artifacts
                   WHERE execution_id = ? AND artifact_id = ? AND expired = 0""",
                (execution_id, artifact_id),
            ).fetchone()
        if row is None:
            raise ArtifactNotFoundError("artifact not found")
        target = root / row["storage_key"]
        try:
            # Path checks alone are vulnerable to a leaf being swapped for a
            # symlink between validation and read. Open without following a
            # symlink where the platform supports O_NOFOLLOW, then validate the
            # opened file descriptor itself before reading any evidence bytes.
            if target.is_symlink() or target.resolve(strict=True).parent != root:
                raise ArtifactNotFoundError("artifact not found")
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(target, flags)
            try:
                file_stat = os.fstat(descriptor)
                if not stat.S_ISREG(file_stat.st_mode):
                    raise ArtifactNotFoundError("artifact not found")
                with os.fdopen(descriptor, "rb") as stream:
                    descriptor = -1
                    content = stream.read(self.max_artifact_bytes + 1)
            finally:
                if descriptor >= 0:
                    os.close(descriptor)
        except (OSError, ValueError) as exc:
            raise ArtifactNotFoundError("artifact not found") from exc
        if len(content) > self.max_artifact_bytes:
            raise ArtifactNotFoundError("artifact not found")
        if len(content) != metadata["byte_size"] or hashlib.sha256(content).hexdigest() != metadata["sha256"]:
            raise ArtifactNotFoundError("artifact not found")
        return metadata, content

    def cleanup(self, *, now: datetime | None = None) -> int:
        """Expire by age, then oldest-first until total live bytes fit the budget."""
        if not self.enabled:
            return 0
        root = self._prepare()
        current = now or datetime.now(timezone.utc)
        cutoff = current - timedelta(days=self.retention_days)
        removed = 0
        with self._connection() as connection:
            # Serialize cleanup decisions across store instances/process threads.
            # Without an early write lock, concurrent cleaners can compute the
            # live-byte total from the same snapshot and both make stale
            # retention decisions before either marks rows expired.
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                """SELECT artifact_id, storage_key, byte_size, created_at
                   FROM artifacts WHERE expired = 0
                   ORDER BY created_at ASC, artifact_id ASC"""
            ).fetchall()
            total = sum(max(0, int(row["byte_size"])) for row in rows)
            for row in rows:
                try:
                    created = datetime.fromisoformat(row["created_at"])
                    too_old = created < cutoff
                except (TypeError, ValueError):
                    too_old = True
                over_budget = total > self.max_total_bytes
                if not too_old and not over_budget:
                    continue
                target = root / row["storage_key"]
                try:
                    if target.parent.resolve(strict=True) == root and not target.is_symlink():
                        target.unlink(missing_ok=True)
                except OSError:
                    # Mark metadata expired so callers cannot retrieve it; an
                    # orphan file is safe to reconcile on a later cleanup.
                    pass
                connection.execute(
                    "UPDATE artifacts SET expired = 1 WHERE artifact_id = ?",
                    (row["artifact_id"],),
                )
                total -= max(0, int(row["byte_size"]))
                removed += 1
        return removed
