"""Read-only NPS integration diagnostic; never writes or publishes park snapshots."""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from typing import Callable
from .alerts import CollectionError, collect, initial_snapshot, request_page

PILOTS = ('yose', 'romo', 'yell', 'zion', 'grca')
MAX_PAGES_PER_PARK = 2

def run_preflight(key: str, *, transport: Callable[[str, int, str], dict] = request_page) -> dict:
    """Return only safe scalar diagnostics; provider text and keys are never reported.

    A successful HTTP/normalization probe proves the checked API shape, not park
    conditions, coverage completeness, or permission to activate publication.
    """
    report = {'schema_version': 1, 'mode': 'read_only', 'status': 'not_configured',
              'gate_passed': False, 'publication_performed': False, 'checks': []}
    if not isinstance(key, str) or not key.strip():
        return report
    if any(ord(char) < 32 or ord(char) == 127 for char in key):
        report['status'] = 'invalid_configuration'
        return report
    for code in PILOTS:
        attempts = 0
        def fetch(start: int) -> dict:
            nonlocal attempts
            if attempts >= MAX_PAGES_PER_PARK:
                raise CollectionError('preflight_page_budget')
            attempts += 1
            return transport(code, start, key.strip())
        attempted_at = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
        status, count = 'internal_error', None
        try:
            snapshot = collect(code, initial_snapshot(code), attempted_at, fetch)
            status = snapshot['collection_status']
            if status == 'success':
                count = len(snapshot['records'])
        except Exception:
            # A transport exception may contain credentials. Do not stringify it.
            status = 'internal_error'
        report['checks'].append({'park_code': code, 'attempted_at': attempted_at,
                                 'collection_status': status, 'record_count': count,
                                 'pages_requested': attempts})
    report['gate_passed'] = all(item['collection_status'] == 'success' for item in report['checks'])
    report['status'] = 'verified' if report['gate_passed'] else 'needs_review'
    return report

def main() -> int:
    report = run_preflight(os.environ.get('NPS_API_KEY', ''))
    print(json.dumps(report, indent=2))
    # Only a verified integration returns zero. Configuration and provider
    # failures must make the workflow visibly fail rather than look green.
    if report['gate_passed']:
        return 0
    return 2 if report['status'] in ('not_configured', 'invalid_configuration') else 1

if __name__ == '__main__':
    raise SystemExit(main())
