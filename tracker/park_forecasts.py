"""Pure named-location NWS forecasts; injected requests, no writes or publication.

Known transport failures retain last-good evidence with generic codes. Rejected
payloads and exception text are never copied. Unexpected exceptions propagate.
Location provenance is a validation contract, not geographic/rights approval.
"""
from __future__ import annotations

import copy
import math
import posixpath
import re
from datetime import timedelta
from typing import Callable
from urllib.parse import urlsplit

from .history_model import HistoryError, canonical, digest, instant
from .park_profiles import PILOT_CODES


FORECAST_MAX_AGE = timedelta(hours=6)
MAPPING_MAX_AGE = timedelta(hours=168)
MAX_BYTES = 1024 * 1024
# Leave room for bounded location, current mapping and success/failure metadata.
MAX_RECORD_BYTES = MAX_BYTES - 8192
LOCATION_FIELDS = {'id', 'park_code', 'name', 'latitude', 'longitude',
                   'coordinate_source_url', 'coordinate_checked_at'}
MAPPING_FIELDS = {'source_url', 'grid_id', 'grid_x', 'grid_y', 'forecast_url', 'checked_at'}
PERIOD_FIELDS = {'number', 'name', 'starts_at', 'ends_at', 'is_daytime', 'temperature',
                 'wind_speed', 'wind_direction', 'probability_of_precipitation',
                 'short_forecast', 'detailed_forecast'}
RECORD_FIELDS = {'kind', 'source_url', 'mapping', 'units', 'source_generated_at',
                 'source_updated_at', 'valid_times', 'valid_from', 'valid_to',
                 'periods', 'content_hash', 'hash_scope'}
SNAPSHOT_FIELDS = {'schema_version', 'location', 'provider', 'source_url',
                   'collection_status', 'coverage_status', 'last_checked_at',
                   'last_successful_fetch_at', 'mapping', 'forecast', 'published_at',
                   'error_code', 'error_stage'}
TEMPERATURE_UNITS = ('wmoUnit:degF', 'wmoUnit:degC')
WIND_UNITS = ('wmoUnit:km_h-1', 'wmoUnit:m_s-1', 'wmoUnit:mi_h-1')


class ForecastError(ValueError):
    """Safe fixed validation code, never provider data."""


class ForecastCollectionError(RuntimeError):
    """Caller-classified transport failure; message is never retained."""


def _require(condition: bool, code: str = 'invalid_forecast') -> None:
    if not condition:
        raise ForecastError(code)


def _time(value: object):
    try:
        return instant(value)
    except HistoryError:
        raise ForecastError('invalid_timestamp') from None


def _json(value: object, *, max_bytes: int = MAX_BYTES) -> None:
    try:
        canonical(value, max_bytes=max_bytes)
    except HistoryError:
        raise ForecastError('invalid_encoding_or_size') from None


def _hash(record: dict) -> str:
    try:
        return digest({k: v for k, v in record.items() if k not in ('content_hash', 'hash_scope')},
                      max_bytes=MAX_BYTES)
    except HistoryError:
        raise ForecastError('invalid_encoding_or_size') from None


def _number(value: object) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def _text(value: object, *, limit: int = 65536, empty: bool = True) -> None:
    _require(isinstance(value, str) and len(value) <= limit and (empty or bool(value.strip())), 'invalid_text')
    _require(re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', value) is None, 'invalid_text')


def _optional_text(value: object, limit: int = 65536) -> None:
    if value is not None:
        _text(value, limit=limit)


def _location(value: object) -> dict:
    _require(isinstance(value, dict) and set(value) == LOCATION_FIELDS, 'invalid_location')
    _require(isinstance(value['id'], str) and re.fullmatch(r'[a-z][a-z0-9-]{1,63}', value['id']) is not None,
             'invalid_location_id')
    _require(isinstance(value['park_code'], str) and value['park_code'] in PILOT_CODES, 'invalid_park_code')
    _text(value['name'], limit=256, empty=False)
    _require(_number(value['latitude']) and -90 <= value['latitude'] <= 90
             and _number(value['longitude']) and -180 <= value['longitude'] <= 180, 'invalid_coordinates')
    url = value['coordinate_source_url']
    _require(isinstance(url, str) and len(url) <= 2048 and re.fullmatch(
        rf'https://(?:www\.)?nps\.gov/{value["park_code"]}/[A-Za-z0-9/_.-]+', url) is not None,
        'invalid_coordinate_source')
    path = urlsplit(url).path
    _require(posixpath.normpath(path) == path.removesuffix('/'), 'invalid_coordinate_source')
    _time(value['coordinate_checked_at'])
    _json(value)
    return copy.deepcopy(value)


def _point_url(loc: dict) -> str:
    return f'https://api.weather.gov/points/{loc["latitude"]:.4f},{loc["longitude"]:.4f}'


def _lookup_coordinates(loc: dict) -> tuple[float, float]:
    return float(f'{loc["longitude"]:.4f}'), float(f'{loc["latitude"]:.4f}')


def _mapping(value: object, loc: dict, checked) -> None:
    _require(isinstance(value, dict) and set(value) == MAPPING_FIELDS, 'invalid_mapping')
    _require(value['source_url'] == _point_url(loc), 'point_source_mismatch')
    office, x, y = value['grid_id'], value['grid_x'], value['grid_y']
    _require(isinstance(office, str) and re.fullmatch('[A-Z]{3}', office) is not None
             and type(x) is int and 0 <= x <= 100000 and type(y) is int and 0 <= y <= 100000, 'invalid_grid')
    _require(value['forecast_url'] == f'https://api.weather.gov/gridpoints/{office}/{x},{y}/forecast',
             'untrusted_forecast_url')
    _require(_time(loc['coordinate_checked_at']) <= _time(value['checked_at']) <= checked, 'invalid_mapping_clock')


def _position(value: object) -> None:
    _require(isinstance(value, list) and len(value) == 2 and _number(value[0])
             and _number(value[1]) and -180 <= value[0] <= 180 and -90 <= value[1] <= 90, 'invalid_geometry')


def _discover(payload: object, loc: dict, now: str) -> dict:
    _json(payload)
    _require(isinstance(payload, dict) and payload.get('type') == 'Feature', 'invalid_point_response')
    geometry, props = payload.get('geometry'), payload.get('properties')
    _require(isinstance(geometry, dict) and geometry.get('type') == 'Point'
             and isinstance(props, dict), 'invalid_point_response')
    coords = geometry.get('coordinates'); _position(coords)
    _require(all(abs(a - b) <= 1e-7 for a, b in zip(coords, _lookup_coordinates(loc))), 'point_coordinate_mismatch')
    for source in (payload.get('id'), props.get('@id')):
        _require(source is None or source == _point_url(loc), 'point_source_mismatch')
    result = {'source_url': _point_url(loc), 'grid_id': props.get('gridId'),
              'grid_x': props.get('gridX'), 'grid_y': props.get('gridY'),
              'forecast_url': props.get('forecast'), 'checked_at': now}
    _mapping(result, loc, _time(now))
    return result


def _cross(a, b, p):
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def _on_segment(a, b, p):
    return abs(_cross(a, b, p)) <= 1e-10 and all(
        min(a[i], b[i]) - 1e-10 <= p[i] <= max(a[i], b[i]) + 1e-10 for i in (0, 1))


def _intersects(a, b, c, d):
    return (_cross(a, b, c) * _cross(a, b, d) < 0 and _cross(c, d, a) * _cross(c, d, b) < 0
            or any((_on_segment(a, b, c), _on_segment(a, b, d), _on_segment(c, d, a), _on_segment(c, d, b))))


def _forecast_geometry(geometry: object, loc: dict) -> None:
    _require(isinstance(geometry, dict) and geometry.get('type') == 'Polygon', 'unsupported_forecast_geometry')
    rings = geometry.get('coordinates')
    _require(isinstance(rings, list) and len(rings) == 1 and isinstance(rings[0], list)
             and 4 <= len(rings[0]) <= 100, 'unsupported_forecast_geometry')
    ring = rings[0]
    for pos in ring:
        _position(pos)
    _require(ring[0] == ring[-1], 'unclosed_forecast_geometry')
    edges = list(zip(ring, ring[1:]))
    _require(all(a != b for a, b in edges), 'degenerate_forecast_geometry')
    _require(abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in edges)) > 1e-10, 'degenerate_forecast_geometry')
    for i, (a, b) in enumerate(edges):
        for j in range(i + 2, len(edges)):
            if i == 0 and j == len(edges) - 1:
                continue
            _require(not _intersects(a, b, *edges[j]), 'self_crossing_forecast_geometry')
    target = _lookup_coordinates(loc)
    if any(_on_segment(a, b, target) for a, b in edges):
        return
    inside = False
    for a, b in edges:
        if (a[1] > target[1]) != (b[1] > target[1]):
            if target[0] < a[0] + (target[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
                inside = not inside
    _require(inside, 'forecast_grid_mismatch')


def _interval(value: object) -> tuple[str, str]:
    _require(isinstance(value, str) and len(value) <= 256 and value.count('/') == 1, 'invalid_validity_interval')
    start, end = value.split('/')
    first = _time(start)
    if end.startswith('P'):
        match = re.fullmatch(r'P(?:(\d{1,3})D)?(?:T(?:(\d{1,4})H)?(?:(\d{1,5})M)?(?:(\d{1,6}(?:\.\d{1,6})?)S)?)?', end)
        _require(match is not None and any(v is not None for v in match.groups()), 'unsupported_duration')
        _require('T' not in end or any(v is not None for v in match.groups()[1:]), 'unsupported_duration')
        d, h, m, s = (float(v or 0) for v in match.groups())
        duration = timedelta(days=d, hours=h, minutes=m, seconds=s)
        _require(timedelta(0) < duration <= timedelta(days=8), 'invalid_duration')
        try:
            last = first + duration
        except OverflowError:
            raise ForecastError('invalid_duration') from None
        end = last.isoformat().replace('+00:00', 'Z')
    else:
        last = _time(end)
    _require(timedelta(0) < last - first <= timedelta(days=8), 'invalid_validity_interval')
    return start, end


def _quantity(value: object, units: tuple[str, ...], *, percentage=False) -> None:
    _require(isinstance(value, dict) and set(value) == {'value', 'unit_code'}
             and isinstance(value['unit_code'], str) and value['unit_code'] in units, 'unsupported_unit')
    number = value['value']
    _require(number is None or _number(number), 'invalid_quantity')
    if percentage:
        _require(number is None or 0 <= number <= 100, 'invalid_probability')


def _normalize_quantity(raw: object, units: tuple[str, ...], *, percentage=False):
    if raw is None:
        return None
    _require(isinstance(raw, dict), 'invalid_quantity')
    value = {'value': raw.get('value'), 'unit_code': raw.get('unitCode')}
    _quantity(value, units, percentage=percentage)
    return value


def _validate_period(value: object, number: int, valid_start, valid_end, previous_end) -> None:
    _require(isinstance(value, dict) and set(value) == PERIOD_FIELDS, 'invalid_period')
    _require(type(value['number']) is int and value['number'] == number
             and type(value['is_daytime']) is bool, 'invalid_period_identity')
    start, end = _time(value['starts_at']), _time(value['ends_at'])
    _require(valid_start <= start < end <= valid_end and end - start <= timedelta(hours=24)
             and (previous_end is None or previous_end <= start), 'invalid_period_window')
    _optional_text(value['name'], 256)
    for field in ('short_forecast', 'detailed_forecast'):
        _optional_text(value[field])
    _optional_text(value['wind_direction'], 256)
    if value['temperature'] is not None:
        _quantity(value['temperature'], TEMPERATURE_UNITS)
    if value['probability_of_precipitation'] is not None:
        _quantity(value['probability_of_precipitation'], ('wmoUnit:percent',), percentage=True)
    wind = value['wind_speed']
    if wind is not None:
        _require(isinstance(wind, dict), 'invalid_wind')
        if wind.get('kind') == 'text':
            _require(set(wind) == {'kind', 'text'}, 'invalid_wind')
            _text(wind['text'], limit=256)
        else:
            _require(set(wind) == {'kind', 'value', 'unit_code'} and wind.get('kind') == 'quantity', 'invalid_wind')
            _quantity({'value': wind['value'], 'unit_code': wind['unit_code']}, WIND_UNITS)
            _require(wind['value'] is None or wind['value'] >= 0, 'invalid_wind')


def _normalize_period(raw: object) -> dict:
    _require(isinstance(raw, dict), 'invalid_period')
    temperature = raw.get('temperature')
    if temperature is not None:
        if isinstance(temperature, dict):
            temperature = _normalize_quantity(temperature, TEMPERATURE_UNITS)
        else:
            unit = raw.get('temperatureUnit')
            _require(isinstance(unit, str) and unit in ('F', 'C') and type(temperature) is int, 'invalid_temperature')
            temperature = {'value': temperature, 'unit_code': 'wmoUnit:deg' + unit}
    wind = raw.get('windSpeed')
    if wind is not None:
        wind = ({'kind': 'text', 'text': wind} if isinstance(wind, str)
                else {'kind': 'quantity', **_normalize_quantity(wind, WIND_UNITS)})
    return {'number': raw.get('number'), 'name': raw.get('name'),
            'starts_at': raw.get('startTime'), 'ends_at': raw.get('endTime'),
            'is_daytime': raw.get('isDaytime'), 'temperature': temperature,
            'wind_speed': wind, 'wind_direction': raw.get('windDirection'),
            'probability_of_precipitation': _normalize_quantity(raw.get('probabilityOfPrecipitation'),
                                                               ('wmoUnit:percent',), percentage=True),
            'short_forecast': raw.get('shortForecast'), 'detailed_forecast': raw.get('detailedForecast')}


def _validate_record(value: object, loc: dict, successful) -> None:
    _require(isinstance(value, dict) and set(value) == RECORD_FIELDS, 'invalid_record')
    _json(value, max_bytes=MAX_RECORD_BYTES)
    _require(value['kind'] == 'forecast' and value['units'] == 'us'
             and value['hash_scope'] == 'normalized_forecast', 'unsupported_forecast')
    _mapping(value['mapping'], loc, successful)
    _require(value['source_url'] == value['mapping']['forecast_url'], 'forecast_source_mismatch')
    _require(_time(value['source_updated_at']) <= _time(value['source_generated_at']) <= successful,
             'invalid_source_clock')
    start, end = _interval(value['valid_times'])
    _require((value['valid_from'], value['valid_to']) == (start, end), 'validity_mismatch')
    periods = value['periods']
    _require(isinstance(periods, list) and 1 <= len(periods) <= 32, 'invalid_period_inventory')
    previous_end = None
    for number, period in enumerate(periods, 1):
        _validate_period(period, number, _time(start), _time(end), previous_end)
        previous_end = _time(period['ends_at'])
    _require(value['content_hash'] == _hash(value), 'forecast_hash_mismatch')


def _normalize_forecast(payload: object, loc: dict, mapping: dict, now: str) -> dict:
    _json(payload)
    _require(isinstance(payload, dict) and payload.get('type') == 'Feature'
             and isinstance(payload.get('properties'), dict), 'invalid_response')
    _require(payload.get('id') is None or payload['id'] == mapping['forecast_url'], 'forecast_source_mismatch')
    _forecast_geometry(payload.get('geometry'), loc)
    raw = payload['properties']
    start, end = _interval(raw.get('validTimes'))
    periods = raw.get('periods')
    _require(isinstance(periods, list) and 1 <= len(periods) <= 32, 'invalid_period_inventory')
    value = {'kind': 'forecast', 'source_url': mapping['forecast_url'], 'mapping': copy.deepcopy(mapping),
             'units': raw.get('units'), 'source_generated_at': raw.get('generatedAt'),
             'source_updated_at': raw.get('updateTime'), 'valid_times': raw['validTimes'],
             'valid_from': start, 'valid_to': end, 'periods': [_normalize_period(p) for p in periods],
             'hash_scope': 'normalized_forecast'}
    value['content_hash'] = _hash(value)
    _validate_record(value, loc, _time(now))
    return value


def initial_forecast(location: dict) -> dict:
    """Unknown forecast for a named location; provenance is not approval."""
    loc = _location(location)
    return validate_forecast({'schema_version': 1, 'location': loc, 'provider': 'NWS', 'source_url': _point_url(loc),
            'collection_status': 'never_checked', 'coverage_status': 'not_collected',
            'last_checked_at': None, 'last_successful_fetch_at': None, 'mapping': None,
            'forecast': None, 'published_at': None, 'error_code': None, 'error_stage': None})


def validate_forecast(snapshot: dict) -> dict:
    """Strict complete source-specific state and hashes, returning a copy."""
    _require(isinstance(snapshot, dict) and set(snapshot) == SNAPSHOT_FIELDS)
    _require(type(snapshot['schema_version']) is int and snapshot['schema_version'] == 1, 'invalid_schema')
    loc = _location(snapshot['location'])
    _require(snapshot['provider'] == 'NWS' and snapshot['source_url'] == _point_url(loc), 'invalid_source')
    _require(snapshot['published_at'] is None, 'unsupported_publication_clock')
    status = snapshot['collection_status']
    _require(isinstance(status, str) and status in ('never_checked', 'success', 'failed', 'quarantined'), 'invalid_state')
    if status == 'never_checked':
        _require(snapshot['coverage_status'] == 'not_collected' and all(snapshot[f] is None for f in
                 ('last_checked_at', 'last_successful_fetch_at', 'mapping', 'forecast', 'error_code', 'error_stage')),
                 'invalid_initial_state')
    else:
        checked = _time(snapshot['last_checked_at'])
        _require(_time(loc['coordinate_checked_at']) <= checked, 'future_coordinate_evidence')
        success_value = snapshot['last_successful_fetch_at']
        successful = None if success_value is None else _time(success_value)
        _require(successful is None or successful <= checked, 'incoherent_check_clock')
        _require((snapshot['forecast'] is None) == (successful is None), 'missing_success_evidence')
        _require(snapshot['coverage_status'] == ('checked_named_grid_only' if status == 'success' else 'incomplete'),
                 'incoherent_coverage')
        expected_error = {'success': None, 'failed': 'provider_request_failed', 'quarantined': 'response_requires_review'}[status]
        _require(snapshot['error_code'] == expected_error, 'incoherent_error')
        _require(snapshot['error_stage'] is None if status == 'success' else
                 isinstance(snapshot['error_stage'], str) and snapshot['error_stage'] in ('point_lookup', 'forecast'),
                 'incoherent_error_stage')
        if snapshot['mapping'] is not None:
            _mapping(snapshot['mapping'], loc, checked)
        if snapshot['forecast'] is not None:
            _require(snapshot['mapping'] is not None, 'missing_mapping')
            _validate_record(snapshot['forecast'], loc, successful)
        if status == 'success':
            _require(successful is not None and success_value == snapshot['last_checked_at']
                     and snapshot['forecast']['mapping'] == snapshot['mapping'], 'incoherent_success')
    _json(snapshot)
    return copy.deepcopy(snapshot)


def _checked_now(snapshot: dict, now: str):
    current = _time(now)
    _require(_time(snapshot['location']['coordinate_checked_at']) <= current, 'future_coordinate_evidence')
    if snapshot['last_checked_at'] is not None:
        _require(_time(snapshot['last_checked_at']) <= current, 'collection_clock_rewind')
    return current


def collect_forecast(location: dict, previous: dict, now: str, fetch_json: Callable[[str], dict]) -> dict:
    """Discover/cache a point mapping, then validate its forecast atomically.

Mapping success is retained independently; forecast failure never rebinds the
last-good forecast to a new grid. Validation precedes all injected requests.
"""
    loc = _location(location)
    result = validate_forecast(previous)
    _require(loc == result['location'], 'location_mismatch')
    current = _checked_now(result, now)
    _require(callable(fetch_json), 'invalid_transport')
    result['last_checked_at'] = now
    mapping = result['mapping']
    stage = 'point_lookup'
    try:
        if mapping is None or current - _time(mapping['checked_at']) >= MAPPING_MAX_AGE:
            mapping = _discover(fetch_json(result['source_url']), loc, now)
            result['mapping'] = copy.deepcopy(mapping)
        stage = 'forecast'
        forecast = _normalize_forecast(fetch_json(mapping['forecast_url']), loc, mapping, now)
        previous_forecast = result['forecast']
        if previous_forecast is not None and previous_forecast['source_url'] == forecast['source_url']:
            _require(all(_time(previous_forecast[field]) <= _time(forecast[field]) for field in
                         ('source_generated_at', 'source_updated_at')), 'source_clock_rewind')
        candidate = {**result, 'collection_status': 'success', 'coverage_status': 'checked_named_grid_only',
                     'forecast': forecast, 'last_successful_fetch_at': now, 'error_code': None, 'error_stage': None}
        return validate_forecast(candidate)
    except ForecastError:
        result.update(collection_status='quarantined', coverage_status='incomplete',
                      error_code='response_requires_review', error_stage=stage)
        return validate_forecast(result)
    except (ForecastCollectionError, TimeoutError, OSError):
        result.update(collection_status='failed', coverage_status='incomplete',
                      error_code='provider_request_failed', error_stage=stage)
        return validate_forecast(result)


def forecast_freshness(snapshot: dict, now: str) -> str:
    """Source-aware age, period coverage and mapping age; no all-clear inference."""
    value = validate_forecast(snapshot)
    current = _checked_now(value, now)
    status = value['collection_status']
    if status == 'never_checked':
        return 'not_collected'
    if status != 'success':
        return status
    forecast = value['forecast']
    if current >= min(_time(forecast['valid_to']), _time(forecast['periods'][-1]['ends_at'])):
        return 'expired'
    if not any(_time(p['starts_at']) <= current < _time(p['ends_at']) for p in forecast['periods']):
        return 'not_covered'
    if current - _time(value['mapping']['checked_at']) >= MAPPING_MAX_AGE:
        return 'mapping_stale'
    oldest = min(_time(value['last_successful_fetch_at']), _time(forecast['source_generated_at']),
                 _time(forecast['source_updated_at']))
    return 'stale' if current - oldest >= FORECAST_MAX_AGE else 'fresh'
