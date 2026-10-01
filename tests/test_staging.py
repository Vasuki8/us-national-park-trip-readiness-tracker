import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from staging_fixtures import T0, T1, T2, T3, feed, raw, snapshot
from tracker.history_model import HistoryError, canonical, digest
from tracker.staging import StagingCollector

class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'stage'; self.stage = StagingCollector(self.root)

    def run_check(self, at=T0, records=None, code='yose'):
        return self.stage.collect(code, at, lambda start: feed(records if records is not None else [raw(code=code)]))

    def test_empty_status_and_recovery_do_not_create_state(self):
        result = self.stage.status('yose')
        self.assertEqual(result['collection_status'], 'never_checked')
        self.assertEqual(result['stage_state'], 'idle'); self.assertFalse(self.root.exists())
        result = self.stage.recover('yose')
        self.assertEqual(result['operation'], 'nothing_to_recover'); self.assertFalse(self.root.exists())

    def test_success_archives_real_collector_output_without_website_writes(self):
        result = self.run_check()
        self.assertEqual(result['operation'], 'archived')
        self.assertFalse(result['publication_performed']); self.assertFalse(result['site_data_written'])
        self.assertEqual(result['comparison'], 'baseline')
        self.assertEqual(self.stage.archive.read('yose')[0]['snapshot'], snapshot())
        self.assertFalse((self.root/'pending/yose.json').exists())
        self.assertNotIn('Synthetic', json.dumps(result)); self.assertNotIn('test.htm', json.dumps(result))

    def test_successful_empty_feed_is_baseline_not_all_clear(self):
        result = self.run_check(records=[])
        self.assertEqual(result['collection_status'], 'success')
        self.assertEqual(result['comparison'], 'baseline'); self.assertEqual(result['change_count'], 0)
        self.assertNotIn('all_clear', result)

    def test_failures_and_quarantine_preserve_original_success_and_records(self):
        self.run_check(); before = self.stage.archive.read('yose')[-1]['snapshot']
        def fail(start): raise TimeoutError('synthetic-private-key')
        failed = self.stage.collect('yose', T1, fail)
        self.assertEqual(failed['collection_status'], 'failed'); self.assertEqual(failed['comparison'], 'not_compared')
        result = self.run_check(T2, records=[])
        self.assertEqual(result['collection_status'], 'quarantined'); self.assertEqual(result['change_count'], 0)
        last = self.stage.archive.read('yose')[-1]['snapshot']
        self.assertEqual(last['records'], before['records']); self.assertEqual(last['last_successful_fetch_at'], T0)
        self.assertEqual(last['last_checked_at'], T2)
        for file in self.root.rglob('*.json'): self.assertNotIn('synthetic-private-key', file.read_text())

    def test_recovery_after_initial_failure_still_establishes_baseline(self):
        def fail(start): raise TimeoutError()
        self.stage.collect('yose', T0, fail)
        self.assertEqual(self.run_check(T1)['comparison'], 'baseline')

    def test_add_edit_and_disappearance_use_archive_baseline(self):
        self.run_check(records=[raw('a'), raw('b')])
        result = self.run_check(T1, records=[raw('a', title='Changed synthetic notice'), raw('c')])
        entry = self.stage.archive.read('yose')[-1]
        self.assertEqual(result['change_count'], 3)
        self.assertEqual([e['kind'] for e in entry['changes']], ['edited', 'removed', 'added'])
        self.assertEqual(entry['snapshot']['records'][0]['observed_first_at'], T0)

    def test_archive_stricter_validation_quarantines_without_retaining_bad_text(self):
        self.run_check()
        result = self.run_check(T1, records=[raw(url='https://www.nps.gov/yose/test.htm#token=do-not-retain')])
        self.assertEqual(result['collection_status'], 'quarantined')
        self.assertEqual(result['last_successful_fetch_at'], T0)
        for file in self.root.rglob('*.json'): self.assertNotIn('do-not-retain', file.read_text())

    def test_all_five_parks_keep_separate_histories(self):
        for code in ('yose', 'romo', 'yell', 'zion', 'grca'):
            self.run_check(code=code)
            self.assertEqual(self.stage.archive.read(code)[0]['snapshot']['park_code'], code)
        self.assertEqual(len(list((self.root/'archive/parks').iterdir())), 5)

    def test_archive_failure_leaves_receipt_and_blocks_another_fetch(self):
        with patch.object(self.stage.archive, 'append', side_effect=OSError('synthetic disk failure')):
            with self.assertRaises(OSError): self.run_check()
        receipt = (self.root/'pending/yose.json').read_bytes()
        self.assertEqual(self.stage.status('yose')['stage_state'], 'pending')
        with self.assertRaisesRegex(HistoryError, 'pending_recovery_required'):
            self.stage.collect('yose', T1, lambda start: self.fail('must not fetch over a receipt'))
        self.assertEqual((self.root/'pending/yose.json').read_bytes(), receipt)
        result = self.stage.recover('yose')
        self.assertEqual(result['last_checked_at'], T0); self.assertEqual(result['operation'], 'recovered')
        self.assertEqual(len(self.stage.archive.read('yose')), 1)

    def test_cleanup_failure_recovers_committed_candidate_without_duplicate(self):
        with patch.object(self.stage, '_clear_pending', side_effect=OSError('interruption')):
            with self.assertRaises(OSError): self.run_check()
        self.assertEqual(self.stage.status('yose')['stage_state'], 'committed_needs_cleanup')
        result = self.stage.recover('yose')
        self.assertEqual(result['operation'], 'recovered'); self.assertEqual(len(self.stage.archive.read('yose')), 1)

    def test_recovery_can_acknowledge_a_committed_ancestor_without_moving_head(self):
        with patch.object(self.stage, '_clear_pending', side_effect=OSError()):
            with self.assertRaises(OSError): self.run_check()
        first = self.stage.archive.read('yose')[-1]['snapshot']
        new_head = self.stage.archive.append(snapshot(T1, first))
        self.stage.recover('yose')
        self.assertEqual(self.stage.archive.read('yose')[-1]['observation_id'], new_head)
        self.assertEqual(len(self.stage.archive.read('yose')), 2)

    def test_intervening_archive_writer_keeps_conflicting_receipt_for_review(self):
        self.run_check(); first = self.stage.archive.read('yose')[-1]['snapshot']
        def raced(start):
            self.stage.archive.append(snapshot(T1, first))
            return feed([raw()])
        with self.assertRaisesRegex(HistoryError, 'archive_head_changed'):
            self.stage.collect('yose', T2, raced)
        self.assertEqual(self.stage.status('yose')['stage_state'], 'conflict')
        with self.assertRaisesRegex(HistoryError, 'archive_head_changed'): self.stage.recover('yose')
        self.assertTrue((self.root/'pending/yose.json').exists())
        self.assertEqual(len(self.stage.archive.read('yose')), 2)

    def test_pending_receipt_tampering_blocks_recovery_and_preserves_file(self):
        with patch.object(self.stage.archive, 'append', side_effect=OSError()):
            with self.assertRaises(OSError): self.run_check()
        path = self.root/'pending/yose.json'; value = json.loads(path.read_text())
        value['payload']['expected_head'] = 'a'*64; path.write_text(json.dumps(value))
        with self.assertRaises(HistoryError): self.stage.recover('yose')
        self.assertTrue(path.exists()); self.assertEqual(self.stage.archive.read('yose'), [])

    def test_invalid_or_repeated_clocks_refuse_before_network(self):
        self.run_check()
        for at in (T0, '2026-02-30T20:00:00Z', '2026-09-27T20:00:00Z', 'bad'):
            with self.subTest(at=at), self.assertRaises(HistoryError):
                self.stage.collect('yose', at, lambda start: self.fail('invalid clock fetched'))
        self.assertEqual(len(self.stage.archive.read('yose')), 1)

    def test_unsupported_park_refuses_before_state_or_network(self):
        for code in ('abcd', '../yose', 'YOSE', ''):
            with self.subTest(code=code), self.assertRaises(HistoryError):
                self.stage.collect(code, T0, lambda start: self.fail('unsupported park fetched'))
        self.assertFalse(self.root.exists())

    def test_active_stage_lock_is_not_stolen(self):
        self.root.mkdir(); lock = self.root/'.stage.lock'; lock.write_text('owner')
        with self.assertRaisesRegex(HistoryError, 'staging_locked'): self.run_check()
        self.assertEqual(lock.read_text(), 'owner'); self.assertTrue(self.stage.status('yose')['writer_locked'])

    def test_corrupt_archive_refuses_before_network(self):
        self.run_check(); evidence = next((self.root/'archive/evidence').glob('*.json')); evidence.write_text('{}')
        with self.assertRaises(HistoryError):
            self.stage.collect('yose', T1, lambda start: self.fail('corrupt archive fetched'))

    def test_root_symlink_and_protected_destination_refuse(self):
        outside = Path(self.temp.name)/'outside'; outside.mkdir(); self.root.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(HistoryError): self.run_check()
        self.assertEqual(list(outside.iterdir()), [])
        project = Path(__file__).resolve().parents[1]
        for folder in ('', 'data/new-stage', 'public/new-stage', 'src/new-stage', '.git/new-stage'):
            with self.subTest(folder=folder), self.assertRaises(HistoryError): StagingCollector(project/folder)

    def test_staging_destination_requires_absolute_storage_outside_the_whole_checkout(self):
        project = Path(__file__).resolve().parents[1]
        destinations = [Path('state/staging'), Path('../staging'), project.parent,
                        project/'state/staging', project/'.superpowers/private-staging',
                        project/'unlisted-private-staging', self.root/'..'/'other-stage']
        if project.anchor == '/':
            destinations.extend([Path('/' + str(project))/'state/staging',
                                 Path('/' + str(project.parent))])
        for destination in destinations:
            with self.subTest(destination=str(destination)):
                with self.assertRaisesRegex(HistoryError, 'unsafe_staging_destination'):
                    StagingCollector(destination)
        self.assertFalse(self.root.exists())

    def test_receipt_size_limit_refuses_oversize_without_reading_all_bytes(self):
        (self.root/'pending').mkdir(parents=True)
        path = self.root/'pending/yose.json'; path.write_bytes(b' '*(10*1024*1024+1))
        with self.assertRaises(HistoryError): self.stage.recover('yose')
        self.assertEqual(self.stage.archive.read('yose'), [])

    def test_status_repeated_reads_do_not_modify_files(self):
        self.run_check()
        before = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()}
        self.stage.status('yose'); self.stage.status('yose')
        after = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_pending_file_capacity_is_reserved_before_creating_receipt(self):
        pending = self.root/'pending'; pending.mkdir(parents=True)
        (pending/'.receipt-orphan.tmp').write_bytes(b'')
        with patch('tracker.staging.MAX_PENDING_FILES', 2):
            with self.assertRaisesRegex(HistoryError, 'staging_limit'):
                self.run_check()
        self.assertFalse((pending/'yose.json').exists())
        self.assertEqual(self.stage.archive.read('yose'), [])

    def test_archive_lock_blocks_network_without_stealing_lock(self):
        archive = self.root/'archive'; archive.mkdir(parents=True)
        lock = archive/'.writer.lock'; lock.write_text('owner')
        with self.assertRaisesRegex(HistoryError, 'archive_locked'):
            self.stage.collect('yose', T0, lambda start: self.fail('locked archive fetched'))
        self.assertEqual(lock.read_text(), 'owner')
