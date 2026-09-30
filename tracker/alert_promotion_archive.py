"""Read-only archive continuity verifier for the private alert-data patch preparer.

Only small hash/count requests and replies cross this bridge. It neither approves
source content nor exports raw evidence, creates archives, or writes public data.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from .entry_review_io import ReviewStoreError, check_path, private_stat
from .history_model import HistoryError, digest, parse_json, require
from .history_projection import MAX_VISIBLE_OBSERVATIONS, _project_entries
from .history_store import HistoryStore, MAX_OBSERVATIONS
from .preview import PILOT_CODES

MAX_REQUEST_BYTES = 16 * 1024
PARK_FIELDS = {'park_code', 'public_snapshot_hash', 'public_history_hash',
               'public_total_observations', 'public_visible_observations',
               'candidate_snapshot_hash', 'candidate_history_hash',
               'candidate_total_observations', 'candidate_visible_observations'}


def _hash(value):
    require(isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None, 'invalid_archive_request')


def verify_archive_request(archive_dir: Path, request: object) -> dict:
    require(isinstance(request, dict) and set(request) == {'schema_version', 'purpose', 'bundle_id', 'parks'}, 'invalid_archive_request')
    require(type(request['schema_version']) is int and request['schema_version'] == 1
            and request['purpose'] == 'alert_archive_request', 'invalid_archive_request')
    _hash(request['bundle_id'])
    require(isinstance(request['parks'], list) and len(request['parks']) == len(PILOT_CODES), 'invalid_archive_request')
    for code, item in zip(PILOT_CODES, request['parks']):
        require(isinstance(item, dict) and set(item) == PARK_FIELDS and item['park_code'] == code, 'invalid_archive_request')
        for prefix in ('public', 'candidate'):
            _hash(item[f'{prefix}_snapshot_hash']); _hash(item[f'{prefix}_history_hash'])
            count, visible = item[f'{prefix}_total_observations'], item[f'{prefix}_visible_observations']
            require(type(count) is int and 0 <= count <= MAX_OBSERVATIONS, 'invalid_archive_request')
            require(type(visible) is int and (visible == 0 if count == 0 else 1 <= visible <= min(count, MAX_VISIBLE_OBSERVATIONS)), 'invalid_archive_request')
        require(item['public_total_observations'] <= item['candidate_total_observations'], 'archive_candidate_rewind')

    archive = check_path(archive_dir)
    private_stat(archive, directory=True)
    store = HistoryStore(archive)
    store._usage()  # Enforce existing entry/size/symlink bounds before traversing permissions.
    for path in archive.rglob('*'):
        private_stat(path, directory=path.is_dir())
    views = []
    for code, item in zip(PILOT_CODES, request['parks']):
        entries = store.read(code)  # Replays every committed observation, including hidden changes.
        require(item['candidate_total_observations'] <= len(entries), 'archive_checkpoint_missing')
        for prefix in ('public', 'candidate'):
            count = item[f'{prefix}_total_observations']
            view = _project_entries(entries[:count], code, limit=item[f'{prefix}_visible_observations'] or MAX_VISIBLE_OBSERVATIONS)
            require(digest(view['snapshot']) == item[f'{prefix}_snapshot_hash']
                    and digest(view['history']) == item[f'{prefix}_history_hash'], 'archive_checkpoint_mismatch')
            if prefix == 'candidate':
                views.append(view)
    body = {'schema_version': 1, 'purpose': 'private_preview', 'data_kind': 'unreviewed_source',
            'publication_performed': False, 'views': views}
    require(digest(body) == request['bundle_id'], 'archive_bundle_mismatch')
    return {'schema_version': 1, 'purpose': 'alert_archive_continuity',
            'request_hash': digest(request), 'bundle_id': request['bundle_id'],
            'verified_parks': len(PILOT_CODES), 'publication_performed': False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        require(len(raw) <= MAX_REQUEST_BYTES, 'archive_request_too_large')
        result = verify_archive_request(args.archive_dir, parse_json(raw))
    except (HistoryError, ReviewStoreError, OSError, ValueError, TypeError, KeyError, RecursionError):
        print('Private archive continuity verification refused.', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(',', ':')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
