"""Synthetic normalized snapshots, never examples of current park conditions."""
import copy
import hashlib
import json

T0 = '2026-09-28T10:00:00Z'
T1 = '2026-09-28T12:00:00Z'
T2 = '2026-09-28T14:00:00Z'
T3 = '2026-09-28T16:00:00Z'

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()

def notice(identifier='a', code='yose', now=T0, **changes):
    semantic = dict(id=identifier, title='Synthetic facility notice', description='Synthetic text, not a real closure.', category='Park Closure', url=f'https://www.nps.gov/{code}/test.htm')
    semantic.update(changes)
    return dict(**semantic, park_code=code, area_id=None, scope_status='unclassified', effective_from=None, effective_to=None, source_updated_at=None, observed_first_at=now, observed_changed_at=now, content_hash=digest(semantic), hash_scope='normalized_record', evidence_excerpt=semantic['description'])

def snapshot(records=None, now=T0, code='yose'):
    return dict(schema_version=1, park_code=code, provider='NPS', source_url=f'https://developer.nps.gov/api/v1/alerts?parkCode={code}', collection_status='success', coverage_status='checked_feed_only', last_checked_at=now, last_successful_fetch_at=now, source_updated_at=None, published_at=None, records=[notice(code=code, now=now)] if records is None else records, error_code=None)

def next_snapshot(old, now=T1, records=None, status='success'):
    result = copy.deepcopy(old)
    result['last_checked_at'] = now
    result['collection_status'] = status
    result['coverage_status'] = 'checked_feed_only' if status == 'success' else 'incomplete'
    result['error_code'] = {'success': None, 'failed': 'provider_request_failed', 'quarantined': 'response_requires_review'}[status]
    if status == 'success':
        result['last_successful_fetch_at'] = now
        if records is not None:
            result['records'] = records
    return result
