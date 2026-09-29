import copy
import unittest
from history_fixtures import T0, T1, T2, notice, snapshot, next_snapshot, digest
from tracker.history_model import HistoryError, compare, validate_snapshot

class ModelTests(unittest.TestCase):
    def test_first_success_is_baseline_not_new_closures(self):
        self.assertEqual(compare(None, snapshot()), {'comparison': 'baseline', 'changes': []})

    def test_empty_success_is_a_baseline_not_an_all_clear(self):
        self.assertEqual(compare(None, snapshot([])), {'comparison': 'baseline', 'changes': []})

    def test_reordering_and_check_clock_alone_do_not_change_notices(self):
        old = snapshot([notice('a'), notice('b')])
        new = next_snapshot(old, records=list(reversed(old['records'])))
        self.assertEqual(compare(old, new), {'comparison': 'compared', 'changes': []})
        self.assertEqual(new['records'][0]['observed_changed_at'], T0)

    def test_add_edit_and_disappearance_have_before_and_after_evidence(self):
        old = snapshot([notice('a'), notice('b'), notice('c')])
        edited = notice('a', now=T1, title='Revised synthetic wording')
        edited['observed_first_at'] = T0
        new = next_snapshot(old, records=[edited, old['records'][1], notice('d', now=T1)])
        changes = compare(old, new)['changes']
        self.assertEqual([item['kind'] for item in changes], ['edited', 'removed', 'added'])
        self.assertEqual(changes[0]['before_hash'], old['records'][0]['content_hash'])
        self.assertEqual(changes[0]['after_hash'], edited['content_hash'])
        self.assertEqual(changes[1]['record_id'], 'c')
        self.assertIsNone(changes[1]['after_hash'])
        self.assertIsNone(changes[2]['before_hash'])
        self.assertNotIn('reopened', str(changes))

    def test_failed_and_quarantined_attempts_never_generate_removals(self):
        old = snapshot()
        for status in ('failed', 'quarantined'):
            self.assertEqual(compare(old, next_snapshot(old, status=status)), {'comparison': 'not_compared', 'changes': []})

    def test_failed_attempt_cannot_rewrite_last_good_data_or_clock(self):
        old = snapshot()
        for field, value in [('records', []), ('last_successful_fetch_at', T1), ('records', [notice(title='Tampered')])]:
            bad = next_snapshot(old, status='failed'); bad[field] = value
            with self.subTest(field=field), self.assertRaises(HistoryError):
                compare(old, bad)

    def test_recovery_compares_with_retained_last_success(self):
        old = snapshot([notice('a'), notice('b')])
        failed = next_snapshot(old, status='failed')
        recovered = next_snapshot(failed, now=T2, records=[old['records'][1]])
        self.assertEqual(compare(failed, recovered)['changes'][0]['record_id'], 'a')

    def test_first_success_after_initial_failure_is_still_baseline(self):
        failed = next_snapshot(snapshot([]), status='failed'); failed['last_successful_fetch_at'] = None
        self.assertEqual(compare(None, failed)['comparison'], 'not_compared')
        self.assertEqual(compare(failed, snapshot(now=T2))['comparison'], 'baseline')

    def test_missing_baseline_cannot_import_retained_records_as_known_history(self):
        with self.assertRaises(HistoryError):
            compare(None, next_snapshot(snapshot(), status='failed'))

    def test_identical_retry_is_idempotent_but_conflicting_same_instant_is_not(self):
        old = snapshot()
        self.assertEqual(compare(old, copy.deepcopy(old))['comparison'], 'duplicate')
        bad = snapshot([notice(title='Different response at same instant')])
        with self.assertRaises(HistoryError): compare(old, bad)
        with self.assertRaises(HistoryError): compare(next_snapshot(old), old)

    def test_suspicious_success_drop_is_rejected_even_if_snapshot_claims_success(self):
        with self.assertRaises(HistoryError): compare(snapshot(), snapshot([], now=T1))

    def test_new_existing_and_edited_record_observation_clocks_are_validated(self):
        old = snapshot()
        for item in [notice(now=T1), notice(title='Edited without updated change time')]:
            with self.subTest(item=item), self.assertRaises(HistoryError):
                compare(old, next_snapshot(old, records=[item]))
        with self.assertRaises(HistoryError):
            compare(old, next_snapshot(old, records=[old['records'][0], notice('new')]))

    def test_reappearing_id_is_added_without_claiming_when_conditions_changed(self):
        old = snapshot([notice('a'), notice('b')])
        removed = next_snapshot(old, records=[old['records'][1]])
        returned = next_snapshot(removed, T2, records=[old['records'][1], notice('a', now=T2)])
        self.assertEqual(compare(removed, returned)['changes'][0]['kind'], 'added')

    def test_record_hash_and_excerpt_tampering_are_rejected(self):
        for field, value in [('title', 'tampered'), ('content_hash', '0'*64), ('evidence_excerpt', 'wrong')]:
            bad = snapshot(); bad['records'][0][field] = value
            with self.subTest(field=field), self.assertRaises(HistoryError): validate_snapshot(bad)

    def test_schema_rejects_secret_headers_unknown_fields_and_duplicate_ids(self):
        bad = snapshot(); bad['request_headers'] = {'X-Api-Key': 'must-not-persist'}
        with self.assertRaises(HistoryError): validate_snapshot(bad)
        bad = snapshot(); bad['records'][0]['token'] = 'must-not-persist'
        with self.assertRaises(HistoryError): validate_snapshot(bad)
        with self.assertRaises(HistoryError): validate_snapshot(snapshot([notice(), notice()]))

    def test_never_checked_is_not_an_observation(self):
        bad = snapshot([]); bad.update(collection_status='never_checked', coverage_status='not_collected', last_checked_at=None, last_successful_fetch_at=None)
        with self.assertRaises(HistoryError): validate_snapshot(bad)

    def test_unknown_status_boolean_version_and_fake_publisher_times_fail_closed(self):
        for field, value in [('schema_version', True), ('collection_status', 'open'), ('source_updated_at', T0), ('published_at', T1), ('error_code', 'raw exception text')]:
            bad = snapshot(); bad[field] = value
            with self.subTest(field=field), self.assertRaises(HistoryError): validate_snapshot(bad)

    def test_alert_urls_are_optional_but_nonempty_links_must_be_safe_nps_urls(self):
        for url in [None, 'https://go.nps.gov/short-link', 'https://www.nps.gov/subjects/developer/index.htm']:
            with self.subTest(url=url):
                validate_snapshot(snapshot([notice(url=url)]))
        urls = ['https://www.nps.gov/yose/test?token=key', 'https://www.nps.gov/yose/test#api_key=key',
                'https://www.nps.gov.evil.test/yose/test', 'https://example.com/yose/test',
                'https://user:password@www.nps.gov/yose/test', 'https://www.nps.gov/yose/../grca/test',
                'https://www.nps.gov/yose/%2e%2e/grca/test', 'https://www.nps.gov/yose/te\nst']
        for url in urls:
            with self.subTest(url=url), self.assertRaises(HistoryError): validate_snapshot(snapshot([notice(url=url)]))
        bad = snapshot(); bad['source_url'] += '&api_key=key'
        with self.assertRaises(HistoryError): validate_snapshot(bad)

    def test_bad_calendar_and_offset_timestamps_do_not_normalize(self):
        for now in ['2026-02-30T10:00:00Z', '2026-09-28T24:00:00Z', '2026-09-28T10:00:00+00:99', '2026-09-28']:
            with self.subTest(now=now), self.assertRaises(HistoryError): validate_snapshot(snapshot([], now=now))

    def test_valid_offsets_are_compared_as_instants_not_lexical_strings(self):
        old = snapshot([], now='2026-09-28T10:00:00+02:00')
        new = snapshot([], now='2026-09-28T09:00:00Z')
        self.assertEqual(compare(old, new)['comparison'], 'compared')

    def test_validation_is_a_defensive_copy_and_preserves_unicode_text(self):
        original = snapshot([notice(description='Synthetic café 🏞 text')]); result = validate_snapshot(original)
        self.assertEqual(result, original)
        result['records'].clear()
        self.assertEqual(len(original['records']), 1)

    def test_cross_park_snapshots_cannot_share_a_history(self):
        with self.assertRaises(HistoryError): compare(snapshot(), snapshot(now=T1, code='grca'))

if __name__ == '__main__': unittest.main()
