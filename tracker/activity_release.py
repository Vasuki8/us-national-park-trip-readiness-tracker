"""Offline exact activity text review, immutable recovery and paired patches.

Explicit approval records an operator decision. Integrity hashes do not prove
source authenticity, text rights, human review or an off-host backup. Commands
never request sources, apply patches, write public data or deploy.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .activity_checkpoints import (MAX_CHECKPOINT_BYTES, ActivityCheckpointError,
                                   verify_checkpoint)
from .activity_public import (MAX_PUBLIC_BYTES, MAX_RIGHTS_BYTES, PUBLIC_FILES,
                              ActivityPublicError, activity_digest,
                              canonical_activity_json, parse_activity_json,
                              project_checkpoint, read_public_activity_pair,
                              validate_activity_rights, validate_public_activities)
from .entry_review_io import REPO_ROOT, ReviewStoreError, private_stat, read_private_json
from .history_model import HistoryError, instant
from .park_activities import PILOT_CODES
from .private_checkpoint_io import (install_private_bytes, locked_private_output,
                                    private_checkpoint_path)

MAX_BUNDLE_BYTES = MAX_CHECKPOINT_BYTES + MAX_PUBLIC_BYTES + MAX_RIGHTS_BYTES + 65536
MAX_PATCH_BYTES = 2 * (MAX_PUBLIC_BYTES + MAX_RIGHTS_BYTES + 2) + 65536


class ActivityReleaseError(ValueError):
    """Fixed machine refusal codes, without paths, source strings or arguments."""


def _require(condition: object, code='invalid_activity_release') -> None:
    if not condition:
        raise ActivityReleaseError(code)


def _encoded(value: object, *, max_bytes: int) -> bytes:
    try:
        return canonical_activity_json(value, max_bytes=max_bytes)
    except ActivityPublicError:
        raise ActivityReleaseError('invalid_activity_release_encoding_or_size') from None


def _digest(value: object, *, max_bytes: int) -> str:
    try:
        return activity_digest(value, max_bytes=max_bytes)
    except ActivityPublicError:
        raise ActivityReleaseError('invalid_activity_release_encoding_or_size') from None


def _clock(value: object):
    try:
        return instant(value)
    except HistoryError:
        raise ActivityReleaseError('invalid_activity_release_clock') from None


def build_release_bundle(checkpoint: dict, rights: dict, approved_at: str, *,
                         dispositions: dict | None = None) -> dict:
    """Bind an asserted decision to every retained field, clock and rights row."""
    try:
        if dispositions is not None:
            from .activity_catalog import validate_dispositions
            dispositions = validate_dispositions(dispositions, checkpoint)
        public = (project_checkpoint(checkpoint) if dispositions is None else
                  project_checkpoint(checkpoint, dispositions=dispositions))
        rights = validate_activity_rights(rights, public)
    except ActivityPublicError:
        raise ActivityReleaseError('invalid_activity_release_evidence') from None
    approval = {'decision': 'approved', 'approved_at': approved_at,
                'checkpoint_id': checkpoint['checkpoint_id'],
                'projection_hash': _digest(public, max_bytes=MAX_PUBLIC_BYTES),
                'rights_hash': _digest(rights, max_bytes=MAX_RIGHTS_BYTES)}
    core = {'schema_version': 1 if dispositions is None else 2, 'purpose': 'private_reviewed_park_activities',
            'checkpoint': copy.deepcopy(checkpoint), 'public_activities': public,
            'rights': rights, 'approval': approval}
    if dispositions is not None:
        core['dispositions'] = dispositions
        approval['dispositions_hash'] = _digest(dispositions, max_bytes=MAX_PUBLIC_BYTES)
    return validate_release_bundle({**core, 'bundle_id': _digest(core, max_bytes=MAX_BUNDLE_BYTES)})


def validate_release_bundle(value: dict) -> dict:
    """Verify a complete self-contained bundle offline; return a detached copy."""
    _require(type(value) is dict)
    version = value.get('schema_version')
    _require(type(version) is int and version in (1, 2))
    _require(set(value) == {
        'schema_version', 'purpose', 'checkpoint', 'public_activities', 'rights', 'approval', 'bundle_id'}
        | ({'dispositions'} if version == 2 else set()))
    _require(value['purpose'] == 'private_reviewed_park_activities')
    try:
        if version == 2:
            from .activity_catalog import validate_dispositions
            dispositions = validate_dispositions(value['dispositions'], value['checkpoint'])
            projection = project_checkpoint(value['checkpoint'], dispositions=dispositions)
        else:
            projection = project_checkpoint(value['checkpoint'])
        public = validate_public_activities(value['public_activities'])
        rights = validate_activity_rights(value['rights'], public)
    except ActivityPublicError:
        raise ActivityReleaseError('invalid_activity_release_evidence') from None
    _require(public['schema_version'] == version and rights['schema_version'] == version,
             'activity_release_version_mismatch')
    _require(_encoded(projection, max_bytes=MAX_PUBLIC_BYTES) ==
             _encoded(public, max_bytes=MAX_PUBLIC_BYTES), 'activity_projection_mismatch')
    approval = value['approval']
    _require(type(approval) is dict and set(approval) == {
        'decision', 'approved_at', 'checkpoint_id', 'projection_hash', 'rights_hash'}
        | ({'dispositions_hash'} if version == 2 else set()))
    _require(approval['decision'] == 'approved'
             and approval['checkpoint_id'] == value['checkpoint']['checkpoint_id']
             and approval['projection_hash'] == _digest(public, max_bytes=MAX_PUBLIC_BYTES)
             and approval['rights_hash'] == _digest(rights, max_bytes=MAX_RIGHTS_BYTES),
             'activity_approval_binding_mismatch')
    if version == 2:
        _require(approval['dispositions_hash'] == _digest(dispositions, max_bytes=MAX_PUBLIC_BYTES),
                 'activity_approval_binding_mismatch')
        _require(_clock(rights['reviewed_at']) >= _clock(dispositions['reviewed_at']),
                 'activity_rights_review_predates_dispositions')
    _require(_clock(approval['approved_at']) >= _clock(rights['reviewed_at']),
             'activity_approval_predates_review')
    _encoded(value, max_bytes=MAX_BUNDLE_BYTES)
    _require(value['bundle_id'] == _digest({k: v for k, v in value.items() if k != 'bundle_id'},
                                         max_bytes=MAX_BUNDLE_BYTES), 'activity_release_hash_mismatch')
    return copy.deepcopy(value)


def _private_path(path: Path) -> Path:
    try:
        return private_checkpoint_path(path)
    except (ReviewStoreError, OSError):
        raise ActivityReleaseError('activity_release_private_storage_refused') from None


def _read_private(path: Path, *, max_bytes: int) -> object:
    source = _private_path(path)
    try:
        return read_private_json(source, max_bytes=max_bytes)
    except (ReviewStoreError, OSError):
        raise ActivityReleaseError('activity_release_input_unreadable') from None


def verify_release_bundle(path: Path) -> dict:
    """Verify integrity only; never read a credential, parent or remote copy."""
    return validate_release_bundle(_read_private(path, max_bytes=MAX_BUNDLE_BYTES))


def _protect_inputs(destination: Path, *sources: Path) -> None:
    # Check both names before invoking the writer: a review/checkpoint input may
    # itself be named like the destination lock. That input must never be unlinked.
    output = _private_path(destination)
    lock = _private_path(Path(str(output) + '.lock'))
    _require(all(source not in (output, lock) for source in sources), 'overlapping_activity_release_paths')


def _install(destination: Path, source: Path, data: bytes, *, max_bytes: int) -> Path:
    try:
        with locked_private_output(destination, source) as output:
            install_private_bytes(output, data, max_bytes=max_bytes)
    except (ReviewStoreError, OSError):
        # Installation is the commit point. A later cleanup/sync error can leave
        # completed output; the neutral installer preserves that evidence.
        raise ActivityReleaseError('activity_release_private_storage_refused') from None
    return output


def create_release_bundle(checkpoint: Path, rights: Path, destination: Path,
                          approved_at: str, *, approve=False, dispositions: Path | None = None) -> dict:
    """Record only an explicit approval, without overwrite or private-input loss."""
    _require(approve is True, 'activity_approval_confirmation_required')
    source, rights_source = _private_path(checkpoint), _private_path(rights)
    disposition_source = None if dispositions is None else _private_path(dispositions)
    try:
        retained = verify_checkpoint(source)
    except ActivityCheckpointError:
        raise ActivityReleaseError('invalid_activity_release_checkpoint') from None
    plan = None if disposition_source is None else _read_private(disposition_source, max_bytes=MAX_PUBLIC_BYTES)
    # A supplied file selects the catalog contract. JSON null cannot turn that
    # explicit input into an absent plan and silently restore v1 review scope.
    _require(disposition_source is None or type(plan) is dict, 'invalid_activity_release_evidence')
    bundle = build_release_bundle(retained, _read_private(rights_source, max_bytes=MAX_RIGHTS_BYTES),
                                  approved_at, dispositions=plan)
    data = _encoded(bundle, max_bytes=MAX_BUNDLE_BYTES)  # Refuse before locks or temporary files.
    _protect_inputs(destination, source, rights_source,
                    *((disposition_source,) if disposition_source is not None else ()))
    _install(destination, source, data, max_bytes=MAX_BUNDLE_BYTES)
    return bundle


def restore_release_bundle(source: Path, destination: Path) -> dict:
    """Restore a fresh canonical copy and reverify without changing source clocks."""
    original = _private_path(source)
    bundle = verify_release_bundle(original)
    data = _encoded(bundle, max_bytes=MAX_BUNDLE_BYTES)
    _protect_inputs(destination, original)
    output = _install(destination, original, data, max_bytes=MAX_BUNDLE_BYTES)
    restored = verify_release_bundle(output)
    _require(restored['bundle_id'] == bundle['bundle_id'], 'activity_release_restore_mismatch')
    return restored


def _source_inventory(inventory: dict) -> dict:
    """Comparable original source metadata, independent of the public view."""
    result = {key: value for key, value in inventory.items()
              if key not in ('schema_version', 'records', 'source_records')}
    records = inventory['source_records'] if inventory['schema_version'] == 2 else inventory['records']
    result['records'] = [{key: record[key] for key in (
        'id', 'content_hash', 'hash_scope', 'observed_first_at', 'observed_changed_at')}
        for record in records]
    return result


def _advance(old: dict, new: dict) -> None:
    """Refuse unsupported public evidence replacement, including private forks."""
    for before, after in zip(old['inventories'], new['inventories']):
        # Preserve v1 strict snapshot comparison. With either catalog version,
        # original evidence carries the guards; editorial choices renew no age.
        if old['schema_version'] == 2 or new['schema_version'] == 2:
            before, after = _source_inventory(before), _source_inventory(after)
        _require(_clock(after['last_checked_at']) >= _clock(before['last_checked_at']),
                 'activity_promotion_clock_rewind')
        if _clock(after['last_checked_at']) == _clock(before['last_checked_at']):
            _require(_encoded(after, max_bytes=MAX_PUBLIC_BYTES) == _encoded(before, max_bytes=MAX_PUBLIC_BYTES),
                     'activity_promotion_same_clock_change')
        successful = _clock(before['last_successful_fetch_at'])
        _require(_clock(after['last_successful_fetch_at']) >= successful, 'activity_promotion_clock_rewind')
        if after['collection_status'] != 'success':
            _require(after['last_successful_fetch_at'] == before['last_successful_fetch_at']
                     and _encoded(after['records'], max_bytes=MAX_PUBLIC_BYTES) ==
                     _encoded(before['records'], max_bytes=MAX_PUBLIC_BYTES),
                     'activity_promotion_degraded_evidence_changed')
            continue
        previous = {record['id']: record for record in before['records']}
        _require(len(after['records']) * 2 >= len(previous), 'activity_promotion_inventory_drop_requires_review')
        for record in after['records']:
            retained = previous.get(record['id'])
            if retained is None:
                _require(_clock(record['observed_first_at']) > successful,
                         'activity_promotion_conflicting_observation')
                continue
            _require(record['observed_first_at'] == retained['observed_first_at']
                     and _clock(record['observed_changed_at']) >= _clock(retained['observed_changed_at']),
                     'activity_promotion_observation_rewind')
            if record['content_hash'] == retained['content_hash']:
                _require(record['observed_changed_at'] == retained['observed_changed_at'],
                         'activity_promotion_unchanged_clock_changed')
            else:
                _require(_clock(record['observed_changed_at']) > successful,
                         'activity_promotion_conflicting_observation')


def _hunk(path: str, before: bytes | None, after: bytes) -> bytes:
    def lines(data: bytes, prefix: bytes):
        parts = data.split(b'\n')
        if parts[-1] == b'':
            parts.pop()
        result = b''.join(prefix + line + b'\n' for line in parts)
        if data and not data.endswith(b'\n'):
            result += b'\\ No newline at end of file\n'
        return len(parts), result
    old_count, old_lines = (0, b'') if before is None else lines(before, b'-')
    new_count, new_lines = lines(after, b'+')
    header = f'diff --git a/{path} b/{path}\n'
    if before is None:
        header += 'new file mode 100644\n'
    header += f'--- {"/dev/null" if before is None else "a/"+path}\n+++ b/{path}\n'
    header += f'@@ -{0 if before is None else 1},{old_count} +1,{new_count} @@\n'
    return header.encode('ascii') + old_lines + new_lines


def _validate_base(current: dict[str, bytes | None]) -> dict | None:
    _require(type(current) is dict and set(current) == set(PUBLIC_FILES), 'invalid_activity_public_base')
    _require((current[PUBLIC_FILES[0]] is None) == (current[PUBLIC_FILES[1]] is None),
             'activity_public_pair_incomplete')
    if current[PUBLIC_FILES[0]] is None:
        return None
    values = []
    for name, limit in zip(PUBLIC_FILES, (MAX_PUBLIC_BYTES, MAX_RIGHTS_BYTES)):
        raw = current[name]
        _require(isinstance(raw, bytes) and 0 < len(raw) <= limit + 1, 'invalid_activity_public_base')
        try:
            value = parse_activity_json(raw, max_bytes=limit + 1)
            canonical = canonical_activity_json(value, max_bytes=limit)
        except ActivityPublicError:
            raise ActivityReleaseError('invalid_activity_public_base') from None
        _require(raw in (canonical, canonical + b'\n'), 'invalid_activity_public_base')
        values.append(value)
    try:
        previous = validate_public_activities(values[0])
        validate_activity_rights(values[1], previous)
    except ActivityPublicError:
        raise ActivityReleaseError('invalid_activity_public_base') from None
    return previous


def build_promotion(bundle: dict, current: dict[str, bytes | None]) -> dict:
    """Prepare the exact paired Git patch, binding bundle and raw public bases."""
    reviewed = validate_release_bundle(bundle)
    previous = _validate_base(current)
    if previous is not None:
        _advance(previous, reviewed['public_activities'])
    after = (_encoded(reviewed['public_activities'], max_bytes=MAX_PUBLIC_BYTES) + b'\n',
             _encoded(reviewed['rights'], max_bytes=MAX_RIGHTS_BYTES) + b'\n')
    patch_bytes = b''.join(_hunk(name, current[name], data) for name, data in zip(PUBLIC_FILES, after))
    _require(len(patch_bytes) <= MAX_PATCH_BYTES, 'activity_promotion_patch_too_large')
    bases = {name: None if current[name] is None else hashlib.sha256(current[name]).hexdigest()
             for name in PUBLIC_FILES}
    core = {'schema_version': 1, 'purpose': 'reviewed_activity_promotion',
            'bundle_id': reviewed['bundle_id'], 'base_hashes': bases,
            'patch_hash': hashlib.sha256(patch_bytes).hexdigest()}
    return {'patch': patch_bytes, 'receipt': {**core, 'candidate_id': _digest(core, max_bytes=MAX_BUNDLE_BYTES)}}


def _public_base(root: Path) -> dict:
    try:
        return read_public_activity_pair(root)['current']
    except ActivityPublicError:
        raise ActivityReleaseError('invalid_activity_public_base') from None


def prepare_promotion(bundle: Path, destination: Path, *, root: Path = REPO_ROOT) -> dict:
    """Write only a fresh private patch; never apply it or touch public data."""
    source = _private_path(bundle)
    candidate = build_promotion(verify_release_bundle(source), _public_base(root))
    _protect_inputs(destination, source)
    _install(destination, source, candidate['patch'], max_bytes=MAX_PATCH_BYTES)
    return candidate['receipt']


def _read_patch(path: Path) -> bytes:
    source = _private_path(path)
    try:
        original = private_stat(source)
        _require(0 < original.st_size <= MAX_PATCH_BYTES, 'invalid_activity_promotion_patch')
        fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            actual = os.fstat(stream.fileno())
            _require((actual.st_dev, actual.st_ino) == (original.st_dev, original.st_ino),
                     'activity_promotion_patch_changed')
            data = stream.read(MAX_PATCH_BYTES + 1)
        _require(0 < len(data) <= MAX_PATCH_BYTES, 'invalid_activity_promotion_patch')
        return data
    except (ReviewStoreError, OSError):
        raise ActivityReleaseError('activity_promotion_patch_unreadable') from None


def check_promotion(bundle: Path, patch: Path, candidate_id: str, *, root: Path = REPO_ROOT) -> dict:
    """Regenerate and compare exact current inputs without any writes."""
    candidate = build_promotion(verify_release_bundle(bundle), _public_base(root))
    _require(candidate['receipt']['candidate_id'] == candidate_id, 'activity_promotion_candidate_changed')
    _require(candidate['patch'] == _read_patch(patch), 'activity_promotion_patch_changed')
    return candidate['receipt']


class _Parser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('allow_abbrev', False)
        super().__init__(*args, **kwargs)

    def error(self, _message):
        raise ActivityReleaseError('invalid_activity_release_arguments')


def _parser():
    parser = _Parser(prog='python -m tracker.activity_release', description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    approve = commands.add_parser('approve')
    approve.add_argument('--checkpoint', type=Path, required=True)
    approve.add_argument('--rights', type=Path, required=True)
    approve.add_argument('--dispositions', type=Path)
    approve.add_argument('--output', type=Path, required=True)
    approve.add_argument('--approve', action='store_true')
    verify = commands.add_parser('verify')
    verify.add_argument('--bundle', type=Path, required=True)
    for name in ('restore', 'prepare-promotion'):
        operation = commands.add_parser(name)
        operation.add_argument('--bundle', type=Path, required=True)
        operation.add_argument('--output', type=Path, required=True)
    check = commands.add_parser('check-promotion')
    check.add_argument('--bundle', type=Path, required=True)
    check.add_argument('--patch', type=Path, required=True)
    check.add_argument('--candidate-id', required=True)
    return parser


def main(argv=None) -> int:
    report = {'schema_version': 1, 'network_attempted': False, 'approval_performed': False,
              'publication_performed': False, 'site_data_written': False}
    try:
        args = _parser().parse_args(argv)
        if args.command == 'approve':
            now = datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')
            bundle = create_release_bundle(args.checkpoint, args.rights, args.output, now,
                                           approve=args.approve, dispositions=args.dispositions)
            report.update(operation='approval_recorded', bundle_id=bundle['bundle_id'], approval_performed=True)
        elif args.command in ('verify', 'restore'):
            bundle = verify_release_bundle(args.bundle) if args.command == 'verify' else \
                restore_release_bundle(args.bundle, args.output)
            report.update(operation=args.command, bundle_id=bundle['bundle_id'], park_count=len(PILOT_CODES))
        else:
            receipt = prepare_promotion(args.bundle, args.output) if args.command == 'prepare-promotion' else \
                check_promotion(args.bundle, args.patch, args.candidate_id)
            report.update(operation=args.command, **receipt)
        status = 0
    except (Exception, KeyboardInterrupt) as error:
        # Never echo exception text or dependency details, even for programmer errors.
        report.update(operation='refused', error_code='activity_release_interrupted'
                      if isinstance(error, KeyboardInterrupt) else 'activity_release_refused')
        status = 2
    print(json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False))
    return status


if __name__ == '__main__':
    raise SystemExit(main())
