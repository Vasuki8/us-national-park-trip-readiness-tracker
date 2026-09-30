"""Explicit private staging commands. No schedule, site-data export or publication."""
from __future__ import annotations
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from .alerts import InvalidFeed, request_page
from .history_model import HistoryError, canonical, instant, require
from .staging import PILOT_CODES, StagingCollector

SAFE_ERRORS = frozenset(('live_confirmation_required', 'nps_key_not_configured',
    'nps_key_invalid', 'staging_locked', 'archive_locked', 'pending_recovery_required',
    'archive_head_changed', 'receipt_hash_mismatch', 'invalid_receipt',
    'staging_limit', 'archive_limit', 'history_limit', 'history_expansion_limit',
    'unsafe_staging_destination', 'symlink_in_staging_path', 'collection_clock_not_advanced',
    'invalid_timestamp', 'archive_hash_mismatch', 'missing_archive_object'))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def _fetch_for(code: str, key: str):
    def fetch(start: int) -> dict:
        payload = request_page(code, start, key)
        # A provider echo must not write the private key into an archive.
        if key in canonical(payload).decode('utf-8'):
            raise InvalidFeed('credential_echo')
        return payload
    return fetch


def _collect_all(stage: StagingCollector, key: str) -> int:
    """Precheck all parks, then report every committed result or a partial interruption."""
    checks: list[dict] = []
    report = {'schema_version': 1, 'scope': 'private_staging_only', 'operation': 'collect_all',
              'status': 'interrupted', 'checks': checks, 'publication_performed': False,
              'site_data_written': False}
    try:
        checked_at = utc_now()
        for code in PILOT_CODES:
            status = stage.status(code)
            require(status['stage_state'] == 'idle', 'pending_recovery_required')
            require(not status['writer_locked'], 'staging_locked')
            require(not status['archive_writer_locked'], 'archive_locked')
            last_checked = status['last_checked_at']
            require(last_checked is None or instant(checked_at) > instant(last_checked),
                    'collection_clock_not_advanced')
        for code in PILOT_CODES:
            checks.append(stage.collect(code, checked_at, _fetch_for(code, key)))
    except Exception as error:
        report['error_code'] = (str(error) if isinstance(error, HistoryError)
                                and str(error) in SAFE_ERRORS else 'staging_operation_failed')
        print(json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False))
        return 2
    report['status'] = ('archived' if all(item['collection_status'] == 'success' for item in checks)
                        else 'needs_review')
    print(json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False))
    return 0 if report['status'] == 'archived' else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('collect', 'recover', 'status'):
        command = commands.add_parser(name)
        command.add_argument('--park', choices=PILOT_CODES if name == 'recover' else (*PILOT_CODES, 'all'), required=True)
        command.add_argument('--staging-dir', type=Path, required=True)
        if name == 'collect':
            command.add_argument('--live', action='store_true', help='Explicitly allow private NPS API requests')
    args = parser.parse_args(argv)
    try:
        if args.command == 'collect':
            require(args.live, 'live_confirmation_required')
            key = os.environ.get('NPS_API_KEY', '')
            require(bool(key.strip()), 'nps_key_not_configured')
            require(key.isascii() and all(32 < ord(char) < 127 for char in key), 'nps_key_invalid')
            stage = StagingCollector(args.staging_dir)
            if args.park == 'all':
                return _collect_all(stage, key)
            result = stage.collect(args.park, utc_now(), _fetch_for(args.park, key))
        else:
            stage = StagingCollector(args.staging_dir)
            if args.command == 'status' and args.park == 'all':
                result = {'schema_version': 1, 'scope': 'private_staging_only',
                          'operation': 'status_all',
                          'parks': [stage.status(code) for code in PILOT_CODES],
                          'publication_performed': False, 'site_data_written': False}
            else:
                result = stage.recover(args.park) if args.command == 'recover' else stage.status(args.park)
    except Exception as error:
        # Never print arbitrary provider text, OS paths, raw responses or credentials.
        aggregate_status = args.command == 'status' and args.park == 'all'
        code = (str(error) if not aggregate_status and isinstance(error, HistoryError)
                and str(error) in SAFE_ERRORS else 'staging_operation_failed')
        print(json.dumps({'schema_version': 1, 'operation': 'refused', 'error_code': code,
                          'publication_performed': False, 'site_data_written': False}))
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False))
    return 1 if result['operation'] in ('archived', 'recovered') and result['collection_status'] != 'success' else 0


if __name__ == '__main__':
    raise SystemExit(main())
