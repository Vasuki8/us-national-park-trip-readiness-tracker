"""Offline private entry-review ledger commands. No network or production writes."""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from .entry_review_io import ReviewStoreError, read_private_json
from .entry_review_model import safe_summary
from .entry_review_store import EntryReviewStore

class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse normally echoes invalid user arguments, including sensitive paths.
        raise ReviewStoreError('invalid_review_arguments')

def main(argv=None) -> int:
    try:
        parser = _Parser(description='Private offline evidence ledger; never publishes.')
        parser.add_argument('command', choices=('status','record','disposition','reconcile','recover'))
        parser.add_argument('--store', required=True, type=Path)
        parser.add_argument('--input', type=Path)
        parser.add_argument('--expected-revision')
        args = parser.parse_args(argv)
        store = EntryReviewStore(args.store)
        if args.command in ('record','disposition','reconcile'):
            if args.input is None or args.expected_revision is None:
                raise ReviewStoreError('missing_review_write_arguments')
            expected = None if args.expected_revision == 'empty' else args.expected_revision
            method = {'record': store.record, 'disposition': store.disposition, 'reconcile': store.reconcile}[args.command]
            result = method(read_private_json(args.input), expected_revision=expected, now=datetime.now(timezone.utc))
        else:
            if args.input is not None or args.expected_revision is not None:
                raise ReviewStoreError('unexpected_review_arguments')
            result = store.recover() if args.command == 'recover' else safe_summary(store.read())
        sys.stdout.write(json.dumps(result, sort_keys=True, separators=(',',':'))+'\n')
        return 0
    except ReviewStoreError as error:
        # All store codes originate in trusted code, never in supplied source content.
        sys.stderr.write(str(error)+'\n')
        return 2
    except Exception:
        sys.stderr.write('review_operation_failed\n')
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
