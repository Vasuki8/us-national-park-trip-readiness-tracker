"""Replayable editorial events using the existing extractor and TypeScript gate."""
from __future__ import annotations
import copy
import os
import re
import subprocess
from datetime import datetime, timezone
from .entry_sources import (PROFILES, PROFILE_VERSION, canonical, context_value, digest,
    inspect_entry_sources, instant, normalized, shape)
from .entry_html import clean_text, SourceExtractionError
from .entry_review_io import REPO_ROOT, MAX_INPUT_BYTES, ReviewStoreError, parse_json, require

MAX_EVENT_BYTES = 12 * 1024 * 1024
MAX_EVENTS = 64
MAX_LEDGER_BYTES = 128 * 1024 * 1024
EMPTY_REGISTER = {'schema_version': 1, 'proposals': []}


def empty_state() -> dict:
    return {'revision': None, 'events': [], 'records': [], 'register': copy.deepcopy(EMPTY_REGISTER), 'baselines': []}


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


def reconcile_gate(records: list, pending: dict, proposal_ids: list, next_records: list, reviewed_at: str) -> dict:
    payload = canonical({'current': records, 'pending': pending, 'proposal_ids': proposal_ids,
                         'next': next_records, 'reviewed_at': reviewed_at})
    require(len(payload) <= 4 * 1024 * 1024, 'review_gate_input_too_large')
    try:
        result = subprocess.run(['node', '--experimental-strip-types', str(REPO_ROOT/'scripts/entry-reconcile-bridge.ts')],
            input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=REPO_ROOT,
            env={'PATH': os.environ.get('PATH', os.defpath), 'NODE_NO_WARNINGS': '1'}, timeout=10, check=False)
        require(result.returncode == 0 and len(result.stdout) <= 4 * 1024 * 1024, 'review_reconciliation_failed')
        value = shape(parse_json(result.stdout), 'register affected_guidance_ids source_urls')
        require(type(value['affected_guidance_ids']) is list and type(value['source_urls']) is list,
                'review_reconciliation_failed')
        return value
    except ReviewStoreError:
        raise
    except (OSError, subprocess.SubprocessError, SourceExtractionError):
        raise ReviewStoreError('review_reconciliation_failed') from None


def request_key(kind: str, request: dict, parent) -> str:
    return digest({'kind': kind, 'request': request, 'expected_revision': parent})


def _reviewer(value: dict) -> None:
    require(isinstance(value['reviewer'], str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', value['reviewer']),
            'invalid_reviewer')
    clean_text(value['rationale'], 4096)


def _baseline_from_context(source: dict, records: list, reviewed_at: str) -> dict:
    url = source['source_url']
    code = next((code for code, profile in PROFILES.items() if profile['url'] == url), None)
    require(code is not None and source['profile_id'] == f'{PROFILE_VERSION}:{code}', 'review_source_event_mismatch')
    context = context_value(source['context'], PROFILES[code]['heading'])
    require(source['context_hash'] == digest(context), 'review_source_event_mismatch')
    guidance = [record for record in records if record['evidence']['url'] == url]
    require(guidance, 'review_source_event_mismatch')
    for record in guidance:
        require(normalized(context['text']).count(normalized(record['evidence']['excerpt'])) == 1,
                'reviewed_excerpt_not_in_context')
    return {'schema_version': 2, 'source_url': url, 'profile_id': source['profile_id'],
            'guidance_hashes': {record['id']: digest(record) for record in guidance},
            'checked_at': source['checked_at'], 'reviewed_at': reviewed_at,
            'context': copy.deepcopy(context), 'context_hash': source['context_hash']}


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
                # Canonical bytes preserve JSON types; Python equality conflates True and 1.
                require(canonical(value['records']) == canonical(state['records']), 'review_guidance_revision_mismatch')
                require(canonical(value['seed_register']) == canonical(state['events'][0]['request']['seed_register']), 'review_seed_mismatch')
            if state['baselines']:
                require(canonical(value['baselines']) == b'[]', 'review_baseline_override')
                effective_baselines = state['baselines']
            else:
                effective_baselines = value['baselines']  # Legacy trusted input until an explicit reconciliation exists.
            extraction = inspect_entry_sources(value['records'], value['captures'], effective_baselines, when)
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
            _reviewer(value)
            evidence = {'extraction': None, 'register': state['register'], 'checks': []}
        elif kind == 'reconciliation':
            value = shape(request, 'source_event_revision proposal_ids reviewer rationale reviewed_at records')
            require(type(value['source_event_revision']) is str, 'review_source_event_mismatch')
            revision(value['source_event_revision']); _reviewer(value)
            reviewed = instant(value['reviewed_at'])
            require(reviewed <= when, 'invalid_review_clock')
            source_event = next((event for event in state['events']
                                 if event['kind'] == 'observation' and digest(event) == value['source_event_revision']), None)
            require(source_event is not None, 'review_source_event_mismatch')
            assessed = reconcile_gate(state['records'], state['register'], value['proposal_ids'], value['records'],
                                      value['reviewed_at'])
            if state['baselines']:
                prior_baselines = state['baselines']
            else:
                latest_observation = next((event for event in reversed(state['events']) if event['kind'] == 'observation'), None)
                prior_baselines = latest_observation['request']['baselines'] if latest_observation else []
            baselines = [copy.deepcopy(baseline) for baseline in prior_baselines
                         if baseline['source_url'] not in assessed['source_urls']]
            selected = [proposal for proposal in state['register']['proposals'] if proposal['id'] in value['proposal_ids']]
            for url in assessed['source_urls']:
                source = next((item for item in source_event['extraction']['sources'] if item['source_url'] == url), None)
                require(source is not None and source['context'] is not None, 'review_source_event_mismatch')
                related = [proposal for proposal in selected if proposal['source_url'] == url]
                source_checked = instant(source['checked_at'])
                latest_retained = max(
                    instant(capture['checked_at'])
                    for event in state['events'] if event['kind'] == 'observation'
                    for capture in event['request']['captures'] if capture['source_url'] == url
                )
                require(related
                        and source_checked >= max(instant(proposal['checked_at']) for proposal in related)
                        and source_checked == latest_retained, 'stale_review_source_event')
                require(source_checked <= reviewed, 'invalid_review_clock')
                baselines.append(_baseline_from_context(source, value['records'], value['reviewed_at']))
            baselines.sort(key=lambda item: item['source_url'])
            evidence = {'extraction': None, 'register': assessed['register'], 'checks': [],
                        'baselines': baselines,
                        'reconciliation': {'source_event_revision': value['source_event_revision'],
                            'proposal_ids': list(value['proposal_ids']),
                            'affected_guidance_ids': assessed['affected_guidance_ids'],
                            'source_urls': assessed['source_urls'],
                            'previous_guidance_hashes': {r['id']: digest(r) for r in state['records']},
                            'next_guidance_hashes': {r['id']: digest(r) for r in value['records']}}}
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
    records = event['request']['records'] if event['kind'] in ('observation', 'reconciliation') else state['records']
    baselines = event['baselines'] if event['kind'] == 'reconciliation' else state['baselines']
    return {'revision': identifier, 'events': [*state['events'], event],
            'records': records, 'register': event['register'], 'baselines': baselines}


def safe_summary(state: dict) -> dict:
    observations = [event for event in state['events'] if event['kind'] == 'observation']
    dispositions = [event for event in state['events'] if event['kind'] == 'disposition']
    reconciliations = [event for event in state['events'] if event['kind'] == 'reconciliation']
    return {'revision': state['revision'], 'events': len(state['events']), 'recorded_batches': len(observations),
            'pending_proposals': len(state['register']['proposals']),
            'pending': [{'proposal_id': p['id'], 'guidance_id': p['guidance_id'],
                         'reason': p['reason'], 'checked_at': p['checked_at']}
                        for p in state['register']['proposals']],
            'reviewer_dispositions': len(dispositions), 'guidance_reconciliations': len(reconciliations),
            'approved_context_baselines': len(state['baselines']),
            'guidance_records': len(state['records']),
            'last_recorded_at': state['events'][-1]['saved_at'] if state['events'] else None,
            'network_performed': False, 'publication_performed': False,
            'approval_performed': bool(reconciliations)}
