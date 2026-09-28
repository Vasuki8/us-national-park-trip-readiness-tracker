import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch
from staging_fixtures import T0, feed, raw
from tracker.stage import main

class StageCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'stage'

    def invoke(self, command='status', *extra, key=''):
        out, err = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, {'NPS_API_KEY': key}), redirect_stdout(out), redirect_stderr(err):
            code = main([command, '--park', 'yose', '--staging-dir', str(self.root), *extra])
        return code, out.getvalue(), err.getvalue()

    def test_missing_key_blocks_without_requests_or_directory_writes(self):
        with patch('tracker.stage.request_page', side_effect=AssertionError('must not request')):
            code, out, err = self.invoke('collect', '--live')
        self.assertEqual(code, 2); self.assertEqual(json.loads(out)['error_code'], 'nps_key_not_configured')
        self.assertFalse(self.root.exists()); self.assertEqual(err, '')

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
