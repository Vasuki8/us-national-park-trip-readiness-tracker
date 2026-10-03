"""Pure NPS /parks normalization; no transport, credentials, persistence or publication.

Callers inject a scoped ``fetch_page(0)``. Raise ProfileCollectionError for known
transport failures; TimeoutError and OSError also produce a generic failed
attempt. ProfileError from fetch quarantines a known response refusal. Other
transport exceptions propagate as programming errors.
ProfileError contains a fixed validation code, never provider bodies or secrets.
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
PROFILE_MAX_AGE = timedelta(hours=168)
SNAPSHOT_FIELDS = {
    'schema_version', 'park_code', 'provider', 'source_url', 'collection_status',
    'coverage_status', 'last_checked_at', 'last_successful_fetch_at',
    'source_issued_at', 'source_updated_at', 'published_at', 'profile', 'error_code',
}
SEMANTIC_FIELDS = (
    'id', 'park_code', 'full_name', 'url', 'description', 'seasonal_weather',
    'activity_categories', 'activity_scope',
)
PROFILE_FIELDS = set(SEMANTIC_FIELDS) | {
    'source_updated_at', 'observed_first_at', 'observed_changed_at',
    'content_hash', 'hash_scope',
}


class ProfileError(ValueError):
    """An invalid snapshot or provider response, identified by a safe fixed code."""


class ProfileCollectionError(RuntimeError):
    """An explicitly classified transport failure; its message is never retained."""


def _require(condition: bool, code: str = 'invalid_profile') -> None:
    if not condition:
        raise ProfileError(code)


def _pilot(value: object) -> str:
    _require(isinstance(value, str) and value in PILOT_CODES, 'invalid_park_code')
    return value


def _instant(value: object):
    try:
        return instant(value)
    except HistoryError:
        raise ProfileError('invalid_timestamp') from None


def _canonical(value: object) -> bytes:
    try:
        return canonical(value)
    except HistoryError:
        raise ProfileError('invalid_profile_encoding') from None


def _hash(profile: dict) -> str:
    try:
        return digest({field: profile[field] for field in SEMANTIC_FIELDS})
    except HistoryError:
        raise ProfileError('invalid_profile_encoding') from None


def _text(value: object, *, empty: bool = False, identifier: bool = False) -> None:
    _require(isinstance(value, str) and len(value) <= (256 if identifier else 65536)
             and (empty or bool(value.strip())), 'invalid_text')
    if identifier:
        _require(re.search(r'[\x00-\x1f\x7f]', value) is None, 'invalid_identifier')


def _optional_text(value: object) -> None:
    if value is not None:
        _text(value, empty=True)


def _official_url(value: object, code: str) -> None:
    _text(value)
    _require(re.search(r'[\x00-\x20\x7f\\]', value) is None, 'invalid_official_url')
    try:
        url = urlsplit(value)
        _require(url.scheme == 'https' and (url.hostname or '').lower() in ('nps.gov', 'www.nps.gov')
                 and not url.username and not url.password and url.port in (None, 443), 'invalid_official_url')
        path = unquote(url.path)
        comparison_path = path.removesuffix('/') if path != '/' else path
        _require(path.startswith(f'/{code}/') or path == f'/{code}', 'cross_park_url')
        _require(posixpath.normpath(path) == comparison_path and not path.startswith('//')
                 and re.search(r'[\x00-\x20\x7f\\%]', path) is None, 'invalid_official_url')
        _require(re.search(r'api.?key|token|secret', unquote(url.query + url.fragment), re.I) is None,
                 'invalid_official_url')
    except ValueError:
        raise ProfileError('invalid_official_url') from None


def _categories(value: object) -> None:
    if value is None:
        return
    _require(isinstance(value, list) and len(value) <= 1000, 'invalid_categories')
    seen = set()
    for category in value:
        _require(isinstance(category, dict) and set(category) == {'id', 'name'}, 'invalid_categories')
        _text(category['id'], identifier=True)
        _text(category['name'])
        _require(category['id'] not in seen, 'duplicate_category')
        seen.add(category['id'])
    _require([item['id'] for item in value] == sorted(seen), 'unsorted_categories')


def _validate_record(profile: object, code: str, successful) -> None:
    _require(isinstance(profile, dict) and set(profile) == PROFILE_FIELDS)
    _text(profile['id'], identifier=True)
    _text(profile['full_name'])
    _require(profile['park_code'] == code, 'cross_park_profile')
    _official_url(profile['url'], code)
    _optional_text(profile['description'])
    weather = profile['seasonal_weather']
    if weather is not None:
        _require(isinstance(weather, dict) and set(weather) == {'kind', 'text'}
                 and weather['kind'] == 'seasonal_context', 'invalid_seasonal_context')
        _text(weather['text'], empty=True)
    _require(profile['activity_scope'] == 'categories_only', 'invalid_activity_scope')
    _categories(profile['activity_categories'])
    _require(profile['source_updated_at'] is None, 'unsupported_source_time')
    _require(profile['hash_scope'] == 'normalized_record', 'invalid_hash_scope')
    _require(profile['content_hash'] == _hash(profile), 'profile_hash_mismatch')
    first, changed = _instant(profile['observed_first_at']), _instant(profile['observed_changed_at'])
    _require(first <= changed <= successful, 'incoherent_observation_clock')


def initial_profile(park_code: str) -> dict:
    """Return an uncollected, unknown profile for exactly one supported pilot."""
    code = _pilot(park_code)
    return {
        'schema_version': 1, 'park_code': code, 'provider': 'NPS',
        'source_url': f'https://developer.nps.gov/api/v1/parks?parkCode={code}',
        'collection_status': 'never_checked', 'coverage_status': 'not_collected',
        'last_checked_at': None, 'last_successful_fetch_at': None,
        'source_issued_at': None, 'source_updated_at': None, 'published_at': None,
        'profile': None, 'error_code': None,
    }


def validate_profile(snapshot: dict) -> dict:
    """Validate the complete source-specific schema, returning a defensive copy.

    Unknown fields, invented publisher clocks and incoherent states are refused.
    Unlike an archive observation, the initial uncollected state is accepted.
    """
    _require(isinstance(snapshot, dict) and set(snapshot) == SNAPSHOT_FIELDS)
    _require(type(snapshot['schema_version']) is int and snapshot['schema_version'] == 1, 'invalid_schema')
    code = _pilot(snapshot['park_code'])
    _require(snapshot['provider'] == 'NPS' and snapshot['source_url'] ==
             f'https://developer.nps.gov/api/v1/parks?parkCode={code}', 'invalid_source')
    _require(all(snapshot[field] is None for field in ('source_issued_at', 'source_updated_at', 'published_at')),
             'unsupported_source_or_publication_time')
    status = snapshot['collection_status']
    _require(isinstance(status, str) and status in ('never_checked', 'success', 'failed', 'quarantined'), 'invalid_state')
    if status == 'never_checked':
        _require(snapshot['coverage_status'] == 'not_collected' and snapshot['error_code'] is None
                 and snapshot['last_checked_at'] is None and snapshot['last_successful_fetch_at'] is None
                 and snapshot['profile'] is None, 'incoherent_initial_state')
    else:
        expected_error = {'success': None, 'failed': 'provider_request_failed',
                          'quarantined': 'response_requires_review'}[status]
        _require(snapshot['error_code'] == expected_error and snapshot['coverage_status'] ==
                 ('checked_profile_only' if status == 'success' else 'incomplete'), 'incoherent_state')
        checked = _instant(snapshot['last_checked_at'])
        success_value = snapshot['last_successful_fetch_at']
        successful = None if success_value is None else _instant(success_value)
        _require(successful is None or successful <= checked, 'incoherent_check_clock')
        _require((snapshot['profile'] is None) == (successful is None), 'missing_success_evidence')
        if status == 'success':
            _require(successful is not None and success_value == snapshot['last_checked_at'], 'incoherent_success_clock')
        if snapshot['profile'] is not None:
            _validate_record(snapshot['profile'], code, successful)
    _canonical(snapshot)
    return copy.deepcopy(snapshot)


def _count(value: object) -> int:
    _require(type(value) is int or (isinstance(value, str) and re.fullmatch(r'[0-9]{1,8}', value) is not None),
             'invalid_count')
    return int(value)


def _normalize(payload: object, code: str, now: str, previous: dict | None) -> dict:
    _require(isinstance(payload, dict) and isinstance(payload.get('data'), list), 'invalid_response')
    _require(_count(payload.get('total')) == 1 and _count(payload.get('start')) == 0
             and len(payload['data']) == 1, 'incomplete_scoped_profile')
    raw = payload['data'][0]
    _require(isinstance(raw, dict), 'invalid_response')
    _require(raw.get('parkCode') == code, 'cross_park_profile')
    _text(raw.get('id'), identifier=True)
    _text(raw.get('fullName'))
    _official_url(raw.get('url'), code)
    description, weather_text = raw.get('description'), raw.get('weatherInfo')
    _optional_text(description)
    _optional_text(weather_text)
    categories = raw.get('activities')
    if categories is not None:
        _require(isinstance(categories, list) and len(categories) <= 1000, 'invalid_categories')
        normalized = []
        for item in categories:
            _require(isinstance(item, dict), 'invalid_categories')
            _text(item.get('id'), identifier=True)
            _text(item.get('name'))
            normalized.append({'id': item['id'], 'name': item['name']})
        categories = sorted(normalized, key=lambda item: item['id'])
        _categories(categories)
    profile = {
        'id': raw['id'], 'park_code': code, 'full_name': raw['fullName'], 'url': raw['url'],
        'description': description,
        'seasonal_weather': None if weather_text is None else {'kind': 'seasonal_context', 'text': weather_text},
        'activity_categories': categories, 'activity_scope': 'categories_only', 'source_updated_at': None,
        'observed_first_at': now, 'observed_changed_at': now, 'hash_scope': 'normalized_record',
    }
    profile['content_hash'] = _hash(profile)
    if previous is not None and previous['id'] == profile['id']:
        profile['observed_first_at'] = previous['observed_first_at']
        if previous['content_hash'] == profile['content_hash']:
            profile['observed_changed_at'] = previous['observed_changed_at']
    return profile


def _checked_now(snapshot: dict, now: str):
    current = _instant(now)
    if snapshot['last_checked_at'] is not None:
        _require(_instant(snapshot['last_checked_at']) <= current, 'collection_clock_rewind')
    return current


def collect_profile(park_code: str, previous: dict, now: str, fetch_page: Callable[[int], dict]) -> dict:
    """Validate a single scoped response or retain accepted evidence on failure.

    All previous evidence and clocks are validated before transport. Known
    transport failures and response refusals are caught; unexpected exceptions
    propagate. Rejected payloads and exception messages are never copied into
    the returned snapshot.
    """
    code = _pilot(park_code)
    result = validate_profile(previous)
    _require(result['park_code'] == code, 'cross_park_profile')
    _checked_now(result, now)
    _require(callable(fetch_page), 'invalid_transport')
    result['last_checked_at'] = now
    try:
        payload = fetch_page(0)
    except ProfileError:
        result.update(collection_status='quarantined',
                      coverage_status='incomplete', error_code='response_requires_review')
        return result
    except (ProfileCollectionError, TimeoutError, OSError):
        result.update(collection_status='failed', coverage_status='incomplete', error_code='provider_request_failed')
        return result
    try:
        profile = _normalize(payload, code, now, result['profile'])
        candidate = {**result, 'collection_status': 'success', 'coverage_status': 'checked_profile_only',
                     'last_successful_fetch_at': now, 'profile': profile, 'error_code': None}
        return validate_profile(candidate)
    except ProfileError:
        # Retain the copy validated before transport; caller state may have changed.
        result.update(collection_status='quarantined',
                      coverage_status='incomplete', error_code='response_requires_review')
        return result


def profile_freshness(snapshot: dict, now: str) -> str:
    """Return not_collected, failed, quarantined, fresh or stale.

    The latest failed/quarantined attempt takes precedence over age; retained
    last-good evidence remains dated by last_successful_fetch_at. Successful
    profiles expire at exactly 168 hours. Future evidence is refused.
    """
    validated = validate_profile(snapshot)
    current = _checked_now(validated, now)
    status = validated['collection_status']
    if status == 'never_checked':
        return 'not_collected'
    if status != 'success':
        return status
    return 'stale' if current - _instant(validated['last_successful_fetch_at']) >= PROFILE_MAX_AGE else 'fresh'
