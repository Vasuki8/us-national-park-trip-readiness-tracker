"""Neutral immutable checkpoint files on trusted owner-only POSIX storage.

Reuse the editorial path/permission guards. Installation never overwrites and
is the commit point: later sync or cleanup errors may leave completed output.
No abandoned locks, old temporary files or retained evidence are repaired.
"""
from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .entry_review_io import ReviewStoreError, check_path, private_stat, require


def private_checkpoint_path(value: Path) -> Path:
    """Require an external canonical path and an existing owner-only parent."""
    try:
        path = check_path(Path(value))
        private_stat(path.parent, directory=True)
        return path
    except OSError:
        raise ReviewStoreError('private_checkpoint_storage_refused') from None


def _output_paths(destination: Path, source: Path | None) -> tuple[Path, Path]:
    output = private_checkpoint_path(destination)
    lock = private_checkpoint_path(Path(str(output) + '.lock'))
    original = None if source is None else private_checkpoint_path(source)
    require(original not in (output, lock), 'overlapping_private_checkpoint_paths')
    require(not output.exists(), 'private_checkpoint_destination_exists')
    require(not lock.exists(), 'private_checkpoint_output_locked')
    return output, lock


@contextmanager
def locked_private_output(destination: Path, source: Path | None = None):
    """Exclusively lock a fresh output; never steal an existing writer lock."""
    output, lock = _output_paths(destination, source)
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        raise ReviewStoreError('private_checkpoint_output_locked') from None
    try:
        with os.fdopen(fd, 'w', encoding='ascii') as stream:
            stream.write(str(os.getpid()))
            stream.flush()
            os.fsync(stream.fileno())
        require(not output.exists(), 'private_checkpoint_destination_exists')
        yield output
    finally:
        lock.unlink()


def sync_private_directory(path: Path) -> None:
    """Sync a local directory after its final file has been installed."""
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def install_private_bytes(output: Path, data: bytes, *, max_bytes: int) -> None:
    """Install bounded bytes once; preserve output after the exclusive link."""
    require(type(max_bytes) is int and max_bytes > 0 and isinstance(data, bytes)
            and 0 < len(data) <= max_bytes, 'private_checkpoint_too_large')
    destination = private_checkpoint_path(output)
    temporary = None
    try:
        fd, name = tempfile.mkstemp(dir=destination.parent, prefix='.checkpoint-', suffix='.tmp')
        temporary = Path(name)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, destination)
        temporary.unlink()
        temporary = None
        sync_private_directory(destination.parent)
        private_stat(destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
