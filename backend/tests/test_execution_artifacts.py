import hashlib
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from aac.execution.artifacts import (
    ArtifactNotFoundError,
    ArtifactStoreError,
    LocalEvidenceArtifactStore,
)


def test_store_is_disabled_by_default_and_does_not_write(tmp_path) -> None:
    store = LocalEvidenceArtifactStore(tmp_path / "artifacts", enabled=False)
    with pytest.raises(ArtifactStoreError, match="disabled"):
        store.save("run-1", "junit", b"<testsuite/>")
    assert not (tmp_path / "artifacts" / "artifacts.sqlite3").exists()


def test_save_read_metadata_and_digest(tmp_path) -> None:
    store = LocalEvidenceArtifactStore(
        tmp_path / "artifacts", enabled=True, max_artifact_bytes=100,
        max_total_bytes=200, retention_days=7,
    )
    payload = b"<testsuite tests='1'/>"
    metadata = store.save("run-1", "junit", payload, "application/xml")

    listed = store.list_metadata("run-1")
    read_metadata, content = store.read("run-1", metadata["artifact_id"])

    assert len(listed) == 1
    assert content == payload
    assert read_metadata["sha256"] == hashlib.sha256(payload).hexdigest()
    assert read_metadata["byte_size"] == len(payload)
    assert "storage_key" not in metadata
    assert "storage_key" not in listed[0]


def test_artifact_is_scoped_to_execution_and_rejects_oversize(tmp_path) -> None:
    store = LocalEvidenceArtifactStore(
        tmp_path / "artifacts", enabled=True, max_artifact_bytes=4,
        max_total_bytes=8,
    )
    metadata = store.save("run-1", "log", b"safe")
    with pytest.raises(ArtifactNotFoundError):
        store.read("run-2", metadata["artifact_id"])
    with pytest.raises(ValueError, match="size limit"):
        store.save("run-1", "log", b"oversized")


def test_cleanup_expires_oldest_artifact_to_respect_budget(tmp_path) -> None:
    store = LocalEvidenceArtifactStore(
        tmp_path / "artifacts", enabled=True, max_artifact_bytes=8,
        max_total_bytes=12, retention_days=30,
    )
    first = store.save("run-1", "log", b"123456")
    second = store.save("run-2", "log", b"abcdef")
    # Set stable, old/new timestamps for deterministic oldest-first cleanup.
    with store._connection() as connection:
        connection.execute(
            "UPDATE artifacts SET created_at = ? WHERE artifact_id = ?",
            ((datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat(),
             first["artifact_id"]),
        )
        connection.execute(
            "UPDATE artifacts SET created_at = ? WHERE artifact_id = ?",
            (datetime.now(timezone.utc).isoformat(), second["artifact_id"]),
        )

    store.max_total_bytes = 8
    store.cleanup()

    with pytest.raises(ArtifactNotFoundError):
        store.read("run-1", first["artifact_id"])
    assert store.read("run-2", second["artifact_id"])[1] == b"abcdef"


def test_tampered_artifact_is_not_returned(tmp_path) -> None:
    store = LocalEvidenceArtifactStore(
        tmp_path / "artifacts", enabled=True, max_artifact_bytes=100,
        max_total_bytes=200,
    )
    metadata = store.save("run-1", "log", b"original")
    path = tmp_path / "artifacts" / f"{metadata['artifact_id']}.bin"
    path.write_bytes(b"tampered")

    with pytest.raises(ArtifactNotFoundError):
        store.read("run-1", metadata["artifact_id"])


def test_cleanup_expires_artifact_past_retention_age(tmp_path) -> None:
    store = LocalEvidenceArtifactStore(
        tmp_path / "artifacts", enabled=True, max_artifact_bytes=100,
        max_total_bytes=200, retention_days=1,
    )
    metadata = store.save("run-1", "log", b"old")
    old_time = datetime.now(timezone.utc) - timedelta(days=2)
    with store._connection() as connection:
        connection.execute(
            "UPDATE artifacts SET created_at = ? WHERE artifact_id = ?",
            (old_time.isoformat(), metadata["artifact_id"]),
        )

    store.cleanup()

    assert store.get_metadata("run-1", metadata["artifact_id"]) is None


def test_missing_artifact_file_is_not_returned(tmp_path) -> None:
    store = LocalEvidenceArtifactStore(
        tmp_path / "artifacts", enabled=True, max_artifact_bytes=100,
        max_total_bytes=200,
    )
    metadata = store.save("run-missing", "log", b"evidence")
    (tmp_path / "artifacts" / f"{metadata['artifact_id']}.bin").unlink()

    with pytest.raises(ArtifactNotFoundError):
        store.read("run-missing", metadata["artifact_id"])


def test_symlinked_artifact_file_is_not_returned(tmp_path) -> None:
    store = LocalEvidenceArtifactStore(
        tmp_path / "artifacts", enabled=True, max_artifact_bytes=100,
        max_total_bytes=200,
    )
    metadata = store.save("run-symlink", "log", b"evidence")
    artifact_path = tmp_path / "artifacts" / f"{metadata['artifact_id']}.bin"
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"evidence")
    artifact_path.unlink()
    try:
        artifact_path.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable in this environment")

    with pytest.raises(ArtifactNotFoundError):
        store.read("run-symlink", metadata["artifact_id"])


def test_cleanup_expires_metadata_even_when_artifact_file_is_missing(tmp_path) -> None:
    store = LocalEvidenceArtifactStore(
        tmp_path / "artifacts", enabled=True, max_artifact_bytes=100,
        max_total_bytes=200, retention_days=1,
    )
    metadata = store.save("run-orphan", "log", b"old")
    artifact_path = tmp_path / "artifacts" / f"{metadata['artifact_id']}.bin"
    artifact_path.unlink()
    old_time = datetime.now(timezone.utc) - timedelta(days=2)
    with store._connection() as connection:
        connection.execute(
            "UPDATE artifacts SET created_at = ? WHERE artifact_id = ?",
            (old_time.isoformat(), metadata["artifact_id"]),
        )

    assert store.cleanup() == 1
    assert store.get_metadata("run-orphan", metadata["artifact_id"]) is None




def test_database_symlink_is_rejected_without_opening_target(tmp_path) -> None:
    root = tmp_path / "artifacts"
    root.mkdir()
    external_db = tmp_path / "outside.sqlite3"
    external_db.write_bytes(b"must remain untouched")
    (root / "artifacts.sqlite3").symlink_to(external_db)

    store = LocalEvidenceArtifactStore(root, enabled=True)

    with pytest.raises(ArtifactStoreError, match="must not be symlinks"):
        store.save("run-1", "log", b"evidence")
    assert external_db.read_bytes() == b"must remain untouched"


def test_store_applies_restrictive_permissions_on_posix(tmp_path) -> None:
    import os
    import stat

    if os.name != "posix":
        pytest.skip("POSIX permission bits are not portable")

    root = tmp_path / "artifacts"
    root.mkdir(mode=0o777)
    store = LocalEvidenceArtifactStore(root, enabled=True)
    store.save("run-1", "log", b"evidence")

    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert stat.S_IMODE((root / "artifacts.sqlite3").stat().st_mode) == 0o600


def test_non_regular_artifact_path_is_not_returned(tmp_path) -> None:
    store = LocalEvidenceArtifactStore(
        tmp_path / "artifacts", enabled=True, max_artifact_bytes=100,
        max_total_bytes=200,
    )
    metadata = store.save("run-directory", "log", b"evidence")
    artifact_path = tmp_path / "artifacts" / f"{metadata['artifact_id']}.bin"
    artifact_path.unlink()
    artifact_path.mkdir()

    with pytest.raises(ArtifactNotFoundError):
        store.read("run-directory", metadata["artifact_id"])


def test_store_closes_all_database_connections(tmp_path, monkeypatch) -> None:
    store = LocalEvidenceArtifactStore(
        tmp_path / "artifacts", enabled=True, max_artifact_bytes=100,
        max_total_bytes=200,
    )
    opened = []
    original_connect = store._connect

    def tracking_connect():
        connection = original_connect()
        opened.append(connection)
        return connection

    monkeypatch.setattr(store, "_connect", tracking_connect)
    store.save("run-connections", "log", b"evidence")

    assert opened
    for connection in opened:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("SELECT 1")


def test_symlinked_artifact_root_is_rejected(tmp_path) -> None:
    real_root = tmp_path / "real-artifacts"
    real_root.mkdir()
    linked_root = tmp_path / "linked-artifacts"
    try:
        linked_root.symlink_to(real_root, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks are unavailable in this environment")

    store = LocalEvidenceArtifactStore(linked_root, enabled=True)

    with pytest.raises(ArtifactStoreError, match="symlink"):
        store.list_metadata("run-root-link")


def test_corrupt_storage_key_cannot_escape_artifact_root(tmp_path) -> None:
    store = LocalEvidenceArtifactStore(
        tmp_path / "artifacts", enabled=True, max_artifact_bytes=100,
        max_total_bytes=200,
    )
    metadata = store.save("run-corrupt-key", "log", b"evidence")
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"evidence")
    with store._connection() as connection:
        connection.execute(
            "UPDATE artifacts SET storage_key = ? WHERE artifact_id = ?",
            ("../outside.bin", metadata["artifact_id"]),
        )

    with pytest.raises(ArtifactNotFoundError):
        store.read("run-corrupt-key", metadata["artifact_id"])

def test_concurrent_cleanup_serializes_retention_decisions(tmp_path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    root = tmp_path / "artifacts"
    store = LocalEvidenceArtifactStore(
        root, enabled=True, max_artifact_bytes=8, max_total_bytes=100,
        retention_days=30,
    )
    artifacts = [
        store.save(f"run-{index}", "log", b"123456")
        for index in range(3)
    ]
    now = datetime.now(timezone.utc)
    with store._connection() as connection:
        for index, artifact in enumerate(artifacts):
            connection.execute(
                "UPDATE artifacts SET created_at = ? WHERE artifact_id = ?",
                ((now - timedelta(minutes=3 - index)).isoformat(), artifact["artifact_id"]),
            )

    # Independent store objects model concurrent callers sharing the same DB.
    first = LocalEvidenceArtifactStore(
        root, enabled=True, max_artifact_bytes=8, max_total_bytes=8, retention_days=30,
    )
    second = LocalEvidenceArtifactStore(
        root, enabled=True, max_artifact_bytes=8, max_total_bytes=8, retention_days=30,
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        removed = list(pool.map(lambda instance: instance.cleanup(), (first, second)))

    assert sum(removed) == 2
    assert first.list_metadata("run-2")
    assert first.list_metadata("run-0") == []
    assert first.list_metadata("run-1") == []
