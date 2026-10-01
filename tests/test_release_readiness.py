"""Read-only pilot release-readiness reporting contracts."""
import copy
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import ExitStack, contextmanager, redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from unittest.mock import patch

from entry_source_fixtures import synthetic_guidance
from tracker.release_readiness import evaluate_readiness, main, _gate
from tracker.entry_review_io import ReviewStoreError
from tracker.entry_sources import PROFILES, digest
from tracker.entry_review_store import EntryReviewStore

ROOT=Path(__file__).resolve().parents[1]
ALL_URLS={
 'https://www.nps.gov/yose/planyourvisit/reservations.htm',
 'https://www.nps.gov/romo/planyourvisit/timed-entry-permit-system.htm',
 'https://www.nps.gov/yell/planyourvisit/permitsandreservations.htm',
 'https://www.nps.gov/zion/planyourvisit/permitsandreservations.htm',
 'https://www.nps.gov/grca/planyourvisit/grand-canyon-national-park-public-health-update.htm',
}

def public_records():
    return json.loads((ROOT/'data/rules.json').read_text()) + json.loads((ROOT/'data/entry-notes.json').read_text())


def private_state(*, approved=False, pending=False, revision='a'*64, records=None):
    # Synthetic report input; the CLI integration separately exercises replay.
    records = public_records() if records is None else copy.deepcopy(records)
    baselines=[]
    if approved:
        baselines=[
          {'schema_version':2,'source_url':url,'profile_id':'synthetic',
           'guidance_hashes':{r['id']:digest(r) for r in records if r['evidence']['url']==url},
           'checked_at':'2026-09-29T12:00:00Z','reviewed_at':'2026-09-29T13:00:00Z',
           'context':{},'context_hash':'b'*64}
          for url in sorted(ALL_URLS)
        ]
    proposals=[] if not pending else [{
      'id':'c'*64,'guidance_id':'synthetic','guidance_hash':'d'*64,
      'source_url':next(iter(ALL_URLS)),'checked_at':'2026-09-29T14:00:00Z',
      'reason':'check_failed','state':'pending','before_excerpt':'x','after_excerpt':None
    }]
    events=[{'kind':'observation','register':{'proposals':[
        {'id':str(number),'source_url':url} for number,url in enumerate(sorted(ALL_URLS))]}}]
    if approved:
        for number,baseline in enumerate(baselines):
            events.append({'kind':'reconciliation',
                'request':{'proposal_ids':[str(number)],'reviewed_at':baseline['reviewed_at']},
                'baselines':copy.deepcopy(baselines),
                'register':{'proposals':copy.deepcopy(events[-1]['register']['proposals'][1:])}})
    return {
      'revision':revision,
      'events':events,
      'records':records,
      'register':{'schema_version':1,'proposals':proposals},
      'baselines':baselines,
    }

def backup_manifest(revision='a'*64):
    return {
      'schema_version':1,'purpose':'private_entry_review_backup','backup_id':'e'*64,
      'ledger_revision':revision,'event_count':6,'guidance_records':6,'pending_proposals':0,
      'database_file':'review.sqlite3','database_bytes':100,'database_sha256':'f'*64,
      'network_performed':False,'approval_performed':False,'publication_performed':False,
    }

@contextmanager
def synthetic_core_ready():
    """Model externally verified core gates; never create real approval evidence."""
    with ExitStack() as stack:
        for function, identifier in [('_durable_review','durable_source_review'),
                ('_alerts','nps_alert_api'), ('_backup','storage_backup'),
                ('_rights','source_rights'), ('_hosting','hosting_rollback')]:
            stack.enter_context(patch(f'tracker.release_readiness.{function}',
                return_value=_gate(identifier,'pass','synthetic_test_only',{})))
        yield

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
        self.assertEqual(alerts['status'],'not_checked')
        self.assertEqual(alerts['reason'],
            'success_present_but_freshness_and_provider_compatibility_need_release_validation')
        self.assertTrue(alerts['blocking'])
        self.assertEqual(alerts['evidence']['never_checked'],0)
        self.assertEqual(alerts['evidence']['successful'],5)
        self.assertEqual(self.gate(report,'storage_backup')['status'],'not_checked')
        self.assertEqual(self.gate(report,'source_rights')['status'],'pass')
        self.assertEqual(self.gate(report,'hosting_rollback')['status'],'not_checked')
        self.assertEqual(self.gate(report,'indexing')['status'],'blocked')
        self.assertEqual(self.gate(report,'advertising')['status'],'blocked')
        self.assertEqual(report['summary']['pass'],1)
        self.assertEqual(report['summary']['blocked']+report['summary']['not_checked'],6)

    def test_pilot_requires_core_gates_but_not_disabled_future_features(self):
        report=evaluate_readiness(ROOT)
        self.assertEqual(report['schema_version'],2)
        self.assertEqual(report['release_target'],'pilot')
        self.assertEqual([gate['id'] for gate in report['gates'] if gate['required']], [
            'durable_source_review','nps_alert_api','storage_backup','source_rights','hosting_rollback'])
        self.assertEqual(report['required_summary'],{'pass':1,'blocked':0,'not_checked':4})
        self.assertFalse(self.gate(report,'indexing')['blocking'])
        self.assertFalse(self.gate(report,'advertising')['blocking'])
        self.assertFalse(report['release_ready'])

    def test_reviewed_ad_free_unindexed_pilot_can_pass_without_enabling_ads(self):
        with synthetic_core_ready():
            report=evaluate_readiness(ROOT)
        self.assertTrue(report['release_ready'])
        self.assertEqual(report['required_summary'],{'pass':5,'blocked':0,'not_checked':0})
        self.assertEqual(self.gate(report,'advertising')['status'],'blocked')
        self.assertFalse(report['advertising_changed'])
        self.assertFalse(report['indexing_changed'])

    def test_every_core_gate_still_blocks_pilot_when_failed_or_unchecked(self):
        for function, identifier in [('_durable_review','durable_source_review'),
                ('_alerts','nps_alert_api'), ('_backup','storage_backup'),
                ('_rights','source_rights'), ('_hosting','hosting_rollback')]:
            for status in ('blocked','not_checked'):
                with self.subTest(gate=identifier,status=status), synthetic_core_ready(), \
                        patch(f'tracker.release_readiness.{function}',
                            return_value=_gate(identifier,status,'synthetic_test_only',{})):
                    report=evaluate_readiness(ROOT)
                    self.assertFalse(report['release_ready'])
                    self.assertTrue(self.gate(report,identifier)['blocking'])
                    self.assertTrue(self.gate(report,identifier)['required'])

    def test_indexed_and_advertising_targets_require_their_later_gates(self):
        with synthetic_core_ready():
            indexed=evaluate_readiness(ROOT,release_target='indexed')
            advertising=evaluate_readiness(ROOT,release_target='advertising')
        self.assertFalse(indexed['release_ready']); self.assertFalse(advertising['release_ready'])
        self.assertTrue(self.gate(indexed,'indexing')['required'])
        self.assertFalse(self.gate(indexed,'advertising')['required'])
        self.assertTrue(all(gate['required'] for gate in advertising['gates']))

    def test_detected_ad_integration_still_blocks_a_pilot_target(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.copy_indexing_controls(root)
            (root/'public'/'synthetic-ad.js').write_text('window.adsbygoogle = [];')
            with synthetic_core_ready():
                for target in ('pilot','indexed'):
                    with self.subTest(target=target):
                        report=evaluate_readiness(root,release_target=target)
                        gate=self.gate(report,'advertising')
                        self.assertTrue(gate['required']); self.assertTrue(gate['blocking'])
                        self.assertEqual(gate['required_reason'],'ad_integration_present')
                        self.assertFalse(report['release_ready'])

    def copy_indexing_controls(self, root):
        for file in ('src/layouts/Layout.astro','public/robots.txt','public/_headers'):
            destination=root/file
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes((ROOT/file).read_bytes())

    def test_partial_or_complete_indexing_control_removal_blocks_pilot(self):
        controls=('src/layouts/Layout.astro','public/robots.txt','public/_headers')
        for removed in [(file,) for file in controls]+[controls]:
            with self.subTest(removed=removed), tempfile.TemporaryDirectory() as folder:
                root=Path(folder); self.copy_indexing_controls(root)
                for file in removed:
                    (root/file).write_text('synthetic test: indexing control removed')
                with synthetic_core_ready():
                    report=evaluate_readiness(root)
                gate=self.gate(report,'indexing')
                self.assertTrue(gate['required']); self.assertTrue(gate['blocking'])
                self.assertEqual(gate['required_reason'],'pilot_indexing_controls_changed')
                self.assertFalse(report['release_ready'])

    def test_comment_conditional_agent_and_path_changes_cannot_fake_intact_controls(self):
        meta='<meta name="robots" content="noindex, nofollow" />'
        mutations=[
            ('src/layouts/Layout.astro',lambda text:text.replace(meta,f'<!-- {meta} -->')),
            ('src/layouts/Layout.astro',lambda text:text.replace(meta,f'{{/* {meta} */}}')),
            ('src/layouts/Layout.astro',lambda text:text.replace(meta,f'{{false && {meta}}}')),
            ('src/layouts/Layout.astro',lambda text:text.replace(meta,meta.replace('<meta','<Meta'))),
            ('src/layouts/Layout.astro',lambda text:text.replace('<head>','<Head>').replace('</head>','</Head>')),
            ('src/layouts/Layout.astro',lambda text:text.replace(meta,f'<script>const fake = \'{meta}\';</script>')),
            ('src/layouts/Layout.astro',lambda text:text.replace(meta,'').replace('<body>',f'<body>{meta}')),
            ('public/robots.txt',lambda text:text.replace('User-agent: *','User-agent: Googlebot')),
            ('public/robots.txt',lambda text:text+'Allow: /public/\n'),
            ('public/robots.txt',lambda text:text+'\nUser-agent: Googlebot\nDisallow:\n'),
            ('public/robots.txt',lambda text:'\n'.join('# '+line for line in text.splitlines())),
            ('public/_headers',lambda text:text.replace('/*','/private/*')),
            ('public/_headers',lambda text:text.replace('  X-Robots-Tag:','  # X-Robots-Tag:')),
            ('public/_headers',lambda text:text.replace('X-Robots-Tag:','X-Example:')),
            ('public/_headers',lambda text:text.replace('noindex, nofollow','googlebot: noindex')),
            ('public/_headers',lambda text:text.replace('noindex, nofollow','googlebot: noindex, nofollow, noindex')),
            ('public/_headers',lambda text:text+'\n/public/*\n  ! X-Robots-Tag\n'),
        ]
        for number,(file,mutate) in enumerate(mutations):
            with self.subTest(case=number,file=file), tempfile.TemporaryDirectory() as folder:
                root=Path(folder); self.copy_indexing_controls(root)
                (root/file).write_text(mutate((root/file).read_text()))
                with synthetic_core_ready():
                    report=evaluate_readiness(root)
                self.assertFalse(report['release_ready'])
                self.assertTrue(self.gate(report,'indexing')['required'])
                self.assertTrue(self.gate(report,'indexing')['blocking'])

    def test_recognized_active_controls_allow_formatting_without_requiring_indexing(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); self.copy_indexing_controls(root)
            layout=root/'src/layouts/Layout.astro'
            layout.write_text(layout.read_text().replace(
                '<meta name="robots" content="noindex, nofollow" />',
                '<meta content="NOINDEX, NOFOLLOW" name="ROBOTS" />'))
            (root/'public/robots.txt').write_text('# Pilot\nUSER-AGENT: *\n\nDISALLOW: / # all paths\n')
            (root/'public/_headers').write_text('# Pilot\n/*\n\tX-Robots-Tag: NOINDEX, NOFOLLOW\n')
            with synthetic_core_ready():
                report=evaluate_readiness(root)
            self.assertTrue(report['release_ready'])
            self.assertFalse(self.gate(report,'indexing')['required'])

    def test_invalid_release_target_is_refused_without_echoing_input(self):
        with self.assertRaisesRegex(ReviewStoreError,'^invalid_release_readiness_arguments$'):
            evaluate_readiness(ROOT,release_target='/private/sentinel/path')

    def test_cli_target_selection_and_later_gate_labels_are_explicit(self):
        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            code=main(['--target','pilot','--format','text'])
        self.assertEqual(code,1); self.assertEqual(err.getvalue(),'')
        self.assertIn('Required for pilot: 1 pass, 0 blocked, 4 not checked',out.getvalue())
        self.assertIn('later target; not required',out.getvalue())
        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            code=main(['--target','advertising','--format','json'])
        self.assertEqual(code,1); self.assertEqual(err.getvalue(),'')
        report=json.loads(out.getvalue())
        self.assertEqual(report['release_target'],'advertising')
        self.assertTrue(all(gate['required'] for gate in report['gates']))

        out,err=io.StringIO(),io.StringIO()
        with synthetic_core_ready(), redirect_stdout(out), redirect_stderr(err):
            code=main(['--target','pilot','--format','json'])
        self.assertEqual(code,0); self.assertEqual(err.getvalue(),'')
        self.assertTrue(json.loads(out.getvalue())['release_ready'])

    def test_cli_invalid_target_is_sanitized_and_produces_no_report(self):
        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            code=main(['--target','/private/sentinel/path','--format','json'])
        self.assertEqual(code,2); self.assertEqual(out.getvalue(),'')
        self.assertEqual(err.getvalue(),'invalid_release_readiness_arguments\n')

    def test_never_checked_alerts_can_never_be_described_as_clear_or_ready(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.copy_indexing_controls(root)
            (root/'data/alerts').mkdir(parents=True)
            for filename in ('rules.json','entry-notes.json'):
                (root/'data'/filename).write_text('[]')
            for code in PROFILES:
                (root/'data/alerts'/f'{code}.json').write_text(json.dumps({
                    'park_code':code,'collection_status':'never_checked',
                    'last_checked_at':None,'last_successful_fetch_at':None,'records':[]}))
            report=evaluate_readiness(root)
        text=json.dumps(report).lower()
        self.assertNotIn('all clear',text)
        self.assertNotIn('no alerts',text)
        alerts=self.gate(report,'nps_alert_api')
        self.assertFalse(report['release_ready'])
        self.assertEqual(alerts['status'],'blocked')
        self.assertEqual(alerts['evidence']['never_checked'],5)
        self.assertEqual(alerts['evidence']['successful'],0)
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

    def test_changed_private_guidance_cannot_approve_the_old_public_inventory(self):
        for field, value in [('summary','Private revised summary.'),
                             ('reviewed_at','2026-09-29T13:00:00Z'),
                             ('effective_to','2026-10-01'),
                             ('exception_note','Private revised exception.'),
                             ('rights_basis','Private revised rights review.')]:
            records=public_records(); records[0][field]=value
            state=private_state(approved=True,records=records)
            with self.subTest(field=field):
                gate=self.gate(evaluate_readiness(ROOT,private_state=state),'durable_source_review')
                self.assertEqual(gate['status'],'blocked')
                self.assertEqual(gate['reason'],'public_guidance_differs_from_reviewed_ledger')
                self.assertFalse(gate['evidence']['public_guidance_matches_ledger'])

    def test_reviewed_context_hashes_must_cover_the_exact_private_guidance(self):
        mutations=[
            lambda hashes: hashes.clear(),
            lambda hashes: hashes.update({next(iter(hashes)):'0'*64}),
            lambda hashes: hashes.update({'synthetic-extra':'0'*64}),
        ]
        for mutate in mutations:
            state=private_state(approved=True)
            # Rocky Mountain has two guidance records on one reviewed source.
            baseline=next(b for b in state['baselines'] if '/romo/' in b['source_url'])
            mutate(baseline['guidance_hashes'])
            with self.subTest(hashes=baseline['guidance_hashes']):
                gate=self.gate(evaluate_readiness(ROOT,private_state=state),'durable_source_review')
                self.assertEqual(gate['status'],'blocked')
                self.assertEqual(gate['reason'],'reviewed_context_guidance_mismatch')
                self.assertFalse(gate['evidence']['reviewed_guidance_matches_baselines'])

    def test_empty_missing_duplicate_or_extra_private_inventory_never_passes(self):
        rows=public_records()
        variants=[[],rows[:-1],rows+[copy.deepcopy(rows[0])],
                  rows+[{**copy.deepcopy(rows[0]),'id':'synthetic-extra'}]]
        for records in variants:
            with self.subTest(count=len(records)):
                gate=self.gate(evaluate_readiness(ROOT,private_state=private_state(approved=True,records=records)),
                               'durable_source_review')
                self.assertEqual(gate['status'],'blocked')
        state=private_state(approved=True); del state['records']
        gate=self.gate(evaluate_readiness(ROOT,private_state=state),'durable_source_review')
        self.assertEqual(gate['status'],'blocked')

    def test_duplicate_approved_source_baseline_cannot_hide_ambiguous_binding(self):
        state=private_state(approved=True)
        state['baselines'].append(copy.deepcopy(state['baselines'][0]))
        gate=self.gate(evaluate_readiness(ROOT,private_state=state),'durable_source_review')
        self.assertEqual(gate['status'],'blocked')

    def test_current_baseline_must_match_its_reconciliation_in_full(self):
        for field,value in [('checked_at','2026-09-29T11:00:00Z'),
                             ('reviewed_at','2026-09-29T13:01:00Z'),
                             ('context_hash','0'*64),('context',{'text':'Synthetic different context.'})]:
            with self.subTest(field=field):
                state=private_state(approved=True)
                state['baselines'][0][field]=value
                gate=self.gate(evaluate_readiness(ROOT,private_state=state),'durable_source_review')
                self.assertEqual(gate['status'],'blocked')
                self.assertEqual(gate['reason'],'context_approval_provenance_incomplete')
                self.assertEqual(gate['evidence']['reconciled_v2_sources'],4)

    def test_inventory_and_object_key_order_do_not_change_record_identity(self):
        rows=[dict(reversed(list(r.items()))) for r in reversed(public_records())]
        gate=self.gate(evaluate_readiness(ROOT,private_state=private_state(approved=True,records=rows)),
                       'durable_source_review')
        self.assertEqual(gate['status'],'pass')
        self.assertTrue(gate['evidence']['public_guidance_matches_ledger'])
        self.assertTrue(gate['evidence']['reviewed_guidance_matches_baselines'])
        self.assertEqual(gate['evidence']['public_guidance_records'],6)
        self.assertEqual(gate['evidence']['private_guidance_records'],6)

    def test_guidance_match_report_never_echoes_private_records_or_hashes(self):
        rows=public_records(); secret='/private/sentinel/changed-guidance'
        rows[0]['summary']=secret
        state=private_state(approved=True,records=rows)
        before=[(ROOT/path).read_bytes() for path in ('data/rules.json','data/entry-notes.json')]
        report=evaluate_readiness(ROOT,private_state=state)
        serialized=json.dumps(report)
        self.assertNotIn(secret,serialized)
        self.assertNotIn(digest(rows[0]),serialized)
        self.assertFalse(report['writes_performed'])
        self.assertEqual(before,[(ROOT/path).read_bytes() for path in ('data/rules.json','data/entry-notes.json')])
        self.assertEqual(self.gate(report,'durable_source_review')['status'],'blocked')

    def replayed_synthetic_fixture(self, directory):
        directory=Path(directory); root=directory/'public-fixture'
        self.copy_indexing_controls(root)
        for name in ['source-rights.json']+[f'alerts/{code}.json' for code in PROFILES]:
            target=root/'data'/name; target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((ROOT/'data'/name).read_bytes())
        guidance=synthetic_guidance()
        records=guidance['rules']+guidance['notes']
        for row in records:
            row['summary']='Synthetic test guidance for '+row['id']+'.'
            row['evidence']['excerpt']='Synthetic source excerpt for '+row['id']+'.'
            row['evidence']['content_hash']=hashlib.sha256(row['evidence']['excerpt'].encode()).hexdigest()
        captures=[]
        for code,profile in PROFILES.items():
            text=''.join('<p>'+escape(r['evidence']['excerpt'])+'</p>' for r in records if r['park_code']==code)
            captures.append({'source_url':profile['url'],'final_url':profile['url'],
                'checked_at':'2026-09-29T12:00:00Z','status':'success','content_type':'text/html',
                'html':'<html><body><h1>'+escape(profile['heading'])+'</h1>'+text+'</body></html>'})
        store=EntryReviewStore(directory/'private-ledger')
        first=store.record({'records':records,'captures':captures,'baselines':[],
                            'seed_register':{'schema_version':1,'proposals':[]}},
                           expected_revision=None,now=datetime(2026,9,29,12,1,tzinfo=timezone.utc))
        for number,profile in enumerate(PROFILES.values()):
            state=store.read(); rows=copy.deepcopy(state['records'])
            for row in rows:
                if row['evidence']['url']==profile['url']:
                    row['reviewed_at']=row['evidence']['reviewed_at']='2026-09-29T13:00:00Z'
            proposals=[p['id'] for p in state['register']['proposals'] if p['source_url']==profile['url']]
            store.reconcile({'source_event_revision':first['revision'],'proposal_ids':proposals,
                             'reviewer':'synthetic-test-reviewer','rationale':'Synthetic fixture approval only.',
                             'reviewed_at':'2026-09-29T13:00:00Z','records':rows},
                            expected_revision=state['revision'],
                            now=datetime(2026,9,29,13,30,number,tzinfo=timezone.utc))
        state=store.read()
        self.assertEqual(len(state['baselines']),5)
        self.assertEqual(state['register']['proposals'],[])
        rules=[r for r in state['records'] if 'requirement' in r]
        notes=[r for r in state['records'] if 'subject_type' in r]
        (root/'data/rules.json').write_text(json.dumps(rules))
        (root/'data/entry-notes.json').write_text(json.dumps(notes))
        return root,store,captures

    def test_cli_compares_replayed_synthetic_ledger_with_public_inventory_without_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            root,store,captures=self.replayed_synthetic_fixture(folder)
            state=store.read()
            for capture in captures:
                capture['checked_at']='2026-09-29T14:00:00Z'
            store.record({'records':state['records'],'captures':captures,'baselines':[],
                'seed_register':{'schema_version':1,'proposals':[]}},
                expected_revision=state['revision'],now=datetime(2026,9,29,14,1,tzinfo=timezone.utc))
            self.assertEqual(store.read()['register']['proposals'],[])
            rules=json.loads((root/"data/rules.json").read_text())
            for mismatched in (False,True):
                if mismatched:
                    rules[0]['summary']='Synthetic unreviewed public edit.'
                    (root/'data/rules.json').write_text(json.dumps(rules))
                paths=[root/'data/rules.json',root/'data/entry-notes.json',store.root/'review.sqlite3']
                before=[p.read_bytes() for p in paths]
                out,err=io.StringIO(),io.StringIO()
                with patch('tracker.release_readiness.REPO_ROOT',root), redirect_stdout(out),redirect_stderr(err):
                    code=main(['--format','json','--store',str(store.root)])
                self.assertEqual(code,1); self.assertEqual(err.getvalue(),'')
                report=json.loads(out.getvalue()); gate=self.gate(report,'durable_source_review')
                self.assertEqual(gate['status'],'blocked' if mismatched else 'pass')
                self.assertEqual(gate['evidence']['public_guidance_matches_ledger'],not mismatched)
                if not mismatched:
                    self.assertEqual(gate['evidence']['reconciled_v2_sources'],5)
                self.assertNotIn(str(store.root),out.getvalue())
                self.assertEqual(before,[p.read_bytes() for p in paths])
                self.assertFalse(report['release_ready'])

    def test_cli_requires_each_source_baseline_to_originate_in_reconciliation(self):
        with tempfile.TemporaryDirectory() as folder:
            root,original,captures=self.replayed_synthetic_fixture(folder)
            approved=original.read()
            yose_url=PROFILES['yose']['url']
            for capture in captures:
                capture['checked_at']='2026-09-29T14:00:00Z'
            seeded=EntryReviewStore(Path(folder)/'seeded-ledger')
            first=seeded.record({'records':approved['records'],'captures':captures,
                'baselines':[b for b in approved['baselines'] if b['source_url']!=yose_url],
                'seed_register':{'schema_version':1,'proposals':[]}},
                expected_revision=None,now=datetime(2026,9,29,14,1,tzinfo=timezone.utc))
            state=seeded.read(); rows=copy.deepcopy(state['records'])
            self.assertEqual({p['source_url'] for p in state['register']['proposals']},{yose_url})
            for row in rows:
                if row['evidence']['url']==yose_url:
                    row['reviewed_at']=row['evidence']['reviewed_at']='2026-09-29T15:00:00Z'
            seeded.reconcile({'source_event_revision':first['revision'],
                'proposal_ids':[p['id'] for p in state['register']['proposals']],
                'reviewer':'synthetic-test-reviewer','rationale':'Synthetic fixture approval only.',
                'reviewed_at':'2026-09-29T15:00:00Z','records':rows},
                expected_revision=state['revision'],now=datetime(2026,9,29,15,30,tzinfo=timezone.utc))
            state=seeded.read()
            self.assertEqual(len(state['baselines']),5)
            self.assertEqual(state['register']['proposals'],[])
            for filename,key in [('rules.json','requirement'),('entry-notes.json','subject_type')]:
                (root/'data'/filename).write_text(json.dumps([r for r in state['records'] if key in r]))
            out,err=io.StringIO(),io.StringIO()
            with patch('tracker.release_readiness.REPO_ROOT',root), redirect_stdout(out),redirect_stderr(err):
                code=main(['--format','json','--store',str(seeded.root)])
            self.assertEqual(code,1); self.assertEqual(err.getvalue(),'')
            gate=self.gate(json.loads(out.getvalue()),'durable_source_review')
            self.assertEqual(gate['status'],'blocked')
            self.assertEqual(gate['reason'],'context_approval_provenance_incomplete')
            self.assertEqual(gate['evidence']['approved_v2_sources'],5)
            self.assertEqual(gate['evidence']['reconciled_v2_sources'],1)
            self.assertTrue(gate['evidence']['public_guidance_matches_ledger'])

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
                for target in ('pilot','indexed','advertising'):
                    report=evaluate_readiness(ROOT,release_target=target)
                    self.assertFalse(report['network_performed']); self.assertFalse(report['writes_performed'])
            self.assertEqual(marker.read_text(),'unchanged'); self.assertEqual(marker.stat().st_mtime_ns,before)
            self.assertFalse(report['network_performed']); self.assertFalse(report['writes_performed'])

    def test_cli_has_human_and_json_modes_without_private_path_leakage(self):
        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            code=main(['--format','text'])
        self.assertEqual(code,1); self.assertEqual(err.getvalue(),'')
        self.assertIn('Pilot release readiness: BLOCKED',out.getvalue())
        self.assertIn('[NOT CHECKED] NPS alert API validation',out.getvalue())

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
