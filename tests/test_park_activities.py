"""Synthetic source-contract tests; no real activity collection or publication."""
import copy
import hashlib
import importlib
import importlib.util
import json
import unittest
from unittest.mock import patch

T0 = '2026-10-03T10:00:00Z'
T1 = '2026-10-03T11:00:00Z'
T2 = '2026-10-03T12:00:00Z'
META = {'source_updated_at', 'observed_first_at', 'observed_changed_at', 'content_hash', 'hash_scope'}


def activity(identifier='synthetic-a', code='yose', **changes):
    """Mirror the documented item, including excluded fields, with synthetic text."""
    raw = {
        'id': identifier, 'title': 'Synthetic activity',
        'url': 'https://www.nps.gov/thingstodo/synthetic-outside-destination.htm',
        'shortDescription': 'Synthetic café 🏞 introduction.',
        'longDescription': '<p>Synthetic trail continues outside the park.</p>',
        'location': 'Synthetic trailhead', 'locationDescription': 'Synthetic route crosses a boundary.',
        'duration': '1-2 hours', 'durationDescription': 'Synthetic estimate varies.',
        'season': ['Winter', 'Fall'], 'seasonDescription': 'Synthetic seasonal context.',
        'accessibilityInformation': '<p>Synthetic accessibility information.</p>',
        'activities': [{'id': 'b', 'name': 'Wildlife Watching'}, {'id': 'a', 'name': 'Hiking'}],
        'activityDescription': 'Synthetic easy route.', 'doFeesApply': 'false',
        'feeDescription': 'Synthetic fee information.', 'isReservationRequired': 'true',
        'reservationDescription': 'Synthetic reservation instructions.',
        'arePetsPermitted': False, 'arePetsPermittedWithRestrictions': 'false',
        'petsDescription': 'Synthetic pet information.', 'age': 'All Ages',
        'ageDescription': 'Synthetic age guidance.', 'timeOfDay': ['Day', 'Dawn'],
        'timeOfDayDescription': 'Synthetic timing.', 'credit': 'Synthetic credit; not a licence.',
        'relatedParks': [{'parkCode': code, 'fullName': 'Synthetic National Park',
                          'url': f'https://www.nps.gov/{code}/index.htm',
                          'states': 'CA', 'designation': 'National Park', 'name': 'Synthetic'}],
        'relatedOrganizations': [{'uncontracted': 'excluded'}],
        'latitude': '37', 'longitude': '-119', 'geometryPoiId': 'excluded',
        'images': [{'credit': 'Not reviewed', 'crops': [], 'altText': 'Synthetic image',
                    'title': 'Synthetic image', 'caption': '', 'description': '',
                    'url': 'https://www.nps.gov/common/uploads/synthetic.jpg'}],
        'amenities': ['Synthetic amenity'], 'topics': [], 'tags': [], 'relevanceScore': 1,
    }
    raw.update(changes)
    return raw


def page(records=None, *, total=None, start=0, **changes):
    records = [activity()] if records is None else records
    result = {'data': records, 'total': str(len(records) if total is None else total),
              'start': str(start), 'limit': '50'}
    result.update(changes)
    return result


def rehash(record):
    semantic = {key: value for key, value in record.items() if key not in META}
    record['content_hash'] = hashlib.sha256(json.dumps(semantic, ensure_ascii=False,
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class ActivityTests(unittest.TestCase):
    def adapter(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.park_activities'),
                             'The source-specific activity adapter is not implemented.')
        return importlib.import_module('tracker.park_activities')

    def collected(self, records=None, *, code='yose', at=T0):
        adapter = self.adapter()
        records = [activity(code=code)] if records is None else records
        return adapter.collect_activities(code, adapter.initial_activities(code), at,
                                          lambda start: page(records, start=start))

    def retained(self, result, baseline, status='quarantined'):
        self.assertEqual(result['collection_status'], status)
        self.assertEqual(result['coverage_status'], 'incomplete')
        self.assertEqual(result['last_checked_at'], T1)
        self.assertEqual(result['last_successful_fetch_at'], baseline['last_successful_fetch_at'])
        self.assertEqual(result['records'], baseline['records'])
        self.assertEqual(result['error_code'], 'provider_request_failed' if status == 'failed'
                         else 'response_requires_review')

    def test_initial_unknown_and_success_source_identity_for_all_five_pilots(self):
        adapter = self.adapter()
        for code in ('yose', 'romo', 'yell', 'zion', 'grca'):
            with self.subTest(code=code):
                initial = adapter.initial_activities(code)
                self.assertEqual(initial['source_url'], f'https://developer.nps.gov/api/v1/thingstodo?parkCode={code}')
                self.assertEqual(initial['records'], [])
                self.assertIsNone(initial['last_successful_fetch_at'])
                self.assertEqual(adapter.activity_freshness(initial, T0), 'not_collected')
                self.assertEqual(adapter.validate_activities(initial), initial)
                value = self.collected(code=code)
                self.assertEqual(value['collection_status'], 'success')
                self.assertEqual(value['coverage_status'], 'checked_activity_feed_only')
                self.assertEqual(value['records'][0]['park_code'], code)
                self.assertEqual(value['last_checked_at'], T0)
                self.assertEqual(value['last_successful_fetch_at'], T0)

    def test_normalized_source_text_relationship_and_hash_preserve_interpretation_limits(self):
        record = self.collected()['records'][0]
        self.assertEqual(record['description'], 'Synthetic café 🏞 introduction.')
        self.assertEqual(record['long_description'], '<p>Synthetic trail continues outside the park.</p>')
        self.assertEqual(record['location'], 'Synthetic trailhead')
        self.assertEqual(record['location_description'], 'Synthetic route crosses a boundary.')
        self.assertEqual(record['duration'], '1-2 hours')
        self.assertEqual(record['duration_description'], 'Synthetic estimate varies.')
        self.assertEqual(record['seasons'], ['Fall', 'Winter'])
        self.assertEqual(record['times_of_day'], ['Dawn', 'Day'])
        self.assertEqual(record['accessibility_information'], '<p>Synthetic accessibility information.</p>')
        self.assertEqual(record['activity_categories'], [{'id': 'a', 'name': 'Hiking'}, {'id': 'b', 'name': 'Wildlife Watching'}])
        self.assertFalse(record['fees_apply'])
        self.assertTrue(record['reservation_required'])
        self.assertFalse(record['pets_permitted'])
        self.assertEqual(record['credit'], 'Synthetic credit; not a licence.')
        self.assertEqual(record['geographic_relationship'], 'unconfirmed')
        for key in ('responsible_agency', 'difficulty', 'permit_required', 'source_updated_at'):
            self.assertIsNone(record[key])
        for key in ('images', 'relatedOrganizations', 'latitude', 'longitude', 'geometryPoiId', 'amenities', 'relevanceScore'):
            self.assertNotIn(key, record)
        expected = copy.deepcopy(record)
        rehash(expected)
        self.assertEqual(record['content_hash'], expected['content_hash'])
        self.assertEqual(record['observed_first_at'], T0)
        self.assertEqual(record['observed_changed_at'], T0)

    def test_missing_null_empty_text_and_empty_lists_are_distinct(self):
        raw = activity(shortDescription=None, longDescription='', duration=None, durationDescription='',
                       season=[], seasonDescription=None, activities=None, timeOfDay=[], doFeesApply='',
                       isReservationRequired=None, arePetsPermitted=None)
        del raw['accessibilityInformation']
        record = self.collected([raw])['records'][0]
        self.assertIsNone(record['description'])
        self.assertEqual(record['long_description'], '')
        self.assertIsNone(record['duration'])
        self.assertEqual(record['duration_description'], '')
        self.assertEqual(record['seasons'], [])
        self.assertIsNone(record['season_description'])
        self.assertIsNone(record['activity_categories'])
        self.assertIsNone(record['accessibility_information'])
        self.assertEqual(record['times_of_day'], [])
        for key in ('fees_apply', 'reservation_required', 'pets_permitted'):
            self.assertIsNone(record[key])

    def test_explicit_boolean_and_string_flags_normalize_without_truthiness(self):
        for raw, expected in ((True, True), (False, False), ('true', True), ('false', False), ('', None), (None, None)):
            with self.subTest(raw=raw):
                record = self.collected([activity(doFeesApply=raw)])['records'][0]
                self.assertIs(record['fees_apply'], expected)
        for raw in (0, 1, '0', 'FALSE', ' true ', [], {}):
            with self.subTest(raw=raw):
                value = self.collected([activity(doFeesApply=raw)])
                self.assertEqual(value['collection_status'], 'quarantined')

    def test_documented_pet_flag_aliases_agree_or_refuse_conflicts(self):
        raw = activity()
        del raw['arePetsPermittedWithRestrictions']
        raw['arePetsPermittedwithRestrictions'] = 'true'
        self.assertTrue(self.collected([raw])['records'][0]['pets_permitted_with_restrictions'])
        raw['arePetsPermittedWithRestrictions'] = True
        self.assertEqual(self.collected([raw])['collection_status'], 'success')
        raw['arePetsPermittedWithRestrictions'] = False
        self.assertEqual(self.collected([raw])['collection_status'], 'quarantined')

    def test_related_park_attribution_never_proves_geography_or_responsible_agency(self):
        raw = activity()
        raw['relatedParks'].append({'parkCode': 'lavo', 'fullName': 'Synthetic other park',
                                    'url': 'https://www.nps.gov/lavo/index.htm'})
        record = self.collected([raw])['records'][0]
        self.assertEqual([park['park_code'] for park in record['related_parks']], ['lavo', 'yose'])
        self.assertIsNone(record['related_parks'][0]['states'])
        self.assertEqual(record['geographic_relationship'], 'unconfirmed')
        self.assertIsNone(record['responsible_agency'])
        raw['url'] = 'https://www.nps.gov/lavo/planyourvisit/synthetic.htm'
        self.assertEqual(self.collected([raw])['collection_status'], 'success')

    def test_missing_cross_park_and_malformed_associations_quarantine_the_complete_candidate(self):
        for related in (None, [], [{'parkCode': 'yell'}], [{'parkCode': 'yose', 'url': 'https://www.nps.gov/yell/index.htm'}],
                        [{'parkCode': 'YOSE'}], [{'parkCode': True}], [{'parkCode': 'yose'}, {'parkCode': 'yose'}]):
            with self.subTest(related=related):
                self.assertEqual(self.collected([activity(relatedParks=related)])['collection_status'], 'quarantined')

    def test_unsafe_official_urls_never_replace_last_good_evidence(self):
        adapter = self.adapter()
        baseline = self.collected()
        for url in ('http://www.nps.gov/thingstodo/a.htm', 'https://nps.gov.evil.example/thingstodo/a.htm',
                    'https://user:secret@www.nps.gov/thingstodo/a.htm', 'https://www.nps.gov:444/thingstodo/a.htm',
                    'https://www.nps.gov//thingstodo/a.htm', 'https://www.nps.gov/thingstodo/%2e%2e/yose/a.htm',
                    'https://www.nps.gov/thingstodo/%252e%252e/a.htm', 'https://www.nps.gov/thingstodo/a.htm?api%5fkey=secret',
                    'https://www.nps.gov/thingstodo/a.htm#to%6ben=secret', 'https://www.nps.gov/yell/a.htm',
                    'https://www.nps.gov/thingstodo/a\\b.htm', 'https://www.nps.gov/thingstodo/a.htm\n'):
            with self.subTest(url=url):
                result = adapter.collect_activities('yose', baseline, T1, lambda _start: page([activity(url=url)]))
                self.retained(result, baseline)

    def test_nested_duplicates_and_invalid_optional_fields_quarantine(self):
        for changes in ({'activities': [{'id': 'a', 'name': 'Hike'}, {'id': 'a', 'name': 'Other'}]},
                        {'activities': [{'id': 'a', 'name': 3}]}, {'season': ['Winter', 'Winter']},
                        {'season': [False]}, {'timeOfDay': {}}, {'duration': 0}, {'shortDescription': []},
                        {'title': ''}, {'id': '\x00'}, {'credit': '\ud800'},
                        {'longDescription': 'x' * 65537}):
            with self.subTest(changes=changes):
                self.assertEqual(self.collected([activity(**changes)])['collection_status'], 'quarantined')

    def test_complete_pagination_is_sorted_and_detached_from_payloads(self):
        adapter = self.adapter()
        first, second = activity('z'), activity('a')
        expected_first = copy.deepcopy(first)
        offsets = []
        def fetch(start):
            offsets.append(start)
            if start == 0:
                return page([first], total=2)
            first['activities'].clear()
            return page([second], total=2, start=1)
        value = adapter.collect_activities('yose', adapter.initial_activities('yose'), T0, fetch)
        self.assertEqual(offsets, [0, 1])
        self.assertEqual([record['id'] for record in value['records']], ['a', 'z'])
        self.assertEqual(value['records'][1]['activity_categories'][0]['name'], expected_first['activities'][1]['name'])
        value['records'][0]['related_parks'].clear()
        self.assertEqual(len(second['relatedParks']), 1)

    def test_hostile_pagination_retains_baseline_and_discards_partial_results(self):
        adapter = self.adapter()
        baseline = self.collected()
        candidates = [page([activity('b')], total=3, start=1), page([activity('a')], total=2, start=0),
                      page([activity('a')], total=2, start=1), page([], total=2, start=1),
                      page([activity('b'), activity('c')], total=2, start=1),
                      page([activity('b')], total=2, start=1, limit='0')]
        for later in candidates:
            with self.subTest(later=later):
                result = adapter.collect_activities('yose', baseline, T1,
                    lambda start: page([activity('a')], total=2) if start == 0 else later)
                self.retained(result, baseline)

    def test_duplicate_ids_on_first_page_refuse(self):
        self.assertEqual(self.collected([activity(), activity()])['collection_status'], 'quarantined')

    def test_strict_counts_and_total_bound_refuse_before_partial_success(self):
        adapter = self.adapter()
        for total in (True, False, -1, 1.0, ' 1', '+1', '-1', '\u0661', '1.0', 5001, '999999999', None):
            with self.subTest(total=total):
                result = adapter.collect_activities('yose', adapter.initial_activities('yose'), T0,
                    lambda _start: page([activity()], total=total) if total is not None else {'data': [], 'start': '0'})
                self.assertEqual(result['collection_status'], 'quarantined')
        self.assertEqual(self.collected([activity()])['collection_status'], 'success')

    def test_page_limit_terminates_with_original_evidence(self):
        adapter = self.adapter()
        baseline = self.collected()
        offsets = []
        def fetch(start):
            offsets.append(start)
            return page([activity(f'item-{start:03d}')], total=101, start=start)
        value = adapter.collect_activities('yose', baseline, T1, fetch)
        self.assertEqual(offsets, list(range(100)))
        self.retained(value, baseline)

    def test_later_page_transport_failure_or_explicit_refusal_retains_original_success(self):
        adapter = self.adapter()
        baseline = self.collected()
        for error, status in ((TimeoutError('secret'), 'failed'), (OSError('secret'), 'failed'),
                              (adapter.ActivityCollectionError('secret'), 'failed'),
                              (adapter.ActivityError('secret'), 'quarantined')):
            with self.subTest(status=status, error=type(error)):
                def fetch(start):
                    if start == 0:
                        return page([activity('new')], total=2)
                    raise error
                result = adapter.collect_activities('yose', baseline, T1, fetch)
                self.retained(result, baseline, status)
                self.assertNotIn('secret', json.dumps(result))

    def test_initial_failure_retains_unknown_and_unexpected_transport_errors_propagate(self):
        adapter = self.adapter()
        def failed(_start):
            raise adapter.ActivityCollectionError('private key')
        value = adapter.collect_activities('yose', adapter.initial_activities('yose'), T0, failed)
        self.assertEqual(value['records'], [])
        self.assertIsNone(value['last_successful_fetch_at'])
        self.assertEqual(value['collection_status'], 'failed')
        self.assertNotIn('private key', json.dumps(value))
        def unexpected(_start):
            raise RuntimeError('programming fault')
        with self.assertRaisesRegex(RuntimeError, 'programming fault'):
            adapter.collect_activities('yose', adapter.initial_activities('yose'), T0, unexpected)

    def test_complete_empty_baseline_is_checked_inventory_not_unknown(self):
        adapter = self.adapter()
        value = self.collected([])
        self.assertEqual(value['collection_status'], 'success')
        self.assertEqual(value['coverage_status'], 'checked_activity_feed_only')
        self.assertEqual(value['records'], [])
        self.assertEqual(value['last_successful_fetch_at'], T0)
        self.assertEqual(adapter.activity_freshness(value, T0), 'fresh')

    def test_below_half_or_empty_drop_quarantines_but_exact_half_is_accepted(self):
        adapter = self.adapter()
        baseline = self.collected([activity(str(number)) for number in range(4)])
        for count, status in ((0, 'quarantined'), (1, 'quarantined'), (2, 'success')):
            with self.subTest(count=count):
                value = adapter.collect_activities('yose', baseline, T1,
                    lambda _start: page([activity(str(number)) for number in range(count)]))
                self.assertEqual(value['collection_status'], status)
                if status == 'quarantined':
                    self.retained(value, baseline)

    def test_observation_clocks_follow_semantic_changes_and_recovery(self):
        adapter = self.adapter()
        first = self.collected()
        raw = activity()
        raw['activities'].reverse()
        raw['season'].reverse()
        second = adapter.collect_activities('yose', first, T1, lambda _start: page([raw]))
        self.assertEqual(second['records'], first['records'])
        third = adapter.collect_activities('yose', second, T2,
            lambda _start: page([activity(title='Changed source title'), activity('new-id')]))
        by_id = {record['id']: record for record in third['records']}
        self.assertEqual(by_id['synthetic-a']['observed_first_at'], T0)
        self.assertEqual(by_id['synthetic-a']['observed_changed_at'], T2)
        self.assertEqual(by_id['new-id']['observed_first_at'], T2)
        self.assertNotEqual(by_id['synthetic-a']['content_hash'], first['records'][0]['content_hash'])

    def test_callback_mutation_of_caller_baseline_cannot_rewrite_retained_or_unchanged_records(self):
        adapter = self.adapter()
        original = self.collected()
        for mode in ('failed', 'quarantined', 'success'):
            baseline = copy.deepcopy(original)
            def fetch(_start):
                baseline['records'][0]['title'] = 'Callback changed caller'
                baseline['records'][0]['observed_first_at'] = T1
                rehash(baseline['records'][0])
                baseline['last_successful_fetch_at'] = T2
                if mode == 'failed':
                    raise TimeoutError('discard')
                if mode == 'quarantined':
                    return page([activity(relatedParks=[])])
                return page([activity()])
            value = adapter.collect_activities('yose', baseline, T1, fetch)
            self.assertEqual(value['records'], original['records'])
            if mode != 'success':
                self.retained(value, original, mode)
            else:
                self.assertEqual(value['last_successful_fetch_at'], T1)

    def test_validation_defensive_copy_and_no_input_mutation_during_collection(self):
        adapter = self.adapter()
        previous, raw = self.collected(), activity(title='New title')
        before, raw_before = copy.deepcopy(previous), copy.deepcopy(raw)
        checked = adapter.validate_activities(previous)
        checked['records'][0]['related_parks'].clear()
        adapter.collect_activities('yose', previous, T1, lambda _start: page([raw]))
        self.assertEqual(previous, before)
        self.assertEqual(raw, raw_before)

    def test_nonpilot_invalid_baseline_and_clock_are_refused_before_transport(self):
        adapter = self.adapter()
        def forbidden(_start):
            self.fail('Invalid evidence must fail before transport.')
        for code in ('acad', 'YOSE', None, True, [], {}):
            with self.subTest(code=code):
                with self.assertRaises(adapter.ActivityError):
                    adapter.collect_activities(code, adapter.initial_activities('yose'), T0, forbidden)
        baseline = self.collected()
        for now in (T0, '2026-10-03T06:00:00-04:00', '2026-10-03T09:59:59Z', '2026-02-30T10:00:00Z', None):
            with self.subTest(now=now):
                with self.assertRaises(adapter.ActivityError):
                    adapter.collect_activities('yose', baseline, now, forbidden)
        for field, value in (('schema_version', True), ('park_code', 'yell'), ('provider', 'Other'),
                             ('source_updated_at', T0), ('source_issued_at', T0), ('published_at', T0),
                             ('coverage_status', 'all_activities_available'), ('last_successful_fetch_at', T2),
                             ('error_code', 'secret'), ('records', {})):
            changed = copy.deepcopy(baseline)
            changed[field] = value
            with self.subTest(field=field):
                with self.assertRaises(adapter.ActivityError):
                    adapter.collect_activities('yose', changed, T1, forbidden)

    def test_rehashed_malformed_record_does_not_bypass_previous_validation(self):
        adapter = self.adapter()
        baseline = self.collected()
        for field, value in (('geographic_relationship', 'inside'), ('responsible_agency', 'NPS'),
                             ('difficulty', 'easy'), ('permit_required', False), ('fees_apply', 'false'),
                             ('related_parks', []), ('seasons', ['Winter', 'Winter']), ('duration', 0)):
            changed = copy.deepcopy(baseline)
            changed['records'][0][field] = value
            rehash(changed['records'][0])
            with self.subTest(field=field):
                with self.assertRaises(adapter.ActivityError):
                    adapter.validate_activities(changed)
        changed = copy.deepcopy(baseline)
        changed['records'][0]['observed_changed_at'] = T2
        with self.assertRaises(adapter.ActivityError):
            adapter.validate_activities(changed)

    def test_unknown_normalized_fields_and_altered_hash_are_refused(self):
        adapter = self.adapter()
        baseline = self.collected()
        for extra in ('snapshot', 'record', 'hash'):
            changed = copy.deepcopy(baseline)
            if extra == 'snapshot':
                changed['unreviewed'] = 'extra'
            elif extra == 'record':
                changed['records'][0]['unreviewed'] = 'extra'
                rehash(changed['records'][0])
            else:
                changed['records'][0]['content_hash'] = '0' * 64
            with self.subTest(extra=extra):
                with self.assertRaises(adapter.ActivityError):
                    adapter.validate_activities(changed)

    def test_freshness_exact_microsecond_boundary_failed_precedence_and_future_refusal(self):
        adapter = self.adapter()
        value = self.collected(at='2026-10-03T10:00:00.000001Z')
        self.assertEqual(adapter.activity_freshness(value, '2026-10-10T10:00:00Z'), 'fresh')
        self.assertEqual(adapter.activity_freshness(value, '2026-10-10T10:00:00.000001Z'), 'stale')
        self.assertEqual(adapter.activity_freshness(value, '2026-10-10T10:00:00.000002Z'), 'stale')
        for error, status in ((TimeoutError(), 'failed'), (adapter.ActivityError(), 'quarantined')):
            def fail(_start):
                raise error
            failed = adapter.collect_activities('yose', value, T1, fail)
            self.assertEqual(adapter.activity_freshness(failed, '2026-11-01T10:00:00Z'), status)
        with self.assertRaises(adapter.ActivityError):
            adapter.activity_freshness(value, T0)

    def test_programmatic_bounded_inventory_refuses_oversized_normalized_record(self):
        raw = activity(**{field: 'x' * 65536 for field in ('shortDescription', 'longDescription',
                       'locationDescription', 'accessibilityInformation', 'reservationDescription')})
        self.assertEqual(self.collected([raw])['collection_status'], 'quarantined')

    def test_aggregate_inventory_limit_stops_pagination_and_preserves_last_good(self):
        adapter = self.adapter()
        baseline = self.collected()
        offsets = []
        large = {field: 'x' * 50000 for field in ('shortDescription', 'longDescription',
                  'accessibilityInformation', 'reservationDescription')}
        def fetch(start):
            offsets.append(start)
            return page([activity(f'item-{number:03d}', **large)
                         for number in range(start, start + 30)], total=90, start=start)
        result = adapter.collect_activities('yose', baseline, T1, fetch)
        self.retained(result, baseline)
        self.assertEqual(offsets, [0, 30])
        oversized = self.collected([activity('large', **large)])
        template = oversized['records'][0]
        oversized['records'] = []
        for number in range(45):
            record = copy.deepcopy(template)
            record['id'] = f'item-{number:03d}'
            rehash(record)
            oversized['records'].append(record)
        with self.assertRaises(adapter.ActivityError):
            adapter.validate_activities(oversized)

    def test_exact_snapshot_size_limit_is_accepted_and_one_byte_over_is_refused(self):
        adapter = self.adapter()
        value = self.collected()
        size = len(json.dumps(value, ensure_ascii=False, sort_keys=True,
                              separators=(',', ':')).encode('utf-8'))
        with patch.object(adapter, 'MAX_SNAPSHOT_BYTES', size):
            self.assertEqual(adapter.validate_activities(value), value)
            self.assertEqual(self.collected(), value)
        with patch.object(adapter, 'MAX_SNAPSHOT_BYTES', size - 1):
            with self.assertRaises(adapter.ActivityError):
                adapter.validate_activities(value)
            self.assertEqual(self.collected()['collection_status'], 'quarantined')

    def test_incoherent_initial_and_degraded_states_refuse_without_success_evidence(self):
        adapter = self.adapter()
        for field, value in (('records', self.collected()['records']), ('last_checked_at', T0),
                             ('coverage_status', 'incomplete'), ('error_code', 'provider_request_failed')):
            changed = adapter.initial_activities('yose')
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(adapter.ActivityError):
                adapter.validate_activities(changed)
        changed = self.collected()
        changed.update(collection_status='failed', coverage_status='incomplete',
                       error_code='provider_request_failed', last_successful_fetch_at=None)
        with self.assertRaises(adapter.ActivityError):
            adapter.validate_activities(changed)

    def test_insufficient_failure_metadata_capacity_refuses_before_transport(self):
        adapter = self.adapter()
        baseline = self.collected()
        original = copy.deepcopy(baseline)
        size = len(json.dumps(baseline, ensure_ascii=False, sort_keys=True,
                              separators=(',', ':')).encode('utf-8'))
        def forbidden(_start):
            self.fail('A refresh must be able to retain its failure metadata before requesting.')
        with patch.object(adapter, 'MAX_SNAPSHOT_BYTES', size):
            with self.assertRaises(adapter.ActivityError):
                adapter.collect_activities('yose', baseline, T1, forbidden)
        self.assertEqual(baseline, original)
        def failed(_start):
            raise TimeoutError('not retained')
        def refused(_start):
            raise adapter.ActivityError('not retained')
        outcomes = [adapter.collect_activities('yose', baseline, T1, fetch)
                    for fetch in (failed, refused)]
        capacity = max(len(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode('utf-8')) for result in outcomes)
        with patch.object(adapter, 'MAX_SNAPSHOT_BYTES', capacity):
            for fetch, expected in zip((failed, refused), outcomes):
                result = adapter.collect_activities('yose', baseline, T1, fetch)
                self.assertEqual(adapter.validate_activities(result), expected)

    def test_odd_drop_boundary_and_recovery_keep_original_observation_clocks(self):
        adapter = self.adapter()
        original = self.collected([activity(str(number)) for number in range(5)])
        rejected = adapter.collect_activities('yose', original, T1,
            lambda _start: page([activity('0'), activity('1')]))
        self.retained(rejected, original)
        recovered = adapter.collect_activities('yose', rejected, T2,
            lambda _start: page([activity('0'), activity('1'), activity('2')]))
        self.assertEqual(recovered['collection_status'], 'success')
        self.assertEqual(recovered['last_successful_fetch_at'], T2)
        self.assertEqual(recovered['records'], original['records'][:3])


if __name__ == '__main__':
    unittest.main()
