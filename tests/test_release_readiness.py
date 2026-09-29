"""Read-only pilot release-readiness reporting contracts."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from tracker.release_readiness import evaluate_readiness, main

ROOT=Path(__file__).resolve().parents[1]
ALL_URLS={
 'https://www.nps.gov/yose/planyourvisit/reservations.htm',
 'https://www.nps.gov/romo/planyourvisit/timed-entry-permit-system.htm',
 'https://www.nps.gov/yell/planyourvisit/permitsandreservations.htm',
 'https://www.nps.gov/zion/planyourvisit/permitsandreservations.htm',
 'https://www.nps.gov/grca/planyourvisit/grand-canyon-national-park-public-health-update.htm',
}

def private_state(*, approved=False, pending=False, revision='a'*64):
    baselines=[]
    if approved:
        baselines=[
          {'schema_version':2,'source_url':url,'profile_id':'synthetic','guidance_hashes':{},
           'checked_at':'2026-09-29T12:00:00Z','reviewed_at':'2026-09-29T13:00:00Z',
           'context':{},'context_hash':'b'*64}
          for url in sorted(ALL_URLS)
        ]
    proposals=[] if not pending else [{
      'id':'c'*64,'guidance_id':'synthetic','guidance_hash':'d'*64,
      'source_url':next(iter(ALL_URLS)),'checked_at':'2026-09-29T14:00:00Z',
      'reason':'check_failed','state':'pending','before_excerpt':'x','after_excerpt':None
    }]
    return {
      'revision':revision,
      'events':[{'kind':'observation'}],
      'records':[{'id':'synthetic'}],
      'register':{'schema_version':1,'proposals':proposals},
      'baselines':baselines,
    }

def backup_manifest(revision='a'*64):
    return {
      'schema_version':1,'purpose':'private_entry_review_backup','backup_id':'e'*64,
      'ledger_revision':revision,'event_count':1,'guidance_records':1,'pending_proposals':0,
      'database_file':'review.sqlite3','database_bytes':100,'database_sha256':'f'*64,
      'network_performed':False,'approval_performed':False,'publication_performed':False,
    }

class ReleaseReadinessTests(unittest.TestCase):
    def gate(self, report, gate_id):
        return next(g for g in report['gates'] if g['id']==gate_id)

    def test_current_repository_is_explicitly_not_release_ready(self):
        report=evaluate_readiness(ROOT)
        self.assertFalse(report['release_ready'])
        self.assertFalse(report['network_performed']); self.assertFalse(report['writes_performed'])
        self.assertEqual([g['id'] for g in report['gates']],[
          'durable_source_review','nps_alert_api','storage_backup','source_rights',
          'hosting_rollback','indexing','advertising'])
        self.assertEqual(self.gate(report,'durable_source_review')['status'],'not_checked')
        alerts=self.gate(report,'nps_alert_api')
        self.assertEqual(alerts['status'],'blocked')
        self.assertEqual(alerts['evidence']['never_checked'],5)
        self.assertEqual(alerts['evidence']['successful'],0)
        self.assertEqual(self.gate(report,'storage_backup')['status'],'not_checked')
        self.assertEqual(self.gate(report,'source_rights')['status'],'pass')
        self.assertEqual(self.gate(report,'hosting_rollback')['status'],'not_checked')
        self.assertEqual(self.gate(report,'indexing')['status'],'blocked')
        self.assertEqual(self.gate(report,'advertising')['status'],'blocked')
        self.assertEqual(report['summary']['pass'],1)
        self.assertEqual(report['summary']['blocked']+report['summary']['not_checked'],6)

    def test_never_checked_alerts_can_never_be_described_as_clear_or_ready(self):
        report=evaluate_readiness(ROOT)
        text=json.dumps(report).lower()
        self.assertNotIn('all clear',text)
        self.assertNotIn('no alerts',text)
        alerts=self.gate(report,'nps_alert_api')
        self.assertTrue(alerts['blocking'])
        self.assertIn('never_checked',alerts['reason'])

    def test_private_review_pass_requires_all_five_v2_baselines_and_no_holds(self):
        report=evaluate_readiness(ROOT,private_state=private_state(approved=True))
        gate=self.gate(report,'durable_source_review')
        self.assertEqual(gate['status'],'pass')
        self.assertEqual(gate['evidence']['approved_v2_sources'],5)
        for state in [
          private_state(approved=False),
          private_state(approved=True,pending=True),
          {**private_state(approved=True),'baselines':private_state(approved=True)['baselines'][:-1]},
          {**private_state(approved=True),'baselines':[
             {**b,'schema_version':1} for b in private_state(approved=True)['baselines']]},
        ]:
            with self.subTest(state=state):
                self.assertEqual(self.gate(evaluate_readiness(ROOT,private_state=state),'durable_source_review')['status'],'blocked')

    def test_backup_pass_requires_verified_manifest_for_exact_current_head(self):
        state=private_state(approved=True)
        missing=evaluate_readiness(ROOT,private_state=state)
        self.assertEqual(self.gate(missing,'storage_backup')['status'],'blocked')
        good=evaluate_readiness(ROOT,private_state=state,backup_manifest=backup_manifest())
        self.assertEqual(self.gate(good,'storage_backup')['status'],'pass')
        stale=evaluate_readiness(ROOT,private_state=state,backup_manifest=backup_manifest('9'*64))
        self.assertEqual(self.gate(stale,'storage_backup')['status'],'blocked')

    def test_exact_source_rights_manifest_can_pass_only_the_public_text_scope(self):
        gate=self.gate(evaluate_readiness(ROOT),'source_rights')
        self.assertEqual(gate['status'],'pass')
        self.assertEqual(gate['evidence']['guidance_records_with_rights_metadata'],6)
        self.assertEqual(gate['evidence']['guidance_records_total'],6)
        self.assertEqual(gate['evidence']['covered_guidance_records'],6)
        self.assertTrue(gate['evidence']['commercial_notice_present'])
        self.assertFalse(gate['evidence']['nps_marks_or_media_detected'])

    def test_indexing_gate_requires_all_three_release_controls_to_be_removed(self):
        gate=self.gate(evaluate_readiness(ROOT),'indexing')
        self.assertEqual(gate['status'],'blocked')
        self.assertTrue(gate['evidence']['meta_noindex'])
        self.assertTrue(gate['evidence']['robots_disallow_all'])
        self.assertTrue(gate['evidence']['header_noindex'])

    def test_report_does_no_network_or_filesystem_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            marker=Path(folder)/'marker'; marker.write_text('unchanged')
            before=marker.stat().st_mtime_ns
            with patch('socket.create_connection',side_effect=AssertionError('network forbidden')), \
                 patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden')):
                report=evaluate_readiness(ROOT)
            self.assertEqual(marker.read_text(),'unchanged'); self.assertEqual(marker.stat().st_mtime_ns,before)
            self.assertFalse(report['network_performed']); self.assertFalse(report['writes_performed'])

    def test_cli_has_human_and_json_modes_without_private_path_leakage(self):
        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            code=main(['--format','text'])
        self.assertEqual(code,1); self.assertEqual(err.getvalue(),'')
        self.assertIn('Pilot release readiness: BLOCKED',out.getvalue())
        self.assertIn('[BLOCKED] NPS alert API validation',out.getvalue())

        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            code=main(['--format','json'])
        self.assertEqual(code,1); self.assertEqual(err.getvalue(),'')
        payload=json.loads(out.getvalue()); self.assertFalse(payload['release_ready'])

    def test_cli_refuses_backup_without_store_and_sanitizes_bad_paths(self):
        out,err=io.StringIO(),io.StringIO()
        secret='/private/sentinel/path'
        with redirect_stdout(out),redirect_stderr(err):
            code=main(['--format','json','--backup',secret])
        self.assertEqual(code,2); self.assertEqual(out.getvalue(),'')
        self.assertNotIn(secret,err.getvalue())
        self.assertEqual(err.getvalue(),'invalid_release_readiness_arguments\n')

if __name__=='__main__': unittest.main()
