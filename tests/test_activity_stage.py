"""Private activity CLI integration with synthetic sources and disposable files."""
import hashlib
import importlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tracker.park_activities import ActivityCollectionError, collect_activities, initial_activities
from test_park_activities import T0, T1, activity, page

CODES = ('yose', 'romo', 'yell', 'zion', 'grca')


def checkpoint_fixture(*, larger_last=False):
    inventories = []
    for code in CODES:
        raw = activity(code=code, title='Synthetic activity' if code != 'grca' or not larger_last else 'x' * 2000)
        inventories.append(collect_activities(code, initial_activities(code), T0,
                                             lambda _start: page([raw])))
    core = {'schema_version': 1, 'purpose': 'private_park_activity_checkpoint',
            'parent_checkpoint_id': None, 'checked_at': T0, 'inventories': inventories}
    raw = json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return {**core, 'checkpoint_id': hashlib.sha256(raw).hexdigest()}


@unittest.skipUnless(os.name == 'posix', 'Private activity CLI requires POSIX.')
class ActivityStageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root.chmod(0o700)
        self.output = self.root / 'checkpoint.json'
        self.source = self.root / 'previous.json'
        self.source.write_bytes(json.dumps(checkpoint_fixture()).encode())
        self.source.chmod(0o600)

    def adapter(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.activity_stage'),
                             'The private activity CLI is not implemented.')
        return importlib.import_module('tracker.activity_stage')

    def invoke(self, module, arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = module.main(arguments)
        self.assertEqual(stderr.getvalue(), '')
        return status, json.loads(stdout.getvalue())

    def collect_args(self, *extra):
        return ['collect', '--output', str(self.output), *extra]

    @contextmanager
    def forbid_key(self):
        original = os.environ.get
        def get(name, *args):
            if name == 'NPS_API_KEY':
                self.fail('Private key accessed before complete storage/baseline preflight.')
            return original(name, *args)
        with patch.object(os.environ, 'get', side_effect=get):
            yield

    def test_live_acknowledgement_required_without_key_or_transport(self):
        module = self.adapter()
        with self.forbid_key(), patch.object(module, 'request_activity_page', side_effect=AssertionError('Requested')):
            status, report = self.invoke(module, self.collect_args())
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'live_confirmation_required')
        self.assertFalse(report['network_attempted'])
        self.assertFalse(self.output.exists())

    def test_unsafe_destination_precedes_key_access(self):
        module = self.adapter()
        with self.forbid_key():
            status, report = self.invoke(module, ['collect', '--live', '--output', 'relative/private.json'])
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'activity_private_storage_refused')

    def test_corrupt_baseline_precedes_key_access(self):
        module = self.adapter()
        self.source.write_bytes(b'invalid private source')
        with self.forbid_key():
            status, report = self.invoke(module, self.collect_args('--live', '--previous', str(self.source)))
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'activity_checkpoint_unreadable')

    def test_nonadvancing_batch_clock_precedes_key_access(self):
        module = self.adapter()
        with self.forbid_key(), patch.object(module, 'utc_now', return_value=T0):
            status, report = self.invoke(module, self.collect_args('--live', '--previous', str(self.source)))
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'activity_collection_clock_not_advanced')

    def test_last_park_failure_capacity_precedes_any_key_or_request(self):
        module = self.adapter()
        value = checkpoint_fixture(larger_last=True)
        self.source.write_bytes(json.dumps(value).encode())
        capacity = len(json.dumps(value['inventories'][-1], ensure_ascii=False,
                                  sort_keys=True, separators=(',', ':')).encode())
        with self.forbid_key(), patch.object(module, 'utc_now', return_value=T1), \
             patch('tracker.park_activities.MAX_SNAPSHOT_BYTES', capacity):
            status, report = self.invoke(module, self.collect_args('--live', '--previous', str(self.source)))
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'activity_attempt_refused')
        self.assertFalse(report['network_attempted'])
        self.assertFalse(self.output.exists())
        self.assertFalse(Path(str(self.output) + '.lock').exists())

    def test_existing_output_and_lock_precede_key_access_without_overwrite(self):
        module = self.adapter()
        for path, code in ((self.output, 'activity_destination_exists'),
                           (Path(str(self.output) + '.lock'), 'activity_output_locked')):
            path.write_bytes(b'keep evidence')
            path.chmod(0o600)
            with self.forbid_key():
                status, report = self.invoke(module, self.collect_args('--live'))
            self.assertEqual(status, 2)
            self.assertEqual(report['error_code'], code)
            self.assertEqual(path.read_bytes(), b'keep evidence')
            path.unlink()

    def test_missing_and_malformed_keys_never_attempt_transport_or_install(self):
        module = self.adapter()
        for key, code in (('', 'nps_key_not_configured'), (' ', 'nps_key_not_configured'),
                          (' padded ', 'nps_key_invalid'), ('key\nheader', 'nps_key_invalid'), ('非ASCII', 'nps_key_invalid')):
            with self.subTest(key=key), patch.dict(os.environ, {'NPS_API_KEY': key}), \
                 patch.object(module, 'request_activity_page', side_effect=AssertionError('Requested')):
                status, report = self.invoke(module, self.collect_args('--live'))
            self.assertEqual(status, 2)
            self.assertEqual(report['error_code'], code)
            self.assertFalse(report['network_attempted'])
            self.assertFalse(self.output.exists())
            self.assertFalse(Path(str(self.output) + '.lock').exists())

    def test_all_five_paginated_collection_reports_counts_without_private_content(self):
        module = self.adapter()
        calls = []
        def request(code, start, key):
            calls.append((code, start, key))
            return page([activity(f'{code}-{start}', code)], total=2, start=start)
        with patch.dict(os.environ, {'NPS_API_KEY': 'synthetic-activity-key'}), \
             patch.object(module, 'utc_now', return_value=T1), \
             patch.object(module, 'request_activity_page', side_effect=request):
            status, report = self.invoke(module, self.collect_args('--live', '--previous', str(self.source)))
        self.assertEqual(status, 0)
        self.assertEqual([(code, start) for code, start, _key in calls],
                         [(code, offset) for code in CODES for offset in (0, 1)])
        self.assertTrue(all(key == 'synthetic-activity-key' for _, _, key in calls))
        self.assertEqual(report['scope'], 'private_activity_only')
        self.assertEqual(report['operation'], 'checkpoint_created')
        self.assertEqual(report['park_count'], 5)
        self.assertEqual(report['retained_activity_count'], 10)
        self.assertEqual(report['collection_counts'], {'success': 5, 'failed': 0, 'quarantined': 0})
        self.assertTrue(report['network_attempted'])
        for flag in ('approval_performed', 'publication_performed', 'site_data_written'):
            self.assertFalse(report[flag])
        for excluded in ('synthetic-activity-key', str(self.root), 'Synthetic trail', 'long_description'):
            self.assertNotIn(excluded, json.dumps(report))
        retained = module.verify_checkpoint(self.output)
        self.assertEqual(retained['parent_checkpoint_id'], checkpoint_fixture()['checkpoint_id'])

    def test_degraded_complete_batch_exits_one_and_retains_last_good(self):
        module = self.adapter()
        def request(code, start, _key):
            if code == 'romo':
                raise ActivityCollectionError('private provider text')
            return page([], total=0) if code == 'zion' else page([activity(code=code)], start=start)
        with patch.dict(os.environ, {'NPS_API_KEY': 'synthetic-key'}), \
             patch.object(module, 'utc_now', return_value=T1), \
             patch.object(module, 'request_activity_page', side_effect=request):
            status, report = self.invoke(module, self.collect_args('--live', '--previous', str(self.source)))
        self.assertEqual(status, 1)
        self.assertEqual(report['collection_counts'], {'success': 3, 'failed': 1, 'quarantined': 1})
        value = module.verify_checkpoint(self.output)
        original = checkpoint_fixture()
        for index in (1, 3):
            self.assertEqual(value['inventories'][index]['records'], original['inventories'][index]['records'])
            self.assertEqual(value['inventories'][index]['last_successful_fetch_at'], T0)
        self.assertNotIn('private provider text', json.dumps(report))

    def test_unexpected_error_is_sanitized_with_truthful_transport_attempt(self):
        module = self.adapter()
        with patch.dict(os.environ, {'NPS_API_KEY': 'synthetic-key'}), \
             patch.object(module, 'request_activity_page', side_effect=RuntimeError('secret ' + str(self.root))):
            status, report = self.invoke(module, self.collect_args('--live'))
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'activity_operation_failed')
        self.assertTrue(report['network_attempted'])
        self.assertNotIn('secret', json.dumps(report))
        self.assertFalse(self.output.exists())

    def test_keyboard_interrupt_preserves_no_preinstall_output_and_sanitizes(self):
        module = self.adapter()
        with patch.dict(os.environ, {'NPS_API_KEY': 'synthetic-key'}), \
             patch.object(module, 'request_activity_page', side_effect=KeyboardInterrupt('private interrupt')):
            status, report = self.invoke(module, self.collect_args('--live'))
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'activity_operation_interrupted')
        self.assertTrue(report['network_attempted'])
        self.assertFalse(self.output.exists())
        self.assertFalse(Path(str(self.output) + '.lock').exists())

    def test_postinstall_interrupt_leaves_checkpoint_for_offline_verification(self):
        module = self.adapter()
        original = module.collect_checkpoint
        def interrupt(*args, **kwargs):
            original(*args, **kwargs)
            raise KeyboardInterrupt('private interrupt')
        with patch.dict(os.environ, {'NPS_API_KEY': 'synthetic-key'}), \
             patch.object(module, 'utc_now', return_value=T0), \
             patch.object(module, 'request_activity_page', side_effect=lambda code, start, _key: page([activity(code=code)], start=start)), \
             patch.object(module, 'collect_checkpoint', side_effect=interrupt):
            status, report = self.invoke(module, self.collect_args('--live'))
        self.assertEqual(status, 2)
        self.assertEqual(report['error_code'], 'activity_operation_interrupted')
        self.assertEqual(module.verify_checkpoint(self.output), checkpoint_fixture())
        self.assertNotIn('private interrupt', json.dumps(report))

    def test_offline_verify_restore_review_never_read_key_or_request(self):
        module = self.adapter()
        commands = [['verify', '--checkpoint', str(self.source)],
                    ['restore', '--checkpoint', str(self.source), '--output', str(self.output)],
                    ['export-review', '--checkpoint', str(self.source), '--output', str(self.root / 'review.json')]]
        with self.forbid_key(), patch.object(module, 'request_activity_page', side_effect=AssertionError('Requested')):
            for arguments in commands:
                status, report = self.invoke(module, arguments)
                self.assertEqual(status, 0)
                self.assertEqual(report['checkpoint_id'], checkpoint_fixture()['checkpoint_id'])
                self.assertFalse(report['network_attempted'])
                for flag in ('approval_performed', 'publication_performed', 'site_data_written'):
                    self.assertFalse(report[flag])
        self.assertEqual(report['source_rights_status'], 'not_checked')

    def test_invalid_arguments_are_json_reports_without_echo_or_abbreviation(self):
        module = self.adapter()
        for arguments in ([], ['secret-command'], ['verify'], ['verify', '--checkpoint'],
                          ['collect', '--out', str(self.output), '--live'],
                          ['collect', '--output', str(self.output), '--api-key', 'secret-key']):
            with self.subTest(arguments=arguments):
                status, report = self.invoke(module, arguments)
                self.assertEqual(status, 2)
                self.assertEqual(report['error_code'], 'invalid_activity_arguments')
                self.assertNotIn('secret', json.dumps(report))
                self.assertNotIn(str(self.root), json.dumps(report))

    def test_real_subprocess_offline_verify_and_safe_argument_refusal(self):
        self.adapter()
        command = [sys.executable, '-m', 'tracker.activity_stage']
        result = subprocess.run(command + ['verify', '--checkpoint', str(self.source)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)['network_attempted'])
        result = subprocess.run(command + ['--api-key', 'secret-key'], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, '')
        self.assertNotIn('secret-key', result.stdout)
