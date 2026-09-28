"""Offline operator history commands; no collection, website writes or publication."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .history_model import HistoryError, MAX_OBJECT_BYTES, parse_json, require
from .history_store import HistoryStore

LABELS = {'added': 'Notice added to the checked feed', 'edited': 'Notice text changed in the checked feed',
          'removed': 'Notice no longer present in the checked feed'}
MAX_CHANGES_PER_OBSERVATION = 100
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROTECTED_DIRS = ('data', 'public', 'src', 'dist', 'tracker', 'tests', 'docs', '.git', '.github')

def make_report(store: HistoryStore, code: str, limit: int) -> dict:
    require(type(limit) is int and 1 <= limit <= 100, 'invalid_report_limit')
    entries = store.read(code)
    latest = entries[-1]['snapshot'] if entries else None
    observations = []
    for entry in reversed(entries[-limit:]):
        changes = entry['changes']
        observations.append({'observation_id': entry['observation_id'],
                             'checked_at': entry['snapshot']['last_checked_at'],
                             'collection_status': entry['snapshot']['collection_status'],
                             'comparison': entry['comparison'], 'change_count': len(changes),
                             'omitted_changes': max(0, len(changes) - MAX_CHANGES_PER_OBSERVATION),
                             'changes': [{**item, 'label': LABELS[item['kind']]} for item in changes[:MAX_CHANGES_PER_OBSERVATION]]})
    return {'schema_version': 1, 'scope': 'local_archive_only', 'park_code': code,
            'publication_performed': False, 'site_data_written': False,
            'observation_count': len(entries), 'omitted_observations': max(0, len(entries) - limit),
            'last_checked_at': latest['last_checked_at'] if latest else None,
            'last_successful_fetch_at': latest['last_successful_fetch_at'] if latest else None,
            'collection_status': latest['collection_status'] if latest else 'never_checked',
            'observations': observations}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    record = commands.add_parser('record', help='Retain an already-collected normalized snapshot')
    record.add_argument('--snapshot', type=Path, required=True)
    report = commands.add_parser('report', help='Read and verify an existing local archive')
    report.add_argument('--park', required=True)
    report.add_argument('--limit', type=int, default=20)
    for command in (record, report):
        command.add_argument('--archive-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        destination = args.archive_dir.resolve()
        require(destination != PROJECT_ROOT and not any(destination == PROJECT_ROOT / folder or PROJECT_ROOT / folder in destination.parents for folder in PROTECTED_DIRS), 'unsafe_archive_destination')
        store = HistoryStore(args.archive_dir)
        if args.command == 'record':
            with args.snapshot.open('rb') as handle:
                snapshot = parse_json(handle.read(MAX_OBJECT_BYTES + 1))
            identifier = store.append(snapshot)
            result = {'schema_version': 1, 'operation': 'recorded', 'observation_id': identifier,
                      'source_collection_status': snapshot['collection_status'],
                      'publication_performed': False, 'site_data_written': False}
        else:
            result = make_report(store, args.park, args.limit)
    except HistoryError as error:
        print(f'History operation refused: {error}', file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        print('History operation failed; inspect local inputs and archive. No website data was written.', file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
