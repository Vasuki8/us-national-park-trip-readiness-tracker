"""POSIX private-file boundary for offline editorial operations, not hosted storage."""
from __future__ import annotations
import json
import os
import re
import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_INPUT_BYTES = 8 * 1024 * 1024

class ReviewStoreError(ValueError):
    """Fixed machine codes only; never interpolate user/source payloads."""

def require(value: object, code: str = 'invalid_review_store') -> None:
    if not value:
        raise ReviewStoreError(code)

def check_path(value: Path) -> Path:
    require(os.name == 'posix' and hasattr(os, 'getuid'), 'unsupported_review_platform')
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts, 'invalid_private_path')
    require(path != REPO_ROOT and REPO_ROOT not in path.parents and path not in REPO_ROOT.parents,
            'protected_repository_path')
    for item in reversed((path, *path.parents)):
        if item.is_symlink():
            raise ReviewStoreError('symlink_private_path')
    # POSIX permits a distinct lexical // anchor for the same local destination.
    path = path.resolve()
    require(path != REPO_ROOT and REPO_ROOT not in path.parents and path not in REPO_ROOT.parents,
            'protected_repository_path')
    return path

def private_stat(path: Path, *, directory: bool = False):
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode), 'not_private_regular_file')
    require(info.st_uid == os.getuid() and info.st_mode & 0o077 == 0, 'insecure_private_permissions')
    if not directory:
        require(info.st_nlink == 1, 'hardlinked_private_file')
    return info

def _pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate_json_key')
        result[key] = value
    return result

def parse_json(raw: bytes):
    try:
        def bad_constant(_):
            raise ReviewStoreError('nonfinite_json')
        return json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=bad_constant)
    except ReviewStoreError:
        raise
    except (ValueError, UnicodeError, RecursionError):
        raise ReviewStoreError('invalid_private_json') from None

def read_private_json(value: Path):
    path = check_path(value)
    try:
        original = private_stat(path)
        require(0 < original.st_size <= MAX_INPUT_BYTES, 'private_input_too_large')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            actual = os.fstat(stream.fileno())
            require((actual.st_dev, actual.st_ino) == (original.st_dev, original.st_ino), 'private_input_changed')
            raw = stream.read(MAX_INPUT_BYTES + 1)
        require(len(raw) <= MAX_INPUT_BYTES, 'private_input_too_large')
        return parse_json(raw)
    except ReviewStoreError:
        raise
    except OSError:
        raise ReviewStoreError('private_input_unreadable') from None
