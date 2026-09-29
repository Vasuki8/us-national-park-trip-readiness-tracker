"""Explicit guidance reconciliation contracts using synthetic private evidence only."""
import copy, hashlib, json, os, subprocess, sys, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path
from tracker.entry_review_store import EntryReviewStore, ReviewStoreError

T0='2026-09-28T10:00:00Z'; T1='2026-09-28T12:00:00Z'; T2='2026-09-28T13:00:00Z'; T3='2026-09-28T14:00:00Z'
URL='https://www.nps.gov/yose/planyourvisit/reservations.htm'
QUOTE='Synthetic entry guidance for reconciliation testing.'
def sha(text): return hashlib.sha256(text.encode()).hexdigest()
def rule(reviewed=T0, excerpt=QUOTE):
    return {'id':'synthetic-yose','park_code':'yose','summary':'Synthetic reviewed rule.','exception_note':'Synthetic exception note.',
      'areas':['*'],'effective_from':'2026-01-01','effective_to':'2026-12-31','requirement':'no_timed_entry',
      'start_time':None,'end_time':None,'reviewed_at':reviewed,'review_status':'reviewed',
      'evidence':{'url':URL,'excerpt':excerpt,'content_hash':sha(excerpt),'hash_scope':'excerpt','reviewed_at':reviewed,
        'source_updated_at':None,'method':'manual_official_page_review'},
      'rights_basis':'Synthetic test rights basis.','rights_reviewed_at':T0}
def capture(checked, html=None):
    return {'source_url':URL,'final_url':URL,'checked_at':checked,'status':'success','content_type':'text/html',
      'html': html or f'<html><body><h1>Entrance Reservations</h1><p>{QUOTE}</p><p>Synthetic surrounding context.</p></body></html>'}
def batch(record, checked):
    return {'records':[record],'captures':[capture(checked)],'baselines':[],'seed_register':{'schema_version':1,'proposals':[]}}
def reconcile_request(source_revision, proposal_ids, record, reviewed=T2):
    return {'source_event_revision':source_revision,'proposal_ids':proposal_ids,'reviewer':'test-reviewer',
      'rationale':'Reviewed the complete synthetic retained source context.','reviewed_at':reviewed,'records':[record]}

class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'review'; self.store=EntryReviewStore(self.root)
        self.first=self.store.record(batch(rule(),T1),expected_revision=None,now=datetime(2026,9,28,12,30,tzinfo=timezone.utc))
        self.proposal=self.store.read()['register']['proposals'][0]['id']

    def approved(self, excerpt=QUOTE):
        value=rule(T2,excerpt); value['evidence']['content_hash']=sha(excerpt); return value

    def test_reconcile_persists_reviewed_context_and_clears_only_explicit_hold(self):
        result=self.store.reconcile(reconcile_request(self.first['revision'],[self.proposal],self.approved()),
          expected_revision=self.first['revision'],now=datetime(2026,9,28,13,30,tzinfo=timezone.utc))
        state=self.store.read()
        self.assertEqual(result['guidance_reconciliations'],1); self.assertTrue(result['approval_performed'])
        self.assertEqual(state['register']['proposals'],[]); self.assertEqual(state['records'][0]['reviewed_at'],T2)
        self.assertEqual(len(state['baselines']),1); self.assertEqual(state['baselines'][0]['checked_at'],T1)
        self.assertEqual(state['baselines'][0]['reviewed_at'],T2)
        self.assertEqual(state['events'][-1]['kind'],'reconciliation')
        self.assertEqual(state['events'][-1]['request']['source_event_revision'],self.first['revision'])

    def test_later_observation_uses_stored_baseline_and_cannot_replace_it(self):
        reconciled=self.store.reconcile(reconcile_request(self.first['revision'],[self.proposal],self.approved()),
          expected_revision=self.first['revision'],now=datetime(2026,9,28,13,30,tzinfo=timezone.utc))
        current=self.store.read()['records'][0]
        later=batch(current,T3)
        saved=self.store.record(later,expected_revision=reconciled['revision'],now=datetime(2026,9,28,15,tzinfo=timezone.utc))
        event=self.store.read()['events'][-1]
        self.assertEqual(event['extraction']['sources'][0]['reason'],'matching_reviewed_context')
        self.assertEqual(saved['pending_proposals'],0)
        forged=copy.deepcopy(later); forged['captures'][0]['checked_at']='2026-09-28T14:30:00Z'
        forged['baselines']=[{'schema_version':1}]
        with self.assertRaises(ReviewStoreError):
            self.store.record(forged,expected_revision=saved['revision'],now=datetime(2026,9,28,15,30,tzinfo=timezone.utc))

    def test_reconciliation_requires_latest_retained_source_context(self):
        second=self.store.record(batch(rule(),T2),expected_revision=self.first['revision'],
          now=datetime(2026,9,28,13,30,tzinfo=timezone.utc))
        proposals=[p['id'] for p in self.store.read()['register']['proposals']]
        with self.assertRaises(ReviewStoreError):
            self.store.reconcile(reconcile_request(self.first['revision'],proposals,rule(T3)),
              expected_revision=second['revision'],now=datetime(2026,9,28,14,30,tzinfo=timezone.utc))

    def test_new_excerpt_must_be_unique_in_retained_context(self):
        changed='Synthetic replacement that is not present in the retained page.'
        with self.assertRaises(ReviewStoreError):
            self.store.reconcile(reconcile_request(self.first['revision'],[self.proposal],self.approved(changed)),
              expected_revision=self.first['revision'],now=datetime(2026,9,28,13,30,tzinfo=timezone.utc))

    def test_exact_reconcile_retry_is_idempotent(self):
        value=reconcile_request(self.first['revision'],[self.proposal],self.approved())
        saved=self.store.reconcile(value,expected_revision=self.first['revision'],now=datetime(2026,9,28,13,30,tzinfo=timezone.utc))
        again=self.store.reconcile(value,expected_revision=self.first['revision'],now=datetime(2026,9,28,14,tzinfo=timezone.utc))
        self.assertTrue(again['replayed']); self.assertEqual(again['revision'],saved['revision'])
        self.assertEqual(len(self.store.read()['events']),2)

    def test_cli_reconcile_is_private_and_does_not_echo_rationale_or_context(self):
        input_path=Path(self.tmp.name)/'reconcile.json'
        value=reconcile_request(self.first['revision'],[self.proposal],self.approved())
        input_path.write_text(json.dumps(value)); input_path.chmod(0o600)
        result=subprocess.run([sys.executable,'-m','tracker.entry_review_cli','reconcile','--store',str(self.root),
          '--input',str(input_path),'--expected-revision',self.first['revision']],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        payload=json.loads(result.stdout); self.assertEqual(payload['guidance_reconciliations'],1)
        self.assertNotIn(value['rationale'],result.stdout); self.assertNotIn(QUOTE,result.stdout)
        self.assertFalse(payload['publication_performed'])

if __name__=='__main__': unittest.main()
