import tempfile
import unittest
from pathlib import Path
from staging_fixtures import T1, T2, snapshot
from tracker.history_model import HistoryError
from tracker.history_store import HistoryStore

class ExpectedParentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'archive'; self.store = HistoryStore(self.root)

    def test_empty_parent_and_matching_parent_append(self):
        first = snapshot(); head = self.store.append(first, expected_head=None)
        second = snapshot(T1, first); next_head = self.store.append(second, expected_head=head)
        self.assertEqual(self.store.read('yose')[-1]['previous_id'], head)
        self.assertNotEqual(head, next_head)

    def test_intervening_writer_rejects_stale_parent_even_with_later_clock(self):
        first = snapshot(); head = self.store.append(first)
        second = snapshot(T1, first); new_head = self.store.append(second)
        candidate = snapshot(T2, first)
        with self.assertRaisesRegex(HistoryError, 'archive_head_changed'):
            self.store.append(candidate, expected_head=head)
        self.assertEqual(self.store.read('yose')[-1]['observation_id'], new_head)
        self.assertEqual(len(self.store.read('yose')), 2)

    def test_exact_retry_accepts_original_parent_without_duplicate(self):
        first = snapshot(); head = self.store.append(first, expected_head=None)
        self.assertEqual(self.store.append(first, expected_head=None), head)
        second = snapshot(T1, first); next_head = self.store.append(second, expected_head=head)
        self.assertEqual(self.store.append(second, expected_head=head), next_head)
        self.assertEqual(len(self.store.read('yose')), 2)

    def test_unrelated_parent_cannot_acknowledge_identical_snapshot(self):
        first = snapshot(); head = self.store.append(first)
        with self.assertRaisesRegex(HistoryError, 'archive_head_changed'):
            self.store.append(first, expected_head='a'*64)
        self.assertEqual(self.store.read('yose')[-1]['observation_id'], head)

    def test_invalid_parent_is_rejected_before_archive_creation(self):
        for value in (False, '', '../escape', 'g'*64, []):
            with self.subTest(value=value), self.assertRaises(HistoryError):
                self.store.append(snapshot(), expected_head=value)
        self.assertFalse(self.root.exists())
