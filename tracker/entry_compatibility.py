"""Opt-in fixed-source compatibility diagnostic, not a scheduled source collector.

Raw HTML only lives in memory and the existing ledger in a temporary private
folder. Output is allowlisted metadata; no baseline approval or public write.
"""
from __future__ import annotations
import hashlib
import http.client
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from .entry_html import MAX_HTML
from .entry_sources import PROFILES, canonical, inspect_entry_sources, instant, shape
from .entry_review_io import require
from .entry_review_store import EntryReviewStore

REPO_ROOT = Path(__file__).resolve().parents[1]
CAPTURE_REASONS = frozenset(('captured', 'http_not_success', 'unsupported_response',
    'response_too_large', 'response_length_mismatch', 'capture_failed'))
EXTRACTED_REASONS = frozenset(('context_not_reviewed', 'excerpt_missing', 'excerpt_ambiguous'))


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def capture_source(code: str, *, live: bool = False) -> tuple[dict, dict]:
    """One credential-free HTTPS GET to a fixed profile, no redirects or retries.

    The 15-second timeout applies to socket operations, not an entire slow-stream
    or DNS wall-clock deadline. The manual workflow separately caps the whole job.
    """
    require(live is True, 'live_diagnostic_opt_in_required')
    require(type(code) is str and code in PROFILES, 'invalid_compatibility_source')
    url = PROFILES[code]['url']
    receipt = {'park_code': code, 'source_url': url, 'started_at': timestamp(),
               'checked_at': None, 'http_status': None, 'reason': 'capture_failed',
               'byte_count': 0, 'raw_sha256': None}
    capture = {'source_url': url, 'final_url': None, 'checked_at': None,
               'status': 'failed', 'content_type': None, 'html': None}
    conn = None
    try:
        conn = http.client.HTTPSConnection('www.nps.gov', timeout=15)
        conn.request('GET', url.removeprefix('https://www.nps.gov'), headers={
            'User-Agent': 'ParkReadiness-development-compatibility-check/0.1',
            'Accept': 'text/html', 'Accept-Encoding': 'identity'})
        response = conn.getresponse()
        receipt['http_status'] = response.status
        if response.status != 200:
            receipt['reason'] = 'http_not_success'
        elif (len(response.headers.get_all('Content-Type', [])) != 1
              or len(response.headers.get_all('Content-Encoding', [])) > 1
              or response.headers.get_content_type() != 'text/html'
              or response.headers.get_content_charset('utf-8').lower() not in ('utf-8', 'utf8', 'us-ascii')
              or response.getheader('Content-Encoding', 'identity').lower() != 'identity'):
            receipt['reason'] = 'unsupported_response'
        else:
            lengths = response.headers.get_all('Content-Length', [])
            require(len(lengths) <= 1, 'ambiguous_response_length')
            size = None
            if lengths:
                value = lengths[0].strip()
                require(len(value) <= 12 and value.isascii() and value.isdigit(), 'invalid_response_length')
                size = int(value)
            if size is not None and size > MAX_HTML:
                receipt['reason'] = 'response_too_large'
            else:
                raw = response.read(MAX_HTML + 1)
                if len(raw) > MAX_HTML:
                    receipt['reason'] = 'response_too_large'
                elif size is not None and size != len(raw):
                    receipt['reason'] = 'response_length_mismatch'
                else:
                    text = raw.decode('utf-8')
                    capture.update(status='success', final_url=url,
                                   content_type=response.getheader('Content-Type'), html=text)
                    receipt.update(reason='captured', byte_count=len(raw),
                                   raw_sha256=hashlib.sha256(raw).hexdigest())
    except Exception:
        # Never relay provider text, exception strings, cookies, headers or paths.
        receipt['reason'] = 'capture_failed'
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
        receipt['checked_at'] = capture['checked_at'] = timestamp()
    return capture, receipt


def inspect_batch(records: list, captures: list, receipts: list, *, now: datetime,
                  seed_register: dict | None = None) -> dict:
    """Recheck a complete captured batch through the actual extractor and ledger."""
    require(type(captures) is list and type(receipts) is list
            and len(captures) == len(receipts) == len(PROFILES), 'diagnostic_inventory_mismatch')
    extraction = inspect_entry_sources(records, captures, [], now)
    for code, capture, receipt in zip(PROFILES, captures, receipts):
        r = shape(receipt, 'park_code source_url started_at checked_at http_status reason byte_count raw_sha256')
        require(r['park_code'] == code and r['source_url'] == capture['source_url'] == PROFILES[code]['url'], 'diagnostic_source_mismatch')
        require(r['checked_at'] == capture['checked_at'] and instant(r['started_at']) <= instant(r['checked_at']) <= now, 'diagnostic_clock_mismatch')
        require(r['http_status'] is None or type(r['http_status']) is int and 100 <= r['http_status'] <= 599, 'invalid_diagnostic_status')
        require(type(r['reason']) is str and r['reason'] in CAPTURE_REASONS, 'invalid_diagnostic_reason')
        if capture['status'] == 'success':
            raw = capture['html'].encode('utf-8')
            require(r['reason'] == 'captured' and r['http_status'] == 200 and type(r['byte_count']) is int
                    and r['byte_count'] == len(raw) and r['raw_sha256'] == hashlib.sha256(raw).hexdigest(), 'diagnostic_capture_mismatch')
        else:
            require(r['reason'] != 'captured' and type(r['byte_count']) is int and r['byte_count'] == 0
                    and r['raw_sha256'] is None, 'diagnostic_capture_mismatch')
    seed = {'schema_version': 1, 'proposals': []} if seed_register is None else seed_register
    with tempfile.TemporaryDirectory(prefix='park-entry-compatibility-') as folder:
        store = EntryReviewStore(Path(folder)/'review')
        stored = store.record({'records': records, 'captures': captures, 'baselines': [], 'seed_register': seed},
                              expected_revision=None, now=now)
        readback = store.read()
        require(readback['revision'] == stored['revision']
                and canonical(readback['records']) == canonical(records)
                and canonical(readback['events'][0]['extraction']) == canonical(extraction)
                and canonical(readback['events'][0]['request']['captures']) == canonical(captures), 'diagnostic_replay_mismatch')
        pending = len(readback['register']['proposals'])
    by_source = {s['source_url']: s for s in extraction['sources']}
    rows = []
    for receipt in receipts:
        s = by_source[receipt['source_url']]
        rows.append({**receipt, 'capture_reason': receipt['reason'], 'reason': s['reason'],
                     'context_extracted': s['context'] is not None and s['reason'] in EXTRACTED_REASONS,
                     'context_hash': s['context_hash']})
    return {'schema_version': 1, 'diagnostic_only': True,
            'all_contexts_extracted': all(r['context_extracted'] for r in rows),
            'ledger_replay_verified': True, 'pending_proposals': pending,
            'approved_context_baselines': 0, 'approval_performed': False,
            'publication_performed': False, 'raw_captures_uploaded': False,
            'capture_retention': 'temporary_diagnostic_only', 'sources': rows}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args != ['--live']:
        sys.stderr.write('live_diagnostic_opt_in_required\n' if not args else 'invalid_compatibility_arguments\n')
        return 2
    try:
        records = json.loads((REPO_ROOT/'data/rules.json').read_text()) + json.loads((REPO_ROOT/'data/entry-notes.json').read_text())
        seed = json.loads((REPO_ROOT/'data/entry-review.json').read_text())
        pairs = [capture_source(code, live=True) for code in PROFILES]
        report = inspect_batch(records, [p[0] for p in pairs], [p[1] for p in pairs],
                               now=datetime.now(timezone.utc), seed_register=seed)
        print(json.dumps(report, sort_keys=True))
        return 0 if report['all_contexts_extracted'] else 2
    except Exception:
        sys.stderr.write('entry_compatibility_diagnostic_failed\n')
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
