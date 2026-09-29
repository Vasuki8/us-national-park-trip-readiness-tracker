"""Offline source-specific context verification feeding the existing review gate.

Success means only that supplied body text/link targets match a separately
reviewed context. It is not a new guidance approval, a complete rendered-page
comparison, an HTTP probe, or permission to redistribute the returned text.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from .entry_html import SCOPE, MAX_TEXT, SourceExtractionError, clean_text, inspect_html, normalized, require

PROFILES = {
    'yose': {'url': 'https://www.nps.gov/yose/planyourvisit/reservations.htm', 'heading': 'Entrance Reservations'},
    'romo': {'url': 'https://www.nps.gov/romo/planyourvisit/timed-entry-permit-system.htm', 'heading': 'Timed Entry Permit System'},
    'yell': {'url': 'https://www.nps.gov/yell/planyourvisit/permitsandreservations.htm', 'heading': 'Permits & Reservations'},
    'zion': {'url': 'https://www.nps.gov/zion/planyourvisit/permitsandreservations.htm', 'heading': 'Permits & Reservations'},
    'grca': {'url': 'https://www.nps.gov/grca/planyourvisit/grand-canyon-national-park-public-health-update.htm', 'heading': 'Grand Canyon National Park Operations Update'},
}
PROFILE_VERSION = 'nps-entry-body-v1'
MAX_RESULT_BYTES = 2 * 1024 * 1024


def canonical(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise SourceExtractionError('invalid_source_value') from None


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def shape(value: object, keys: str) -> dict:
    require(type(value) is dict and set(value) == set(keys.split()), 'invalid_source_shape')
    return value


def instant(value: object) -> datetime:
    clean_text(value, 24)
    require(re.fullmatch(r'(?!0000)\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z', value), 'invalid_source_clock')
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise SourceExtractionError('invalid_source_clock') from None


def context_value(value: object, heading: str) -> dict:
    c = shape(value, 'scope text h1 links')
    require(c['scope'] == SCOPE, 'invalid_source_scope')
    clean_text(c['text'])
    require(type(c['h1']) is list and len(c['h1']) <= 256, 'invalid_source_scope')
    for h in c['h1']: clean_text(h, 256)
    require(c['h1'].count(heading) == 1 and heading in c['text'].split('\n'), 'invalid_source_scope')
    require(type(c['links']) is list and len(c['links']) <= 2048, 'invalid_source_scope')
    for link in c['links']: clean_text(link, 2048, empty=True)
    require(all(normalized(block) == block and block for block in c['text'].split('\n')), 'invalid_source_scope')
    return c


def _inventory(records: object, now: datetime) -> dict:
    require(type(records) is list and 0 < len(records) <= 32, 'source_inventory_mismatch')
    groups: dict[str, list] = {}; seen: set[str] = set()
    for r in records:
        require(type(r) is dict, 'source_inventory_mismatch')
        clean_text(r.get('id'), 128)
        require(re.fullmatch('[a-z0-9-]+', r['id']) and r['id'] not in seen, 'source_inventory_mismatch')
        seen.add(r['id'])
        code = r.get('park_code'); require(type(code) is str and code in PROFILES, 'source_inventory_mismatch')
        profile = PROFILES[code]
        require(r.get('review_status') in ('reviewed', 'needs_review', 'conflict'), 'invalid_guidance')
        require(instant(r.get('reviewed_at')) <= now, 'invalid_source_clock')
        e = r.get('evidence'); require(type(e) is dict, 'invalid_guidance')
        require(e.get('url') == profile['url'] and e.get('hash_scope') == 'excerpt', 'source_identity_mismatch')
        clean_text(e.get('excerpt'), 32768)
        require(e.get('reviewed_at') == r['reviewed_at'], 'invalid_guidance')
        require(e.get('content_hash') == hashlib.sha256(e['excerpt'].encode()).hexdigest(), 'guidance_evidence_mismatch')
        require(len(canonical(r)) <= 131072, 'invalid_guidance')
        groups.setdefault(code, []).append(r)
    return groups


def inspect_entry_sources(records: object, captures: object, baselines: object, now: datetime) -> dict:
    """Inspect a complete source batch and return gate observations + private context.

    Captures are supplied by a caller; this function does no I/O. Baselines are
    explicit operator-reviewed context records, never inferred from short quotes.
    Failed context verification maps to `failed` in the existing intake; the
    private sources list preserves the precise reason and both context versions.
    """
    require(isinstance(now, datetime) and now.tzinfo is not None and now.utcoffset() is not None, 'invalid_source_clock')
    now = now.astimezone(timezone.utc)
    groups = _inventory(records, now)
    require(type(captures) is list and len(captures) == len(groups), 'source_inventory_mismatch')
    require(type(baselines) is list and len(baselines) <= len(groups), 'baseline_inventory_mismatch')
    by_url = {PROFILES[code]['url']: code for code in groups}
    current: dict[str, dict] = {}; approved: dict[str, dict] = {}
    for value in captures:
        c = shape(value, 'source_url final_url checked_at status content_type html')
        require(type(c['source_url']) is str and c['source_url'] in by_url and c['source_url'] not in current, 'source_identity_mismatch')
        time = instant(c['checked_at']); code = by_url[c['source_url']]
        require(max(instant(r['reviewed_at']) for r in groups[code]) < time <= now, 'invalid_source_clock')
        require(c['status'] in ('success', 'failed'), 'invalid_capture')
        if c['status'] == 'success':
            require(c['final_url'] == c['source_url'], 'source_identity_mismatch')
            require(type(c['content_type']) is str and c['content_type'].split(';')[0].strip().lower() == 'text/html', 'invalid_capture_type')
            require(type(c['html']) is str, 'invalid_capture')
        else:
            require(c['html'] is None and c['content_type'] is None and c['final_url'] is None, 'invalid_capture')
        current[c['source_url']] = c
    require(set(current) == set(by_url), 'source_inventory_mismatch')
    for value in baselines:
        b = shape(value, 'schema_version source_url profile_id guidance_hashes checked_at reviewed_at context context_hash')
        require(type(b['schema_version']) is int and b['schema_version'] == 1, 'invalid_baseline')
        url = b['source_url']; require(type(url) is str and url in by_url and url not in approved, 'baseline_inventory_mismatch')
        code = by_url[url]; require(b['profile_id'] == f'{PROFILE_VERSION}:{code}', 'baseline_revision_mismatch')
        expected = {r['id']: digest(r) for r in groups[code]}
        require(b['guidance_hashes'] == expected, 'baseline_revision_mismatch')
        checked, reviewed = instant(b['checked_at']), instant(b['reviewed_at'])
        require(max(instant(r['reviewed_at']) for r in groups[code]) < checked <= reviewed < instant(current[url]['checked_at']) <= now, 'invalid_source_clock')
        ctx = context_value(b['context'], PROFILES[code]['heading'])
        require(b['context_hash'] == digest(ctx), 'baseline_evidence_mismatch')
        for r in groups[code]:
            require(normalized(ctx['text']).count(normalized(r['evidence']['excerpt'])) == 1, 'invalid_baseline')
        approved[url] = b
    sources = []; observations = {}
    for code, guidance in groups.items():
        p = PROFILES[code]; url = p['url']; c = current[url]; b = approved.get(url)
        context = None; reason = 'capture_failed'
        if c['status'] == 'success':
            try:
                context = inspect_html(c['html'], p['heading'])
                context_value(context, p['heading'])
                counts = [normalized(context['text']).count(normalized(r['evidence']['excerpt'])) for r in guidance]
                if any(n > 1 for n in counts): reason = 'excerpt_ambiguous'
                elif any(n == 0 for n in counts): reason = 'excerpt_missing'
                elif b is None: reason = 'context_not_reviewed'
                elif digest(context) != b['context_hash']: reason = 'context_changed'
                else: reason = 'matching_reviewed_context'
            except SourceExtractionError as error:
                reason = str(error)
        sources.append({'source_url': url, 'profile_id': f'{PROFILE_VERSION}:{code}',
            'guidance_hashes': {r['id']: digest(r) for r in guidance}, 'checked_at': c['checked_at'],
            'reason': reason, 'context': context, 'context_hash': digest(context) if context else None,
            'baseline_context': b['context'] if b else None, 'baseline_context_hash': b['context_hash'] if b else None,
            'baseline_reviewed_at': b['reviewed_at'] if b else None})
        for r in guidance:
            status = 'observed' if reason == 'matching_reviewed_context' else 'missing' if reason == 'excerpt_missing' else 'failed'
            observations[r['id']] = {'guidance_id': r['id'], 'guidance_hash': digest(r), 'source_url': url,
                'checked_at': c['checked_at'], 'status': status,
                'excerpt': r['evidence']['excerpt'] if status == 'observed' else None}
    result = {'schema_version': 1, 'observations': [observations[r['id']] for r in records],
              'sources': sources, 'network_performed': False, 'publication_performed': False}
    require(len(canonical(result)) <= MAX_RESULT_BYTES, 'source_extraction_too_large')
    return copy.deepcopy(result)
