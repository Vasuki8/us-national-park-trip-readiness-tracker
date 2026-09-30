import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch
from staging_fixtures import T0, feed, raw
from tracker.history_model import HistoryError
from tracker.stage import main
from tracker.staging import StagingCollector, PILOT_CODES

class StageCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'stage'

    def invoke(self, command='status', *extra, key=''):
        out, err = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, {'NPS_API_KEY': key}), redirect_stdout(out), redirect_stderr(err):
            code = main([command, '--park', 'yose', '--staging-dir', str(self.root), *extra])
        return code, out.getvalue(), err.getvalue()

    def invoke_all(self, *extra, key='synthetic-private-key'):
        out, err = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, {'NPS_API_KEY': key}), redirect_stdout(out), redirect_stderr(err):
            code = main(['collect', '--park', 'all', '--staging-dir', str(self.root), *extra])
        return code, json.loads(out.getvalue()), err.getvalue()

    def status_all(self):
        out, err = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, {'NPS_API_KEY': ''}), redirect_stdout(out), redirect_stderr(err):
            code = main(['status', '--park', 'all', '--staging-dir', str(self.root)])
        return code, json.loads(out.getvalue()), err.getvalue()

    def test_five_park_status_is_offline_and_does_not_create_storage(self):
        with patch('tracker.stage.request_page', side_effect=AssertionError('must not fetch')):
            code, report, err = self.status_all()
        self.assertEqual(code, 0); self.assertEqual(err, '')
        self.assertEqual(report['operation'], 'status_all')
        self.assertEqual([item['park_code'] for item in report['parks']], list(PILOT_CODES))
        self.assertTrue(all(item['stage_state'] == 'idle' and item['observation_count'] == 0
                            for item in report['parks']))
        self.assertFalse(report['publication_performed']); self.assertFalse(report['site_data_written'])
        self.assertFalse(self.root.exists())

    def test_five_park_status_retains_mixed_archived_and_pending_states(self):
        stage = StagingCollector(self.root)
        stage.collect('yose', T0, lambda start: feed([raw(code='yose')]))
        with patch.object(stage.archive, 'append', side_effect=OSError('interrupted')):
            with self.assertRaises(OSError):
                stage.collect('zion', T0, lambda start: feed([raw(code='zion')]))
        with patch('tracker.stage.request_page', side_effect=AssertionError('must not fetch')):
            code, report, err = self.status_all()
        self.assertEqual(code, 0); self.assertEqual(err, '')
        parks = {item['park_code']: item for item in report['parks']}
        self.assertEqual(parks['yose']['observation_count'], 1)
        self.assertEqual(parks['yose']['collection_status'], 'success')
        self.assertEqual(parks['zion']['stage_state'], 'pending')
        self.assertEqual(parks['zion']['pending_collection_status'], 'success')
        self.assertEqual(stage.status('zion')['stage_state'], 'pending')

    def test_five_park_status_sanitizes_storage_failure_without_partial_report(self):
        with patch('tracker.stage.StagingCollector.status', side_effect=OSError('secret private path')):
            code, report, err = self.status_all()
        self.assertEqual(code, 2); self.assertEqual(err, '')
        self.assertEqual(report['operation'], 'refused')
        self.assertEqual(report['error_code'], 'staging_operation_failed')
        self.assertNotIn('parks', report)
        self.assertNotIn('secret private path', json.dumps(report) + err)

    def test_five_park_status_uses_generic_refusal_for_later_known_archive_error(self):
        original = StagingCollector.status
        seen = []
        def fail_second(stage, park):
            seen.append(park)
            if park == 'romo':
                raise HistoryError('archive_hash_mismatch')
            return original(stage, park)
        with patch('tracker.stage.StagingCollector.status', autospec=True, side_effect=fail_second):
            code, report, err = self.status_all()
        self.assertEqual(seen, ['yose', 'romo'])
        self.assertEqual(code, 2); self.assertEqual(err, '')
        self.assertEqual(report['operation'], 'refused')
        self.assertEqual(report['error_code'], 'staging_operation_failed')
        self.assertNotIn('parks', report)

    def test_five_park_collect_archives_each_and_reports_private_results(self):
        calls = []
        def fetch(code, start, key):
            calls.append(code)
            return feed([raw(code=code)])
        with patch('tracker.stage.utc_now', return_value=T0), patch('tracker.stage.request_page', side_effect=fetch):
            code, report, err = self.invoke_all('--live')
        self.assertEqual(code, 0); self.assertEqual(calls, list(PILOT_CODES))
        self.assertEqual(report['status'], 'archived')
        self.assertEqual([item['park_code'] for item in report['checks']], list(PILOT_CODES))
        self.assertTrue(all(item['collection_status'] == 'success' for item in report['checks']))
        self.assertFalse(report['publication_performed']); self.assertFalse(report['site_data_written'])
        self.assertEqual(err, '')
        for park in PILOT_CODES:
            self.assertEqual(StagingCollector(self.root).archive.read(park)[-1]['snapshot']['park_code'], park)

    def test_five_park_collect_refuses_pending_receipt_before_any_request(self):
        stage = StagingCollector(self.root)
        with patch.object(stage.archive, 'append', side_effect=OSError('interruption')):
            with self.assertRaises(OSError):
                stage.collect('zion', T0, lambda start: feed([raw(code='zion')]))
        with patch('tracker.stage.request_page', side_effect=AssertionError('must not fetch')):
            code, report, err = self.invoke_all('--live')
        self.assertEqual(code, 2); self.assertEqual(report['error_code'], 'pending_recovery_required')
        self.assertEqual(report['checks'], []); self.assertEqual(err, '')
        self.assertEqual(stage.status('yose')['observation_count'], 0)

    def test_five_park_collect_keeps_partial_provider_failure_visible(self):
        def fetch(code, start, key):
            if code == 'yell': raise TimeoutError('synthetic-private-key')
            return feed([raw(code=code)])
        with patch('tracker.stage.utc_now', return_value=T0), patch('tracker.stage.request_page', side_effect=fetch):
            code, report, err = self.invoke_all('--live')
        self.assertEqual(code, 1); self.assertEqual(report['status'], 'needs_review')
        self.assertEqual([item['park_code'] for item in report['checks']], list(PILOT_CODES))
        self.assertEqual(report['checks'][2]['collection_status'], 'failed')
        self.assertEqual(StagingCollector(self.root).archive.read('yell')[-1]['snapshot']['records'], [])
        self.assertNotIn('synthetic-private-key', json.dumps(report) + err)

    def test_five_park_collect_reports_committed_progress_after_interruption(self):
        def fetch(code, start, key):
            if code == 'romo': raise RuntimeError('synthetic-private-key')
            return feed([raw(code=code)])
        with patch('tracker.stage.utc_now', return_value=T0), patch('tracker.stage.request_page', side_effect=fetch):
            code, report, err = self.invoke_all('--live')
        self.assertEqual(code, 2); self.assertEqual(report['status'], 'interrupted')
        self.assertEqual(report['error_code'], 'staging_operation_failed')
        self.assertEqual([item['park_code'] for item in report['checks']], ['yose'])
        self.assertEqual(len(StagingCollector(self.root).archive.read('yose')), 1)
        self.assertEqual(len(StagingCollector(self.root).archive.read('romo')), 0)
        self.assertNotIn('synthetic-private-key', json.dumps(report) + err)

    def test_five_park_collect_prechecks_all_existing_clocks_before_network(self):
        StagingCollector(self.root).collect('grca', T0, lambda start: feed([raw(code='grca')]))
        with patch('tracker.stage.utc_now', return_value=T0), patch('tracker.stage.request_page', side_effect=AssertionError('must not fetch')):
            code, report, err = self.invoke_all('--live')
        self.assertEqual(code, 2); self.assertEqual(report['error_code'], 'collection_clock_not_advanced')
        self.assertEqual(report['checks'], []); self.assertEqual(err, '')
        self.assertEqual(StagingCollector(self.root).status('yose')['observation_count'], 0)

    def test_missing_key_blocks_without_requests_or_directory_writes(self):
        with patch('tracker.stage.request_page', side_effect=AssertionError('must not request')):
            code, out, err = self.invoke('collect', '--live')
        self.assertEqual(code, 2); self.assertEqual(json.loads(out)['error_code'], 'nps_key_not_configured')
        self.assertFalse(self.root.exists()); self.assertEqual(err, '')

    def test_collect_refuses_pages_output_before_requests_or_writes(self):
        for park in ('yose', 'all'):
            for nested in (False, True):
                with self.subTest(park=park, nested=nested):
                    project = Path(self.temp.name)/f'project-{park}-{nested}'
                    project.mkdir()
                    output = project/'dist-pages'
                    if nested:
                        output.mkdir()
                        (output/'index.html').write_text('retained public page')
                    destination = output/'private-stage' if nested else output
                    before = {p:p.read_bytes() for p in project.rglob('*') if p.is_file()}
                    out, err = io.StringIO(), io.StringIO()
                    requests = []
                    def fetch(code, start, key):
                        requests.append(code)
                        return feed([raw(code=code)])
                    with patch('tracker.staging.PROJECT_ROOT', project), \
                         patch('tracker.stage.utc_now', return_value=T0), \
                         patch('tracker.stage.request_page', side_effect=fetch), \
                         patch.dict(os.environ, {'NPS_API_KEY': 'synthetic-private-key'}), \
                         redirect_stdout(out), redirect_stderr(err):
                        code = main(['collect', '--live', '--park', park,
                                     '--staging-dir', str(destination)])
                    self.assertEqual(code, 2)
                    report = json.loads(out.getvalue())
                    self.assertEqual(report['error_code'], 'unsafe_staging_destination')
                    self.assertFalse(report['publication_performed'])
                    self.assertFalse(report['site_data_written'])
                    self.assertEqual(requests, [])
                    self.assertEqual(before, {p:p.read_bytes() for p in project.rglob('*') if p.is_file()})
                    self.assertFalse(destination.exists())
                    self.assertNotIn(str(project), out.getvalue()+err.getvalue())
                    self.assertNotIn('synthetic-private-key', out.getvalue()+err.getvalue())


    def test_live_confirmation_required_even_with_key(self):
        with patch('tracker.stage.request_page', side_effect=AssertionError('must not request')):
            code, out, err = self.invoke('collect', key='synthetic-private-key')
        self.assertEqual(code, 2); self.assertIn('live_confirmation_required', out)
        self.assertNotIn('synthetic-private-key', out+err); self.assertFalse(self.root.exists())

    def test_invalid_header_key_is_never_sent_or_printed(self):
        for key in ('secret\nvalue', 'secret\rvalue', 'secret\tvalue', 'é-secret'):
            with self.subTest(key=repr(key)), patch('tracker.stage.request_page', side_effect=AssertionError()):
                code, out, err = self.invoke('collect', '--live', key=key)
                self.assertEqual(code, 2); self.assertNotIn('secret', out+err); self.assertFalse(self.root.exists())

    def test_successful_collect_reports_private_archival_not_publication(self):
        project = Path(__file__).resolve().parents[1]
        before = {str(p): p.read_bytes() for p in (project/'data').rglob('*') if p.is_file()}
        with patch('tracker.stage.utc_now', return_value=T0), patch('tracker.stage.request_page', return_value=feed([raw()])):
            code, out, err = self.invoke('collect', '--live', key='synthetic-private-key')
        result = json.loads(out)
        self.assertEqual(code, 0); self.assertEqual(result['operation'], 'archived')
        self.assertFalse(result['publication_performed']); self.assertFalse(result['site_data_written'])
        self.assertNotIn('Synthetic', out); self.assertNotIn('synthetic-private-key', out+err)
        after = {str(p): p.read_bytes() for p in (project/'data').rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_provider_failure_is_archived_but_returns_nonzero(self):
        with patch('tracker.stage.utc_now', return_value=T0), patch('tracker.stage.request_page', side_effect=TimeoutError('synthetic-private-key')):
            code, out, err = self.invoke('collect', '--live', key='synthetic-private-key')
        self.assertEqual(code, 1); result = json.loads(out)
        self.assertEqual(result['operation'], 'archived'); self.assertEqual(result['collection_status'], 'failed')
        self.assertNotIn('synthetic-private-key', out+err)

    def test_echoed_credential_in_valid_provider_text_is_quarantined_before_retention(self):
        with patch('tracker.stage.utc_now', return_value=T0), patch('tracker.stage.request_page', return_value=feed([raw(title='synthetic-private-key')])):
            code, out, err = self.invoke('collect', '--live', key='synthetic-private-key')
        self.assertEqual(code, 1); self.assertEqual(json.loads(out)['collection_status'], 'quarantined')
        for path in self.root.rglob('*.json'): self.assertNotIn('synthetic-private-key', path.read_text())
        self.assertNotIn('synthetic-private-key', out+err)

    def test_status_and_empty_recovery_are_offline_and_read_only(self):
        with patch('tracker.stage.request_page', side_effect=AssertionError('offline')):
            for action in ('status', 'recover'):
                code, out, err = self.invoke(action)
                self.assertEqual(code, 0); self.assertFalse(json.loads(out)['site_data_written'])
                self.assertFalse(self.root.exists())

    def test_unexpected_exception_is_not_logged_as_raw_text(self):
        with patch('tracker.stage.utc_now', return_value=T0), patch('tracker.stage.request_page', side_effect=RuntimeError('synthetic-private-key')):
            code, out, err = self.invoke('collect', '--live', key='synthetic-private-key')
        self.assertEqual(code, 2); self.assertEqual(json.loads(out)['error_code'], 'staging_operation_failed')
        self.assertNotIn('synthetic-private-key', out+err); self.assertNotIn('Traceback', out+err)

    def test_recovery_uses_original_receipt_without_key_or_requests(self):
        with patch('tracker.stage.utc_now', return_value=T0), patch('tracker.stage.request_page', return_value=feed([raw()])), patch('tracker.staging.StagingCollector._clear_pending', side_effect=OSError()):
            code, _, _ = self.invoke('collect', '--live', key='synthetic-private-key')
        self.assertEqual(code, 2)
        with patch('tracker.stage.request_page', side_effect=AssertionError('offline')):
            code, out, err = self.invoke('recover')
        self.assertEqual(code, 0); result = json.loads(out)
        self.assertEqual(result['operation'], 'recovered'); self.assertEqual(result['last_checked_at'], T0)
