"""Explicit immutable private activity batches, never a public writer or head.

Hashes establish self-contained integrity. A parent ID references lineage only;
verification does not replay parent history or approve sources, rights or backup.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Callable

from .entry_review_io import ReviewStoreError, read_private_json
from .history_model import HistoryError, canonical, digest, instant
from .park_activities import (PILOT_CODES, ActivityError, collect_activities,
                              initial_activities, preflight_activity_attempt,
                              validate_activities)
from .private_checkpoint_io import (install_private_bytes, locked_private_output,
                                    private_checkpoint_path)

CHECKPOINT_FIELDS = {'schema_version', 'purpose', 'parent_checkpoint_id',
                     'checked_at', 'inventories', 'checkpoint_id'}
MAX_CHECKPOINT_BYTES = len(PILOT_CODES) * 8 * 1024 * 1024 + 64 * 1024
MAX_REVIEW_BYTES = MAX_CHECKPOINT_BYTES + 4096


class ActivityCheckpointError(ValueError):
    """Static machine codes only; never source, path or exception text."""


def _require(condition: object, code: str) -> None:
    if not condition:
        raise ActivityCheckpointError(code)


def _encoded(value: object, *, max_bytes: int) -> bytes:
    try:
        return canonical(value, max_bytes=max_bytes)
    except HistoryError as error:
        code = 'activity_checkpoint_too_large' if str(error) == 'object_too_large' \
            else 'invalid_activity_checkpoint'
        raise ActivityCheckpointError(code) from None


def _digest(value: object) -> str:
    try:
        return digest(value, max_bytes=MAX_CHECKPOINT_BYTES)
    except HistoryError as error:
        code = 'activity_checkpoint_too_large' if str(error) == 'object_too_large' \
            else 'invalid_activity_checkpoint'
        raise ActivityCheckpointError(code) from None


def _clock(value: object):
    try:
        return instant(value)
    except HistoryError:
        raise ActivityCheckpointError('invalid_activity_checkpoint_clock') from None


def validate_checkpoint(value: dict) -> dict:
    """Validate complete bounded all-five state and return a defensive copy."""
    _require(isinstance(value, dict) and set(value) == CHECKPOINT_FIELDS,
             'invalid_activity_checkpoint')
    _require(type(value['schema_version']) is int and value['schema_version'] == 1
             and value['purpose'] == 'private_park_activity_checkpoint',
             'invalid_activity_checkpoint')
    _require(isinstance(value['checkpoint_id'], str)
             and re.fullmatch('[a-f0-9]{64}', value['checkpoint_id']),
             'activity_checkpoint_hash_mismatch')
    parent = value['parent_checkpoint_id']
    _require(parent is None or isinstance(parent, str) and re.fullmatch('[a-f0-9]{64}', parent)
             and parent != value['checkpoint_id'], 'invalid_activity_checkpoint_parent')
    _clock(value['checked_at'])
    inventories = value['inventories']
    _require(isinstance(inventories, list) and len(inventories) == len(PILOT_CODES),
             'invalid_activity_checkpoint_scope')
    for code, inventory in zip(PILOT_CODES, inventories):
        try:
            checked = validate_activities(inventory)
        except ActivityError:
            raise ActivityCheckpointError('invalid_activity_checkpoint') from None
        _require(checked['park_code'] == code and checked['collection_status'] != 'never_checked'
                 and checked['last_checked_at'] == value['checked_at'],
                 'invalid_activity_checkpoint_scope')
    _encoded(value, max_bytes=MAX_CHECKPOINT_BYTES)
    core = {key: item for key, item in value.items() if key != 'checkpoint_id'}
    _require(value['checkpoint_id'] == _digest(core), 'activity_checkpoint_hash_mismatch')
    return copy.deepcopy(value)


def _storage_error(error: ReviewStoreError) -> ActivityCheckpointError:
    code = {
        'overlapping_private_checkpoint_paths': 'overlapping_activity_paths',
        'private_checkpoint_destination_exists': 'activity_destination_exists',
        'private_checkpoint_output_locked': 'activity_output_locked',
        'private_checkpoint_too_large': 'activity_checkpoint_too_large',
    }.get(str(error), 'activity_private_storage_refused')
    return ActivityCheckpointError(code)


def _private_path(value: Path) -> Path:
    try:
        return private_checkpoint_path(value)
    except ReviewStoreError as error:
        raise _storage_error(error) from None
    except OSError:
        raise ActivityCheckpointError('activity_private_storage_refused') from None


def verify_checkpoint(path: Path) -> dict:
    """Read and verify offline; neither credentials nor parents are consulted."""
    source = _private_path(path)
    try:
        value = read_private_json(source, max_bytes=MAX_CHECKPOINT_BYTES)
    except (ReviewStoreError, OSError):
        raise ActivityCheckpointError('activity_checkpoint_unreadable') from None
    return validate_checkpoint(value)


def _core(inventories: list[dict], now: str, parent: str | None) -> dict:
    return {'schema_version': 1, 'purpose': 'private_park_activity_checkpoint',
            'parent_checkpoint_id': parent, 'checked_at': now, 'inventories': inventories}


def _preflight_baselines(previous: dict | None, now: str) -> list[dict]:
    baselines = []
    for index, code in enumerate(PILOT_CODES):
        baseline = initial_activities(code) if previous is None else previous['inventories'][index]
        try:
            baselines.append(preflight_activity_attempt(code, baseline, now))
        except ActivityError:
            raise ActivityCheckpointError('activity_attempt_refused') from None
    # Reserve complete failure evidence as a batch before any callback or lock.
    fallback = []
    for baseline in baselines:
        attempts = [{**baseline, 'last_checked_at': now, 'collection_status': status,
                     'coverage_status': 'incomplete', 'error_code': error}
                    for status, error in (('failed', 'provider_request_failed'),
                                          ('quarantined', 'response_requires_review'))]
        fallback.append(max(attempts, key=lambda item: len(
            _encoded(item, max_bytes=MAX_CHECKPOINT_BYTES))))
    core = _core(fallback, now, None if previous is None else previous['checkpoint_id'])
    _encoded({**core, 'checkpoint_id': '0' * 64}, max_bytes=MAX_CHECKPOINT_BYTES)
    return baselines


def collect_checkpoint(destination: Path, previous_path: Path | None, now: str,
                       fetch_for: Callable[[str], Callable[[int], dict]]) -> dict:
    """Preflight every park, then retain one complete immutable attempt batch.

    Factory callbacks run only inside the validated exclusive output lock.
    All accepted baselines are isolated before the first callback. Different
    destinations can branch from one parent; there is no global latest pointer.
    """
    current = _clock(now)
    source = None if previous_path is None else _private_path(previous_path)
    previous = None if source is None else verify_checkpoint(source)
    if previous is not None:
        _require(current > _clock(previous['checked_at']), 'activity_collection_clock_not_advanced')
    _require(callable(fetch_for), 'invalid_activity_transport')
    baselines = _preflight_baselines(previous, now)
    try:
        with locked_private_output(destination, source) as output:
            inventories = [collect_activities(code, baseline, now, fetch_for(code))
                           for code, baseline in zip(PILOT_CODES, baselines)]
            core = _core(inventories, now, None if previous is None else previous['checkpoint_id'])
            checkpoint = validate_checkpoint({**core, 'checkpoint_id': _digest(core)})
            install_private_bytes(output, _encoded(checkpoint, max_bytes=MAX_CHECKPOINT_BYTES),
                                  max_bytes=MAX_CHECKPOINT_BYTES)
    except ReviewStoreError as error:
        raise _storage_error(error) from None
    return checkpoint


def restore_checkpoint(source: Path, destination: Path) -> dict:
    """Verify and restore to a fresh canonical private file without new clocks."""
    original = _private_path(source)
    checkpoint = verify_checkpoint(original)
    try:
        with locked_private_output(destination, original) as output:
            install_private_bytes(output, _encoded(checkpoint, max_bytes=MAX_CHECKPOINT_BYTES),
                                  max_bytes=MAX_CHECKPOINT_BYTES)
    except ReviewStoreError as error:
        raise _storage_error(error) from None
    restored = verify_checkpoint(output)
    _require(restored['checkpoint_id'] == checkpoint['checkpoint_id'], 'activity_restore_mismatch')
    return restored


def export_review_candidate(source: Path, destination: Path) -> dict:
    """Retain exact private review material; rights and approval remain unclaimed."""
    original = _private_path(source)
    checkpoint = verify_checkpoint(original)
    candidate = {
        'schema_version': 1, 'purpose': 'private_park_activity_review_candidate',
        'checkpoint_id': checkpoint['checkpoint_id'], 'checkpoint': checkpoint,
        'source_rights_status': 'not_checked', 'approval_performed': False,
        'publication_performed': False, 'site_data_written': False,
    }
    data = _encoded(candidate, max_bytes=MAX_REVIEW_BYTES)
    try:
        with locked_private_output(destination, original) as output:
            install_private_bytes(output, data, max_bytes=MAX_REVIEW_BYTES)
    except ReviewStoreError as error:
        raise _storage_error(error) from None
    return candidate
