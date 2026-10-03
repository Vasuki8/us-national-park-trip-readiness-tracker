"""Synthetic contract tests for the private, transport-injected NPS profile adapter."""
import copy
import hashlib
import importlib
import importlib.util
import json
import unittest


T0 = '2026-10-02T10:00:00Z'
T1 = '2026-10-02T11:00:00Z'
T2 = '2026-10-02T12:00:00Z'
PARKS = ('yose', 'romo', 'yell', 'zion', 'grca')


def park(code='yose', **changes):
    """A synthetic /parks item; unused documented fields must stay out of storage."""
    value = {
        'id': 'synthetic-park-id', 'parkCode': code,
        'fullName': 'Synthetic National Park', 'name': 'Synthetic',
        'designation': 'National Park', 'url': f'https://www.nps.gov/{code}/index.htm',
        'description': 'Synthetic café 🏞 introduction.',
        'weatherInfo': 'Synthetic winters are cold; summers are warm.',
        'activities': [{'id': 'b', 'name': 'Wildlife Watching'}, {'id': 'a', 'name': 'Hiking'}],
        'latitude': '37.0', 'longitude': '-119.0', 'latLong': 'lat:37.0, long:-119.0',
        'states': 'CA', 'topics': [], 'contacts': {'phoneNumbers': [], 'emailAddresses': []},
        'entranceFees': [], 'entrancePasses': [], 'fees': [], 'directionsInfo': 'Synthetic directions.',
        'directionsUrl': f'https://www.nps.gov/{code}/planyourvisit/directions.htm',
        'operatingHours': [], 'addresses': [], 'images': [], 'relevanceScore': 1.0,
    }
    value.update(changes)
    return value


def page(records=None, **changes):
    value = {'total': '1', 'limit': '50', 'start': '0', 'data': [park()] if records is None else records}
    value.update(changes)
    return value


def semantic_hash(profile):
    """Independent fixture encoding; never call the adapter's hash builder."""
    fields = ('id', 'park_code', 'full_name', 'url', 'description', 'seasonal_weather',
              'activity_categories', 'activity_scope')
    value = {field: profile[field] for field in fields}
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()


class ProfileTests(unittest.TestCase):
    def adapter(self):
        # The first RED run must report a missing implementation as an assertion,
        # rather than conceal the test suite behind an import-time exception.
        self.assertIsNotNone(importlib.util.find_spec('tracker.park_profiles'),
                             'The source-specific NPS profile adapter is not implemented.')
        return importlib.import_module('tracker.park_profiles')

    def collected(self, code='yose', at=T0, raw=None):
        adapter = self.adapter()
        return adapter.collect_profile(code, adapter.initial_profile(code), at,
                                       lambda start: page([park(code) if raw is None else raw]))

    def assert_retained(self, result, previous, status='quarantined'):
        self.assertEqual(result['collection_status'], status)
        self.assertEqual(result['coverage_status'], 'incomplete')
        self.assertEqual(result['last_checked_at'], T1)
        self.assertEqual(result['last_successful_fetch_at'], previous['last_successful_fetch_at'])
        self.assertEqual(result['profile'], previous['profile'])
        self.assertEqual(result['error_code'], 'provider_request_failed' if status == 'failed'
                         else 'response_requires_review')

    def test_initial_profile_is_unknown_for_every_pilot(self):
        adapter = self.adapter()
        for code in PARKS:
            with self.subTest(code=code):
                initial = adapter.initial_profile(code)
                self.assertEqual(initial, {
                    'schema_version': 1, 'park_code': code, 'provider': 'NPS',
                    'source_url': f'https://developer.nps.gov/api/v1/parks?parkCode={code}',
                    'collection_status': 'never_checked', 'coverage_status': 'not_collected',
                    'last_checked_at': None, 'last_successful_fetch_at': None,
                    'source_issued_at': None, 'source_updated_at': None, 'published_at': None,
                    'profile': None, 'error_code': None,
                })
                self.assertEqual(adapter.validate_profile(initial), initial)
                self.assertEqual(adapter.profile_freshness(initial, T0), 'not_collected')

    def test_nonpilot_and_nonstrings_are_rejected_before_transport(self):
        adapter = self.adapter()
        def forbidden(_start):
            self.fail('Invalid park identity must be refused before transport.')
        for code in ('acad', 'YOSE', 'yose ', '', None, True, 1, [], {}):
            with self.subTest(code=code):
                with self.assertRaises(adapter.ProfileError):
                    adapter.initial_profile(code)
                with self.assertRaises(adapter.ProfileError):
                    adapter.collect_profile(code, adapter.initial_profile('yose'), T0, forbidden)

    def test_valid_profiles_for_all_pilots_keep_source_identity_and_observation_clocks(self):
        adapter = self.adapter()
        for code in PARKS:
            with self.subTest(code=code):
                value = self.collected(code)
                self.assertEqual(value['collection_status'], 'success')
                self.assertEqual(value['coverage_status'], 'checked_profile_only')
                self.assertEqual(value['last_checked_at'], T0)
                self.assertEqual(value['last_successful_fetch_at'], T0)
                self.assertEqual(value['profile']['park_code'], code)
                self.assertEqual(value['profile']['url'], f'https://www.nps.gov/{code}/index.htm')
                self.assertEqual(value['profile']['observed_first_at'], T0)
                self.assertEqual(value['profile']['observed_changed_at'], T0)
                self.assertEqual(adapter.validate_profile(value), value)

    def test_normalization_explicitly_excludes_images_coordinates_fees_and_provider_extras(self):
        adapter = self.adapter()
        raw = park(images=[{'url': 'https://example.test/photo', 'credit': 'not a licence'}],
                   headers={'X-Api-Key': 'synthetic-secret'}, sourceUpdatedAt=T0,
                   sourceIssuedAt=T0, publishedAt=T0, token='synthetic-secret')
        result = self.collected(raw=raw)
        expected = {
            'id': 'synthetic-park-id', 'park_code': 'yose', 'full_name': 'Synthetic National Park',
            'url': 'https://www.nps.gov/yose/index.htm', 'description': 'Synthetic café 🏞 introduction.',
            'seasonal_weather': {'kind': 'seasonal_context',
                                 'text': 'Synthetic winters are cold; summers are warm.'},
            'activity_categories': [{'id': 'a', 'name': 'Hiking'}, {'id': 'b', 'name': 'Wildlife Watching'}],
            'activity_scope': 'categories_only', 'source_updated_at': None,
            'observed_first_at': T0, 'observed_changed_at': T0,
            'hash_scope': 'normalized_record',
        }
        expected['content_hash'] = semantic_hash(expected)
        self.assertEqual(result['profile'], expected)
        for field in ('source_issued_at', 'source_updated_at', 'published_at'):
            self.assertIsNone(result[field])
        self.assertNotIn('synthetic-secret', json.dumps(result))
        self.assertEqual(adapter.validate_profile(result), result)

    def test_missing_optional_information_remains_null(self):
        raw = park()
        for field in ('description', 'weatherInfo', 'activities'):
            del raw[field]
        result = self.collected(raw=raw)['profile']
        self.assertIsNone(result['description'])
        self.assertIsNone(result['seasonal_weather'])
        self.assertIsNone(result['activity_categories'])

    def test_explicit_null_optionals_and_empty_categories_have_distinct_meanings(self):
        missing = self.collected(raw=park(description=None, weatherInfo=None, activities=None))['profile']
        empty = self.collected(raw=park(description='', weatherInfo='', activities=[]))['profile']
        self.assertIsNone(missing['description'])
        self.assertIsNone(missing['seasonal_weather'])
        self.assertIsNone(missing['activity_categories'])
        self.assertEqual(empty['description'], '')
        self.assertEqual(empty['seasonal_weather'], {'kind': 'seasonal_context', 'text': ''})
        self.assertEqual(empty['activity_categories'], [])
        self.assertNotEqual(missing['content_hash'], empty['content_hash'])

    def test_unchanged_content_and_category_reordering_preserve_observation_clocks(self):
        adapter = self.adapter()
        previous = self.collected()
        raw = park(activities=list(reversed(park()['activities'])), images=[{'credit': 'different'}])
        result = adapter.collect_profile('yose', previous, T1, lambda start: page([raw]))
        self.assertEqual(result['profile'], previous['profile'])
        self.assertEqual(result['last_checked_at'], T1)
        self.assertEqual(result['last_successful_fetch_at'], T1)

    def test_edited_content_advances_change_time_but_not_first_observation(self):
        adapter = self.adapter()
        previous = self.collected()
        result = adapter.collect_profile('yose', previous, T1,
                                         lambda start: page([park(description='Revised synthetic introduction.')]))
        self.assertEqual(result['profile']['description'], 'Revised synthetic introduction.')
        self.assertEqual(result['profile']['observed_first_at'], T0)
        self.assertEqual(result['profile']['observed_changed_at'], T1)
        self.assertNotEqual(result['profile']['content_hash'], previous['profile']['content_hash'])

    def test_new_source_record_id_starts_new_observation(self):
        adapter = self.adapter()
        previous = self.collected()
        result = adapter.collect_profile('yose', previous, T1, lambda start: page([park(id='replacement-id')]))
        self.assertEqual(result['profile']['observed_first_at'], T1)
        self.assertEqual(result['profile']['observed_changed_at'], T1)

    def test_transport_is_explicit_and_scoped_response_uses_only_offset_zero(self):
        adapter = self.adapter()
        def fetch(start):
            if start != 0:
                self.fail('A scoped profile request must never continue incomplete pagination.')
            return page()
        result = adapter.collect_profile('yose', adapter.initial_profile('yose'), T0, fetch)
        self.assertEqual(result['collection_status'], 'success')
        with self.assertRaises(TypeError):
            adapter.collect_profile('yose', adapter.initial_profile('yose'), T0)

    def test_empty_wrong_duplicate_or_partial_feeds_preserve_last_good(self):
        adapter = self.adapter()
        previous = self.collected()
        feeds = [page([], total='0'), page([], total='1'), page([park('grca')]),
                 page([park(), park()], total='2'), page([park(), park()], total='1'),
                 page([park()], total='2'), page([park()], start='1')]
        for payload in feeds:
            with self.subTest(payload=payload):
                result = adapter.collect_profile('yose', previous, T1, lambda start: payload)
                self.assert_retained(result, previous)
                self.assertEqual(adapter.validate_profile(result), result)

    def test_bad_counts_and_response_shapes_are_quarantined(self):
        adapter = self.adapter()
        previous = self.collected()
        feeds = [None, [], {}, {'data': [park()]}, page(data={}), page(data=None),
                 page([None]), page([[]]), page(total=True), page(start=False),
                 page(total=1.0), page(start=0.0), page(total='-1'), page(total='1.0'),
                 page(total=' 1'), page(start=' 0'), page(total=None), page(start=None)]
        for payload in feeds:
            with self.subTest(payload=payload):
                self.assert_retained(adapter.collect_profile('yose', previous, T1, lambda start: payload), previous)
        accepted = adapter.collect_profile('yose', previous, T1, lambda start: page(total=1, start=0))
        self.assertEqual(accepted['collection_status'], 'success')

    def test_missing_required_identity_is_quarantined(self):
        adapter = self.adapter()
        previous = self.collected()
        for field in ('id', 'parkCode', 'fullName', 'url'):
            for value in (None, '', ' ', 1, True, [], {}):
                with self.subTest(field=field, value=value):
                    result = adapter.collect_profile('yose', previous, T1, lambda start: page([park(**{field: value})]))
                    self.assert_retained(result, previous)
            raw = park()
            del raw[field]
            self.assert_retained(adapter.collect_profile('yose', previous, T1, lambda start: page([raw])), previous)

    def test_malformed_optional_text_is_quarantined(self):
        adapter = self.adapter()
        previous = self.collected()
        for field in ('description', 'weatherInfo'):
            for value in (False, 1, [], {}, 'x' * 65537):
                with self.subTest(field=field, value=type(value).__name__):
                    self.assert_retained(adapter.collect_profile('yose', previous, T1,
                                         lambda start: page([park(**{field: value})])), previous)

    def test_categories_require_unique_bounded_ids_and_names(self):
        adapter = self.adapter()
        previous = self.collected()
        categories = [False, {}, 'Hiking', [None], [{}], [{'id': 'a'}], [{'name': 'Hiking'}],
                      [{'id': '', 'name': 'Hiking'}], [{'id': 'a', 'name': ''}],
                      [{'id': 'a', 'name': 1}], [{'id': 'a', 'name': 'Hiking'}, {'id': 'a', 'name': 'Other'}],
                      [{'id': 'a\n', 'name': 'Hiking'}], [{'id': 'x' * 257, 'name': 'Hiking'}]]
        for value in categories:
            with self.subTest(categories=value):
                self.assert_retained(adapter.collect_profile('yose', previous, T1,
                                     lambda start: page([park(activities=value)])), previous)

    def test_category_extras_do_not_become_activity_details(self):
        raw = park(activities=[{'id': 'a', 'name': 'Hiking', 'difficulty': 'easy', 'duration': 2,
                                'location': 'invented', 'permit': False}])
        result = self.collected(raw=raw)['profile']
        self.assertEqual(result['activity_categories'], [{'id': 'a', 'name': 'Hiking'}])
        self.assertEqual(result['activity_scope'], 'categories_only')

    def test_official_same_park_urls_preserve_safe_original_values(self):
        for url in ('https://www.nps.gov/yose/', 'https://nps.gov/yose/index.htm',
                    'https://www.nps.gov:443/yose/planyourvisit/',
                    'https://www.nps.gov/yose/%63onditions/?view=full#details'):
            with self.subTest(url=url):
                self.assertEqual(self.collected(raw=park(url=url))['profile']['url'], url)

    def test_nonofficial_cross_park_or_unsafe_urls_are_quarantined(self):
        adapter = self.adapter()
        previous = self.collected()
        urls = ['http://www.nps.gov/yose/', 'https://www.nps.gov/grca/',
                'https://www.nps.gov/yosemite/', 'https://example.test/yose/',
                'https://www.nps.gov.evil.test/yose/', 'https://go.nps.gov/yose/',
                'https://www.nps.gov/subjects/developer/', 'https://www.nps.gov/',
                'https://user:password@www.nps.gov/yose/', 'https://www.nps.gov:444/yose/',
                'https://www.nps.gov:bad/yose/', 'https://[broken/yose/',
                'https://www.nps.gov/yose/../grca/', 'https://www.nps.gov/yose/%2e%2e/grca/',
                'https://www.nps.gov//yose/', 'https://www.nps.gov/yose//conditions/',
                'https://www.nps.gov/yose/%2fconditions/', 'https://www.nps.gov/yose/\\conditions/',
                'https://www.nps.gov/yose/%5cconditions/', 'https://www.nps.gov/yose/%0aconditions/',
                'https://www.nps.gov/yose/te\nst', 'https://www.nps.gov/yose/?api_key=synthetic',
                'https://www.nps.gov/yose/?%74oken=synthetic', 'https://www.nps.gov/yose/#secret=synthetic']
        for url in urls:
            with self.subTest(url=url):
                self.assert_retained(adapter.collect_profile('yose', previous, T1,
                                     lambda start: page([park(url=url)])), previous)

    def test_transport_failures_never_store_exception_text_or_reset_success(self):
        adapter = self.adapter()
        previous = self.collected()
        for error_type in (adapter.ProfileCollectionError, TimeoutError, OSError):
            def failure(_start):
                raise error_type('private-key-and-provider-body-must-not-persist')
            with self.subTest(error_type=error_type):
                result = adapter.collect_profile('yose', previous, T1, failure)
                self.assert_retained(result, previous, 'failed')
                self.assertNotIn('private-key', json.dumps(result))
                self.assertEqual(adapter.validate_profile(result), result)

    def test_initial_failure_or_quarantine_stays_unknown_without_last_good(self):
        adapter = self.adapter()
        def failure(_start):
            raise adapter.ProfileCollectionError('synthetic failure')
        for fetch, status in ((failure, 'failed'), (lambda start: page([], total='0'), 'quarantined')):
            with self.subTest(status=status):
                result = adapter.collect_profile('yose', adapter.initial_profile('yose'), T0, fetch)
                self.assertEqual(result['collection_status'], status)
                self.assertIsNone(result['profile'])
                self.assertIsNone(result['last_successful_fetch_at'])
                self.assertEqual(adapter.profile_freshness(result, T0), status)

    def test_unexpected_programming_exceptions_propagate(self):
        adapter = self.adapter()
        previous = self.collected()
        original = copy.deepcopy(previous)
        for error_type in (RuntimeError, ValueError, TypeError, KeyError, AssertionError):
            def failure(_start):
                raise error_type('synthetic programming error')
            with self.subTest(error_type=error_type), self.assertRaises(error_type):
                adapter.collect_profile('yose', previous, T1, failure)
        self.assertEqual(previous, original)

    def test_recovery_uses_retained_profile_and_preserves_unchanged_evidence(self):
        adapter = self.adapter()
        previous = self.collected()
        failed = adapter.collect_profile('yose', previous, T1, lambda start: page([], total='0'))
        result = adapter.collect_profile('yose', failed, T2, lambda start: page())
        self.assertEqual(result['collection_status'], 'success')
        self.assertEqual(result['last_successful_fetch_at'], T2)
        self.assertEqual(result['profile'], previous['profile'])

    def test_quarantine_retains_entry_baseline_despite_valid_rehashed_caller_mutation(self):
        adapter = self.adapter()
        previous = self.collected()
        accepted = copy.deepcopy(previous)
        def fetch(_start):
            previous['profile']['description'] = 'Callback altered caller-owned evidence.'
            previous['profile']['content_hash'] = semantic_hash(previous['profile'])
            return page([], total='0')
        result = adapter.collect_profile('yose', previous, T1, fetch)
        self.assert_retained(result, accepted)
        self.assertEqual(adapter.validate_profile(result), result)

    def test_quarantine_retains_entry_baseline_despite_invalid_caller_mutation(self):
        adapter = self.adapter()
        previous = self.collected()
        accepted = copy.deepcopy(previous)
        def fetch(_start):
            previous['profile']['description'] = 'Callback invalidated caller-owned evidence.'
            return page([], total='0')
        result = adapter.collect_profile('yose', previous, T1, fetch)
        self.assert_retained(result, accepted)
        self.assertEqual(adapter.validate_profile(result), result)

    def test_quarantine_retains_entry_clocks_despite_coherent_future_caller_mutation(self):
        adapter = self.adapter()
        previous = self.collected()
        accepted = copy.deepcopy(previous)
        def fetch(_start):
            previous.update(last_checked_at=T2, last_successful_fetch_at=T2)
            previous['profile'].update(observed_first_at=T2, observed_changed_at=T2)
            return page([], total='0')
        result = adapter.collect_profile('yose', previous, T1, fetch)
        self.assert_retained(result, accepted)
        self.assertEqual(adapter.validate_profile(result), result)

    def test_unknown_snapshot_or_record_fields_cannot_cross_the_validation_boundary(self):
        adapter = self.adapter()
        for target in ('snapshot', 'profile', 'seasonal_weather', 'category'):
            bad = self.collected()
            selected = {'snapshot': bad, 'profile': bad['profile'],
                        'seasonal_weather': bad['profile']['seasonal_weather'],
                        'category': bad['profile']['activity_categories'][0]}[target]
            selected['credentials'] = 'must-not-persist'
            with self.subTest(target=target), self.assertRaises(adapter.ProfileError):
                adapter.validate_profile(bad)
        bad = self.collected()
        del bad['published_at']
        with self.assertRaises(adapter.ProfileError):
            adapter.validate_profile(bad)

    def test_invalid_schema_source_status_and_untrusted_source_clocks_are_refused(self):
        adapter = self.adapter()
        mutations = [('schema_version', True), ('schema_version', 2), ('park_code', 'acad'),
                     ('provider', 'NWS'), ('source_url', 'https://developer.nps.gov/api/v1/alerts?parkCode=yose'),
                     ('collection_status', 'clear'), ('collection_status', []),
                     ('coverage_status', 'complete'), ('error_code', 'raw exception'),
                     ('source_issued_at', T0), ('source_updated_at', T0), ('published_at', T0)]
        for field, value in mutations:
            bad = self.collected()
            bad[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(adapter.ProfileError):
                adapter.validate_profile(bad)
        with self.assertRaises(adapter.ProfileError):
            adapter.validate_profile([])

    def test_never_checked_state_cannot_claim_attempts_success_or_evidence(self):
        adapter = self.adapter()
        for field, value in [('last_checked_at', T0), ('last_successful_fetch_at', T0),
                             ('error_code', 'provider_request_failed'), ('coverage_status', 'incomplete'),
                             ('profile', self.collected()['profile'])]:
            bad = adapter.initial_profile('yose')
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(adapter.ProfileError):
                adapter.validate_profile(bad)

    def test_collected_state_and_success_clock_must_agree_with_evidence(self):
        adapter = self.adapter()
        mutations = [('last_checked_at', None), ('last_successful_fetch_at', None),
                     ('last_successful_fetch_at', T1), ('last_checked_at', T1), ('profile', None),
                     ('collection_status', 'failed'), ('collection_status', 'quarantined')]
        for field, value in mutations:
            bad = self.collected()
            bad[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(adapter.ProfileError):
                adapter.validate_profile(bad)
        bad = self.collected()
        bad.update(collection_status='failed', coverage_status='incomplete', error_code='provider_request_failed',
                   last_checked_at=T1, last_successful_fetch_at=None)
        with self.assertRaises(adapter.ProfileError):
            adapter.validate_profile(bad)

    def test_tampered_hash_scope_identity_and_interpretation_labels_are_refused(self):
        adapter = self.adapter()
        mutations = [('content_hash', '0' * 64), ('hash_scope', 'raw_payload'),
                     ('full_name', 'tampered'), ('park_code', 'grca'), ('source_updated_at', T0),
                     ('activity_scope', 'individual_activities'), ('seasonal_weather', {'kind': 'forecast', 'text': 'x'})]
        for field, value in mutations:
            bad = self.collected()
            bad['profile'][field] = value
            with self.subTest(field=field), self.assertRaises(adapter.ProfileError):
                adapter.validate_profile(bad)

    def test_rehashed_malformed_profile_values_still_fail_validation(self):
        adapter = self.adapter()
        mutations = [('id', 'bad\nid'), ('id', 'x' * 257), ('full_name', ''),
                     ('url', 'https://www.nps.gov/grca/'), ('description', 1),
                     ('activity_categories', [{'id': 'a', 'name': 'Hiking'}, {'id': 'a', 'name': 'Hiking'}]),
                     ('seasonal_weather', {'kind': 'seasonal_context', 'text': []})]
        for field, value in mutations:
            bad = self.collected()
            bad['profile'][field] = value
            bad['profile']['content_hash'] = semantic_hash(bad['profile'])
            with self.subTest(field=field), self.assertRaises(adapter.ProfileError):
                adapter.validate_profile(bad)

    def test_first_change_success_and_attempt_clocks_are_coherent(self):
        adapter = self.adapter()
        for field, value in [('observed_first_at', T1), ('observed_changed_at', T1),
                             ('observed_first_at', None), ('observed_changed_at', '2026-02-30T10:00:00Z')]:
            bad = self.collected()
            bad['profile'][field] = value
            with self.subTest(field=field), self.assertRaises(adapter.ProfileError):
                adapter.validate_profile(bad)
        bad = self.collected()
        bad['profile'].update(observed_first_at=T0, observed_changed_at='2026-10-02T09:00:00Z')
        with self.assertRaises(adapter.ProfileError):
            adapter.validate_profile(bad)

    def test_invalid_previous_is_refused_before_fetch(self):
        adapter = self.adapter()
        def forbidden(_start):
            self.fail('Previous evidence must be validated before transport.')
        bad_values = [None, [], {}, adapter.initial_profile('grca')]
        for field, value in [('source_url', 'https://example.test/'), ('schema_version', True),
                             ('last_successful_fetch_at', T2), ('collection_status', 'never_checked')]:
            bad = self.collected()
            bad[field] = value
            bad_values.append(bad)
        bad = self.collected()
        bad['profile']['description'] = 'tampered'
        bad_values.append(bad)
        for previous in bad_values:
            with self.subTest(previous=previous), self.assertRaises(adapter.ProfileError):
                adapter.collect_profile('yose', previous, T1, forbidden)

    def test_bad_or_rewound_now_is_refused_before_fetch(self):
        adapter = self.adapter()
        def forbidden(_start):
            self.fail('Invalid collection clocks must be refused before transport.')
        for now in (None, True, '', '2026-10-02', '2026-10-02T10:00:00',
                    '2026-02-30T10:00:00Z', '2026-10-02T24:00:00Z',
                    '2026-10-02T10:00:00+00:99', '2026-10-02T09:59:59Z'):
            with self.subTest(now=now), self.assertRaises(adapter.ProfileError):
                adapter.collect_profile('yose', self.collected(), now, forbidden)

    def test_offsets_are_compared_as_instants_and_equal_clocks_are_allowed(self):
        adapter = self.adapter()
        previous = self.collected(at='2026-10-02T12:00:00+02:00')
        result = adapter.collect_profile('yose', previous, T0, lambda start: page())
        self.assertEqual(result['last_successful_fetch_at'], T0)
        self.assertEqual(result['profile']['observed_first_at'], '2026-10-02T12:00:00+02:00')
        self.assertEqual(adapter.profile_freshness(result, T0), 'fresh')

    def test_seven_day_profile_freshness_has_exact_expiry_and_is_independent_of_alert_age(self):
        adapter = self.adapter()
        previous = self.collected()
        cases = [('2026-10-02T14:00:01Z', 'fresh'), ('2026-10-09T09:59:59.999999Z', 'fresh'),
                 ('2026-10-09T10:00:00Z', 'stale'), ('2026-10-09T10:00:00.000001Z', 'stale')]
        for now, expected in cases:
            with self.subTest(now=now):
                self.assertEqual(adapter.profile_freshness(previous, now), expected)

    def test_failed_and_quarantined_attempts_never_count_as_fresh_success(self):
        adapter = self.adapter()
        previous = self.collected()
        def failure(_start):
            raise adapter.ProfileCollectionError('synthetic failure')
        for fetch, expected in ((failure, 'failed'), (lambda start: page([], total='0'), 'quarantined')):
            result = adapter.collect_profile('yose', previous, T1, fetch)
            self.assertEqual(adapter.profile_freshness(result, T1), expected)
            self.assertEqual(adapter.profile_freshness(result, '2026-10-20T10:00:00Z'), expected)
            self.assertEqual(result['last_successful_fetch_at'], T0)

    def test_freshness_refuses_future_or_invalid_evidence_and_invalid_now(self):
        adapter = self.adapter()
        previous = self.collected()
        for now in ('2026-10-02T09:59:59Z', '2026-02-30T10:00:00Z', None):
            with self.subTest(now=now), self.assertRaises(adapter.ProfileError):
                adapter.profile_freshness(previous, now)
        bad = copy.deepcopy(previous)
        bad['profile']['content_hash'] = '0' * 64
        with self.assertRaises(adapter.ProfileError):
            adapter.profile_freshness(bad, T1)

    def test_validation_and_collection_are_defensive_copies_of_caller_inputs(self):
        adapter = self.adapter()
        previous = self.collected()
        raw = page()
        old_copy, raw_copy = copy.deepcopy(previous), copy.deepcopy(raw)
        result = adapter.collect_profile('yose', previous, T1, lambda start: raw)
        validated = adapter.validate_profile(result)
        validated['profile']['activity_categories'][0]['name'] = 'changed by caller'
        result['profile']['activity_categories'].clear()
        self.assertEqual(previous, old_copy)
        self.assertEqual(raw, raw_copy)


if __name__ == '__main__':
    unittest.main()
