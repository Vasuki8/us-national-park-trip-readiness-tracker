"""Offline exact text-review bindings and paired profile patch preparation.

These tools never request sources, apply patches, deploy or authenticate review
metadata. Explicit approval records an operator decision; hashes are integrity
bindings, not source authenticity, signatures or remote-backup evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .entry_review_io import MAX_INPUT_BYTES, REPO_ROOT, private_stat, read_private_json
from .history_model import HistoryError, canonical, digest, instant, parse_json
from .park_profiles import PILOT_CODES, ProfileError, validate_profile
from .profile_checkpoints import (ProfileCheckpointError, _install, _install_bytes,
                                  _output_path, _private_path, _writer,
                                  validate_checkpoint, verify_checkpoint)

MAX_RELEASE_BYTES = MAX_INPUT_BYTES
PUBLIC_FILES = ('data/park-profiles.json', 'data/profile-source-rights.json')
POLICY = {
    'ownership_url': 'https://www.nps.gov/aboutus/disclaimer.htm',
    'marks_url': 'https://www.nps.gov/subjects/partnerships/arrowhead-requests.htm?fullweb=1',
    'commercial_notice': 'No protection is claimed in original U.S. Government works.',
    'third_party_material_allowed': False, 'nps_marks_allowed': False,
    'raw_private_captures_public': False,
}
RIGHTS_FIELDS = {'park_code', 'profile_id', 'source_url', 'content_hash', 'classification',
                'use_scope', 'third_party_material_reproduced', 'nps_marks_reproduced', 'media_reproduced'}


class ProfileReleaseError(ValueError):
    """A fixed refusal code, without source text, arguments or private paths."""


def _require(condition: object, code='invalid_profile_release') -> None:
    if not condition:
        raise ProfileReleaseError(code)


def _bounded(value: object) -> bytes:
    try:
        data = canonical(value)
    except HistoryError:
        raise ProfileReleaseError('invalid_profile_release') from None
    _require(len(data) <= MAX_RELEASE_BYTES, 'profile_release_too_large')
    return data


def _clock(value: object):
    try:
        return instant(value)
    except HistoryError:
        raise ProfileReleaseError('invalid_profile_release_clock') from None


def validate_public_profiles(value: dict) -> dict:
    _require(type(value) is dict and set(value) == {'schema_version', 'purpose', 'profiles'})
    _require(type(value['schema_version']) is int and value['schema_version'] == 1
             and value['purpose'] == 'public_park_profiles')
    rows = value['profiles']
    _require(type(rows) is list and len(rows) == len(PILOT_CODES), 'invalid_public_profile_scope')
    for code, row in zip(PILOT_CODES, rows):
        try:
            current = validate_profile(row)
        except ProfileError:
            raise ProfileReleaseError('invalid_public_profile') from None
        _require(current['park_code'] == code and current['profile'] is not None
                 and current['last_checked_at'] == rows[0]['last_checked_at'],
                 'invalid_public_profile_scope')
    _bounded(value)
    return copy.deepcopy(value)


def project_checkpoint(value: dict) -> dict:
    try:
        checkpoint = validate_checkpoint(value)
    except ProfileCheckpointError:
        raise ProfileReleaseError('invalid_profile_checkpoint') from None
    return validate_public_profiles({'schema_version': 1, 'purpose': 'public_park_profiles',
                                     'profiles': checkpoint['profiles']})


def validate_profile_rights(value: dict, dataset: dict) -> dict:
    profiles = validate_public_profiles(dataset)['profiles']
    _require(type(value) is dict and set(value) == {
        'schema_version', 'purpose', 'reviewed_at', 'review_method', 'policy', 'records'})
    _require(type(value['schema_version']) is int and value['schema_version'] == 1
             and value['purpose'] == 'public_park_profile_text_rights'
             and value['review_method'] == 'official_nps_policy_and_exact_profile_review')
    reviewed = _clock(value['reviewed_at'])
    _require(type(value['policy']) is dict and set(value['policy']) == set(POLICY)
             and all(type(value['policy'][k]) is type(v) and value['policy'][k] == v
                     for k, v in POLICY.items()), 'invalid_profile_rights_policy')
    records = value['records']
    _require(type(records) is list and len(records) == len(profiles), 'invalid_profile_rights_scope')
    for row, snapshot in zip(records, profiles):
        _require(type(row) is dict and set(row) == RIGHTS_FIELDS, 'invalid_profile_rights_scope')
        profile = snapshot['profile']
        expected = {'park_code': snapshot['park_code'], 'profile_id': profile['id'],
                    'source_url': snapshot['source_url'], 'content_hash': profile['content_hash'],
                    'classification': 'nps_government_text',
                    'use_scope': 'normalized_profile_text_and_category_names',
                    'third_party_material_reproduced': False, 'nps_marks_reproduced': False,
                    'media_reproduced': False}
        _require(all(type(row[k]) is type(v) and row[k] == v for k, v in expected.items()),
                 'profile_rights_binding_mismatch')
        _require(reviewed >= _clock(snapshot['last_checked_at']), 'profile_rights_review_predates_collection')
    _bounded(value)
    return copy.deepcopy(value)


def build_release_bundle(checkpoint: dict, rights: dict, approved_at: str) -> dict:
    public = project_checkpoint(checkpoint)
    rights = validate_profile_rights(rights, public)
    approval = {'decision': 'approved', 'approved_at': approved_at,
                'checkpoint_id': checkpoint['checkpoint_id'], 'projection_hash': digest(public),
                'rights_hash': digest(rights)}
    core = {'schema_version': 1, 'purpose': 'private_reviewed_park_profiles',
            'checkpoint': copy.deepcopy(checkpoint), 'public_profiles': public,
            'rights': rights, 'approval': approval}
    return validate_release_bundle({**core, 'bundle_id': digest(core)})


def validate_release_bundle(value: dict) -> dict:
    _require(type(value) is dict and set(value) == {
        'schema_version', 'purpose', 'checkpoint', 'public_profiles', 'rights', 'approval', 'bundle_id'})
    _require(type(value['schema_version']) is int and value['schema_version'] == 1
             and value['purpose'] == 'private_reviewed_park_profiles')
    projection = project_checkpoint(value['checkpoint'])
    public = validate_public_profiles(value['public_profiles'])
    _require(canonical(projection) == canonical(public), 'profile_projection_mismatch')
    rights = validate_profile_rights(value['rights'], public)
    approval = value['approval']
    _require(type(approval) is dict and set(approval) == {
        'decision', 'approved_at', 'checkpoint_id', 'projection_hash', 'rights_hash'})
    _require(approval['decision'] == 'approved'
             and approval['checkpoint_id'] == value['checkpoint']['checkpoint_id']
             and approval['projection_hash'] == digest(public)
             and approval['rights_hash'] == digest(rights), 'profile_approval_binding_mismatch')
    _require(_clock(approval['approved_at']) >= _clock(rights['reviewed_at']),
             'profile_approval_predates_review')
    _bounded(value)
    _require(value['bundle_id'] == digest({k: v for k, v in value.items() if k != 'bundle_id'}),
             'profile_release_hash_mismatch')
    return copy.deepcopy(value)


def _read_private(path: Path) -> dict:
    return read_private_json(_private_path(path))


def verify_release_bundle(path: Path) -> dict:
    return validate_release_bundle(_read_private(path))


def create_release_bundle(checkpoint: Path, rights: Path, destination: Path,
                          approved_at: str, *, approve=False) -> dict:
    _require(approve is True, 'profile_approval_confirmation_required')
    source, rights_source = _private_path(checkpoint), _private_path(rights)
    value = build_release_bundle(verify_checkpoint(source), _read_private(rights_source), approved_at)
    _bounded(value)  # Refuse size and binding problems before output locks/writes.
    _output_path(destination, rights_source)
    with _writer(destination, source) as output:
        _install(output, value)
    return value


def restore_release_bundle(source: Path, destination: Path) -> dict:
    original = _private_path(source)
    bundle = verify_release_bundle(original)
    with _writer(destination, original) as output:
        _install(output, bundle)
    restored = verify_release_bundle(output)
    _require(restored['bundle_id'] == bundle['bundle_id'], 'profile_release_restore_mismatch')
    return restored


def _advance(old: dict, new: dict) -> None:
    for before, after in zip(old['profiles'], new['profiles']):
        _require(_clock(after['last_checked_at']) >= _clock(before['last_checked_at']),
                 'profile_promotion_clock_rewind')
        if _clock(after['last_checked_at']) == _clock(before['last_checked_at']):
            _require(canonical(after) == canonical(before), 'profile_promotion_same_clock_change')
        _require(_clock(after['last_successful_fetch_at']) >= _clock(before['last_successful_fetch_at']),
                 'profile_promotion_clock_rewind')
        if after['collection_status'] != 'success':
            _require(after['last_successful_fetch_at'] == before['last_successful_fetch_at']
                     and canonical(after['profile']) == canonical(before['profile']),
                     'profile_promotion_degraded_evidence_changed')
        elif before['profile']['id'] == after['profile']['id']:
            first, changed = 'observed_first_at', 'observed_changed_at'
            _require(before['profile'][first] == after['profile'][first]
                     and _clock(after['profile'][changed]) >= _clock(before['profile'][changed]),
                     'profile_promotion_observation_rewind')
            if before['profile']['content_hash'] == after['profile']['content_hash']:
                _require(before['profile'][changed] == after['profile'][changed],
                         'profile_promotion_unchanged_clock_changed')
            else:
                _require(_clock(after['profile'][changed]) > _clock(before['last_successful_fetch_at']),
                         'profile_promotion_conflicting_observation')
        else:
            _require(_clock(after['profile']['observed_first_at']) > _clock(before['last_successful_fetch_at']),
                     'profile_promotion_conflicting_observation')


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


def build_promotion(bundle: dict, current: dict[str, bytes | None]) -> dict:
    reviewed = validate_release_bundle(bundle)
    _require(type(current) is dict and set(current) == set(PUBLIC_FILES), 'invalid_profile_public_base')
    _require(all(v is None or isinstance(v, bytes) and 0 < len(v) <= MAX_RELEASE_BYTES
                 for v in current.values()), 'invalid_profile_public_base')
    _require((current[PUBLIC_FILES[0]] is None) == (current[PUBLIC_FILES[1]] is None),
             'profile_public_pair_incomplete')
    if current[PUBLIC_FILES[0]] is not None:
        try:
            previous = validate_public_profiles(parse_json(current[PUBLIC_FILES[0]]))
            previous_rights = validate_profile_rights(parse_json(current[PUBLIC_FILES[1]]), previous)
            for path, value in zip(PUBLIC_FILES, (previous, previous_rights)):
                _require(current[path] in (canonical(value), canonical(value) + b'\n'),
                         'invalid_profile_public_base')
        except HistoryError:
            raise ProfileReleaseError('invalid_profile_public_base') from None
        _advance(previous, reviewed['public_profiles'])
    after = [canonical(reviewed['public_profiles']) + b'\n', canonical(reviewed['rights']) + b'\n']
    patch_bytes = b''.join(_hunk(path, current[path], text) for path, text in zip(PUBLIC_FILES, after))
    _require(len(patch_bytes) <= MAX_RELEASE_BYTES, 'profile_promotion_patch_too_large')
    bases = {p: None if current[p] is None else hashlib.sha256(current[p]).hexdigest() for p in PUBLIC_FILES}
    core = {'schema_version': 1, 'purpose': 'reviewed_profile_promotion',
            'bundle_id': reviewed['bundle_id'], 'base_hashes': bases,
            'patch_hash': hashlib.sha256(patch_bytes).hexdigest()}
    return {'patch': patch_bytes, 'receipt': {**core, 'candidate_id': digest(core)}}


def _public_base(root: Path) -> dict:
    result = {}
    for name in PUBLIC_FILES:
        path = Path(root)/name
        _require(not path.is_symlink() and not path.parent.is_symlink(), 'invalid_profile_public_base')
        if path.exists():
            _require(path.is_file() and 0 < path.stat().st_size <= MAX_RELEASE_BYTES,
                     'invalid_profile_public_base')
            with path.open('rb') as stream:
                data = stream.read(MAX_RELEASE_BYTES + 1)
            _require(len(data) <= MAX_RELEASE_BYTES, 'invalid_profile_public_base')
            result[name] = data
        else:
            result[name] = None
    return result


def prepare_promotion(bundle: Path, destination: Path, *, root: Path = REPO_ROOT) -> dict:
    source = _private_path(bundle)
    candidate = build_promotion(verify_release_bundle(source), _public_base(root))
    with _writer(destination, source) as output:
        _install_bytes(output, candidate['patch'])
    return candidate['receipt']


def _read_patch(path: Path) -> bytes:
    path = _private_path(path)
    original = private_stat(path)
    _require(0 < original.st_size <= MAX_RELEASE_BYTES, 'invalid_profile_promotion_patch')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        actual = os.fstat(stream.fileno())
        _require((actual.st_dev, actual.st_ino) == (original.st_dev, original.st_ino),
                 'profile_promotion_patch_changed')
        data = stream.read(MAX_RELEASE_BYTES + 1)
    _require(len(data) <= MAX_RELEASE_BYTES, 'invalid_profile_promotion_patch')
    return data


def check_promotion(bundle: Path, patch: Path, candidate_id: str, *, root: Path = REPO_ROOT) -> dict:
    candidate = build_promotion(verify_release_bundle(bundle), _public_base(root))
    _require(candidate['receipt']['candidate_id'] == candidate_id, 'profile_promotion_candidate_changed')
    _require(candidate['patch'] == _read_patch(patch), 'profile_promotion_patch_changed')
    return candidate['receipt']


class _Parser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('allow_abbrev', False)
        super().__init__(*args, **kwargs)

    def error(self, _message):
        raise ProfileReleaseError('invalid_profile_release_arguments')


def _parser():
    parser = _Parser(prog='python -m tracker.profile_release', description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    approve = commands.add_parser('approve')
    approve.add_argument('--checkpoint', type=Path, required=True)
    approve.add_argument('--rights', type=Path, required=True)
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
            bundle = create_release_bundle(args.checkpoint, args.rights, args.output, now, approve=args.approve)
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
        # Never echo exception text, including validation codes from dependencies.
        report.update(operation='refused', error_code='profile_release_interrupted'
                      if isinstance(error, KeyboardInterrupt) else 'profile_release_refused')
        status = 2
    print(json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False))
    return status


if __name__ == '__main__':
    raise SystemExit(main())
