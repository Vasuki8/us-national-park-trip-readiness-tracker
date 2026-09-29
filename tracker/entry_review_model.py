"""Replayable editorial events using the existing extractor and TypeScript gate."""
from __future__ import annotations
import copy
import os
import re
import subprocess
from datetime import datetime, timezone
from .entry_sources import canonical, digest, inspect_entry_sources, instant, shape
from .entry_html import clean_text, SourceExtractionError
from .entry_review_io import REPO_ROOT, MAX_INPUT_BYTES, ReviewStoreError, parse_json, require

MAX_EVENT_BYTES = 12 * 1024 * 1024
MAX_EVENTS = 64
MAX_LEDGER_BYTES = 128 * 1024 * 1024
EMPTY_REGISTER = {'schema_version': 1, 'proposals': []}


def empty_state() -> dict:
    return {'revision': None, 'events': [], 'records': [], 'register': copy.deepcopy(EMPTY_REGISTER)}


def revision(value) -> None:
    require(value is None or isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value), 'invalid_expected_revision')


def clock(now: datetime) -> str:
    require(isinstance(now, datetime) and now.tzinfo is not None and now.utcoffset() is not None, 'invalid_review_clock')
    return now.astimezone(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def gate(records: list, observations: list, pending: dict, saved_at: str) -> dict:
    payload = canonical({'records': records, 'observations': observations, 'pending': pending, 'now': saved_at})
    require(len(payload) <= 4 * 1024 * 1024, 'review_gate_input_too_large')
    try:
        result = subprocess.run(['node', '--experimental-strip-types', str(REPO_ROOT/'scripts/entry-review-bridge.ts')],
            input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=REPO_ROOT,
            env={'PATH': os.environ.get('PATH', os.defpath), 'NODE_NO_WARNINGS': '1'}, timeout=10, check=False)
        require(result.returncode == 0 and len(result.stdout) <= 4 * 1024 * 1024, 'review_gate_failed')
        return shape(parse_json(result.stdout), 'register checks')
    except ReviewStoreError:
        raise
    except (OSError, subprocess.SubprocessError, SourceExtractionError):
        raise ReviewStoreError('review_gate_failed') from None


def request_key(kind: str, request: dict, parent) -> str:
    return digest({'kind': kind, 'request': request, 'expected_revision': parent})


def make_event(kind: str, request: object, state: dict, saved_at: str) -> dict:
    """Compute from source inputs, never trust a caller-supplied extraction/proposal result."""
    try:
        require(len(canonical(request)) <= MAX_INPUT_BYTES, 'private_input_too_large')
        when = instant(saved_at)
        if state['events']:
            require(when > instant(state['events'][-1]['saved_at']), 'older_review_write')
        if kind == 'observation':
            value = shape(request, 'records captures baselines seed_register')
            if state['records']:
                require(value['records'] == state['records'], 'review_guidance_revision_mismatch')
                require(value['seed_register'] == state['events'][0]['request']['seed_register'], 'review_seed_mismatch')
            extraction = inspect_entry_sources(value['records'], value['captures'], value['baselines'], when)
            previous = next((e for e in reversed(state['events']) if e['kind'] == 'observation'), None)
            if previous:
                times = {c['source_url']: instant(c['checked_at']) for c in previous['request']['captures']}
                require(all(instant(c['checked_at']) > times[c['source_url']] for c in value['captures']), 'older_source_observation')
            pending = state['register'] if previous else value['seed_register']
            assessed = gate(value['records'], extraction['observations'], pending, saved_at)
            evidence = {'extraction': extraction, 'register': assessed['register'], 'checks': assessed['checks']}
        elif kind == 'disposition':
            value = shape(request, 'proposal_id reviewer decision rationale')
            require(any(p['id'] == value['proposal_id'] for p in state['register']['proposals']), 'unknown_review_proposal')
            require(value['decision'] in ('retain_hold', 'request_guidance_revision'), 'invalid_review_disposition')
            require(isinstance(value['reviewer'], str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', value['reviewer']), 'invalid_reviewer')
            clean_text(value['rationale'], 4096)
            evidence = {'extraction': None, 'register': state['register'], 'checks': []}
        else:
            raise ReviewStoreError('invalid_review_event')
        event = {'schema_version': 1, 'kind': kind, 'previous_revision': state['revision'],
                 'saved_at': saved_at, 'request': value, **evidence,
                 'operation_id': request_key(kind, value, state['revision'])}
        require(len(canonical(event)) <= MAX_EVENT_BYTES, 'review_event_too_large')
        return copy.deepcopy(event)
    except ReviewStoreError:
        raise
    except (SourceExtractionError, KeyError, TypeError, ValueError, RecursionError, OverflowError):
        raise ReviewStoreError('invalid_review_evidence') from None


def apply_event(state: dict, event: dict, identifier: str) -> dict:
    return {'revision': identifier, 'events': [*state['events'], event],
            'records': event['request']['records'] if event['kind'] == 'observation' else state['records'],
            'register': event['register']}


def safe_summary(state: dict) -> dict:
    observations = [event for event in state['events'] if event['kind'] == 'observation']
    return {'revision': state['revision'], 'events': len(state['events']), 'recorded_batches': len(observations),
            'pending_proposals': len(state['register']['proposals']),
            'pending': [{'proposal_id': p['id'], 'guidance_id': p['guidance_id'],
                         'reason': p['reason'], 'checked_at': p['checked_at']}
                        for p in state['register']['proposals']],
            'reviewer_dispositions': len(state['events']) - len(observations),
            'guidance_records': len(state['records']),
            'last_recorded_at': state['events'][-1]['saved_at'] if state['events'] else None,
            'network_performed': False, 'publication_performed': False, 'approval_performed': False}
