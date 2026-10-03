"""Pure NPS /thingstodo normalization; no transport, persistence or publication.

Inject fetch_page(start) for one park. Classified transport failures retain the
last good inventory; response refusals quarantine the entire candidate. Provider
bodies and exception messages are never retained. Source HTML remains untrusted
text, and a related park establishes attribution rather than physical location.
"""
from __future__ import annotations

import copy
import posixpath
import re
from datetime import timedelta
from typing import Callable
from urllib.parse import unquote, urlsplit

from .history_model import HistoryError, canonical, digest, instant


PILOT_CODES = ('yose', 'romo', 'yell', 'zion', 'grca')
ACTIVITY_MAX_AGE = timedelta(hours=168)
MAX_RECORDS = 5000
MAX_PAGES = 100
MAX_RECORD_BYTES = 256 * 1024
MAX_SNAPSHOT_BYTES = 8 * 1024 * 1024
TEXT_FIELDS = {
    'description': 'shortDescription', 'long_description': 'longDescription',
    'location': 'location', 'location_description': 'locationDescription',
    'duration': 'duration', 'duration_description': 'durationDescription',
    'season_description': 'seasonDescription',
    'accessibility_information': 'accessibilityInformation',
    'activity_description': 'activityDescription', 'fee_description': 'feeDescription',
    'reservation_description': 'reservationDescription', 'pets_description': 'petsDescription',
    'age': 'age', 'age_description': 'ageDescription',
    'time_of_day_description': 'timeOfDayDescription', 'credit': 'credit',
}
FLAG_FIELDS = {'fees_apply': 'doFeesApply', 'reservation_required': 'isReservationRequired',
               'pets_permitted': 'arePetsPermitted'}
RELATION_FIELDS = {'park_code', 'full_name', 'url', 'states', 'designation', 'name'}
SEMANTIC_FIELDS = (
    'id', 'park_code', 'title', 'url', *TEXT_FIELDS, *FLAG_FIELDS,
    'pets_permitted_with_restrictions', 'seasons', 'times_of_day',
    'activity_categories', 'related_parks', 'geographic_relationship',
    'responsible_agency', 'difficulty', 'permit_required',
)
RECORD_FIELDS = set(SEMANTIC_FIELDS) | {
    'source_updated_at', 'observed_first_at', 'observed_changed_at', 'content_hash', 'hash_scope',
}
SNAPSHOT_FIELDS = {
    'schema_version', 'park_code', 'provider', 'source_url', 'collection_status',
    'coverage_status', 'last_checked_at', 'last_successful_fetch_at',
    'source_issued_at', 'source_updated_at', 'published_at', 'records', 'error_code',
}


class ActivityError(ValueError):
    """A safe fixed validation code, never provider text or credentials."""


class ActivityCollectionError(RuntimeError):
    """An explicitly classified transport failure; its message is not retained."""


def _require(condition: bool, code: str = 'invalid_activity') -> None:
    if not condition:
        raise ActivityError(code)


def _pilot(value: object) -> str:
    _require(isinstance(value, str) and value in PILOT_CODES, 'invalid_park_code')
    return value


def _instant(value: object):
    try:
        return instant(value)
    except HistoryError:
        raise ActivityError('invalid_timestamp') from None


def _canonical(value: object) -> bytes:
    try:
        return canonical(value)
    except HistoryError:
        raise ActivityError('invalid_activity_encoding') from None


def _hash(record: dict) -> str:
    try:
        return digest({field: record[field] for field in SEMANTIC_FIELDS})
    except HistoryError:
        raise ActivityError('invalid_activity_encoding') from None


def _text(value: object, *, empty: bool = False, identifier: bool = False) -> None:
    _require(isinstance(value, str) and len(value) <= (256 if identifier else 65536)
             and (empty or bool(value.strip())), 'invalid_text')
    if identifier:
        _require(re.search(r'[\x00-\x1f\x7f]', value) is None, 'invalid_identifier')


def _optional_text(value: object) -> None:
    if value is not None:
        _text(value, empty=True)


def _official_url(value: object, codes: set[str], *, global_activity: bool = False) -> None:
    _text(value)
    _require(re.search(r'[\x00-\x20\x7f\\]', value) is None, 'invalid_official_url')
    try:
        url = urlsplit(value)
        _require(url.scheme == 'https' and (url.hostname or '').lower() in ('nps.gov', 'www.nps.gov')
                 and not url.username and not url.password and url.port in (None, 443), 'invalid_official_url')
        path = unquote(url.path)
        comparison = path.removesuffix('/') if path != '/' else path
        _require(posixpath.normpath(path) == comparison and not path.startswith('//')
                 and re.search(r'[\x00-\x20\x7f\\%]', path) is None, 'invalid_official_url')
        _require(any(path == f'/{code}' or path.startswith(f'/{code}/') for code in codes)
                 or (global_activity and path.startswith('/thingstodo/')), 'unrelated_activity_url')
        _require(re.search(r'api.?key|token|secret', unquote(url.query + url.fragment), re.I) is None,
                 'invalid_official_url')
    except ValueError:
        raise ActivityError('invalid_official_url') from None


def _flag(value: object) -> bool | None:
    if value is None or value == '':
        return None
    if type(value) is bool:
        return value
    _require(isinstance(value, str) and value in ('true', 'false'), 'invalid_flag')
    return value == 'true'


def _strings(value: object) -> None:
    if value is None:
        return
    _require(isinstance(value, list) and len(value) <= 1000, 'invalid_list')
    for item in value:
        _text(item)
    _require(value == sorted(set(value)) and len(value) == len(set(value)), 'invalid_list_order')


def _categories(value: object) -> None:
    if value is None:
        return
    _require(isinstance(value, list) and len(value) <= 1000, 'invalid_categories')
    seen = set()
    for item in value:
        _require(isinstance(item, dict) and set(item) == {'id', 'name'}, 'invalid_categories')
        _text(item['id'], identifier=True)
        _text(item['name'])
        _require(item['id'] not in seen, 'duplicate_category')
        seen.add(item['id'])
    _require([item['id'] for item in value] == sorted(seen), 'unsorted_categories')


def _relations(value: object, code: str) -> set[str]:
    _require(isinstance(value, list) and 0 < len(value) <= 1000, 'invalid_relations')
    seen = set()
    for item in value:
        _require(isinstance(item, dict) and set(item) == RELATION_FIELDS, 'invalid_relations')
        related = item['park_code']
        _require(isinstance(related, str) and re.fullmatch(r'[a-z]{4}', related) is not None,
                 'invalid_related_park')
        _require(related not in seen, 'duplicate_related_park')
        seen.add(related)
        for field in ('full_name', 'states', 'designation', 'name'):
            _optional_text(item[field])
        if item['url'] is not None:
            _official_url(item['url'], {related})
    _require(code in seen, 'missing_park_relationship')
    _require([item['park_code'] for item in value] == sorted(seen), 'unsorted_relations')
    return seen


def _validate_record(record: object, code: str, successful) -> int:
    _require(isinstance(record, dict) and set(record) == RECORD_FIELDS)
    _text(record['id'], identifier=True)
    _text(record['title'])
    _require(record['park_code'] == code, 'cross_park_activity')
    related = _relations(record['related_parks'], code)
    _official_url(record['url'], related, global_activity=True)
    for field in TEXT_FIELDS:
        _optional_text(record[field])
    for field in (*FLAG_FIELDS, 'pets_permitted_with_restrictions'):
        _require(record[field] is None or type(record[field]) is bool, 'invalid_flag')
    for field in ('seasons', 'times_of_day'):
        _strings(record[field])
    _categories(record['activity_categories'])
    _require(record['geographic_relationship'] == 'unconfirmed'
             and all(record[field] is None for field in ('responsible_agency', 'difficulty', 'permit_required')),
             'unsupported_activity_interpretation')
    _require(record['source_updated_at'] is None, 'unsupported_source_time')
    _require(record['hash_scope'] == 'normalized_record', 'invalid_hash_scope')
    size = len(_canonical(record))
    _require(size <= MAX_RECORD_BYTES, 'activity_too_large')
    _require(record['content_hash'] == _hash(record), 'activity_hash_mismatch')
    first, changed = _instant(record['observed_first_at']), _instant(record['observed_changed_at'])
    _require(first <= changed <= successful, 'incoherent_observation_clock')
    return size


def initial_activities(park_code: str) -> dict:
    """Return an uncollected, unknown inventory for one supported pilot park."""
    code = _pilot(park_code)
    return {
        'schema_version': 1, 'park_code': code, 'provider': 'NPS',
        'source_url': f'https://developer.nps.gov/api/v1/thingstodo?parkCode={code}',
        'collection_status': 'never_checked', 'coverage_status': 'not_collected',
        'last_checked_at': None, 'last_successful_fetch_at': None,
        'source_issued_at': None, 'source_updated_at': None, 'published_at': None,
        'records': [], 'error_code': None,
    }


def validate_activities(snapshot: dict) -> dict:
    """Validate the complete source-specific schema and return a defensive copy."""
    _require(isinstance(snapshot, dict) and set(snapshot) == SNAPSHOT_FIELDS)
    _require(type(snapshot['schema_version']) is int and snapshot['schema_version'] == 1, 'invalid_schema')
    code = _pilot(snapshot['park_code'])
    _require(snapshot['provider'] == 'NPS' and snapshot['source_url'] ==
             f'https://developer.nps.gov/api/v1/thingstodo?parkCode={code}', 'invalid_source')
    _require(all(snapshot[field] is None for field in ('source_issued_at', 'source_updated_at', 'published_at')),
             'unsupported_source_or_publication_time')
    _require(isinstance(snapshot['records'], list) and len(snapshot['records']) <= MAX_RECORDS,
             'invalid_inventory')
    status = snapshot['collection_status']
    _require(isinstance(status, str) and status in ('never_checked', 'success', 'failed', 'quarantined'),
             'invalid_state')
    if status == 'never_checked':
        _require(snapshot['coverage_status'] == 'not_collected' and snapshot['error_code'] is None
                 and snapshot['last_checked_at'] is None and snapshot['last_successful_fetch_at'] is None
                 and not snapshot['records'], 'incoherent_initial_state')
    else:
        expected_error = {'success': None, 'failed': 'provider_request_failed',
                          'quarantined': 'response_requires_review'}[status]
        _require(snapshot['error_code'] == expected_error and snapshot['coverage_status'] ==
                 ('checked_activity_feed_only' if status == 'success' else 'incomplete'), 'incoherent_state')
        checked = _instant(snapshot['last_checked_at'])
        success_value = snapshot['last_successful_fetch_at']
        successful = None if success_value is None else _instant(success_value)
        _require(successful is None or successful <= checked, 'incoherent_check_clock')
        _require(successful is not None or not snapshot['records'], 'missing_success_evidence')
        if status == 'success':
            _require(successful is not None and success_value == snapshot['last_checked_at'],
                     'incoherent_success_clock')
        seen = set()
        size = len(_canonical({**snapshot, 'records': []}))
        for record in snapshot['records']:
            size += _validate_record(record, code, successful) + (1 if seen else 0)
            _require(size <= MAX_SNAPSHOT_BYTES, 'inventory_too_large')
            _require(record['id'] not in seen, 'duplicate_activity')
            seen.add(record['id'])
        _require([record['id'] for record in snapshot['records']] == sorted(seen), 'unsorted_inventory')
    _require(len(_canonical(snapshot)) <= MAX_SNAPSHOT_BYTES, 'inventory_too_large')
    return copy.deepcopy(snapshot)


def _count(value: object) -> int:
    _require(type(value) is int or (isinstance(value, str) and re.fullmatch(r'[0-9]{1,8}', value) is not None),
             'invalid_count')
    count = int(value)
    _require(count >= 0, 'invalid_count')
    return count


def _normalize(raw: object, code: str, now: str, previous: dict[str, dict]) -> dict:
    _require(isinstance(raw, dict), 'invalid_response')
    _text(raw.get('id'), identifier=True)
    _text(raw.get('title'))
    relations = raw.get('relatedParks')
    _require(isinstance(relations, list) and 0 < len(relations) <= 1000, 'invalid_relations')
    related = []
    for item in relations:
        _require(isinstance(item, dict), 'invalid_relations')
        _require(isinstance(item.get('parkCode'), str), 'invalid_related_park')
        related.append({'park_code': item['parkCode'], 'full_name': item.get('fullName'),
                        **{field: item.get(field) for field in ('url', 'states', 'designation', 'name')}})
    related.sort(key=lambda item: item['park_code'])
    record = {
        'id': raw['id'], 'park_code': code, 'title': raw['title'], 'url': raw.get('url'),
        **{field: raw.get(source) for field, source in TEXT_FIELDS.items()},
        **{field: _flag(raw.get(source)) for field, source in FLAG_FIELDS.items()},
        'related_parks': related, 'geographic_relationship': 'unconfirmed',
        'responsible_agency': None, 'difficulty': None, 'permit_required': None,
        'source_updated_at': None, 'observed_first_at': now, 'observed_changed_at': now,
        'hash_scope': 'normalized_record',
    }
    aliases = ('arePetsPermittedWithRestrictions', 'arePetsPermittedwithRestrictions')
    flags = [_flag(raw[key]) for key in aliases if key in raw]
    _require(not flags or all(value == flags[0] for value in flags), 'conflicting_pet_flags')
    record['pets_permitted_with_restrictions'] = flags[0] if flags else None
    for field, source in (('seasons', 'season'), ('times_of_day', 'timeOfDay')):
        items = raw.get(source)
        _require(items is None or (isinstance(items, list) and len(items) <= 1000), 'invalid_list')
        if items is not None:
            for item in items:
                _text(item)
        record[field] = None if items is None else sorted(items)
    categories = raw.get('activities')
    _require(categories is None or (isinstance(categories, list) and len(categories) <= 1000),
             'invalid_categories')
    normalized = None if categories is None else []
    for item in categories or []:
        _require(isinstance(item, dict), 'invalid_categories')
        _text(item.get('id'), identifier=True)
        normalized.append({'id': item['id'], 'name': item.get('name')})
    record['activity_categories'] = None if normalized is None else sorted(normalized, key=lambda item: item['id'])
    # Check the serialized bound before hashing an oversized candidate.
    record['content_hash'] = '0' * 64
    _require(len(_canonical(record)) <= MAX_RECORD_BYTES, 'activity_too_large')
    record['content_hash'] = _hash(record)
    old = previous.get(record['id'])
    if old is not None:
        record['observed_first_at'] = old['observed_first_at']
        if old['content_hash'] == record['content_hash']:
            record['observed_changed_at'] = old['observed_changed_at']
    _validate_record(record, code, _instant(now))
    return record


def collect_activities(park_code: str, previous: dict, now: str, fetch_page: Callable[[int], dict]) -> dict:
    """Accept a complete bounded feed or retain the validated last good inventory.

    Attempts must strictly advance the check clock. Every page must agree on
    total, offset and IDs; empty or severely reduced established feeds need
    review. All partial candidate data is discarded on a refused/failed page.
    """
    code = _pilot(park_code)
    result = validate_activities(previous)
    _require(result['park_code'] == code, 'cross_park_activity')
    current = _instant(now)
    _require(result['last_checked_at'] is None or _instant(result['last_checked_at']) < current,
             'collection_clock_not_advanced')
    _require(callable(fetch_page), 'invalid_transport')
    result['last_checked_at'] = now
    # Refuse before requests if retaining all accepted evidence could no longer
    # fit with either degraded envelope. Never trim records to fit a failure.
    for status, error in (('failed', 'provider_request_failed'), ('quarantined', 'response_requires_review')):
        fallback = {**result, 'collection_status': status, 'coverage_status': 'incomplete', 'error_code': error}
        _require(len(_canonical(fallback)) <= MAX_SNAPSHOT_BYTES, 'insufficient_failure_capacity')
    old = {record['id']: record for record in result['records']}
    records = {}
    total = None
    offset = 0
    candidate = {**result, 'collection_status': 'success', 'coverage_status': 'checked_activity_feed_only',
                 'last_successful_fetch_at': now, 'records': [], 'error_code': None}
    size = len(_canonical(candidate))
    try:
        for _ in range(MAX_PAGES):
            payload = fetch_page(offset)
            _require(isinstance(payload, dict) and isinstance(payload.get('data'), list), 'invalid_response')
            reported = _count(payload.get('total'))
            _require(reported <= MAX_RECORDS and _count(payload.get('start')) == offset, 'invalid_pagination')
            _require(total is None or total == reported, 'changed_total')
            total = reported
            data = payload['data']
            _require(len(data) <= total - offset and (data or offset == total), 'incomplete_inventory')
            if 'limit' in payload:
                limit = _count(payload['limit'])
                _require(0 < limit <= MAX_RECORDS and len(data) <= limit, 'invalid_page_limit')
            for raw in data:
                record = _normalize(raw, code, now, old)
                _require(record['id'] not in records, 'duplicate_activity')
                size += len(_canonical(record)) + (1 if records else 0)
                _require(size <= MAX_SNAPSHOT_BYTES, 'inventory_too_large')
                records[record['id']] = record
            offset += len(data)
            if offset == total:
                break
        _require(offset == total, 'pagination_limit')
        _require(len(records) * 2 >= len(old), 'inventory_drop_requires_review')
        candidate['records'] = [records[key] for key in sorted(records)]
        return validate_activities(candidate)
    except ActivityError:
        result.update(collection_status='quarantined', coverage_status='incomplete', error_code='response_requires_review')
    except (ActivityCollectionError, TimeoutError, OSError):
        result.update(collection_status='failed', coverage_status='incomplete', error_code='provider_request_failed')
    return result


def activity_freshness(snapshot: dict, now: str) -> str:
    """Return the current state, expiring successful inventories at 168 hours."""
    validated = validate_activities(snapshot)
    current = _instant(now)
    _require(validated['last_checked_at'] is None or _instant(validated['last_checked_at']) <= current,
             'freshness_clock_rewind')
    status = validated['collection_status']
    if status == 'never_checked':
        return 'not_collected'
    if status != 'success':
        return status
    return 'stale' if current - _instant(validated['last_successful_fetch_at']) >= ACTIVITY_MAX_AGE else 'fresh'
