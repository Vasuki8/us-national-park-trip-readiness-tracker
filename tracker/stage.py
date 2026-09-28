"""Explicit private staging commands. No schedule, site-data export or publication."""
from __future__ import annotations
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from .alerts import InvalidFeed, request_page
from .history_model import HistoryError, canonical, require
from .staging import PILOT_CODES, StagingCollector

SAFE_ERRORS = frozenset(('live_confirmation_required', 'nps_key_not_configured',
    'nps_key_invalid', 'staging_locked', 'archive_locked', 'pending_recovery_required',
    'archive_head_changed', 'receipt_hash_mismatch', 'invalid_receipt',
    'staging_limit', 'archive_limit', 'history_limit', 'history_expansion_limit',
    'unsafe_staging_destination', 'symlink_in_staging_path', 'collection_clock_not_advanced',
    'invalid_timestamp', 'archive_hash_mismatch', 'missing_archive_object'))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('collect', 'recover', 'status'):
        command = commands.add_parser(name)
        command.add_argument('--park', choices=PILOT_CODES, required=True)
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
            def fetch(start: int) -> dict:
                payload = request_page(args.park, start, key)
                # A provider echo must not write the private key into an archive.
                if key in canonical(payload).decode('utf-8'):
                    raise InvalidFeed('credential_echo')
                return payload
            result = stage.collect(args.park, utc_now(), fetch)
        else:
            stage = StagingCollector(args.staging_dir)
            result = stage.recover(args.park) if args.command == 'recover' else stage.status(args.park)
    except Exception as error:
        # Never print arbitrary provider text, OS paths, raw responses or credentials.
        code = str(error) if isinstance(error, HistoryError) and str(error) in SAFE_ERRORS else 'staging_operation_failed'
        print(json.dumps({'schema_version': 1, 'operation': 'refused', 'error_code': code,
                          'publication_performed': False, 'site_data_written': False}))
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False))
    return 1 if result['operation'] in ('archived', 'recovered') and result['collection_status'] != 'success' else 0


if __name__ == '__main__':
    raise SystemExit(main())
