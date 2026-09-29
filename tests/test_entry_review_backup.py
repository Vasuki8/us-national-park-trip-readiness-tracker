"""Private entry-review backup/restore contracts. Synthetic evidence only."""
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from tracker.entry_review_store import EntryReviewStore, ReviewStoreError
from tracker.entry_review_backup import create_backup, verify_backup, restore_backup, main
from test_entry_review_store import request, NOW

class ReviewBackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name); self.base.chmod(0o700)
        self.root=self.base/'review'; self.store=EntryReviewStore(self.root)
        self.saved=self.store.record(request(),expected_revision=None,now=NOW)
        self.backups=self.base/'backups'
        self.restored=self.base/'restored'

    def test_backup_is_content_addressed_private_and_source_is_unchanged(self):
        before=(self.root/'review.sqlite3').read_bytes()
        manifest=create_backup(self.store,self.backups)
        bundle=self.backups/manifest['backup_id']
        database=bundle/'review.sqlite3'; meta=bundle/'manifest.json'
        self.assertEqual(self.backups.stat().st_mode & 0o777,0o700)
        self.assertEqual(bundle.stat().st_mode & 0o777,0o700)
        self.assertEqual(database.stat().st_mode & 0o777,0o600)
        self.assertEqual(meta.stat().st_mode & 0o777,0o600)
        self.assertEqual((self.root/'review.sqlite3').read_bytes(),before)
        self.assertEqual(manifest['purpose'],'private_entry_review_backup')
        self.assertEqual(manifest['ledger_revision'],self.saved['revision'])
        self.assertEqual(manifest['event_count'],1)
        self.assertEqual(manifest['database_bytes'],len(database.read_bytes()))
        self.assertEqual(manifest['database_sha256'],hashlib.sha256(database.read_bytes()).hexdigest())
        core={k:v for k,v in manifest.items() if k!='backup_id'}
        from tracker.entry_sources import digest
        self.assertEqual(manifest['backup_id'],digest(core))
        self.assertEqual(json.loads(meta.read_text()),manifest)

    def test_verify_replays_complete_backup_without_modifying_it(self):
        manifest=create_backup(self.store,self.backups)
        bundle=self.backups/manifest['backup_id']
        before={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in bundle.iterdir()}
        verified=verify_backup(bundle)
        self.assertEqual(verified,manifest)
        after={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in bundle.iterdir()}
        self.assertEqual(after,before)

    def test_exact_backup_retry_is_idempotent(self):
        first=create_backup(self.store,self.backups)
        bundle=self.backups/first['backup_id']; stamp=(bundle/'review.sqlite3').stat().st_mtime_ns
        second=create_backup(self.store,self.backups)
        self.assertEqual(second,first)
        self.assertEqual((bundle/'review.sqlite3').stat().st_mtime_ns,stamp)
        self.assertEqual(len(list(self.backups.iterdir())),1)

    def test_corrupt_database_manifest_mismatch_and_unexpected_files_fail(self):
        manifest=create_backup(self.store,self.backups); bundle=self.backups/manifest['backup_id']
        database=bundle/'review.sqlite3'
        original=database.read_bytes(); database.write_bytes(original[:-32]+b'x'*32); database.chmod(0o600)
        with self.assertRaises(ReviewStoreError): verify_backup(bundle)
        database.write_bytes(original); database.chmod(0o600)
        meta=bundle/'manifest.json'; value=json.loads(meta.read_text()); value['event_count']=2
        meta.write_text(json.dumps(value,separators=(',',':'),sort_keys=True)); meta.chmod(0o600)
        with self.assertRaises(ReviewStoreError): verify_backup(bundle)
        meta.write_text(json.dumps(manifest,separators=(',',':'),sort_keys=True)); meta.chmod(0o600)
        extra=bundle/'unexpected'; extra.write_text('private'); extra.chmod(0o600)
        with self.assertRaises(ReviewStoreError): verify_backup(bundle)

    def test_restore_creates_fresh_verified_ledger_without_manifest(self):
        manifest=create_backup(self.store,self.backups); bundle=self.backups/manifest['backup_id']
        result=restore_backup(bundle,self.restored)
        restored=EntryReviewStore(self.restored).read()
        self.assertEqual(result['ledger_revision'],manifest['ledger_revision'])
        self.assertEqual(restored,self.store.read())
        self.assertEqual(set(p.name for p in self.restored.iterdir()),{'review.sqlite3'})
        self.assertEqual(self.restored.stat().st_mode & 0o777,0o700)
        self.assertEqual((self.restored/'review.sqlite3').stat().st_mode & 0o777,0o600)
        self.assertFalse(result['network_performed']); self.assertFalse(result['publication_performed'])

    def test_restore_refuses_existing_destination_before_changing_it(self):
        manifest=create_backup(self.store,self.backups); bundle=self.backups/manifest['backup_id']
        self.restored.mkdir(mode=0o700); marker=self.restored/'keep'; marker.write_text('keep'); marker.chmod(0o600)
        with self.assertRaises(ReviewStoreError): restore_backup(bundle,self.restored)
        self.assertEqual(marker.read_text(),'keep')

    def test_protected_symlink_and_insecure_paths_are_refused(self):
        manifest=create_backup(self.store,self.backups); bundle=self.backups/manifest['backup_id']
        repo=Path(__file__).resolve().parents[1]
        with self.assertRaises(ReviewStoreError): create_backup(self.store,repo/'data'/'review-backups')
        with self.assertRaises(ReviewStoreError): restore_backup(bundle,repo/'data'/'restored-review')
        real=self.base/'real'; real.mkdir(mode=0o700); alias=self.base/'alias'; alias.symlink_to(real,target_is_directory=True)
        with self.assertRaises(ReviewStoreError): create_backup(self.store,alias/'backups')
        insecure=self.base/'insecure'; insecure.mkdir(mode=0o755)
        with self.assertRaises(ReviewStoreError): restore_backup(bundle,insecure/'restored')

    def test_interrupted_backup_and_restore_leave_no_completed_destination(self):
        with patch('tracker.entry_review_backup.os.rename',side_effect=OSError('synthetic interruption')):
            with self.assertRaises(OSError): create_backup(self.store,self.backups)
        self.assertTrue(self.backups.exists())
        self.assertEqual([p for p in self.backups.iterdir() if not p.name.startswith('.pending-')],[])
        manifest=create_backup(self.store,self.backups); bundle=self.backups/manifest['backup_id']
        with patch('tracker.entry_review_backup.os.rename',side_effect=OSError('synthetic interruption')):
            with self.assertRaises(OSError): restore_backup(bundle,self.restored)
        self.assertFalse(self.restored.exists())
        self.assertFalse(any(p.name.startswith('.restore-') for p in self.base.iterdir()))
        self.assertEqual(restore_backup(bundle,self.restored)['ledger_revision'],manifest['ledger_revision'])

    def test_empty_or_unreadable_ledger_cannot_be_backed_up(self):
        empty=EntryReviewStore(self.base/'empty')
        with self.assertRaises(ReviewStoreError): create_backup(empty,self.backups/'empty')
        self.assertFalse((self.backups/'empty').exists())

    def test_cli_backup_verify_restore_reports_metadata_without_private_paths(self):
        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            code=main(['backup','--store',str(self.root),'--backup-root',str(self.backups)])
        self.assertEqual(code,0,err.getvalue()); backup=json.loads(out.getvalue())
        self.assertNotIn(str(self.base),out.getvalue()+err.getvalue())
        self.assertEqual(backup['ledger_revision'],self.saved['revision'])
        bundle=self.backups/backup['backup_id']

        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            code=main(['verify','--backup',str(bundle)])
        self.assertEqual(code,0,err.getvalue()); self.assertEqual(json.loads(out.getvalue())['backup_id'],backup['backup_id'])
        self.assertNotIn(str(self.base),out.getvalue()+err.getvalue())

        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            code=main(['restore','--backup',str(bundle),'--destination',str(self.restored)])
        self.assertEqual(code,0,err.getvalue()); result=json.loads(out.getvalue())
        self.assertEqual(result['ledger_revision'],self.saved['revision'])
        self.assertNotIn(str(self.base),out.getvalue()+err.getvalue())

if __name__=='__main__': unittest.main()
