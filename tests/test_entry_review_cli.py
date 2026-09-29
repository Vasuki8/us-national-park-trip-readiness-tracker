"""Real subprocess CLI tests with synthetic data and private temporary files."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from tracker.entry_review_io import read_private_json, ReviewStoreError
from test_entry_review_store import request, NOW

class ReviewCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'store'; self.input=Path(self.tmp.name)/'input.json'
        self.input.write_text(json.dumps(request())); self.input.chmod(0o600)
    def cli(self,*args):
        return subprocess.run([sys.executable,'-m','tracker.entry_review_cli',*args],capture_output=True,text=True,timeout=15)
    def test_status_missing_store_does_not_create_it(self):
        result=self.cli('status','--store',str(self.root))
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['revision'],None); self.assertFalse(self.root.exists())
    def test_record_and_disposition_cli_are_usable_without_echoing_text(self):
        result=self.cli('record','--store',str(self.root),'--input',str(self.input),'--expected-revision','empty')
        self.assertEqual(result.returncode,0,result.stderr)
        saved=json.loads(result.stdout); self.assertEqual(saved['pending_proposals'],1)
        self.assertFalse(saved['publication_performed']); self.assertFalse(saved['approval_performed'])
        self.assertNotIn('Synthetic guidance',result.stdout); self.assertNotIn(str(self.root),result.stdout)
        note={'proposal_id':saved['pending'][0]['proposal_id'],'reviewer':'test-operator','decision':'request_guidance_revision','rationale':'Check the surrounding synthetic exception.'}
        self.input.write_text(json.dumps(note))
        result=self.cli('disposition','--store',str(self.root),'--input',str(self.input),'--expected-revision',saved['revision'])
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['reviewer_dispositions'],1)
        self.assertEqual(json.loads(result.stdout)['pending_proposals'],1)
        self.assertNotIn(note['rationale'],result.stdout)
    def test_unknown_arguments_and_missing_private_input_do_not_echo_paths(self):
        for args in [('secret-path-name',),('record','--store',str(self.root),'--input',str(self.input/'secret-key'),'--expected-revision','empty')]:
            result=self.cli(*args)
            self.assertNotEqual(result.returncode,0)
            self.assertNotIn('secret-path',result.stderr); self.assertNotIn('secret-key',result.stderr)
            self.assertEqual(result.stdout,'')
    def test_duplicate_json_keys_invalid_utf8_and_nonfinite_input_are_refused(self):
        for raw in (b'{"a":1,"a":2}',b'\xff',b'{"a":NaN}'):
            self.input.write_bytes(raw)
            with self.assertRaises(ReviewStoreError): read_private_json(self.input)
    def test_symlink_hardlink_and_publicly_readable_input_are_refused(self):
        link=Path(self.tmp.name)/'link.json'; link.symlink_to(self.input)
        with self.assertRaises(ReviewStoreError): read_private_json(link)
        link.unlink(); os.link(self.input,link)
        with self.assertRaises(ReviewStoreError): read_private_json(self.input)
        link.unlink(); self.input.chmod(0o644)
        with self.assertRaises(ReviewStoreError): read_private_json(self.input)
    def test_fifo_input_refuses_without_waiting_for_a_writer(self):
        self.input.unlink(); os.mkfifo(self.input,0o600)
        result=self.cli('record','--store',str(self.root),'--input',str(self.input),'--expected-revision','empty')
        self.assertNotEqual(result.returncode,0); self.assertFalse(self.root.exists())
    def test_oversized_input_is_refused_before_parsing(self):
        with self.input.open('wb') as stream: stream.truncate(8*1024*1024+1)
        with self.assertRaises(ReviewStoreError): read_private_json(self.input)
    def test_recover_does_not_initialize_missing_store(self):
        result=self.cli('recover','--store',str(self.root))
        self.assertNotEqual(result.returncode,0); self.assertFalse(self.root.exists())

if __name__=='__main__': unittest.main()
