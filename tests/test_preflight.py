"""Preflight contract tests: real collector normalization, synthetic network boundary only."""
import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from tracker.alerts import CollectionError
try:
    from tracker.preflight import run_preflight, main
except ImportError:
    run_preflight = main = None

KEY = 'PRIVATE-KEY-TEST-SENTINEL'

def record(code, identifier='1'):
    return dict(id=identifier, parkCode=code, title=KEY, description=KEY, category='Information', url=f'https://www.nps.gov/{code}/planyourvisit/conditions.htm')

def success(code, start, key):
    return {'total': '1', 'start': str(start), 'data': [record(code)]}

class PreflightTests(unittest.TestCase):
    def run_check(self, key=KEY, transport=success):
        self.assertTrue(callable(run_preflight), 'read-only preflight is implemented')
        return run_preflight(key, transport=transport)

    def test_missing_key_is_blocked_without_requests(self):
        def forbidden(*args): self.fail('no network call allowed without a key')
        for key in ['', '   ']:
            report = self.run_check(key, forbidden)
            self.assertEqual(report['status'], 'not_configured')
            self.assertFalse(report['gate_passed']); self.assertEqual(report['checks'], [])

    def test_invalid_header_key_does_not_leave_the_process(self):
        def forbidden(*args): self.fail('invalid key must not be sent')
        report = self.run_check(KEY + '\ninvalid', forbidden)
        self.assertEqual(report['status'], 'invalid_configuration'); self.assertFalse(report['gate_passed'])
        self.assertNotIn(KEY, json.dumps(report))

    def test_complete_five_park_probe_only_reports_safe_metadata(self):
        calls = []
        def fetch(code, start, key):
            calls.append((code, start)); self.assertEqual(key, KEY)
            return success(code, start, key)
        report = self.run_check(transport=fetch)
        self.assertTrue(report['gate_passed']); self.assertEqual(report['status'], 'verified')
        self.assertEqual(len(calls), 5); self.assertEqual(len(report['checks']), 5)
        self.assertTrue(all(item['record_count'] == 1 for item in report['checks']))
        self.assertFalse(report['publication_performed']); self.assertNotIn(KEY, json.dumps(report))
        self.assertNotIn('records', report)

    def test_successful_empty_feed_is_validated_not_an_all_clear(self):
        report = self.run_check(transport=lambda code, start, key: dict(total='0', start='0', data=[]))
        self.assertTrue(report['gate_passed'])
        self.assertTrue(all(item['record_count'] == 0 for item in report['checks']))
        self.assertNotIn('open', json.dumps(report)); self.assertFalse(report['publication_performed'])

    def test_provider_errors_do_not_leak_error_messages(self):
        def fetch(*args): raise CollectionError(KEY)
        report = self.run_check(transport=fetch)
        self.assertFalse(report['gate_passed']); self.assertEqual(report['status'], 'needs_review')
        self.assertNotIn(KEY, json.dumps(report)); self.assertEqual(report['checks'][0]['collection_status'], 'failed')

    def test_malformed_response_remains_quarantined(self):
        report = self.run_check(transport=lambda *args: {'message': KEY})
        self.assertFalse(report['gate_passed']); self.assertEqual(report['checks'][0]['collection_status'], 'quarantined')
        self.assertNotIn(KEY, json.dumps(report))

    def test_unexpected_exception_stays_sanitized(self):
        def fetch(*args): raise RuntimeError(KEY)
        report = self.run_check(transport=fetch)
        self.assertFalse(report['gate_passed']); self.assertNotIn(KEY, json.dumps(report))
        self.assertEqual(report['checks'][0]['collection_status'], 'internal_error')

    def test_two_page_budget_does_not_make_a_third_provider_call(self):
        calls = []
        def fetch(code, start, key):
            calls.append((code, start))
            return dict(total='3', start=str(start), data=[record(code, str(start))])
        report = self.run_check(transport=fetch)
        self.assertEqual(len(calls), 10); self.assertFalse(report['gate_passed'])
        self.assertTrue(all(item['pages_requested'] == 2 for item in report['checks']))

    def test_complete_two_page_feed_is_allowed(self):
        def fetch(code, start, key): return dict(total='2', start=str(start), data=[record(code, str(start))])
        report = self.run_check(transport=fetch)
        self.assertTrue(report['gate_passed']); self.assertTrue(all(item['record_count'] == 2 for item in report['checks']))

    def test_no_snapshot_writer_is_called(self):
        with patch('tracker.alerts.write_snapshot', side_effect=AssertionError('must not write')):
            report = self.run_check()
        self.assertFalse(report['publication_performed'])

    def test_missing_key_cli_reports_blocked_gate_without_false_live_success(self):
        self.assertTrue(callable(main))
        output = io.StringIO()
        with patch.dict('os.environ', {'NPS_API_KEY': ''}), redirect_stdout(output): result = main()
        report = json.loads(output.getvalue())
        self.assertEqual(result, 0)  # Diagnostic completion, not integration approval.
        self.assertFalse(report['gate_passed']); self.assertEqual(report['status'], 'not_configured')

if __name__ == '__main__': unittest.main()
