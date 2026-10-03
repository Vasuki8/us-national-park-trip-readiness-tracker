"""Deliberate private activity collection, offline verification, restore and review."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .activity_checkpoints import (ActivityCheckpointError, collect_checkpoint,
                                   export_review_candidate, restore_checkpoint, verify_checkpoint)
from .activity_transport import request_activity_page, validate_activity_key
from .park_activities import ActivityCollectionError

SAFE_ERRORS = frozenset({
    'invalid_activity_arguments', 'live_confirmation_required', 'nps_key_not_configured', 'nps_key_invalid',
    'activity_checkpoint_too_large', 'invalid_activity_checkpoint', 'invalid_activity_checkpoint_clock',
    'invalid_activity_checkpoint_parent', 'invalid_activity_checkpoint_scope', 'activity_checkpoint_hash_mismatch',
    'activity_private_storage_refused', 'activity_checkpoint_unreadable', 'overlapping_activity_paths',
    'activity_destination_exists', 'activity_output_locked', 'activity_collection_clock_not_advanced',
    'invalid_activity_transport', 'activity_attempt_refused', 'activity_restore_mismatch',
})


class _Parser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('allow_abbrev', False)
        super().__init__(*args, **kwargs)

    def error(self, _message):
        raise ActivityCheckpointError('invalid_activity_arguments')


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def _base_report(operation: str, network_attempted: bool) -> dict:
    return {'schema_version': 1, 'scope': 'private_activity_only', 'operation': operation,
            'network_attempted': network_attempted, 'approval_performed': False,
            'publication_performed': False, 'site_data_written': False}


def _summary(checkpoint: dict, operation: str, network_attempted: bool) -> dict:
    inventories = checkpoint['inventories']
    counts = {status: sum(item['collection_status'] == status for item in inventories)
              for status in ('success', 'failed', 'quarantined')}
    return {**_base_report(operation, network_attempted),
            'checkpoint_id': checkpoint['checkpoint_id'], 'checked_at': checkpoint['checked_at'],
            'park_count': len(inventories), 'retained_activity_count': sum(len(item['records']) for item in inventories),
            'collection_counts': counts}


def _parser() -> _Parser:
    parser = _Parser(prog='python -m tracker.activity_stage', description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    collect = commands.add_parser('collect', help='Create a fresh private five-park activity checkpoint')
    collect.add_argument('--live', action='store_true')
    collect.add_argument('--previous', type=Path)
    collect.add_argument('--output', type=Path, required=True)
    verify = commands.add_parser('verify', help='Validate a checkpoint offline')
    verify.add_argument('--checkpoint', type=Path, required=True)
    for name in ('restore', 'export-review'):
        command = commands.add_parser(name)
        command.add_argument('--checkpoint', type=Path, required=True)
        command.add_argument('--output', type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    network_attempted = False
    try:
        args = _parser().parse_args(argv)
        if args.command == 'collect':
            if not args.live:
                raise ActivityCheckpointError('live_confirmation_required')
            key = None

            def fetch_for(code: str):
                nonlocal key
                # Every baseline, clock, capacity and destination was checked,
                # and the exclusive output lock is held before this factory.
                if key is None:
                    key = os.environ.get('NPS_API_KEY', '')
                    if not isinstance(key, str) or not key.strip():
                        raise ActivityCheckpointError('nps_key_not_configured')
                    try:
                        validate_activity_key(key)
                    except ActivityCollectionError:
                        raise ActivityCheckpointError('nps_key_invalid') from None

                def fetch(start: int):
                    nonlocal network_attempted
                    network_attempted = True
                    return request_activity_page(code, start, key)
                return fetch

            checkpoint = collect_checkpoint(args.output, args.previous, utc_now(), fetch_for)
            report = _summary(checkpoint, 'checkpoint_created', network_attempted)
            status = 0 if report['collection_counts']['success'] == report['park_count'] else 1
        elif args.command == 'verify':
            report = _summary(verify_checkpoint(args.checkpoint), 'verified', False)
            status = 0
        elif args.command == 'restore':
            report = _summary(restore_checkpoint(args.checkpoint, args.output), 'restored', False)
            status = 0
        else:
            candidate = export_review_candidate(args.checkpoint, args.output)
            report = {**_summary(candidate['checkpoint'], 'review_exported', False),
                      'source_rights_status': candidate['source_rights_status']}
            status = 0
    except (Exception, KeyboardInterrupt) as error:
        if isinstance(error, KeyboardInterrupt):
            code = 'activity_operation_interrupted'
        else:
            code = str(error) if isinstance(error, ActivityCheckpointError) and str(error) in SAFE_ERRORS \
                else 'activity_operation_failed'
        report = {**_base_report('refused', network_attempted), 'error_code': code}
        status = 2
    print(json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False))
    return status


if __name__ == '__main__':
    raise SystemExit(main())
