"""Process termination at transaction boundaries; not hardware-power-loss simulation."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from staging_fixtures import T0, T1, feed, raw
from tracker.history_model import HistoryError
from tracker.staging import StagingCollector

class StagingCrashTests(unittest.TestCase):
    def check_boundary(self, boundary):
        child = r'''
import os, sys
from pathlib import Path
from tracker.staging import StagingCollector
stage = StagingCollector(Path(sys.argv[1]))
mode = sys.argv[2]
if mode == 'before_archive': stage._finish = lambda *args: os._exit(99)
elif mode == 'during_archive': stage.archive._commit_head = lambda *args: os._exit(99)
else: stage._clear_pending = lambda *args: os._exit(99)
stage.collect('yose', '2026-09-28T21:00:00Z', lambda start: {'total':'0','start':'0','data':[]})
'''
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/'stage'; stage = StagingCollector(root)
            stage.collect('yose', T0, lambda start: feed([]))
            result = subprocess.run([sys.executable, '-c', child, str(root), boundary],
                                    capture_output=True, text=True, timeout=10,
                                    cwd=Path(__file__).resolve().parents[1])
            self.assertEqual(result.returncode, 99, result.stderr)
            self.assertTrue(stage.status('yose')['writer_locked'])
            self.assertTrue((root/'pending/yose.json').exists())
            with self.assertRaisesRegex(HistoryError, 'staging_locked'): stage.recover('yose')
            # Test-only explicit recovery after subprocess.run proves that writer stopped.
            (root/'.stage.lock').unlink()
            archive_lock = root/'archive/.writer.lock'
            if archive_lock.exists(): archive_lock.unlink()
            stage.recover('yose')
            entries = stage.archive.read('yose')
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[-1]['snapshot']['last_checked_at'], T1)
            self.assertEqual(stage.status('yose')['stage_state'], 'idle')
            self.assertEqual(stage.recover('yose')['operation'], 'nothing_to_recover')

    def test_termination_before_archive_commit_recovers_receipt(self): self.check_boundary('before_archive')
    def test_termination_during_archive_commit_recovers_receipt(self): self.check_boundary('during_archive')
    def test_termination_after_archive_commit_recovers_without_duplicate(self): self.check_boundary('after_archive')
