"""Explicit immutable private profile files; no public writer or mutable head.

Checkpoint hashes verify self-contained current state, not parent history,
source authenticity, approval or remote backup. POSIX local storage only.
"""
from __future__ import annotations

import copy
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

from .entry_review_io import (MAX_INPUT_BYTES, ReviewStoreError, check_path,
                              private_stat, read_private_json)
from .history_model import HistoryError, canonical, digest, instant
from .park_profiles import (PILOT_CODES, ProfileError, collect_profile,
                            initial_profile, validate_profile)

CHECKPOINT_FIELDS = {'schema_version', 'purpose', 'parent_checkpoint_id',
                     'checked_at', 'profiles', 'checkpoint_id'}
MAX_CHECKPOINT_BYTES = MAX_INPUT_BYTES


class ProfileCheckpointError(ValueError):
    """Fixed machine codes; never interpolate source, path or exception text."""


def _require(condition: object, code: str) -> None:
    if not condition:
        raise ProfileCheckpointError(code)


def _encoded(value: object) -> bytes:
    try:
        data = canonical(value)
    except HistoryError:
        raise ProfileCheckpointError('invalid_profile_checkpoint') from None
    _require(len(data) <= MAX_CHECKPOINT_BYTES, 'profile_checkpoint_too_large')
    return data


def _clock(value: object):
    try:
        return instant(value)
    except HistoryError:
        raise ProfileCheckpointError('invalid_profile_checkpoint_clock') from None


def validate_checkpoint(value: dict) -> dict:
    """Validate a bounded complete five-park attempt and return an isolated copy."""
    _require(isinstance(value, dict) and set(value) == CHECKPOINT_FIELDS,
             'invalid_profile_checkpoint')
    _require(type(value['schema_version']) is int and value['schema_version'] == 1
             and value['purpose'] == 'private_park_profile_checkpoint',
             'invalid_profile_checkpoint')
    parent = value['parent_checkpoint_id']
    _require(parent is None or isinstance(parent, str) and re.fullmatch('[a-f0-9]{64}', parent)
             and parent != value['checkpoint_id'], 'invalid_profile_checkpoint_parent')
    _clock(value['checked_at'])
    profiles = value['profiles']
    _require(isinstance(profiles, list) and len(profiles) == len(PILOT_CODES),
             'invalid_profile_checkpoint_scope')
    for code, profile in zip(PILOT_CODES, profiles):
        try:
            current = validate_profile(profile)
        except ProfileError:
            raise ProfileCheckpointError('invalid_profile_checkpoint') from None
        _require(current['park_code'] == code and current['collection_status'] != 'never_checked'
                 and current['last_checked_at'] == value['checked_at'],
                 'invalid_profile_checkpoint_scope')
    _encoded(value)
    core = {key: item for key, item in value.items() if key != 'checkpoint_id'}
    _require(value['checkpoint_id'] == digest(core), 'profile_checkpoint_hash_mismatch')
    return copy.deepcopy(value)


def _private_path(value: Path) -> Path:
    try:
        path = check_path(Path(value))
        private_stat(path.parent, directory=True)
        return path
    except (ReviewStoreError, OSError):
        raise ProfileCheckpointError('profile_private_storage_refused') from None


def verify_checkpoint(path: Path) -> dict:
    """Read and validate offline; neither keys nor parent files are consulted."""
    source = _private_path(path)
    try:
        value = read_private_json(source)
    except (ReviewStoreError, OSError):
        raise ProfileCheckpointError('profile_checkpoint_unreadable') from None
    return validate_checkpoint(value)


def _output_path(destination: Path, source: Path | None = None) -> tuple[Path, Path]:
    output = _private_path(destination)
    lock = _private_path(Path(str(output) + '.lock'))
    _require(source not in (output, lock), 'overlapping_profile_paths')
    _require(not output.exists(), 'profile_destination_exists')
    _require(not lock.exists(), 'profile_output_locked')
    return output, lock


@contextmanager
def _writer(destination: Path, source: Path | None = None):
    output, lock = _output_path(destination, source)
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        raise ProfileCheckpointError('profile_output_locked') from None
    try:
        with os.fdopen(fd, 'w', encoding='ascii') as stream:
            stream.write(str(os.getpid()))
            stream.flush()
            os.fsync(stream.fileno())
        # Refuse a destination installed by another writer before our lock.
        _require(not output.exists(), 'profile_destination_exists')
        yield output
    finally:
        lock.unlink()


def _sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _install(output: Path, value: dict) -> None:
    """Install once. Errors after the link commit preserve the final output."""
    data = _encoded(value)
    temporary = None
    try:
        fd, name = tempfile.mkstemp(dir=output.parent, prefix='.profile-', suffix='.tmp')
        temporary = Path(name)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, output)  # Never overwrite even an unexpected writer.
        temporary.unlink()
        temporary = None
        _sync_directory(output.parent)
        try:
            private_stat(output)
        except ReviewStoreError:
            raise ProfileCheckpointError('profile_private_storage_refused') from None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def collect_checkpoint(destination: Path, previous_path: Path | None, now: str,
                       fetch_for: Callable[[str], Callable[[int], dict]]) -> dict:
    """Validate inputs before fetching; atomically retain all five attempt states.

    fetch_for runs inside the validated output lock, allowing a CLI to acquire
    its key lazily after storage/previous-clock checks. Different destinations
    can form concurrent branches. No implicit latest pointer is maintained.
    """
    current_time = _clock(now)
    source = None if previous_path is None else _private_path(previous_path)
    previous = None if source is None else verify_checkpoint(source)
    if previous is not None:
        _require(current_time > _clock(previous['checked_at']), 'profile_collection_clock_not_advanced')
    _require(callable(fetch_for), 'invalid_profile_transport')
    _output_path(destination, source)
    with _writer(destination, source) as output:
        # Bind the exact input checked before requests; no mutable head lookup.
        profiles = []
        for index, code in enumerate(PILOT_CODES):
            baseline = initial_profile(code) if previous is None else previous['profiles'][index]
            profiles.append(collect_profile(code, baseline, now, fetch_for(code)))
        core = {'schema_version': 1, 'purpose': 'private_park_profile_checkpoint',
                'parent_checkpoint_id': None if previous is None else previous['checkpoint_id'],
                'checked_at': now, 'profiles': profiles}
        checkpoint = validate_checkpoint({**core, 'checkpoint_id': digest(core)})
        _install(output, checkpoint)
    return checkpoint


def restore_checkpoint(source: Path, destination: Path) -> dict:
    """Verify then create a fresh canonical private copy; never repair/overwrite."""
    original = _private_path(source)
    checkpoint = verify_checkpoint(original)
    with _writer(destination, original) as output:
        _install(output, checkpoint)
    restored = verify_checkpoint(output)
    _require(restored['checkpoint_id'] == checkpoint['checkpoint_id'], 'profile_restore_mismatch')
    return restored


def export_review_candidate(source: Path, destination: Path) -> dict:
    """Create private review material, preserving degraded states and all clocks."""
    original = _private_path(source)
    checkpoint = verify_checkpoint(original)
    candidate = {
        'schema_version': 1, 'purpose': 'private_park_profile_review_candidate',
        'checkpoint_id': checkpoint['checkpoint_id'], 'checkpoint': checkpoint,
        'source_rights_status': 'not_checked', 'approval_performed': False,
        'publication_performed': False, 'site_data_written': False,
    }
    _encoded(candidate)  # Envelope overhead must fit before creating any output lock.
    with _writer(destination, original) as output:
        _install(output, candidate)
    return candidate
