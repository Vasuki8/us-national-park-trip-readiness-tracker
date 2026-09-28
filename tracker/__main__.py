"""Explicit operator command; no automatic scheduling or publication."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from .alerts import collect, initial_snapshot, request_page, write_snapshot

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--park', choices=['yose', 'romo', 'yell', 'zion', 'grca'], required=True)
    parser.add_argument('--data-dir', type=Path, default=Path('data/alerts'))
    args = parser.parse_args()
    key = os.environ.get('NPS_API_KEY', '')
    if not key.strip():
        parser.exit(2, 'Set NPS_API_KEY privately; no request was made and no snapshot was changed.\n')
    path = args.data_dir / f'{args.park}.json'
    try:
        previous = json.loads(path.read_text()) if path.exists() else initial_snapshot(args.park)
        now = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
        snapshot = collect(args.park, previous, now, lambda start: request_page(args.park, start, key))
        write_snapshot(path, snapshot)
    except (ValueError, OSError):
        parser.exit(2, 'Local snapshot or clock validation failed; existing data was not replaced.\n')
    print(f"{args.park}: {snapshot['collection_status']}; {len(snapshot['records'])} retained records")
    return 0 if snapshot['collection_status'] == 'success' else 1

if __name__ == '__main__':
    raise SystemExit(main())
