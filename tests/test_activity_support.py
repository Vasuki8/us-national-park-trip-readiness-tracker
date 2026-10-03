"""Pure attempt preflight and explicit large-checkpoint encoding/read bounds."""
import copy
import hashlib
import inspect
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tracker import entry_review_io, history_model, park_activities
from test_park_activities import T0, T1, activity, page


class ActivitySupportTests(unittest.TestCase):
    def preflight(self):
        self.assertTrue(hasattr(park_activities, 'preflight_activity_attempt'),
                        'The pure activity attempt preflight is not implemented.')
        return park_activities.preflight_activity_attempt

    def baseline(self):
        return park_activities.collect_activities('yose', park_activities.initial_activities('yose'),
                                                 T0, lambda _start: page([activity()]))

    def test_preflight_returns_accepted_copy_without_advancing_attempt_clock(self):
        baseline = self.baseline()
        result = self.preflight()('yose', baseline, T1)
        self.assertEqual(result, baseline)
        result['records'][0]['related_parks'].clear()
        self.assertEqual(len(baseline['records'][0]['related_parks']), 1)

    def test_preflight_refuses_scope_clock_corruption_and_insufficient_failure_capacity(self):
        preflight = self.preflight()
        baseline = self.baseline()
        for code, now in (('yell', T1), ('acad', T1), ('yose', T0),
                          ('yose', '2026-10-03T06:00:00-04:00'), ('yose', 'invalid')):
            with self.subTest(code=code, now=now), self.assertRaises(park_activities.ActivityError):
                preflight(code, baseline, now)
        corrupt = copy.deepcopy(baseline)
        corrupt['records'][0]['title'] = 'Unbound mutation'
        with self.assertRaises(park_activities.ActivityError):
            preflight('yose', corrupt, T1)
        size = len(json.dumps(baseline, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
        with patch.object(park_activities, 'MAX_SNAPSHOT_BYTES', size):
            with self.assertRaises(park_activities.ActivityError):
                preflight('yose', baseline, T1)

    def test_explicit_encoding_limit_preserves_canonical_bytes_and_digest(self):
        self.assertIn('max_bytes', inspect.signature(history_model.canonical).parameters,
                      'Canonical encoding needs an explicit bounded override.')
        value = {'text': 'Synthetic café 🏞'}
        expected = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(history_model.canonical(value, max_bytes=len(expected)), expected)
        self.assertEqual(history_model.digest(value, max_bytes=len(expected)), hashlib.sha256(expected).hexdigest())
        with self.assertRaises(history_model.HistoryError):
            history_model.canonical(value, max_bytes=len(expected) - 1)
        with self.assertRaises(history_model.HistoryError):
            history_model.digest(value, max_bytes=len(expected) - 1)
        for limit in (True, False, 0, -1, 2.0, '100'):
            with self.subTest(limit=limit), self.assertRaises(history_model.HistoryError):
                history_model.canonical(value, max_bytes=limit)

    def test_legacy_encoding_default_stays_bounded_while_explicit_large_value_succeeds(self):
        self.assertIn('max_bytes', inspect.signature(history_model.canonical).parameters,
                      'Large activity checkpoints need an explicit encoding limit.')
        value = {'padding': 'x' * (10 * 1024 * 1024)}
        with self.assertRaises(history_model.HistoryError):
            history_model.canonical(value)
        encoded = history_model.canonical(value, max_bytes=11 * 1024 * 1024)
        self.assertEqual(json.loads(encoded), value)
        self.assertEqual(history_model.digest(value, max_bytes=len(encoded)), hashlib.sha256(encoded).hexdigest())
        for bad in (float('inf'), float('nan'), '\ud800'):
            with self.subTest(value=repr(bad)), self.assertRaises(history_model.HistoryError):
                history_model.canonical({'bad': bad}, max_bytes=11 * 1024 * 1024)

    @unittest.skipUnless(os.name == 'posix', 'Private read requires POSIX.')
    def test_explicit_private_read_limit_keeps_permissions_strict_and_old_default(self):
        self.assertIn('max_bytes', inspect.signature(entry_review_io.read_private_json).parameters,
                      'Large activity checkpoints need an explicitly bounded private reader.')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o700)
            path = root / 'large.json'
            value = {'padding': 'x' * (8 * 1024 * 1024)}
            raw = json.dumps(value, separators=(',', ':')).encode()
            path.write_bytes(raw)
            path.chmod(0o600)
            with self.assertRaises(entry_review_io.ReviewStoreError):
                entry_review_io.read_private_json(path)
            self.assertEqual(entry_review_io.read_private_json(path, max_bytes=len(raw)), value)
            with self.assertRaises(entry_review_io.ReviewStoreError):
                entry_review_io.read_private_json(path, max_bytes=len(raw) - 1)
            path.chmod(0o644)
            with self.assertRaises(entry_review_io.ReviewStoreError):
                entry_review_io.read_private_json(path, max_bytes=len(raw))

    @unittest.skipUnless(os.name == 'posix', 'Private read requires POSIX.')
    def test_explicit_reader_limits_and_strict_json_refuse_without_relaxing_defaults(self):
        self.assertIn('max_bytes', inspect.signature(entry_review_io.read_private_json).parameters)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o700)
            path = root / 'input.json'
            path.write_bytes(b'{}')
            path.chmod(0o600)
            for limit in (True, False, 0, -1, 2.0, '100'):
                with self.subTest(limit=limit), self.assertRaises(entry_review_io.ReviewStoreError):
                    entry_review_io.read_private_json(path, max_bytes=limit)
            for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'\xff'):
                path.write_bytes(raw)
                with self.subTest(raw=raw), self.assertRaises(entry_review_io.ReviewStoreError):
                    entry_review_io.read_private_json(path, max_bytes=1024)
