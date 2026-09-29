"""Synthetic provider fixtures. Tests make no network calls."""
import tempfile
import unittest
from pathlib import Path
from tracker.alerts import collect, initial_snapshot, write_snapshot
NOW = '2026-09-28T20:00:00Z'
OLD = '2026-09-28T18:00:00Z'
def record(identifier='a', **changes):
    value = {'id': identifier, 'parkCode': 'yose', 'title': 'Synthetic closure', 'description': 'A test facility only.', 'category': 'Park Closure', 'url': 'https://www.nps.gov/yose/test.htm'}
    return {**value, **changes}
def page(records, total=None, start=0):
    return {'total': str(len(records) if total is None else total), 'start': str(start), 'limit': '50', 'data': records}
class CollectorTests(unittest.TestCase):
    def previous(self):
        return collect('yose', initial_snapshot('yose'), OLD, lambda start: page([record()]))
    def test_initial_state_is_not_empty_success(self):
        self.assertEqual(initial_snapshot('yose')['collection_status'], 'never_checked')
        self.assertIsNone(initial_snapshot('yose')['last_successful_fetch_at'])
    def test_real_empty_response_is_success_with_limited_scope(self):
        result = collect('yose', initial_snapshot('yose'), NOW, lambda start: page([]))
        self.assertEqual(result['collection_status'], 'success')
        self.assertEqual(result['coverage_status'], 'checked_feed_only')
        self.assertEqual(result['records'], [])
    def test_failure_retains_last_good_records_and_success_time(self):
        old = self.previous()
        def failure(start):
            raise TimeoutError('contains a simulated secret; do not echo')
        result = collect('yose', old, NOW, failure)
        self.assertEqual(result['collection_status'], 'failed')
        self.assertEqual(result['last_checked_at'], NOW)
        self.assertEqual(result['last_successful_fetch_at'], OLD)
        self.assertEqual(result['records'], old['records'])
        self.assertNotIn('simulated secret', str(result))
        self.assertEqual(old['collection_status'], 'success')
    def test_pagination_is_exhausted(self):
        result = collect('yose', initial_snapshot('yose'), NOW, lambda start: page([record(str(start))], total=2, start=start))
        self.assertEqual(len(result['records']), 2)
        self.assertEqual(result['collection_status'], 'success')
    def test_diagnostic_mode_exposes_only_allowlisted_validation_reason(self):
        bad = record(parkCode='grca')
        normal = collect('yose', initial_snapshot('yose'), NOW, lambda start: page([bad]))
        diagnostic = collect('yose', initial_snapshot('yose'), NOW, lambda start: page([bad]), diagnostic=True)
        self.assertEqual(normal['error_code'], 'response_requires_review')
        self.assertEqual(diagnostic['error_code'], 'park_code_mismatch')

    def test_optional_url_and_official_nps_subdomains_are_accepted(self):
        empty_url = collect('yose', initial_snapshot('yose'), NOW, lambda start: page([record(url='')]), diagnostic=True)
        short_link = collect('yose', initial_snapshot('yose'), NOW, lambda start: page([record(url='https://go.nps.gov/short-link')]), diagnostic=True)
        shared_path = collect('yose', initial_snapshot('yose'), NOW, lambda start: page([record(url='https://www.nps.gov/subjects/developer/index.htm')]), diagnostic=True)
        self.assertEqual(empty_url['collection_status'], 'success')
        self.assertIsNone(empty_url['records'][0]['url'])
        self.assertEqual(short_link['collection_status'], 'success')
        self.assertEqual(shared_path['collection_status'], 'success')

    def test_missing_or_inconsistent_pages_are_quarantined(self):
        cases = [lambda start: page([], total=2), lambda start: page([record()], total=2, start=0), lambda start: {'error': 'provider error'}, lambda start: page([record()], total='bad')]
        for fetch in cases:
            with self.subTest(fetch=fetch):
                self.assertEqual(collect('yose', initial_snapshot('yose'), NOW, fetch)['collection_status'], 'quarantined')
    def test_schema_invalid_records_are_not_published(self):
        bad_records = [record(parkCode='grca'), record(url='javascript:alert(1)'), record(url='https://www.nps.gov.evil.test/a'), record(url='https://www.nps.gov@evil.test/a'), record(title=''), record(description=7)]
        for bad in bad_records:
            with self.subTest(record=bad):
                self.assertEqual(collect('yose', initial_snapshot('yose'), NOW, lambda start: page([bad]))['collection_status'], 'quarantined')
    def test_duplicate_ids_fail(self):
        result = collect('yose', initial_snapshot('yose'), NOW, lambda start: page([record(), record()]))
        self.assertEqual(result['collection_status'], 'quarantined')
    def test_large_record_drop_cannot_delete_last_good_history(self):
        old = self.previous()
        result = collect('yose', old, NOW, lambda start: page([]))
        self.assertEqual(result['collection_status'], 'quarantined')
        self.assertEqual(result['records'], old['records'])
    def test_record_scope_is_not_promoted_to_whole_park(self):
        item = self.previous()['records'][0]
        self.assertIsNone(item['area_id'])
        self.assertEqual(item['scope_status'], 'unclassified')
        self.assertNotIn('park_is_closed', item)
        self.assertIsNone(item['effective_from'])
        self.assertIsNone(item['source_updated_at'])
    def test_record_hash_is_stable_and_escapes_are_not_interpreted(self):
        result = collect('yose', initial_snapshot('yose'), NOW, lambda start: page([record(title='<script>bad()</script>')]))
        item = result['records'][0]
        self.assertEqual(len(item['content_hash']), 64)
        self.assertEqual(item['title'], '<script>bad()</script>')
        self.assertEqual(result['collection_status'], 'success')
    def test_invalid_or_backward_clock_does_not_touch_snapshot(self):
        for now in ['bad', '2026-09-28', '2026-09-27T00:00:00Z']:
            with self.subTest(now=now):
                with self.assertRaises(ValueError):
                    collect('yose', self.previous(), now, lambda start: page([]))
    def test_provider_supplied_external_https_links_are_allowed_but_unsafe_hosts_are_rejected(self):
        external = collect('yose', initial_snapshot('yose'), NOW, lambda start: page([record(url='https://inciweb.wildfire.gov/incident/example')]), diagnostic=True)
        self.assertEqual(external['collection_status'], 'success')
        self.assertEqual(external['records'][0]['url'], 'https://inciweb.wildfire.gov/incident/example')
        for url in ['https://www.nps.gov.evil.test/yose/test', 'https://localhost/yose/test', 'https://127.0.0.1/yose/test']:
            with self.subTest(url=url):
                result = collect('yose', initial_snapshot('yose'), NOW, lambda start, url=url: page([record(url=url)]), diagnostic=True)
                self.assertEqual(result['collection_status'], 'quarantined')
    def test_previous_success_cannot_be_later_than_previous_attempt(self):
        previous = self.previous()
        previous['last_checked_at'] = '2026-09-28T17:00:00Z'
        with self.assertRaises(ValueError):
            collect('yose', previous, NOW, lambda start: page([record()]))
    def test_atomic_writer_round_trip(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'snapshot.json'
            write_snapshot(path, self.previous())
            self.assertEqual(json.loads(path.read_text())['last_successful_fetch_at'], OLD)
            self.assertEqual(len(list(Path(folder).iterdir())), 1)
class TransportTests(unittest.TestCase):
    def test_api_key_is_private_header_not_url(self):
        import io
        from tracker.alerts import request_page
        def opener(request, timeout):
            self.assertEqual(timeout, 20)
            self.assertNotIn('synthetic-private-key', request.full_url)
            self.assertEqual(request.get_header('X-api-key'), 'synthetic-private-key')
            return io.BytesIO(b'{"total":"0","start":"0","data":[]}')
        self.assertEqual(request_page('yose', 0, 'synthetic-private-key', opener=opener)['total'], '0')
    def test_retry_budget_and_wait_are_bounded(self):
        from urllib.error import HTTPError
        from tracker.alerts import request_page, CollectionError
        attempts, waits = [], []
        def opener(request, timeout):
            attempts.append(request.full_url)
            raise HTTPError(request.full_url, 429, 'synthetic', {'Retry-After': '99999'}, None)
        with self.assertRaises(CollectionError):
            request_page('yose', 0, 'synthetic-key', opener=opener, sleep=waits.append)
        self.assertEqual(len(attempts), 3)
        self.assertEqual(waits, [30, 30])
    def test_auth_failure_is_not_retried_or_leaked(self):
        from urllib.error import HTTPError
        from tracker.alerts import request_page, CollectionError
        attempts = []
        def opener(request, timeout):
            attempts.append(1)
            raise HTTPError(request.full_url, 401, 'synthetic-private-key', {}, None)
        with self.assertRaises(CollectionError) as error:
            request_page('yose', 0, 'synthetic-private-key', opener=opener)
        self.assertEqual(len(attempts), 1)
        self.assertNotIn('synthetic-private-key', str(error.exception))
    def test_missing_key_does_not_make_request(self):
        from tracker.alerts import request_page, CollectionError
        def opener(request, timeout):
            self.fail('Request must not run without a key')
        with self.assertRaises(CollectionError):
            request_page('yose', 0, '', opener=opener)
    def test_provider_url_cannot_carry_credentials_in_query(self):
        result = collect('yose', initial_snapshot('yose'), NOW, lambda start: page([record(url='https://www.nps.gov/yose/test.htm?api_key=synthetic')]))
        self.assertEqual(result['collection_status'], 'quarantined')
    def test_unchanged_record_does_not_invent_source_update(self):
        old = collect('yose', initial_snapshot('yose'), OLD, lambda start: page([record()]))
        new = collect('yose', old, NOW, lambda start: page([record()]))
        self.assertEqual(new['records'][0]['observed_changed_at'], OLD)
        self.assertIsNone(new['records'][0]['source_updated_at'])
        changed = collect('yose', old, NOW, lambda start: page([record(title='Changed synthetic title')]))
        self.assertEqual(changed['records'][0]['observed_first_at'], OLD)
        self.assertEqual(changed['records'][0]['observed_changed_at'], NOW)
if __name__ == '__main__':
    unittest.main()
