"""Explicit private CLI contracts; synthetic transport and temporary evidence."""
import importlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from tracker.history_model import canonical
from test_profile_checkpoints import NOW, LATER, checkpoint_fixture, payload


@unittest.skipUnless(os.name == 'posix', 'Private CLI requires POSIX.')
class ProfileStageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root.chmod(0o700)
        self.output = self.root / 'checkpoint.json'
        self.source = self.root / 'previous.json'
        self.source.write_bytes(canonical(checkpoint_fixture()))
        self.source.chmod(0o600)

    def adapter(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.profile_stage'),
                             'The explicit private profile CLI is not implemented.')
        return importlib.import_module('tracker.profile_stage')

    def invoke(self, module, arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = module.main(arguments)
        self.assertEqual(stderr.getvalue(), '')
        return status, json.loads(stdout.getvalue())

    def collect_args(self, *extra):
        return ['collect', '--output', str(self.output), *extra]

    @contextmanager
    def forbid_key_access(self):
        original_get = os.environ.get
        def guarded_get(name, *args):
            if name == 'NPS_API_KEY':
                self.fail('The private key was accessed before its authorized collection step.')
            return original_get(name, *args)  # argparse/gettext legitimately reads locale names.
        with patch.object(os.environ, 'get', side_effect=guarded_get):
            yield

    def test_missing_live_refuses_without_key_reads_or_requests(self):
        module = self.adapter()
        with self.forbid_key_access():
            with patch.object(module, 'request_profile_page', side_effect=AssertionError('Source requested')):
                status, report = self.invoke(module, self.collect_args())
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'live_confirmation_required')
        self.assertFalse(report['network_attempted'])
        self.assertFalse(self.output.exists())

    def test_invalid_storage_precedes_key_access(self):
        module = self.adapter()
        with self.forbid_key_access():
            status, report = self.invoke(module, ['collect', '--live', '--output', 'relative/private.json'])
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'profile_private_storage_refused')

    def test_corrupt_previous_precedes_key_access(self):
        module = self.adapter()
        self.source.write_bytes(b'invalid private body')
        with self.forbid_key_access():
            status, report = self.invoke(module, self.collect_args('--live', '--previous', str(self.source)))
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'profile_checkpoint_unreadable')
        self.assertFalse(self.output.exists())

    def test_nonadvancing_previous_precedes_key_access(self):
        module = self.adapter()
        with patch.object(module, 'utc_now', return_value=NOW):
            with self.forbid_key_access():
                status, report = self.invoke(module, self.collect_args('--live', '--previous', str(self.source)))
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'profile_collection_clock_not_advanced')

    def test_existing_output_precedes_key_access(self):
        module = self.adapter()
        self.output.write_bytes(b'keep')
        self.output.chmod(0o600)
        with self.forbid_key_access():
            status, report = self.invoke(module, self.collect_args('--live'))
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'profile_destination_exists')
        self.assertEqual(self.output.read_bytes(), b'keep')

    def test_missing_or_invalid_key_never_fetches_or_leaves_output(self):
        module = self.adapter()
        for key, expected in (('', 'nps_key_not_configured'), (' ', 'nps_key_not_configured'),
                              ('key\nheader', 'nps_key_invalid'), (' padded ', 'nps_key_invalid'),
                              ('非ASCII', 'nps_key_invalid')):
            with self.subTest(key=key):
                with patch.dict(os.environ, {'NPS_API_KEY': key}):
                    with patch.object(module, 'request_profile_page', side_effect=AssertionError('Source requested')):
                        status, report = self.invoke(module, self.collect_args('--live'))
                self.assertEqual(status, 2)
                self.assertEqual(report['error_code'], expected)
                self.assertFalse(self.output.exists())
                self.assertFalse(Path(str(self.output) + '.lock').exists())

    def test_all_successful_checks_report_metadata_and_zero_exit(self):
        module = self.adapter()
        calls = []
        def fetch(code, start, key):
            calls.append((code, start, key))
            return payload(code)
        with patch.dict(os.environ, {'NPS_API_KEY': 'synthetic-private-key'}):
            with patch.object(module, 'utc_now', return_value=LATER):
                with patch.object(module, 'request_profile_page', side_effect=fetch):
                    status, report = self.invoke(module, self.collect_args('--live', '--previous', str(self.source)))
        self.assertEqual(status, 0)
        self.assertEqual([call[0] for call in calls], ['yose', 'romo', 'yell', 'zion', 'grca'])
        self.assertTrue(all(start == 0 and key == 'synthetic-private-key' for _, start, key in calls))
        self.assertEqual(report['operation'], 'checkpoint_created')
        self.assertEqual(report['collection_counts'], {'success': 5, 'failed': 0, 'quarantined': 0})
        self.assertTrue(report['network_attempted'])
        self.assertFalse(report['publication_performed'])
        self.assertFalse(report['site_data_written'])
        text = json.dumps(report)
        for excluded in ('Synthetic introduction', 'synthetic-private-key', str(self.root), 'description'):
            self.assertNotIn(excluded, text)

    def test_completed_degraded_checks_report_one_exit_with_retained_checkpoint(self):
        module = self.adapter()
        from tracker.park_profiles import ProfileCollectionError
        def fetch(code, _start, _key):
            if code == 'romo':
                raise ProfileCollectionError('private-key and provider body')
            return {'total': 0, 'start': 0, 'data': []} if code == 'zion' else payload(code)
        with patch.dict(os.environ, {'NPS_API_KEY': 'synthetic-key'}):
            with patch.object(module, 'utc_now', return_value=LATER):
                with patch.object(module, 'request_profile_page', side_effect=fetch):
                    status, report = self.invoke(module, self.collect_args('--live', '--previous', str(self.source)))
        self.assertEqual(status, 1)
        self.assertEqual(report['collection_counts'], {'success': 3, 'failed': 1, 'quarantined': 1})
        self.assertTrue(self.output.exists())
        self.assertNotIn('private-key', json.dumps(report))

    def test_unexpected_exception_is_safe_and_network_attempt_remains_truthful(self):
        module = self.adapter()
        with patch.dict(os.environ, {'NPS_API_KEY': 'synthetic-key'}):
            with patch.object(module, 'request_profile_page', side_effect=RuntimeError('secret-text ' + str(self.root))):
                status, report = self.invoke(module, self.collect_args('--live'))
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'profile_operation_failed')
        self.assertTrue(report['network_attempted'])
        self.assertNotIn('secret-text', json.dumps(report))
        self.assertFalse(self.output.exists())

    def test_keyboard_interruption_reports_safe_exit_and_leaves_no_preinstall_output(self):
        module = self.adapter()
        with patch.dict(os.environ, {'NPS_API_KEY': 'synthetic-key'}):
            with patch.object(module, 'request_profile_page', side_effect=KeyboardInterrupt('private-interrupt-text')):
                try:
                    status, report = self.invoke(module, self.collect_args('--live'))
                except KeyboardInterrupt:
                    self.fail('An operator interruption escaped the bounded CLI report.')
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'profile_operation_interrupted')
        self.assertTrue(report['network_attempted'])
        self.assertNotIn('private-interrupt-text', json.dumps(report))
        self.assertFalse(self.output.exists())
        self.assertFalse(Path(str(self.output) + '.lock').exists())

    def test_postinstall_keyboard_interruption_preserves_verifiable_output(self):
        module = self.adapter()
        original = module.collect_checkpoint
        def interrupt_after_install(*args, **kwargs):
            original(*args, **kwargs)
            raise KeyboardInterrupt('private-interrupt-text')
        with patch.dict(os.environ, {'NPS_API_KEY': 'synthetic-key'}):
            with patch.object(module, 'utc_now', return_value=NOW):
                with patch.object(module, 'request_profile_page', side_effect=lambda code, _start, _key: payload(code)):
                    with patch.object(module, 'collect_checkpoint', side_effect=interrupt_after_install):
                        try:
                            status, report = self.invoke(module, self.collect_args('--live'))
                        except KeyboardInterrupt:
                            self.fail('A post-install interruption escaped the bounded CLI report.')
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'profile_operation_interrupted')
        self.assertEqual(module.verify_checkpoint(self.output), checkpoint_fixture())
        self.assertNotIn('private-interrupt-text', json.dumps(report))

    def test_all_offline_commands_ignore_key_and_transport(self):
        module = self.adapter()
        commands = [['verify', '--checkpoint', str(self.source)],
                    ['restore', '--checkpoint', str(self.source), '--output', str(self.output)],
                    ['export-review', '--checkpoint', str(self.source), '--output', str(self.root / 'review.json')]]
        with self.forbid_key_access():
            with patch.object(module, 'request_profile_page', side_effect=AssertionError('Offline source requested')):
                for arguments in commands:
                    status, report = self.invoke(module, arguments)
                    self.assertEqual(status, 0)
                    self.assertEqual(report['checkpoint_id'], checkpoint_fixture()['checkpoint_id'])
                    self.assertFalse(report['network_attempted'])
                    self.assertFalse(report['approval_performed'])
                    self.assertFalse(report['publication_performed'])
                    self.assertFalse(report['site_data_written'])

    def test_export_report_does_not_claim_rights_or_approval(self):
        module = self.adapter()
        status, report = self.invoke(module, ['export-review', '--checkpoint', str(self.source), '--output', str(self.output)])
        self.assertEqual(status, 0)
        self.assertEqual(report['operation'], 'review_exported')
        self.assertEqual(report['source_rights_status'], 'not_checked')
        self.assertFalse(report['approval_performed'])

    def test_argument_errors_never_echo_paths_key_or_arbitrary_arguments(self):
        module = self.adapter()
        for arguments in ([], ['unknown-secret-text'], ['verify'],
                          ['collect', '--output', str(self.output), '--api-key', 'private-key-text'],
                          ['verify', '--checkpoint'], ['restore', '--checkpoint', str(self.root / 'private-path')]):
            with self.subTest(arguments=arguments):
                status, report = self.invoke(module, arguments)
                self.assertEqual(status, 2)
                self.assertEqual(report['error_code'], 'invalid_profile_arguments')
                for excluded in ('secret-text', 'private-key-text', str(self.root)):
                    self.assertNotIn(excluded, json.dumps(report))

    def test_real_subprocess_verify_is_offline_and_sanitizes_invalid_arguments(self):
        self.adapter()
        command = [sys.executable, '-m', 'tracker.profile_stage']
        result = subprocess.run(command + ['verify', '--checkpoint', str(self.source)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)['network_attempted'])
        result = subprocess.run(command + ['--api-key', 'private-key-text'],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('private-key-text', result.stdout + result.stderr)
        self.assertEqual(result.stderr, '')


if __name__ == '__main__':
    unittest.main()
