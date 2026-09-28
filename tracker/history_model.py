"""Strict normalized-alert contracts and observation-only semantic differences."""
from __future__ import annotations
import copy
import hashlib
import json
import posixpath
import re
from datetime import datetime, timezone
from urllib.parse import unquote, urlsplit

MAX_OBJECT_BYTES = 10 * 1024 * 1024
SEMANTIC_FIELDS = ('category', 'description', 'id', 'title', 'url')
SNAPSHOT_FIELDS = {'schema_version', 'park_code', 'provider', 'source_url', 'collection_status', 'coverage_status', 'last_checked_at', 'last_successful_fetch_at', 'source_updated_at', 'published_at', 'records', 'error_code'}
RECORD_FIELDS = set(SEMANTIC_FIELDS) | {'park_code', 'area_id', 'scope_status', 'effective_from', 'effective_to', 'source_updated_at', 'observed_first_at', 'observed_changed_at', 'content_hash', 'hash_scope', 'evidence_excerpt'}
TIMESTAMP = re.compile(r'\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,6})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)')

class HistoryError(ValueError):
    """Safe failure code only; never embed input text or credentials."""

def require(condition: bool, code: str = 'invalid_snapshot') -> None:
    if not condition:
        raise HistoryError(code)

def canonical(value: object) -> bytes:
    try:
        data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise HistoryError('invalid_json') from None
    require(len(data) <= MAX_OBJECT_BYTES, 'object_too_large')
    return data

def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()

def parse_json(data: bytes) -> object:
    require(len(data) <= MAX_OBJECT_BYTES, 'object_too_large')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate_json_key')
            result[key] = value
        return result
    def constant(_value):
        raise HistoryError('invalid_json_number')
    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, ValueError, RecursionError):
        raise HistoryError('invalid_json') from None

def park_code(value: object) -> str:
    require(isinstance(value, str) and re.fullmatch('[a-z]{4}', value) is not None, 'invalid_park_code')
    return value

def instant(value: object) -> datetime:
    require(isinstance(value, str) and TIMESTAMP.fullmatch(value) is not None, 'invalid_timestamp')
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise HistoryError('invalid_timestamp') from None

def _text(value: object, *, empty: bool = False) -> None:
    require(isinstance(value, str) and len(value) <= 65536 and (empty or bool(value.strip())))

def _source(value: object, code: str) -> None:
    _text(value)
    require(not re.search(r'[\x00-\x20\x7f\\]', value), 'invalid_source')
    try:
        url = urlsplit(value)
        require(url.scheme == 'https' and url.hostname in {'www.nps.gov', 'nps.gov', 'home.nps.gov'} and not url.username and not url.password and url.port in (None, 443), 'invalid_source')
        path = unquote(url.path)
        require(path.startswith(f'/{code}/') and posixpath.normpath(path) == path and '\\' not in path, 'invalid_source')
        require(not re.search(r'api.?key|token|secret', unquote(url.query + url.fragment), re.I), 'invalid_source')
    except ValueError:
        raise HistoryError('invalid_source') from None

def validate_snapshot(value: object) -> dict:
    """Accept only schema-v1 collector output; return a sorted defensive copy."""
    require(isinstance(value, dict) and set(value) == SNAPSHOT_FIELDS)
    require(type(value['schema_version']) is int and value['schema_version'] == 1)
    code = park_code(value['park_code'])
    require(value['provider'] == 'NPS')
    require(value['source_url'] == f'https://developer.nps.gov/api/v1/alerts?parkCode={code}', 'invalid_source')
    status = value['collection_status']
    require(status in ('success', 'failed', 'quarantined'), 'not_a_collected_observation')
    require(value['coverage_status'] == ('checked_feed_only' if status == 'success' else 'incomplete'))
    require(value['error_code'] == {'success': None, 'failed': 'provider_request_failed', 'quarantined': 'response_requires_review'}[status])
    require(value['source_updated_at'] is None and value['published_at'] is None, 'unsupported_source_or_publication_time')
    checked = instant(value['last_checked_at'])
    successful = None if value['last_successful_fetch_at'] is None else instant(value['last_successful_fetch_at'])
    require(successful is None or successful <= checked, 'incoherent_clock')
    if status == 'success':
        require(value['last_successful_fetch_at'] == value['last_checked_at'], 'incoherent_clock')
    records = value['records']
    require(isinstance(records, list) and len(records) <= 5000)
    require(successful is not None or not records, 'missing_success')
    ids = set()
    for item in records:
        require(isinstance(item, dict) and set(item) == RECORD_FIELDS)
        for key in SEMANTIC_FIELDS:
            _text(item[key], empty=key == 'description')
        require(len(item['id']) <= 256 and not re.search(r'[\x00-\x1f\x7f]', item['id']))
        require(item['id'] not in ids, 'duplicate_record_id'); ids.add(item['id'])
        _source(item['url'], code)
        require(item['park_code'] == code and item['scope_status'] == 'unclassified')
        require(all(item[key] is None for key in ('area_id', 'effective_from', 'effective_to', 'source_updated_at')))
        require(item['hash_scope'] == 'normalized_record')
        require(item['evidence_excerpt'] == item['description'], 'excerpt_mismatch')
        require(item['content_hash'] == digest({key: item[key] for key in SEMANTIC_FIELDS}), 'evidence_hash_mismatch')
        require(instant(item['observed_first_at']) <= instant(item['observed_changed_at']) <= successful, 'incoherent_record_clock')
    canonical(value)  # Encoding and size are checked before any archive write.
    result = copy.deepcopy(value)
    result['records'].sort(key=lambda item: item['id'])
    return result

def compare(previous: dict | None, current: dict) -> dict:
    """Compare observations, not real-world events; failed checks cannot remove data."""
    new = validate_snapshot(current)
    old = None if previous is None else validate_snapshot(previous)
    if old is not None:
        require(old['park_code'] == new['park_code'], 'cross_park_history')
        if new == old:
            return {'comparison': 'duplicate', 'changes': []}
        require(instant(new['last_checked_at']) > instant(old['last_checked_at']), 'replayed_or_conflicting_clock')
    if new['collection_status'] != 'success':
        require(new['last_successful_fetch_at'] == (old['last_successful_fetch_at'] if old else None), 'missing_or_altered_baseline')
        require(new['records'] == (old['records'] if old else []), 'altered_last_good_records')
        return {'comparison': 'not_compared', 'changes': []}
    if old is None or old['last_successful_fetch_at'] is None:
        return {'comparison': 'baseline', 'changes': []}
    before = {item['id']: item for item in old['records']}
    after = {item['id']: item for item in new['records']}
    require(not before or len(after) >= len(before) / 2, 'suspicious_record_drop')
    changes = []
    for identifier in sorted(before.keys() | after.keys()):
        a, b = before.get(identifier), after.get(identifier)
        if b:
            require(b['observed_first_at'] == (a['observed_first_at'] if a else new['last_checked_at']), 'altered_first_observation')
            unchanged = a is not None and a['content_hash'] == b['content_hash']
            require(b['observed_changed_at'] == (a['observed_changed_at'] if unchanged else new['last_checked_at']), 'altered_change_observation')
        if a and b and a['content_hash'] == b['content_hash']:
            continue
        changes.append({'kind': 'added' if a is None else 'removed' if b is None else 'edited', 'record_id': identifier,
                        'before_hash': a['content_hash'] if a else None, 'after_hash': b['content_hash'] if b else None})
    return {'comparison': 'compared', 'changes': changes}
