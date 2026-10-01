import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from history_fixtures import T0, T1, T2, notice, snapshot, next_snapshot
from tracker.history_model import HistoryError, canonical, digest
from tracker.history_store import HistoryStore

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'archive'; self.store = HistoryStore(self.root)

    def test_empty_read_is_read_only_and_has_no_fake_observations(self):
        self.assertEqual(self.store.read('yose'), [])
        self.assertFalse(self.root.exists())

    def test_archive_destination_requires_absolute_storage_outside_the_whole_checkout(self):
        project = Path(__file__).resolve().parents[1]
        destinations = [Path('state/alert-history'), Path('../alert-history'), project,
                        project.parent, project/'state/alert-history',
                        project/'.superpowers/private-history', project/'unlisted-private-history',
                        self.root/'..'/'other-history']
        if project.anchor == '/':
            destinations.extend([Path('/' + str(project))/'state/alert-history',
                                 Path('/' + str(project.parent))])
        for destination in destinations:
            with self.subTest(destination=str(destination)):
                with self.assertRaisesRegex(HistoryError, 'unsafe_archive_destination'):
                    HistoryStore(destination)
        self.assertFalse(self.root.exists())

    def test_round_trip_reconstructs_text_and_original_clocks(self):
        original = snapshot()
        identifier = self.store.append(original)
        entries = HistoryStore(self.root).read('yose')
        self.assertEqual(len(identifier), 64)
        self.assertEqual(entries[0]['snapshot'], original)
        self.assertEqual(entries[0]['comparison'], 'baseline')
        self.assertIsNone(entries[0]['previous_id'])
        self.assertEqual(entries[0]['observation_id'], identifier)

    def test_unchanged_evidence_is_deduplicated_but_attempts_are_retained(self):
        old = snapshot()
        first = self.store.append(old); second = self.store.append(next_snapshot(old))
        self.assertNotEqual(first, second)
        self.assertEqual(len(list((self.root/'evidence').glob('*.json'))), 1)
        self.assertEqual(len(self.store.read('yose')), 2)
        obj = json.loads((self.root/'parks/yose/observations'/f'{second}.json').read_text())
        self.assertNotIn('records', obj['header'])
        self.assertNotIn(old['records'][0]['description'], json.dumps(obj))
        self.assertEqual(obj['previous_id'], first)

    def test_exact_retry_does_not_duplicate_history_or_evidence(self):
        first = self.store.append(snapshot())
        self.assertEqual(self.store.append(snapshot()), first)
        self.assertEqual(len(self.store.read('yose')), 1)

    def test_reordered_retry_is_idempotent(self):
        old = snapshot([notice('a'), notice('b')]); first = self.store.append(old)
        old['records'].reverse()
        self.assertEqual(self.store.append(old), first)

    def test_removed_evidence_remains_reconstructable(self):
        old = snapshot([notice('a'), notice('b')]); self.store.append(old)
        new = next_snapshot(old, records=[old['records'][1]]); self.store.append(new)
        entries = self.store.read('yose')
        removed = entries[-1]['changes'][0]
        self.assertEqual(removed['kind'], 'removed')
        evidence = json.loads((self.root/'evidence'/f"{removed['before_hash']}.json").read_text())
        self.assertEqual(evidence['description'], old['records'][0]['description'])
        self.assertEqual(entries[0]['snapshot'], old)

    def test_failed_checks_survive_restart_without_changes(self):
        old = snapshot(); self.store.append(old)
        failed = next_snapshot(old, status='failed'); self.store.append(failed)
        last = HistoryStore(self.root).read('yose')[-1]
        self.assertEqual(last['snapshot'], failed)
        self.assertEqual(last['changes'], [])
        self.assertEqual(last['comparison'], 'not_compared')

    def test_interrupted_append_preserves_prior_head_and_identical_retry_recovers(self):
        first = self.store.append(snapshot())
        newer = next_snapshot(snapshot(), records=[notice(now=T1, title='Revised')])
        newer['records'][0]['observed_first_at'] = T0
        with patch.object(self.store, '_commit_head', side_effect=OSError('simulated disk problem')):
            with self.assertRaises(OSError): self.store.append(newer)
        self.assertEqual(self.store.read('yose')[-1]['observation_id'], first)
        second = self.store.append(newer)
        self.assertEqual(len(self.store.read('yose')), 2)
        self.assertEqual(self.store.read('yose')[-1]['observation_id'], second)
        self.assertFalse((self.root/'.writer.lock').exists())

    def test_first_append_interrupted_after_objects_leaves_empty_head_retryable(self):
        with patch.object(self.store, '_commit_head', side_effect=OSError('simulated')):
            with self.assertRaises(OSError): self.store.append(snapshot())
        self.assertEqual(self.store.read('yose'), [])
        self.store.append(snapshot())
        self.assertEqual(len(self.store.read('yose')), 1)

    def test_conflicting_same_time_and_older_replays_do_not_change_head(self):
        self.store.append(snapshot()); latest = self.store.append(next_snapshot(snapshot()))
        for candidate in [snapshot(), snapshot([notice(now=T1, title='Conflicting')], now=T1)]:
            with self.assertRaises(HistoryError): self.store.append(candidate)
        self.assertEqual(self.store.read('yose')[-1]['observation_id'], latest)

    def test_active_or_abandoned_lock_is_not_removed_by_another_writer(self):
        self.root.mkdir(); lock = self.root/'.writer.lock'; lock.write_text('123')
        with self.assertRaisesRegex(HistoryError, 'archive_locked'): self.store.append(snapshot())
        self.assertEqual(lock.read_text(), '123')

    def test_corrupt_or_missing_evidence_stops_read_and_append(self):
        self.store.append(snapshot())
        evidence = next((self.root/'evidence').glob('*.json')); original = evidence.read_bytes()
        evidence.write_text('{"description":"corrupt"}')
        with self.assertRaises(HistoryError): self.store.read('yose')
        with self.assertRaises(HistoryError): self.store.append(next_snapshot(snapshot()))
        evidence.write_bytes(original); evidence.unlink()
        with self.assertRaises(HistoryError): self.store.read('yose')

    def test_corrupt_observation_cannot_be_treated_as_empty_history(self):
        identifier = self.store.append(snapshot())
        path = self.root/'parks/yose/observations'/f'{identifier}.json'
        path.write_text('{broken json')
        with self.assertRaises(HistoryError): self.store.read('yose')

    def test_missing_head_with_existing_observations_is_not_a_new_archive(self):
        self.store.append(snapshot()); (self.root/'parks/yose/head.json').unlink()
        with self.assertRaises(HistoryError): self.store.read('yose')
        with self.assertRaises(HistoryError): self.store.append(snapshot())

    def test_broken_chain_is_rejected(self):
        first = self.store.append(snapshot()); self.store.append(next_snapshot(snapshot()))
        (self.root/'parks/yose/observations'/f'{first}.json').unlink()
        with self.assertRaises(HistoryError): self.store.read('yose')

    def test_rehashed_forged_events_fail_semantic_validation(self):
        identifier = self.store.append(snapshot())
        directory = self.root/'parks/yose/observations'; obj = json.loads((directory/f'{identifier}.json').read_text())
        obj['changes'] = [{'kind': 'removed', 'record_id': 'a', 'before_hash': '0'*64, 'after_hash': None}]
        forged = digest(obj); (directory/f'{forged}.json').write_bytes(canonical(obj))
        (self.root/'parks/yose/head.json').write_bytes(canonical({'schema_version': 1, 'observation_id': forged}))
        with self.assertRaises(HistoryError): self.store.read('yose')

    def test_park_histories_are_isolated(self):
        self.store.append(snapshot()); self.store.append(snapshot(code='grca'))
        self.assertEqual(len(self.store.read('yose')), 1)
        self.assertEqual(self.store.read('grca')[0]['snapshot']['park_code'], 'grca')

    def test_path_traversal_and_symlinks_are_rejected(self):
        for code in ['../x', 'YOSE', 'yose/../../x']:
            with self.assertRaises(HistoryError): self.store.read(code)
        self.root.mkdir(); outside = Path(self.tmp.name)/'outside'; outside.mkdir()
        (self.root/'evidence').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(HistoryError): self.store.append(snapshot())
        self.assertEqual(list(outside.iterdir()), [])

    def test_size_and_observation_limits_do_not_delete_history(self):
        limited = HistoryStore(self.root, max_observations=1)
        identifier = limited.append(snapshot())
        with self.assertRaisesRegex(HistoryError, 'history_limit'): limited.append(next_snapshot(snapshot()))
        self.assertEqual(limited.read('yose')[-1]['observation_id'], identifier)
        small = HistoryStore(self.root, max_bytes=1)
        with self.assertRaisesRegex(HistoryError, 'archive_limit'): small.append(next_snapshot(snapshot()))
        self.assertEqual(self.store.read('yose')[-1]['observation_id'], identifier)

    def test_invalid_input_does_not_initialize_archive(self):
        bad = snapshot(); bad['api_key'] = 'synthetic-private-key'
        with self.assertRaises(HistoryError): self.store.append(bad)
        self.assertFalse(self.root.exists())

    def test_unreferenced_incomplete_object_is_not_committed_history(self):
        self.store.append(snapshot()); path = self.root/'parks/yose/observations'/('0'*64+'.json')
        path.write_text('partial uncommitted object')
        self.assertEqual(len(self.store.read('yose')), 1)

    def test_reconstructed_history_is_bounded_even_when_text_is_deduplicated(self):
        old = snapshot([notice(description='Synthetic text ' * 100)])
        limited = HistoryStore(self.root, max_reconstructed_bytes=len(canonical(old)))
        identifier = limited.append(old)
        with self.assertRaisesRegex(HistoryError, 'history_expansion_limit'):
            limited.append(next_snapshot(old))
        self.assertEqual(limited.read('yose')[-1]['observation_id'], identifier)
        self.store.append(next_snapshot(old))
        with self.assertRaisesRegex(HistoryError, 'history_expansion_limit'):
            limited.read('yose')

if __name__ == '__main__': unittest.main()
