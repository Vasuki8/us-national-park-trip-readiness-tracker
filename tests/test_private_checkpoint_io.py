"""Synthetic neutral checkpoint file operations on private POSIX storage."""
import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tracker.entry_review_io import ReviewStoreError


@unittest.skipUnless(os.name == 'posix', 'Private checkpoint storage requires POSIX.')
class PrivateCheckpointIOTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.root.chmod(0o700)
        self.output = self.root / 'checkpoint.json'

    def adapter(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.private_checkpoint_io'),
                             'Neutral private checkpoint primitives are absent.')
        return importlib.import_module('tracker.private_checkpoint_io')

    def test_locked_install_is_private_single_link_and_does_not_overwrite(self):
        module = self.adapter()
        with module.locked_private_output(self.output) as output:
            lock = Path(str(self.output) + '.lock')
            self.assertEqual(lock.stat().st_mode & 0o777, 0o600)
            module.install_private_bytes(output, b'accepted bytes', max_bytes=14)
        self.assertEqual(self.output.read_bytes(), b'accepted bytes')
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.output.stat().st_nlink, 1)
        with self.assertRaises(ReviewStoreError):
            with module.locked_private_output(self.output):
                self.fail('An existing output entered the writer.')
        self.assertEqual(self.output.read_bytes(), b'accepted bytes')
        self.assertEqual(list(self.root.iterdir()), [self.output])

    def test_bounds_refuse_without_temporary_or_completed_files(self):
        module = self.adapter()
        for data, limit in ((b'', 1), (b'ab', 1), ('text', 4), (b'a', 0), (b'a', True)):
            with self.subTest(data=data, limit=limit), self.assertRaises(ReviewStoreError):
                module.install_private_bytes(self.output, data, max_bytes=limit)
            self.assertEqual(list(self.root.iterdir()), [])

    def test_existing_or_competing_lock_is_not_stolen(self):
        module = self.adapter()
        lock = Path(str(self.output) + '.lock')
        with module.locked_private_output(self.output):
            before = lock.read_bytes()
            with self.assertRaises(ReviewStoreError):
                with module.locked_private_output(self.output):
                    self.fail('A competing writer entered.')
            self.assertEqual(lock.read_bytes(), before)
        self.assertFalse(lock.exists())
        lock.write_bytes(b'abandoned writer')
        lock.chmod(0o600)
        with self.assertRaises(ReviewStoreError):
            with module.locked_private_output(self.output):
                self.fail('An abandoned lock was stolen.')
        self.assertEqual(lock.read_bytes(), b'abandoned writer')

    def test_guard_refuses_relative_traversal_checkout_alias_missing_parent_and_symlink(self):
        module = self.adapter()
        repo = Path(__file__).resolve().parents[1]
        alias = Path('//' + str(repo).lstrip('/')) / 'activity.json'
        link = self.root / 'link'
        link.symlink_to(self.root, target_is_directory=True)
        for path in (Path('relative'), self.root / '..' / 'escape', repo / 'ignored.json',
                     alias, repo.parent / 'ancestor.json', self.root / 'missing' / 'file',
                     link / 'file'):
            with self.subTest(path=path), self.assertRaises(ReviewStoreError):
                module.private_checkpoint_path(path)

    def test_insecure_parent_is_not_repaired(self):
        module = self.adapter()
        self.root.chmod(0o755)
        with self.assertRaises(ReviewStoreError):
            with module.locked_private_output(self.output):
                self.fail('An insecure parent entered the writer.')
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o755)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_source_output_or_lock_overlap_refuses_without_modification(self):
        module = self.adapter()
        for source in (self.output, Path(str(self.output) + '.lock')):
            with self.subTest(source=source), self.assertRaises(ReviewStoreError):
                with module.locked_private_output(self.output, source):
                    self.fail('Overlapping paths entered the writer.')
        self.assertEqual(list(self.root.iterdir()), [])

    def test_unexpected_destination_is_never_replaced_at_commit(self):
        module = self.adapter()
        with module.locked_private_output(self.output) as output:
            output.write_bytes(b'other writer')
            output.chmod(0o600)
            with self.assertRaises(FileExistsError):
                module.install_private_bytes(output, b'ours', max_bytes=4)
        self.assertEqual(self.output.read_bytes(), b'other writer')
        self.assertEqual(list(self.root.iterdir()), [self.output])

    def test_preexisting_orphan_temporary_is_not_pruned(self):
        module = self.adapter()
        orphan = self.root / '.checkpoint-old.tmp'
        orphan.write_bytes(b'preserve uncertain evidence')
        orphan.chmod(0o600)
        with module.locked_private_output(self.output) as output:
            module.install_private_bytes(output, b'ours', max_bytes=4)
        self.assertEqual(orphan.read_bytes(), b'preserve uncertain evidence')
        self.assertEqual(set(self.root.iterdir()), {orphan, self.output})

    def test_link_failure_cleans_new_temporary_without_installing_output(self):
        module = self.adapter()
        with patch.object(module.os, 'link', side_effect=OSError('private filesystem error')):
            with self.assertRaises(OSError):
                with module.locked_private_output(self.output) as output:
                    module.install_private_bytes(output, b'ours', max_bytes=4)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_postcommit_sync_failure_preserves_single_link_completed_output(self):
        module = self.adapter()
        with patch.object(module, 'sync_private_directory', side_effect=OSError('private sync error')):
            with self.assertRaises(OSError):
                with module.locked_private_output(self.output) as output:
                    module.install_private_bytes(output, b'ours', max_bytes=4)
        self.assertEqual(self.output.read_bytes(), b'ours')
        self.assertEqual(self.output.stat().st_nlink, 1)
        self.assertEqual(list(self.root.iterdir()), [self.output])


if __name__ == '__main__':
    unittest.main()
