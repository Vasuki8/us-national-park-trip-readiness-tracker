"""Actual abrupt subprocess termination; not a power-loss or network-filesystem test."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from history_fixtures import snapshot, next_snapshot
from tracker.history_model import HistoryError
from tracker.history_store import HistoryStore

class ProcessInterruptionTests(unittest.TestCase):
    def test_abrupt_exit_leaves_old_head_readable_and_requires_lock_recovery(self):
        child = """
import json, os, sys
from pathlib import Path
from tracker.history_store import HistoryStore
store = HistoryStore(Path(sys.argv[1]))
store._commit_head = lambda *args: os._exit(99)
store.append(json.loads(sys.stdin.read()))
"""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/'archive'; store = HistoryStore(root)
            first = snapshot(); identifier = store.append(first); candidate = next_snapshot(first)
            result = subprocess.run([sys.executable, '-c', child, str(root)], input=json.dumps(candidate),
                                    text=True, capture_output=True, timeout=10,
                                    cwd=Path(__file__).resolve().parents[1])
            self.assertEqual(result.returncode, 99)
            self.assertEqual(store.read('yose')[-1]['observation_id'], identifier)
            with self.assertRaisesRegex(HistoryError, 'archive_locked'):
                store.append(candidate)
            # The child has exited (verified above); simulate explicit operator recovery.
            (root/'.writer.lock').unlink()
            store.append(candidate)
            self.assertEqual(len(store.read('yose')), 2)
            self.assertEqual(store.read('yose')[-1]['snapshot'], candidate)

if __name__ == '__main__': unittest.main()
