"""The retired entry point cannot bypass private staging and paired promotion."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tracker import __main__ as legacy
from tracker.alerts import initial_snapshot


class LegacyCollectorCliTests(unittest.TestCase):
    def invoke(self, arguments, key='synthetic-private-key'):
        output, errors = io.StringIO(), io.StringIO()
        # The synthetic response makes the old command perform a real local
        # write. It cannot contact the provider during this refusal regression.
        with patch.dict(os.environ, {'NPS_API_KEY': key}), \
                patch.object(sys, 'argv', ['tracker', *arguments]), \
                patch.object(legacy, 'request_page', create=True,
                             return_value={'total': '0', 'start': '0', 'data': []}) as request, \
                redirect_stdout(output), redirect_stderr(errors):
            try:
                status = legacy.main()
            except SystemExit as error:
                status = error.code
        return status, output.getvalue(), errors.getvalue(), request.call_count

    def assert_refused(self, result):
        status, output, errors, calls = result
        self.assertEqual(status, 2)
        self.assertEqual(output, '')
        self.assertIn('python -m tracker.stage', errors)
        self.assertIn('reviewed promotion', errors)
        self.assertNotIn('synthetic-private-key', errors)
        self.assertEqual(calls, 0)

    def test_default_public_destination_is_never_changed(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / 'data' / 'alerts' / 'yose.json'
            destination.parent.mkdir(parents=True)
            original = json.dumps(initial_snapshot('yose')).encode()
            destination.write_bytes(original)
            previous_directory = Path.cwd()
            try:
                os.chdir(temporary)
                result = self.invoke(['--park', 'yose'])
            finally:
                os.chdir(previous_directory)
            self.assertEqual(destination.read_bytes(), original)
            self.assert_refused(result)

    def test_explicit_destination_is_never_created(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / 'unused-private-destination'
            result = self.invoke(['--park', 'zion', '--data-dir', str(destination)])
            self.assertFalse(destination.exists())
            self.assert_refused(result)
            self.assertNotIn(str(destination), result[2])

    def test_missing_key_still_gives_migration_without_request(self):
        self.assert_refused(self.invoke(['--park', 'yose'], key=''))

    def test_help_empty_and_arbitrary_arguments_are_refused_without_echo(self):
        for arguments in ([], ['--help'], ['--unknown', 'sensitive-argument'],
                          ['--park', 'grca', '--live']):
            with self.subTest(arguments=arguments):
                result = self.invoke(arguments)
                self.assert_refused(result)
                self.assertNotIn('sensitive-argument', result[2])

    def test_entry_point_does_not_read_environment(self):
        class UnreadableEnvironment(dict):
            def get(self, *args):
                raise AssertionError('legacy command must not read credentials')

        errors = io.StringIO()
        with patch.object(os, 'environ', UnreadableEnvironment()), redirect_stderr(errors):
            self.assertEqual(legacy.main(['--park', 'yose']), 2)
        self.assertIn('python -m tracker.stage', errors.getvalue())

    def test_module_process_exits_nonzero_with_safe_migration_message(self):
        result = subprocess.run([sys.executable, '-m', 'tracker', '--park', 'yose'],
                                capture_output=True, text=True,
                                env={**os.environ, 'NPS_API_KEY': ''}, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')
        self.assertIn('python -m tracker.stage', result.stderr)
        self.assertIn('reviewed promotion', result.stderr)
