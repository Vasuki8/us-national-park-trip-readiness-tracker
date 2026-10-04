"""Exact public activity projection and text-rights contracts; no approval/writes.

The complete normalized record is the review scope. Provider provenance, credit,
hashes and machine-valid metadata do not establish text rights or human review.
"""
from __future__ import annotations

import copy
import os
import stat
from pathlib import Path

from .activity_checkpoints import (MAX_CHECKPOINT_BYTES, ActivityCheckpointError,
                                   validate_checkpoint)
from .entry_review_io import ReviewStoreError, parse_json
from .history_model import HistoryError, canonical, digest, instant
from .park_activities import PILOT_CODES, ActivityError, validate_activities

MAX_PUBLIC_BYTES = MAX_CHECKPOINT_BYTES
MAX_RIGHTS_BYTES = MAX_CHECKPOINT_BYTES
PUBLIC_FILES = ('data/park-activities.json', 'data/activity-source-rights.json')
POLICY = {
    'ownership_url': 'https://www.nps.gov/aboutus/disclaimer.htm',
    'marks_url': 'https://www.nps.gov/subjects/partnerships/arrowhead-requests.htm?fullweb=1',
    'commercial_notice': 'No protection is claimed in original U.S. Government works.',
    'third_party_material_allowed': False, 'nps_marks_allowed': False,
    'raw_private_captures_public': False,
}
RIGHTS_FIELDS = {'park_code', 'activity_id', 'source_url', 'content_hash', 'classification',
                'use_scope', 'third_party_material_reproduced', 'nps_marks_reproduced', 'media_reproduced'}


class ActivityPublicError(ValueError):
    """Static refusal codes only, without source strings or private paths."""


def _require(condition: object, code='invalid_public_activities') -> None:
    if not condition:
        raise ActivityPublicError(code)


def canonical_activity_json(value: object, *, max_bytes: int = MAX_PUBLIC_BYTES) -> bytes:
    """Preserve canonical UTF-8/hash bytes with an explicit activity limit."""
    _require(type(max_bytes) is int and max_bytes > 0, 'invalid_activity_public_limit')
    try:
        return canonical(value, max_bytes=max_bytes)
    except HistoryError as error:
        raise ActivityPublicError('activity_public_too_large' if str(error) == 'object_too_large'
                                  else 'invalid_activity_public_encoding') from None


def activity_digest(value: object, *, max_bytes: int = MAX_PUBLIC_BYTES) -> str:
    _require(type(max_bytes) is int and max_bytes > 0, 'invalid_activity_public_limit')
    try:
        return digest(value, max_bytes=max_bytes)
    except HistoryError as error:
        raise ActivityPublicError('activity_public_too_large' if str(error) == 'object_too_large'
                                  else 'invalid_activity_public_encoding') from None


def parse_activity_json(raw: bytes, *, max_bytes: int) -> object:
    """Strict bounded JSON without inheriting a legacy 8/10 MiB ceiling."""
    _require(type(max_bytes) is int and max_bytes > 0, 'invalid_activity_public_limit')
    _require(isinstance(raw, bytes) and 0 < len(raw) <= max_bytes, 'activity_public_too_large')
    try:
        value = parse_json(raw)
    except ReviewStoreError:
        raise ActivityPublicError('invalid_activity_public_encoding') from None
    # Refuse numeric exponent overflow, invalid Unicode and excessive nesting
    # throughout the parsed object, including fields later refused by schemas.
    canonical_activity_json(value, max_bytes=max_bytes)
    return value


def _clock(value: object):
    try:
        return instant(value)
    except HistoryError:
        raise ActivityPublicError('invalid_activity_public_clock') from None


def validate_public_activities(value: dict) -> dict:
    """Validate all-five retained successful evidence, including empty feeds."""
    _require(type(value) is dict and set(value) == {'schema_version', 'purpose', 'inventories'})
    _require(type(value['schema_version']) is int and value['schema_version'] == 1
             and value['purpose'] == 'public_park_activities')
    rows = value['inventories']
    _require(type(rows) is list and len(rows) == len(PILOT_CODES), 'invalid_public_activity_scope')
    for code, row in zip(PILOT_CODES, rows):
        try:
            checked = validate_activities(row)
        except ActivityError:
            raise ActivityPublicError('invalid_public_activity_inventory') from None
        _require(checked['park_code'] == code and checked['last_successful_fetch_at'] is not None
                 and checked['last_checked_at'] == rows[0]['last_checked_at'], 'invalid_public_activity_scope')
    canonical_activity_json(value, max_bytes=MAX_PUBLIC_BYTES)
    return copy.deepcopy(value)


def project_checkpoint(value: dict) -> dict:
    try:
        checkpoint = validate_checkpoint(value)
    except ActivityCheckpointError:
        raise ActivityPublicError('invalid_activity_public_checkpoint') from None
    return validate_public_activities({'schema_version': 1, 'purpose': 'public_park_activities',
                                       'inventories': checkpoint['inventories']})


def validate_activity_rights(value: dict, dataset: dict) -> dict:
    """Check exact asserted review bindings; never infer a licence or review."""
    inventories = validate_public_activities(dataset)['inventories']
    _require(type(value) is dict and set(value) == {
        'schema_version', 'purpose', 'reviewed_at', 'review_method', 'policy', 'records'},
        'invalid_activity_rights')
    _require(type(value['schema_version']) is int and value['schema_version'] == 1
             and value['purpose'] == 'public_park_activity_text_rights'
             and value['review_method'] == 'official_nps_policy_and_exact_activity_review', 'invalid_activity_rights')
    reviewed = _clock(value['reviewed_at'])
    policy = value['policy']
    _require(type(policy) is dict and set(policy) == set(POLICY)
             and all(type(policy[key]) is type(expected) and policy[key] == expected
                     for key, expected in POLICY.items()), 'invalid_activity_rights_policy')
    records = value['records']
    _require(type(records) is list and len(records) == sum(len(s['records']) for s in inventories),
             'invalid_activity_rights_scope')
    offset = 0
    for snapshot in inventories:
        _require(reviewed >= _clock(snapshot['last_checked_at']), 'activity_rights_review_predates_collection')
        for record in snapshot['records']:
            row = records[offset]
            offset += 1
            _require(type(row) is dict and set(row) == RIGHTS_FIELDS, 'invalid_activity_rights_scope')
            expected = {'park_code': snapshot['park_code'], 'activity_id': record['id'],
                        'source_url': snapshot['source_url'], 'content_hash': record['content_hash'],
                        'classification': 'nps_government_text', 'use_scope': 'normalized_activity_text_and_metadata',
                        'third_party_material_reproduced': False, 'nps_marks_reproduced': False,
                        'media_reproduced': False}
            _require(all(type(row[key]) is type(item) and row[key] == item for key, item in expected.items()),
                     'activity_rights_binding_mismatch')
    canonical_activity_json(value, max_bytes=MAX_RIGHTS_BYTES)
    return copy.deepcopy(value)


def _public_bytes(path: Path, limit: int) -> bytes | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    _require(stat.S_ISREG(info.st_mode) and 0 < info.st_size <= limit, 'invalid_activity_public_base')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, 'rb') as stream:
        actual = os.fstat(stream.fileno())
        _require(stat.S_ISREG(actual.st_mode) and (actual.st_dev, actual.st_ino) == (info.st_dev, info.st_ino),
                 'activity_public_input_changed')
        raw = stream.read(limit+1)
    _require(0 < len(raw) <= limit, 'invalid_activity_public_base')
    return raw


def read_public_activity_pair(root: Path) -> dict:
    """Read the fixed public pair, preserving exact base bytes for patch CAS.

    Return current bytes plus validated dataset/rights; both absent is optional.
    Public inputs use ordinary file guards, not private ownership permissions.
    """
    try:
        root = Path(root).absolute()
        folder = root/'data'
        for ancestor in (folder, *folder.parents):
            _require(not ancestor.is_symlink(), 'invalid_activity_public_base')
        _require(stat.S_ISDIR(root.lstat().st_mode), 'invalid_activity_public_base')
        if folder.exists():
            _require(stat.S_ISDIR(folder.lstat().st_mode), 'invalid_activity_public_base')
        limits = (MAX_PUBLIC_BYTES, MAX_RIGHTS_BYTES)
        current = {name: _public_bytes(root/name, limit+1) for name, limit in zip(PUBLIC_FILES, limits)}
        present = [current[name] is not None for name in PUBLIC_FILES]
        _require(present[0] == present[1], 'activity_public_pair_incomplete')
        if not present[0]:
            return {'current': current, 'dataset': None, 'rights': None}
        values = []
        for name, limit in zip(PUBLIC_FILES, limits):
            raw = current[name]
            value = parse_activity_json(raw, max_bytes=limit+1)
            encoded = canonical_activity_json(value, max_bytes=limit)
            _require(raw in (encoded, encoded+b'\n'), 'invalid_activity_public_base')
            values.append(value)
        dataset = validate_public_activities(values[0])
        rights = validate_activity_rights(values[1], dataset)
        return {'current': current, 'dataset': dataset, 'rights': rights}
    except OSError:
        raise ActivityPublicError('invalid_activity_public_base') from None
