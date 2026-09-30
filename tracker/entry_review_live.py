"""Explicit persistent live entry-page capture into the private review ledger.

This is an operator action, never a scheduler. It captures only the five fixed
NPS entry sources, retains the complete batch in the existing private ledger,
and prepares read-only review packets for sources with active holds.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .entry_compatibility import CAPTURE_REASONS, capture_source
from .entry_review_io import REPO_ROOT, ReviewStoreError, check_path, private_stat, require
from .entry_review_model import revision
from .entry_review_packet import prepare_review_packet
from .entry_review_store import EntryReviewStore
from .entry_sources import PROFILES, digest, instant, shape

RECORDS_FILE = REPO_ROOT/'data/rules.json'
NOTES_FILE = REPO_ROOT/'data/entry-notes.json'
SEED_FILE = REPO_ROOT/'data/entry-review.json'


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ReviewStoreError('invalid_live_review_arguments')


def _preflight_output(store: EntryReviewStore, output_dir: Path) -> Path:
    output = check_path(Path(output_dir))
    root = check_path(store.root)
    require(output != root and output not in root.parents and root not in output.parents,
            'overlapping_live_review_paths')
    try:
        private_stat(root.parent, directory=True)
        private_stat(output.parent, directory=True)
        if output.exists():
            private_stat(output, directory=True)
    except OSError:
        raise ReviewStoreError('private_capture_destination_unavailable') from None
    return output


def _initial_records() -> tuple[list, dict]:
    try:
        records = json.loads(RECORDS_FILE.read_text()) + json.loads(NOTES_FILE.read_text())
        seed = json.loads(SEED_FILE.read_text())
        require(type(records) is list and records, 'invalid_live_review_inventory')
        require(type(seed) is dict, 'invalid_live_review_inventory')
        return records, seed
    except ReviewStoreError:
        raise
    except Exception:
        raise ReviewStoreError('invalid_live_review_inventory') from None


def _current_inputs(state: dict) -> tuple[list, list, dict]:
    if not state['events']:
        records, seed = _initial_records()
        return records, [], seed
    first = state['events'][0]
    latest = next((event for event in reversed(state['events']) if event['kind'] == 'observation'), None)
    require(first['kind'] == 'observation' and latest is not None, 'invalid_live_review_history')
    # Explicit reconciliation baselines live in state and are injected internally
    # by make_event. Before any reconciliation, preserve the latest validated
    # legacy baseline input so a live append cannot manufacture fresh holds.
    baselines = [] if state['baselines'] else copy.deepcopy(latest['request']['baselines'])
    return copy.deepcopy(state['records']), baselines, copy.deepcopy(first['request']['seed_register'])


def _capture_setup(store: EntryReviewStore, packet_output_dir: Path, expected_revision):
    revision(expected_revision)
    output = _preflight_output(store, packet_output_dir)
    state = store.read()
    require(state['revision'] == expected_revision, 'stale_review_revision')
    records, baselines, seed = _current_inputs(state)
    return output, state, records, baselines, seed


def check_capture_setup(store: EntryReviewStore, packet_output_dir: Path, *, expected_revision) -> dict:
    """Read-only path/head/input check, independent of live capture or approval."""
    _, state, records, _, _ = _capture_setup(store, packet_output_dir, expected_revision)
    return {
        'schema_version': 1,
        'mode': 'private_entry_capture_preflight',
        'setup_validated': True,
        'ledger_revision': state['revision'],
        'recorded_batches': sum(1 for event in state['events'] if event['kind'] == 'observation'),
        'pending_proposals': len(state['register']['proposals']),
        'guidance_records': len(records),
        'required_sources': len(PROFILES),
        'network_performed': False,
        'writes_performed': False,
        'ledger_committed': False,
        'approval_performed': False,
        'publication_performed': False,
        'public_data_written': False,
    }


def _validate_pair(code: str, capture: dict, receipt: dict, now: datetime) -> dict:
    profile = PROFILES[code]
    c = shape(capture, 'source_url final_url checked_at status content_type html')
    r = shape(receipt, 'park_code source_url started_at checked_at http_status reason byte_count raw_sha256')
    require(r['park_code'] == code and r['source_url'] == c['source_url'] == profile['url'],
            'live_review_capture_mismatch')
    require(r['checked_at'] == c['checked_at']
            and instant(r['started_at']) <= instant(r['checked_at']) <= now,
            'live_review_capture_clock_mismatch')
    require(type(r['reason']) is str and r['reason'] in CAPTURE_REASONS, 'invalid_live_review_capture_reason')
    require(r['http_status'] is None
            or type(r['http_status']) is int and 100 <= r['http_status'] <= 599,
            'invalid_live_review_http_status')
    if c['status'] == 'success':
        require(c['final_url'] == c['source_url'] and type(c['html']) is str
                and type(c['content_type']) is str, 'live_review_capture_mismatch')
        raw = c['html'].encode('utf-8')
        require(r['reason'] == 'captured' and r['http_status'] == 200
                and r['byte_count'] == len(raw)
                and r['raw_sha256'] == hashlib.sha256(raw).hexdigest(),
                'live_review_capture_mismatch')
    else:
        require(c['status'] == 'failed' and c['final_url'] is None and c['html'] is None
                and c['content_type'] is None and r['reason'] != 'captured'
                and r['byte_count'] == 0 and r['raw_sha256'] is None,
                'live_review_capture_mismatch')
    return r


def run_live_capture(store: EntryReviewStore, packet_output_dir: Path, *,
                     expected_revision, live: bool = False,
                     now: datetime | None = None) -> dict:
    """Capture all fixed sources, commit one batch, then prepare review packets.

    Expected-revision and private destination validation happen before network.
    A failed source is still retained as a failed capture in the complete batch.
    Packet failures never roll the committed ledger back.
    """
    require(live is True, 'live_review_opt_in_required')
    output, _, records, baselines, seed = _capture_setup(store, packet_output_dir, expected_revision)

    pairs = [capture_source(code, live=True) for code in PROFILES]
    current_now = datetime.now(timezone.utc) if now is None else now
    require(isinstance(current_now, datetime) and current_now.tzinfo is not None
            and current_now.utcoffset() is not None, 'invalid_review_clock')
    current_now = current_now.astimezone(timezone.utc)
    captures = [pair[0] for pair in pairs]
    receipts = [_validate_pair(code, pair[0], pair[1], current_now)
                for code, pair in zip(PROFILES, pairs)]

    saved = store.record({
        'records': records,
        'captures': captures,
        'baselines': baselines,
        'seed_register': seed,
    }, expected_revision=expected_revision, now=current_now)

    state = store.read()
    require(state['revision'] == saved['revision'], 'live_review_commit_mismatch')
    source_event_revision = saved['committed_revision']
    event = next((item for item in state['events']
                  if item['kind'] == 'observation'
                  and item.get('operation_id') is not None
                  and source_event_revision == digest(item)), None)
    require(event is not None, 'live_review_commit_mismatch')
    extracted = {item['source_url']: item for item in event['extraction']['sources']}

    rows = []
    packet_count = 0
    for code, capture, receipt in zip(PROFILES, captures, receipts):
        url = PROFILES[code]['url']
        source = extracted[url]
        active = [p for p in state['register']['proposals'] if p['source_url'] == url]
        packet_id = None
        if not active:
            packet_status = 'not_needed'
        elif source['context'] is None:
            packet_status = 'context_unavailable'
        else:
            try:
                manifest = prepare_review_packet(store, output, code, source_event_revision)
                packet_id = manifest['packet_id']
                packet_status = 'ready'
                packet_count += 1
            except (ReviewStoreError, OSError, ValueError, TypeError, KeyError, RecursionError):
                packet_status = 'failed'
        rows.append({
            'park_code': code,
            'source_url': url,
            'checked_at': capture['checked_at'],
            'http_status': receipt['http_status'],
            'capture_reason': receipt['reason'],
            'raw_sha256': receipt['raw_sha256'],
            'context_reason': source['reason'],
            'context_hash': source['context_hash'],
            'active_proposals': len(active),
            'packet_status': packet_status,
            'packet_id': packet_id,
        })

    capture_complete = all(capture['status'] == 'success' for capture in captures)
    packets_ready = all(row['packet_status'] in ('ready', 'not_needed') for row in rows)
    return {
        'schema_version': 1,
        'mode': 'persistent_private_live_entry_review',
        'ledger_revision': state['revision'],
        'source_event_revision': source_event_revision,
        'recorded_batches': sum(1 for item in state['events'] if item['kind'] == 'observation'),
        'pending_proposals': len(state['register']['proposals']),
        'packet_count': packet_count,
        'capture_complete': capture_complete,
        'review_packets_ready': packets_ready,
        'review_ready': capture_complete and packets_ready,
        'sources': rows,
        'network_performed': True,
        'ledger_committed': True,
        'approval_performed': False,
        'publication_performed': False,
        'public_data_written': False,
    }


def main(argv: list[str] | None = None) -> int:
    try:
        parser = _Parser(description='Check private capture setup or persist five fixed NPS entry captures.')
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument('--live', action='store_true')
        mode.add_argument('--check-only', action='store_true')
        parser.add_argument('--store', required=True, type=Path)
        parser.add_argument('--packet-output-dir', required=True, type=Path)
        parser.add_argument('--expected-revision', required=True)
        args = parser.parse_args(argv)
        if not args.live and not args.check_only:
            raise ReviewStoreError('live_review_opt_in_required')
        expected = None if args.expected_revision == 'empty' else args.expected_revision
        if args.check_only:
            report = check_capture_setup(EntryReviewStore(args.store), args.packet_output_dir,
                                         expected_revision=expected)
            sys.stdout.write(json.dumps(report, sort_keys=True, separators=(',', ':'))+'\n')
            return 0
        report = run_live_capture(
            EntryReviewStore(args.store),
            args.packet_output_dir,
            expected_revision=expected,
            live=True,
        )
        sys.stdout.write(json.dumps(report, sort_keys=True, separators=(',', ':'))+'\n')
        return 0 if report['review_ready'] else 1
    except ReviewStoreError as error:
        sys.stderr.write(str(error)+'\n')
        return 2
    except Exception:
        sys.stderr.write('entry_review_live_capture_failed\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
