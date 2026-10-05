"""Synthetic NWS contracts; no provider requests or actual park coordinates."""
import copy
import hashlib
import importlib
import importlib.util
import json
import unittest


T0 = '2026-10-04T10:00:00Z'
T1 = '2026-10-04T11:00:00Z'
POINT = 'https://api.weather.gov/points/37.0000,-119.0000'
GRID = 'https://api.weather.gov/gridpoints/HNX/10,20/forecast'


def location(code='yose'):
    return {'id': 'synthetic-valley-center', 'park_code': code,
            'name': 'Synthetic Valley Center', 'latitude': 37.0, 'longitude': -119.0,
            'coordinate_source_url': f'https://www.nps.gov/{code}/planyourvisit/synthetic.htm',
            'coordinate_checked_at': '2026-10-03T00:00:00Z'}


def point(office='HNX', x=10, y=20):
    return {'type': 'Feature', 'id': POINT,
            'geometry': {'type': 'Point', 'coordinates': [-119.0, 37.0]},
            'properties': {'@id': POINT, '@type': 'wx:Point', 'cwa': office,
                           'gridId': office, 'gridX': x, 'gridY': y,
                           'forecast': f'https://api.weather.gov/gridpoints/{office}/{x},{y}/forecast',
                           'forecastHourly': 'unused', 'timeZone': 'America/Los_Angeles'}}


def period(number=1, start='2026-10-04T09:00:00Z', end='2026-10-04T21:00:00Z'):
    return {'number': number, 'name': 'Synthetic Day', 'startTime': start, 'endTime': end,
            'isDaytime': True, 'temperature': 65, 'temperatureUnit': 'F',
            'temperatureTrend': None, 'probabilityOfPrecipitation': {'unitCode': 'wmoUnit:percent', 'value': None},
            'windSpeed': '5 to 10 mph', 'windDirection': 'SW', 'windGust': None,
            'icon': 'https://api.weather.gov/icons/unused', 'shortForecast': 'Synthetic café sunshine.',
            'detailedForecast': 'Synthetic forecast text, never published.'}


def forecast():
    return {'type': 'Feature', 'id': GRID,
            'geometry': {'type': 'Polygon', 'coordinates': [[[-119.01, 36.99], [-118.99, 36.99],
                                                            [-118.99, 37.01], [-119.01, 37.01], [-119.01, 36.99]]]},
            'properties': {'units': 'us', 'forecastGenerator': 'SyntheticGenerator',
                           'generatedAt': '2026-10-04T09:30:00Z', 'updateTime': '2026-10-04T09:00:00Z',
                           'validTimes': '2026-10-04T09:00:00Z/P2D',
                           'elevation': {'unitCode': 'wmoUnit:m', 'value': 1000},
                           'periods': [period(), period(2, '2026-10-04T21:00:00Z', '2026-10-05T09:00:00Z')]}}


def independent_hash(record):
    value = {k: v for k, v in record.items() if k not in ('content_hash', 'hash_scope')}
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class ForecastTests(unittest.TestCase):
    def adapter(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.park_forecasts'),
                             'The named-location NWS adapter is not implemented.')
        return importlib.import_module('tracker.park_forecasts')

    def collect(self, previous=None, at=T0, loc=None, pt=None, fc=None):
        a = self.adapter()
        loc = location() if loc is None else loc
        previous = a.initial_forecast(loc) if previous is None else previous
        requests = []
        def fetch(url):
            requests.append(url)
            return copy.deepcopy((point() if pt is None else pt) if '/points/' in url
                                 else (forecast() if fc is None else fc))
        return a.collect_forecast(loc, previous, at, fetch), requests

    def assert_retained(self, result, old, status='quarantined'):
        self.assertEqual(result['collection_status'], status)
        self.assertEqual(result['coverage_status'], 'incomplete')
        self.assertEqual(result['last_checked_at'], T1)
        self.assertEqual(result['last_successful_fetch_at'], old['last_successful_fetch_at'])
        self.assertEqual(result['forecast'], old['forecast'])
        self.assertEqual(result['error_code'], 'provider_request_failed' if status == 'failed' else 'response_requires_review')
        self.assertEqual(self.adapter().validate_forecast(result), result)

    def test_initial_state_and_every_pilot_are_unknown(self):
        a = self.adapter()
        for code in ('yose', 'romo', 'yell', 'zion', 'grca'):
            initial = a.initial_forecast(location(code))
            self.assertEqual(initial['location'], location(code))
            self.assertIsNone(initial['forecast'])
            self.assertIsNone(initial['mapping'])
            self.assertIsNone(initial['last_checked_at'])
            self.assertIsNone(initial['last_successful_fetch_at'])
            self.assertIsNone(initial['published_at'])
            self.assertEqual(a.forecast_freshness(initial, T0), 'not_collected')
            value, _ = self.collect(loc=location(code))
            self.assertEqual(value['collection_status'], 'success')

    def test_named_location_and_fixed_sources_bind_the_result(self):
        value, requests = self.collect()
        self.assertEqual(requests, [POINT, GRID])
        self.assertEqual(value['source_url'], POINT)
        self.assertEqual(value['provider'], 'NWS')
        self.assertEqual(value['coverage_status'], 'checked_named_grid_only')
        self.assertEqual(value['forecast']['kind'], 'forecast')
        self.assertEqual(value['forecast']['source_url'], GRID)
        self.assertEqual(value['mapping']['grid_id'], 'HNX')
        self.assertEqual(value['mapping']['checked_at'], T0)
        self.assertEqual(value['last_successful_fetch_at'], T0)
        self.assertEqual(value['forecast']['content_hash'], independent_hash(value['forecast']))

    def test_source_generation_update_and_period_clocks_remain_distinct(self):
        f = self.collect()[0]['forecast']
        self.assertEqual(f['source_generated_at'], '2026-10-04T09:30:00Z')
        self.assertEqual(f['source_updated_at'], '2026-10-04T09:00:00Z')
        self.assertEqual(f['valid_from'], '2026-10-04T09:00:00Z')
        self.assertEqual(f['valid_to'], '2026-10-06T09:00:00Z')
        self.assertEqual(f['valid_times'], '2026-10-04T09:00:00Z/P2D')
        self.assertEqual(f['periods'][0]['starts_at'], '2026-10-04T09:00:00Z')
        self.assertIsNone(self.collect()[0]['published_at'])

    def test_optional_nulls_and_empty_text_are_preserved_without_media_or_secrets(self):
        raw = forecast()
        raw['headers'] = {'api-key': 'synthetic-secret'}
        p = raw['properties']['periods'][0]
        for key in ('name', 'temperature', 'temperatureUnit', 'windSpeed', 'windDirection',
                    'shortForecast', 'detailedForecast', 'probabilityOfPrecipitation'):
            p.pop(key)
        value = self.collect(fc=raw)[0]
        out = value['forecast']['periods'][0]
        for key in ('name', 'temperature', 'wind_speed', 'wind_direction', 'short_forecast',
                    'detailed_forecast', 'probability_of_precipitation'):
            self.assertIsNone(out[key])
        self.assertNotIn('synthetic-secret', json.dumps(value))
        self.assertNotIn('elevation', value['forecast'])
        self.assertNotIn('icon', out)
        raw['properties']['periods'][0]['shortForecast'] = ''
        self.assertEqual(self.collect(fc=raw)[0]['forecast']['periods'][0]['short_forecast'], '')

    def test_legacy_and_quantitative_units_preserve_zero_and_unknown(self):
        raw = forecast()
        raw['properties']['periods'][0].update(temperature={'unitCode': 'wmoUnit:degC', 'value': 0},
                                              windSpeed={'unitCode': 'wmoUnit:km_h-1', 'value': None},
                                              probabilityOfPrecipitation={'unitCode': 'wmoUnit:percent', 'value': 0})
        p = self.collect(fc=raw)[0]['forecast']['periods'][0]
        self.assertEqual(p['temperature'], {'value': 0, 'unit_code': 'wmoUnit:degC'})
        self.assertEqual(p['wind_speed'], {'kind': 'quantity', 'value': None, 'unit_code': 'wmoUnit:km_h-1'})
        self.assertEqual(p['probability_of_precipitation'], {'value': 0, 'unit_code': 'wmoUnit:percent'})
        p = self.collect()[0]['forecast']['periods'][0]
        self.assertEqual(p['temperature'], {'value': 65, 'unit_code': 'wmoUnit:degF'})
        self.assertEqual(p['wind_speed'], {'kind': 'text', 'text': '5 to 10 mph'})

    def test_bad_location_refused_before_transport(self):
        a = self.adapter()
        def forbidden(_): self.fail('No requests for invalid previous/location evidence')
        cases = [('park_code', 'acad'), ('latitude', True), ('latitude', float('nan')),
                 ('latitude', 91), ('longitude', -181), ('name', ''), ('id', '../x'),
                 ('coordinate_source_url', 'https://www.nps.gov/zion/test.htm'),
                 ('coordinate_source_url', 'https://www.nps.gov/yose/../zion/test.htm'),
                 ('coordinate_source_url', 'https://www.nps.gov/yose/test.htm?token=x'),
                 ('coordinate_source_url', 'https://user@www.nps.gov/yose/test.htm'),
                 ('coordinate_checked_at', '2026-10-04')]
        for key, val in cases:
            loc = location(); loc[key] = val
            with self.subTest(key=key, val=val), self.assertRaises(a.ForecastError):
                a.collect_forecast(loc, a.initial_forecast(location()), T0, forbidden)

    def test_coordinate_rounding_retains_original_location(self):
        loc = location(); loc.update(latitude=37.00004, longitude=-119.00004)
        value, requests = self.collect(loc=loc)
        self.assertEqual(requests, [POINT, GRID])
        self.assertEqual(value['location']['latitude'], 37.00004)
        self.assertEqual(value['location']['longitude'], -119.00004)

    def test_point_coordinate_mismatch_and_untrusted_urls_are_quarantined(self):
        old = self.adapter().initial_forecast(location())
        for path, val in [(('geometry', 'coordinates'), [-118, 37]),
                          (('properties', 'forecast'), 'https://evil.test/forecast'),
                          (('properties', 'forecast'), GRID + '?token=x'),
                          (('properties', 'gridX'), True), (('properties', 'gridY'), -1),
                          (('properties', 'gridId'), '../HNX'), (('id',), GRID)]:
            raw = point(); obj = raw
            for key in path[:-1]: obj = obj[key]
            obj[path[-1]] = val
            result, requests = self.collect(previous=old, at=T1, pt=raw)
            self.assert_retained(result, old)
            self.assertEqual(requests, [POINT])
            self.assertEqual(result['error_stage'], 'point_lookup')

    def test_bad_forecast_geometry_and_identity_cannot_mislabel_another_grid(self):
        old = self.collect()[0]
        for raw in (None, {}, {'type': 'Feature', 'geometry': None}, forecast()):
            if raw is None: raw = forecast(); raw['id'] = GRID + '?units=si'
            elif raw == forecast(): raw['geometry']['coordinates'][0] = [[0, 0], [1, 0], [1, 1], [0, 0]]
            result, _ = self.collect(previous=old, at=T1, fc=raw)
            self.assert_retained(result, old)
            self.assertEqual(result['error_stage'], 'forecast')

    def test_polygon_boundary_is_valid(self):
        raw = forecast(); raw['geometry']['coordinates'][0][1][0] = -119.0
        raw['geometry']['coordinates'][0][2][0] = -119.0
        self.assertEqual(self.collect(fc=raw)[0]['collection_status'], 'success')

    def test_mapping_cached_then_rechecked_at_exact_168_hours(self):
        a = self.adapter(); old = self.collect()[0]
        before = '2026-10-11T09:59:59.999999Z'; boundary = '2026-10-11T10:00:00Z'
        for at, expected in ((before, [GRID]), (boundary, [POINT, GRID])):
            raw = forecast(); raw['properties'].update(generatedAt=at, updateTime=at,
                                                      validTimes='2026-10-11T09:00:00Z/P2D',
                                                      periods=[period(start='2026-10-11T09:00:00Z', end='2026-10-11T21:00:00Z')])
            value, requests = self.collect(previous=old, at=at, fc=raw)
            self.assertEqual(requests, expected)
            self.assertEqual(value['collection_status'], 'success')

    def test_due_mapping_failure_does_not_request_old_grid(self):
        a = self.adapter(); old = self.collect()[0]; requested = []
        def fetch(url): requested.append(url); raise TimeoutError('synthetic-secret')
        result = a.collect_forecast(location(), old, '2026-10-11T10:00:00Z', fetch)
        self.assertEqual(requested, [POINT])
        self.assertEqual(result['forecast'], old['forecast'])
        self.assertEqual(result['mapping'], old['mapping'])
        self.assertEqual(result['collection_status'], 'failed')
        self.assertNotIn('synthetic-secret', json.dumps(result))

    def test_new_grid_followed_by_failure_retains_old_forecasts_own_mapping(self):
        a = self.adapter(); old = self.collect()[0]; requested = []
        new_url = 'https://api.weather.gov/gridpoints/BOU/30,40/forecast'
        def fetch(url):
            requested.append(url)
            if url == POINT: return point('BOU', 30, 40)
            raise a.ForecastCollectionError('synthetic-secret')
        result = a.collect_forecast(location(), old, '2026-10-11T10:00:00Z', fetch)
        self.assertEqual(requested, [POINT, new_url])
        self.assertEqual(result['mapping']['forecast_url'], new_url)
        self.assertEqual(result['forecast'], old['forecast'])
        self.assertEqual(result['forecast']['mapping']['forecast_url'], GRID)
        self.assertEqual(result['last_successful_fetch_at'], T0)
        self.assertEqual(a.validate_forecast(result), result)

    def test_classified_transport_errors_retain_safe_failure_and_programming_errors_propagate(self):
        a = self.adapter(); old = self.collect()[0]
        for error in (a.ForecastCollectionError, TimeoutError, OSError):
            def fetch(_): raise error('synthetic-secret')
            value = a.collect_forecast(location(), old, T1, fetch)
            self.assert_retained(value, old, 'failed')
            self.assertNotIn('synthetic-secret', json.dumps(value))
        with self.assertRaisesRegex(RuntimeError, 'programming'):
            a.collect_forecast(location(), old, T1, lambda _: (_ for _ in ()).throw(RuntimeError('programming')))

    def test_rejected_previous_and_rewound_or_future_evidence_make_no_requests(self):
        a = self.adapter(); old = self.collect()[0]
        def forbidden(_): self.fail('Previous state refused before transport')
        cases = []
        raw = copy.deepcopy(old); raw['forecast']['periods'][0]['temperature']['value'] = 66; cases.append(raw)
        raw = copy.deepcopy(old); raw['published_at'] = T0; cases.append(raw)
        raw = copy.deepcopy(old); raw['last_successful_fetch_at'] = T1; cases.append(raw)
        raw = copy.deepcopy(old); raw['provider'] = 'NPS'; cases.append(raw)
        raw = copy.deepcopy(old); raw['extra'] = True; cases.append(raw)
        for raw in cases:
            with self.assertRaises(a.ForecastError): a.collect_forecast(location(), raw, T1, forbidden)
        for at in ('2026-10-04T09:59:59.999999Z', '2026-10-02T00:00:00Z'):
            with self.assertRaises(a.ForecastError): a.collect_forecast(location(), old, at, forbidden)
        changed = location(); changed['latitude'] = 38
        with self.assertRaises(a.ForecastError): a.collect_forecast(changed, old, T1, forbidden)

    def test_invalid_source_times_and_intervals_retain_previous(self):
        old = self.collect()[0]
        cases = [('generatedAt', None), ('updateTime', '2026-10-04T12:00:00Z'),
                 ('generatedAt', '2026-10-04T08:00:00Z'), ('validTimes', '2026-10-04T09:00:00Z/P1M'),
                 ('validTimes', '2026-10-04T09:00:00Z/P9D'), ('validTimes', '2026-10-04T09:00:00Z/PT0S'),
                 ('validTimes', '2026-10-04T09:00:00Z/2026-10-04T08:00:00Z'), ('units', 'si')]
        for key, val in cases:
            raw = forecast(); raw['properties'][key] = val
            with self.subTest(key=key, val=val): self.assert_retained(self.collect(previous=old, at=T1, fc=raw)[0], old)

    def test_explicit_end_and_offset_duration_are_accepted(self):
        for interval in ('2026-10-04T02:00:00-07:00/2026-10-06T02:00:00-07:00',
                         '2026-10-04T02:00:00-07:00/P1DT24H', '2026-10-04T09:00:00Z/PT48H'):
            raw = forecast(); raw['properties']['validTimes'] = interval
            self.assertEqual(self.collect(fc=raw)[0]['collection_status'], 'success')

    def test_malformed_periods_and_units_are_quarantined(self):
        old = self.collect()[0]
        for key, val in [('number', True), ('number', 2), ('isDaytime', 1),
                         ('endTime', '2026-10-04T09:00:00Z'), ('endTime', '2026-10-06T09:00:00Z'),
                         ('temperature', True), ('temperatureUnit', 'K'),
                         ('temperature', {'unitCode': 'wmoUnit:degK', 'value': 280}),
                         ('windSpeed', {'unitCode': 'unsupported', 'value': 2}),
                         ('probabilityOfPrecipitation', {'unitCode': 'wmoUnit:percent', 'value': 101}),
                         ('shortForecast', 42)]:
            raw = forecast(); raw['properties']['periods'][0][key] = val
            with self.subTest(key=key): self.assert_retained(self.collect(previous=old, at=T1, fc=raw)[0], old)
        for periods in ([], None, [period()] * 33, [period(), period(2)]):
            raw = forecast(); raw['properties']['periods'] = periods
            self.assert_retained(self.collect(previous=old, at=T1, fc=raw)[0], old)

    def test_freshness_uses_oldest_source_clock_not_the_latest_check(self):
        a = self.adapter(); old = self.collect()[0]
        self.assertEqual(a.forecast_freshness(old, '2026-10-04T14:59:59.999999Z'), 'fresh')
        self.assertEqual(a.forecast_freshness(old, '2026-10-04T15:00:00Z'), 'stale')
        newer = self.collect(previous=old, at='2026-10-04T16:00:00Z')[0]
        self.assertEqual(newer['last_successful_fetch_at'], '2026-10-04T16:00:00Z')
        self.assertEqual(a.forecast_freshness(newer, '2026-10-04T16:00:00Z'), 'stale')

    def test_expiry_and_gaps_are_distinct_from_empty_or_fresh(self):
        a = self.adapter(); old = self.collect()[0]
        self.assertEqual(a.forecast_freshness(old, '2026-10-05T09:00:00Z'), 'expired')
        raw = forecast(); raw['properties']['periods'][1]['startTime'] = '2026-10-04T22:00:00Z'
        value = self.collect(fc=raw)[0]
        self.assertEqual(a.forecast_freshness(value, '2026-10-04T21:30:00Z'), 'not_covered')
        raw['properties']['periods'] = [period(start='2026-10-04T12:00:00Z', end='2026-10-05T00:00:00Z')]
        value = self.collect(fc=raw)[0]
        self.assertEqual(a.forecast_freshness(value, T0), 'not_covered')

    def test_failure_and_quarantine_precede_retained_age(self):
        a = self.adapter(); old = self.collect()[0]
        bad = self.collect(previous=old, at=T1, fc={})[0]
        self.assertEqual(a.forecast_freshness(bad, '2026-10-20T00:00:00Z'), 'quarantined')
        def fail(_): raise OSError('unused')
        bad = a.collect_forecast(location(), old, T1, fail)
        self.assertEqual(a.forecast_freshness(bad, '2026-10-20T00:00:00Z'), 'failed')

    def test_mapping_freshness_boundary_is_independent_of_forecast_age(self):
        a = self.adapter(); old = self.collect()[0]
        raw = forecast(); raw['properties'].update(generatedAt='2026-10-11T09:59:00Z',
                                                  updateTime='2026-10-11T09:59:00Z',
                                                  validTimes='2026-10-11T09:00:00Z/P2D',
                                                  periods=[period(start='2026-10-11T09:00:00Z', end='2026-10-11T21:00:00Z')])
        value = self.collect(previous=old, at='2026-10-11T09:59:00Z', fc=raw)[0]
        self.assertEqual(a.forecast_freshness(value, '2026-10-11T09:59:59.999999Z'), 'fresh')
        self.assertEqual(a.forecast_freshness(value, '2026-10-11T10:00:00Z'), 'mapping_stale')

    def test_inputs_and_returned_copies_are_independent(self):
        a = self.adapter(); loc = location(); old = self.collect()[0]; saved = copy.deepcopy(old)
        fc = forecast(); pt = point(); fc_saved = copy.deepcopy(fc)
        value, _ = self.collect(previous=old, at=T1, loc=loc, pt=pt, fc=fc)
        value['forecast']['periods'][0]['name'] = 'changed'
        self.assertEqual(old, saved)
        self.assertEqual(fc, fc_saved)
        self.assertEqual(loc, location())
        validated = a.validate_forecast(old); validated['location']['name'] = 'changed'
        self.assertEqual(old, saved)

    def test_payload_size_bad_numbers_and_invalid_snapshot_states_are_refused(self):
        a = self.adapter(); old = self.collect()[0]
        for extra in ('x' * (1024 * 1024), float('nan'), '\ud800'):
            raw = forecast(); raw['unused'] = extra
            self.assert_retained(self.collect(previous=old, at=T1, fc=raw)[0], old)
        for key, val in [('collection_status', []), ('coverage_status', 'all_clear'),
                         ('schema_version', True), ('error_code', 'synthetic-secret'),
                         ('error_stage', 'bad')]:
            raw = copy.deepcopy(old); raw[key] = val
            with self.assertRaises(a.ForecastError): a.validate_forecast(raw)

    def test_extreme_integers_are_safe_refusals_in_locations_and_quantities(self):
        a = self.adapter(); old = self.collect()[0]
        loc = location(); loc['latitude'] = 10 ** 400
        with self.assertRaises(a.ForecastError): a.initial_forecast(loc)
        raw = forecast(); raw['properties']['periods'][0]['temperature'] = {
            'unitCode': 'wmoUnit:degF', 'value': 10 ** 400}
        self.assert_retained(self.collect(previous=old, at=T1, fc=raw)[0], old)

    def test_same_grid_source_clock_replay_cannot_replace_newer_evidence(self):
        old = self.collect()[0]
        for key, value in [('generatedAt', '2026-10-04T09:15:00Z'),
                           ('updateTime', '2026-10-04T08:00:00Z')]:
            raw = forecast(); raw['properties'][key] = value
            self.assert_retained(self.collect(previous=old, at=T1, fc=raw)[0], old)

    def test_self_crossing_unclosed_and_unsupported_polygon_rings_are_quarantined(self):
        old = self.collect()[0]
        for ring in ([[-119.02, 36.98], [-118.99, 37.02], [-119.02, 37.02], [-118.98, 36.98], [-119.02, 36.98]],
                     [[-119.01, 36.99], [-118.99, 36.99], [-118.99, 37.01], [-119.01, 37.01]],
                     [[-119.0, 37.0]] * 4):
            raw = forecast(); raw['geometry']['coordinates'] = [ring]
            self.assert_retained(self.collect(previous=old, at=T1, fc=raw)[0], old)
        raw = forecast(); raw['geometry']['coordinates'].append(raw['geometry']['coordinates'][0])
        self.assert_retained(self.collect(previous=old, at=T1, fc=raw)[0], old)

    def test_callback_mutation_cannot_change_validated_previous_or_location(self):
        a = self.adapter(); old = self.collect()[0]; saved = copy.deepcopy(old); loc = location()
        def fetch(_):
            old['forecast']['periods'][0]['name'] = 'caller mutation'
            loc['name'] = 'caller mutation'
            return forecast()
        result = a.collect_forecast(loc, old, T1, fetch)
        self.assertEqual(result['location'], location())
        self.assertEqual(result['forecast']['periods'][0]['name'], saved['forecast']['periods'][0]['name'])

    def test_missing_geojson_id_is_accepted_only_with_checked_geometry(self):
        raw = forecast(); del raw['id']
        self.assertEqual(self.collect(fc=raw)[0]['collection_status'], 'success')

    def test_malformed_timestamp_duration_and_probability_never_escape_quarantine(self):
        old = self.collect()[0]
        for key, val in [('generatedAt', '2026-02-30T09:30:00Z'),
                         ('validTimes', '9999-12-31T23:59:59Z/P1D'),
                         ('validTimes', '2026-10-04T09:00:00Z/P1DT'),
                         ('validTimes', '2026-10-04T09:00:00Z/P1W')]:
            raw = forecast(); raw['properties'][key] = val
            self.assert_retained(self.collect(previous=old, at=T1, fc=raw)[0], old)
        for value in (-1, True, '0'):
            raw = forecast(); raw['properties']['periods'][0]['probabilityOfPrecipitation']['value'] = value
            self.assert_retained(self.collect(previous=old, at=T1, fc=raw)[0], old)


if __name__ == '__main__':
    unittest.main()
