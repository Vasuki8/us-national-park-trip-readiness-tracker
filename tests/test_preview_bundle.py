"""Offline private preview preparation, using the actual committed archive reader."""
import copy
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch
from history_fixtures import snapshot, next_snapshot
from tracker.history_model import HistoryError, canonical, digest
from tracker.history_store import HistoryStore
from tracker.preview import make_bundle, prepare_bundle, main

class PreviewBundleTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(); self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name); self.archive = self.root/'archive'; self.output = self.root/'bundles'
        self.store = HistoryStore(self.archive)

    def test_empty_archive_is_explicit_and_not_initialized(self):
        bundle = make_bundle(self.store)
        self.assertFalse(self.archive.exists())
        self.assertEqual([v['snapshot']['park_code'] for v in bundle['views']], ['yose','romo','yell','zion','grca'])
        self.assertTrue(all(v['snapshot']['collection_status'] == 'never_checked' for v in bundle['views']))
        self.assertFalse(bundle['publication_performed'])
        self.assertEqual(bundle['purpose'], 'private_preview')
        self.assertEqual(bundle['bundle_id'], digest({k:v for k,v in bundle.items() if k != 'bundle_id'}))

    def test_each_pair_is_bound_to_its_committed_head(self):
        identifier = self.store.append(snapshot()); bundle = make_bundle(self.store)
        pair = bundle['views'][0]
        self.assertEqual(pair['history']['head_observation_id'], identifier)
        self.assertEqual(pair['history']['snapshot_hash'], digest(pair['snapshot']))
        self.assertIsNone(pair['snapshot']['published_at'])
        self.assertNotIn('prepared_at', bundle)

    def test_failure_and_quarantine_remain_degraded(self):
        for code, status in [('yose','failed'), ('romo','quarantined')]:
            first = snapshot(code=code); self.store.append(first); self.store.append(next_snapshot(first,status=status))
        bundle = make_bundle(self.store)
        for pair, status in zip(bundle['views'], ['failed','quarantined']):
            self.assertEqual(pair['snapshot']['collection_status'], status)
            self.assertEqual(pair['snapshot']['last_successful_fetch_at'], '2026-09-28T10:00:00Z')
            self.assertEqual(pair['history']['observations'][0]['changes'], [])

    def test_pending_text_and_archive_paths_are_never_exported(self):
        self.store.append(snapshot()); before = make_bundle(self.store)
        (self.archive/'pending.json').write_text('{"secret":"synthetic-pending-private"}')
        after = make_bundle(self.store)
        self.assertEqual(before, after)
        self.assertNotIn('synthetic-pending-private', json.dumps(after))
        self.assertNotIn(str(self.archive), json.dumps(after))

    def test_preparation_keeps_archive_unchanged(self):
        self.store.append(snapshot())
        files = lambda: {str(p.relative_to(self.archive)):p.read_bytes() for p in self.archive.rglob('*') if p.is_file()}
        before = files(); path = prepare_bundle(self.archive, self.output)
        self.assertEqual(files(), before)
        self.assertEqual(path.read_bytes(), canonical(make_bundle(self.store)))
        self.assertEqual(path.name, make_bundle(self.store)['bundle_id'] + '.json')

    def test_exact_retry_is_immutable_and_idempotent(self):
        one = prepare_bundle(self.archive, self.output); timestamp = one.stat().st_mtime_ns
        two = prepare_bundle(self.archive, self.output)
        self.assertEqual(one, two); self.assertEqual(one.stat().st_mtime_ns, timestamp)
        self.assertEqual(len(list(self.output.iterdir())), 1)

    def test_existing_corrupt_bundle_is_not_overwritten(self):
        path = prepare_bundle(self.archive, self.output); path.write_text('corrupt')
        with self.assertRaises(HistoryError): prepare_bundle(self.archive, self.output)
        self.assertEqual(path.read_text(), 'corrupt')

    def test_interrupted_install_leaves_no_completed_bundle(self):
        with patch('tracker.preview.os.link', side_effect=OSError('synthetic interruption')):
            with self.assertRaises(OSError): prepare_bundle(self.archive, self.output)
        self.assertEqual(list(self.output.glob('*.json')), [])
        self.assertTrue(prepare_bundle(self.archive, self.output).is_file())

    def test_corrupt_archive_refuses_before_output_creation(self):
        self.store.append(snapshot()); next((self.archive/'evidence').glob('*.json')).write_text('{}')
        with self.assertRaises(HistoryError): prepare_bundle(self.archive, self.output)
        self.assertFalse(self.output.exists())

    def test_output_cannot_be_archive_or_its_descendant(self):
        for path in [self.archive, self.archive/'previews']:
            with self.subTest(path=path), self.assertRaises(HistoryError): prepare_bundle(self.archive, path)
        self.assertFalse(self.archive.exists())

    def test_protected_repo_paths_and_symlinks_are_rejected(self):
        with patch('tracker.preview.PROJECT_ROOT', self.root):
            for folder in ('data','public','src','dist','.git','scripts','preview','node_modules'):
                with self.subTest(folder=folder), self.assertRaises(HistoryError): prepare_bundle(self.archive, self.root/folder)
        real = self.root/'real'; real.mkdir(); alias = self.root/'alias'; alias.symlink_to(real, target_is_directory=True)
        with self.assertRaises(HistoryError): prepare_bundle(self.archive, alias/'bundles')
        self.assertEqual(list(real.iterdir()), [])

    def test_bounds_do_not_delete_existing_files(self):
        self.output.mkdir(); retained = self.output/'keep'; retained.write_text('keep')
        with patch('tracker.preview.MAX_OUTPUT_BYTES', 1):
            with self.assertRaises(HistoryError): prepare_bundle(self.archive, self.output)
        self.assertEqual(retained.read_text(), 'keep')
        with patch('tracker.preview.MAX_BUNDLE_BYTES', 100):
            with self.assertRaises(HistoryError): make_bundle(self.store)

    def test_cli_reports_identity_not_notice_text_and_never_calls_network(self):
        self.store.append(snapshot()); out, err = io.StringIO(), io.StringIO()
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network forbidden')), redirect_stdout(out), redirect_stderr(err):
            result = main(['--archive-dir',str(self.archive),'--output-dir',str(self.output)])
        self.assertEqual(result, 0); self.assertEqual(err.getvalue(), '')
        report = json.loads(out.getvalue()); self.assertFalse(report['publication_performed'])
        self.assertNotIn('Synthetic facility notice', out.getvalue())

    def test_cli_errors_do_not_echo_private_paths_or_exceptions(self):
        out, err = io.StringIO(), io.StringIO()
        with patch('tracker.preview.prepare_bundle', side_effect=OSError('synthetic-secret-path')), redirect_stdout(out), redirect_stderr(err):
            result = main(['--archive-dir',str(self.archive),'--output-dir',str(self.output)])
        self.assertEqual(result, 2); self.assertNotIn('synthetic-secret-path', err.getvalue())
        self.assertEqual(out.getvalue(), '')

    def test_invalid_kind_is_not_accepted_as_approval(self):
        with self.assertRaises(HistoryError): make_bundle(self.store, data_kind='approved_live')
        self.assertEqual(make_bundle(self.store, data_kind='synthetic')['data_kind'], 'synthetic')

if __name__ == '__main__': unittest.main()
