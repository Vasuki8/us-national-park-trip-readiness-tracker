"""Private read-only reviewer packet contracts. Synthetic evidence only."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tracker.entry_review_store import EntryReviewStore, ReviewStoreError
from tracker.entry_review_packet import build_review_packet, prepare_review_packet
from test_entry_review_store import request, NOW, LATER, QUOTE, URL

PARK='yose'
SCRIPT_TEXT='<script>window.packetInjected=1</script>'
RATIONALE='Review <b>all</b> synthetic context before any approval.'

class ReviewPacketTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'review'
        self.output=Path(self.tmp.name)/'packets'
        self.store=EntryReviewStore(self.root)
        value=request()
        value['captures'][0]['html']=(
            '<html><body><h1>Entrance Reservations</h1>'
            f'<p>{QUOTE}</p><p>&lt;script&gt;window.packetInjected=1&lt;/script&gt;</p><p>Synthetic surrounding context.</p>'
            '</body></html>'
        )
        self.first=self.store.record(value,expected_revision=None,now=NOW)
        self.source_revision=self.first['committed_revision']
        self.proposal=self.store.read()['register']['proposals'][0]['id']

    def test_packet_contains_complete_review_context_without_actions(self):
        state_before=self.store.read()
        decision={'proposal_id':self.proposal,'reviewer':'packet-reviewer','decision':'retain_hold','rationale':RATIONALE}
        self.store.disposition(decision,expected_revision=self.first['revision'],now=LATER)
        packet=build_review_packet(self.store,PARK,self.source_revision)
        html=packet['html']
        self.assertIn('PRIVATE REVIEW PACKET',html)
        self.assertIn('No approval or publication is performed by this packet.',html)
        self.assertIn(QUOTE,html)
        self.assertIn('&lt;script&gt;window.packetInjected=1&lt;/script&gt;',html)
        self.assertNotIn(SCRIPT_TEXT,html)
        self.assertIn('Review &lt;b&gt;all&lt;/b&gt; synthetic context before any approval.',html)
        self.assertIn(self.proposal,html)
        self.assertIn(self.source_revision,html)
        self.assertIn('2026-09-28T12:00:00Z',html)
        self.assertNotIn('<form',html.lower()); self.assertNotIn('<button',html.lower())
        self.assertNotIn('<script',html.lower())
        self.assertEqual(state_before['events'][0],self.store.read()['events'][0])

    def test_packet_browser_policy_denies_network_navigation_and_forms(self):
        html=build_review_packet(self.store,PARK,self.source_revision)['html'].lower()
        self.assertIn('content-security-policy',html)
        self.assertIn("default-src &#x27;none&#x27;",html)
        self.assertIn("connect-src &#x27;none&#x27;",html)
        for tag in ('<a ','<img','<iframe','<object','<embed','<link','<form','<button','<script'):
            self.assertNotIn(tag,html)

    def test_manifest_is_metadata_only_and_binds_html(self):
        packet=build_review_packet(self.store,PARK,self.source_revision)
        manifest=packet['manifest']; encoded=json.dumps(manifest,sort_keys=True)
        self.assertEqual(manifest['schema_version'],1)
        self.assertEqual(manifest['purpose'],'private_entry_review_packet')
        self.assertEqual(manifest['park_code'],PARK)
        self.assertEqual(manifest['source_event_revision'],self.source_revision)
        self.assertEqual(manifest['proposal_ids'],[self.proposal])
        self.assertEqual(manifest['html_sha256'],hashlib.sha256(packet['html'].encode()).hexdigest())
        self.assertFalse(manifest['network_performed']); self.assertFalse(manifest['approval_performed'])
        self.assertFalse(manifest['publication_performed'])
        self.assertNotIn(QUOTE,encoded); self.assertNotIn('Synthetic surrounding context',encoded)
        self.assertNotIn(str(self.root),encoded)

    def test_selected_event_must_be_latest_retained_source_observation(self):
        second=request('2026-09-28T14:00:00Z')
        saved=self.store.record(second,expected_revision=self.first['revision'],now=LATER)
        with self.assertRaises(ReviewStoreError):
            build_review_packet(self.store,PARK,self.source_revision)
        packet=build_review_packet(self.store,PARK,saved['committed_revision'])
        self.assertEqual(packet['manifest']['source_event_revision'],saved['committed_revision'])

    def test_packet_requires_active_source_level_holds(self):
        state=self.store.read()
        state['register']['proposals'].clear()
        with patch.object(self.store,'read',return_value=state):
            with self.assertRaises(ReviewStoreError): build_review_packet(self.store,PARK,self.source_revision)

    def test_missing_context_and_unknown_park_or_event_fail_closed(self):
        state=self.store.read()
        state['events'][0]['extraction']['sources'][0]['context']=None
        with patch.object(self.store,'read',return_value=state):
            with self.assertRaises(ReviewStoreError): build_review_packet(self.store,PARK,self.source_revision)
        for park,revision in [('xxxx',self.source_revision),(PARK,'0'*64)]:
            with self.subTest(park=park,revision=revision),self.assertRaises(ReviewStoreError):
                build_review_packet(self.store,park,revision)

    def test_prepare_packet_is_atomic_private_and_does_not_modify_ledger(self):
        before=(self.root/'review.sqlite3').read_bytes()
        result=prepare_review_packet(self.store,self.output,PARK,self.source_revision)
        packet_dir=self.output/result['packet_id']
        html=packet_dir/'index.html'; manifest=packet_dir/'manifest.json'
        self.assertTrue(html.is_file()); self.assertTrue(manifest.is_file())
        self.assertEqual(self.output.stat().st_mode & 0o777,0o700)
        self.assertEqual(packet_dir.stat().st_mode & 0o777,0o700)
        self.assertEqual(html.stat().st_mode & 0o777,0o600); self.assertEqual(manifest.stat().st_mode & 0o777,0o600)
        self.assertEqual((self.root/'review.sqlite3').read_bytes(),before)
        self.assertEqual(json.loads(manifest.read_text()),result)

    def test_exact_retry_is_idempotent_and_corrupt_existing_packet_is_not_overwritten(self):
        first=prepare_review_packet(self.store,self.output,PARK,self.source_revision)
        html=self.output/first['packet_id']/'index.html'; stamp=html.stat().st_mtime_ns
        second=prepare_review_packet(self.store,self.output,PARK,self.source_revision)
        self.assertEqual(first,second); self.assertEqual(html.stat().st_mtime_ns,stamp)
        html.write_text('corrupt'); html.chmod(0o600)
        with self.assertRaises(ReviewStoreError): prepare_review_packet(self.store,self.output,PARK,self.source_revision)
        self.assertEqual(html.read_text(),'corrupt')

    def test_protected_symlink_and_insecure_destinations_are_refused(self):
        repo=Path(__file__).resolve().parents[1]
        with self.assertRaises(ReviewStoreError):
            prepare_review_packet(self.store,repo/'data'/'review-packets',PARK,self.source_revision)
        real=Path(self.tmp.name)/'real'; real.mkdir(mode=0o700)
        alias=Path(self.tmp.name)/'alias'; alias.symlink_to(real,target_is_directory=True)
        with self.assertRaises(ReviewStoreError):
            prepare_review_packet(self.store,alias/'packets',PARK,self.source_revision)
        insecure=Path(self.tmp.name)/'insecure'; insecure.mkdir(mode=0o755)
        with self.assertRaises(ReviewStoreError):
            prepare_review_packet(self.store,insecure/'packets',PARK,self.source_revision)

    def test_packet_build_and_cli_do_not_call_network_or_echo_private_paths(self):
        before=(self.root/'review.sqlite3').read_bytes()
        with patch('socket.create_connection',side_effect=AssertionError('network forbidden')):
            packet=build_review_packet(self.store,PARK,self.source_revision)
        self.assertFalse(packet['manifest']['network_performed'])
        result=subprocess.run([
            sys.executable,'-m','tracker.entry_review_cli','packet','--store',str(self.root),
            '--output-dir',str(self.output),'--park',PARK,'--source-event-revision',self.source_revision
        ],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(report['packet_id'],packet['manifest']['packet_id'])
        self.assertFalse(report['approval_performed']); self.assertFalse(report['publication_performed'])
        self.assertNotIn(str(self.root),result.stdout); self.assertNotIn(str(self.output),result.stdout)
        self.assertNotIn(QUOTE,result.stdout); self.assertNotIn(QUOTE,result.stderr)
        self.assertEqual((self.root/'review.sqlite3').read_bytes(),before)

if __name__=='__main__': unittest.main()
