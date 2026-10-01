"""Synthetic POSIX path boundaries; no operator evidence or network access."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tracker.entry_review_io import ReviewStoreError, check_path, read_private_json
from tracker.entry_review_store import EntryReviewStore
from test_entry_review_store import NOW, request


@unittest.skipUnless(os.name == 'posix', 'private storage requires POSIX')
class PrivatePathTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / 'checkout'
        self.project.mkdir(mode=0o700)
        repository = patch('tracker.entry_review_io.REPO_ROOT', self.project)
        repository.start()
        self.addCleanup(repository.stop)

    @staticmethod
    def alias(path):
        return Path('//' + str(path).lstrip('/'))

    def test_checkout_and_ancestor_aliases_refuse_before_storage_access(self):
        targets = [self.project, self.project / 'state', self.project / 'private-review',
                   self.project / 'dist', self.project / 'dist-pages', self.root,
                   self.root.parent]
        before = set(self.root.rglob('*'))
        for target in targets:
            for path in (target, self.alias(target)):
                with self.subTest(path=path), self.assertRaisesRegex(
                        ReviewStoreError, '^protected_repository_path$'):
                    check_path(path)
        self.assertEqual(set(self.root.rglob('*')), before)

    def test_absent_checkout_ledger_alias_refuses_without_creating_files(self):
        target = self.project / 'private-review'
        with self.assertRaisesRegex(ReviewStoreError, '^protected_repository_path$'):
            EntryReviewStore(self.alias(target)).read()
        self.assertFalse(target.exists())
        self.assertEqual(list(self.project.iterdir()), [])

    def test_private_json_checkout_alias_is_not_read(self):
        target = self.project / 'capture.json'
        target.write_text('{"synthetic":true}', encoding='utf-8')
        target.chmod(0o600)
        before = target.read_bytes(), target.stat().st_mtime_ns
        with self.assertRaisesRegex(ReviewStoreError, '^protected_repository_path$'):
            read_private_json(self.alias(target))
        self.assertEqual((target.read_bytes(), target.stat().st_mtime_ns), before)
        self.assertEqual(list(self.project.iterdir()), [target])

    def test_external_alias_supports_private_json_and_ledger_operations(self):
        private = self.root / 'external'
        private.mkdir(mode=0o700)
        target = private / 'input.json'
        target.write_text('{"synthetic":true}', encoding='utf-8')
        target.chmod(0o600)
        self.assertEqual(check_path(self.alias(target)), target)
        self.assertEqual(read_private_json(self.alias(target)), {'synthetic': True})
        store = EntryReviewStore(self.alias(private / 'ledger'))
        saved = store.record(request(), expected_revision=None, now=NOW)
        self.assertEqual(EntryReviewStore(private / 'ledger').read()['revision'], saved['revision'])
        self.assertEqual((private / 'ledger' / 'review.sqlite3').stat().st_mode & 0o777, 0o600)

    def test_relative_traversal_and_symlink_checks_keep_their_codes(self):
        for path in (Path('relative'), self.root / '..' / 'traversal'):
            with self.subTest(path=path), self.assertRaisesRegex(
                    ReviewStoreError, '^invalid_private_path$'):
                check_path(path)
        external = self.root / 'external'
        external.mkdir(mode=0o700)
        link = self.root / 'link'
        link.symlink_to(external, target_is_directory=True)
        for path in (link / 'input.json', self.alias(link / 'input.json')):
            with self.subTest(path=path), self.assertRaisesRegex(
                    ReviewStoreError, '^symlink_private_path$'):
                check_path(path)


if __name__ == '__main__':
    unittest.main()
