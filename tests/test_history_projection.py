"""Synthetic archive-to-visitor projection contracts; no live source claims."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from history_fixtures import T0, T1, T2, T3, notice, snapshot, next_snapshot
from tracker.history_model import HistoryError, digest
from tracker.history_store import HistoryStore
from tracker.history_projection import project_history

class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name) / 'archive'
        self.store = HistoryStore(self.root)

    def test_empty_projection_is_read_only_and_never_checked(self):
        result = project_history(self.store, 'yose')
        self.assertFalse(self.root.exists())
        self.assertEqual(result['snapshot']['collection_status'], 'never_checked')
        self.assertEqual(result['history']['observations'], [])
        self.assertIsNone(result['history']['head_observation_id'])
        self.assertEqual(result['history']['snapshot_hash'], digest(result['snapshot']))

    def test_baseline_is_not_a_new_closure(self):
        identifier = self.store.append(snapshot())
        result = project_history(self.store, 'yose')
        self.assertEqual(result['history']['head_observation_id'], identifier)
        self.assertEqual(result['history']['total_observations'], 1)
        self.assertEqual(result['history']['total_changes'], 0)
        self.assertEqual(result['history']['observations'][0]['comparison'], 'baseline')
        self.assertEqual(result['history']['observations'][0]['changes'], [])

    def changed(self):
        first = snapshot([notice('a'), notice('b')]); self.store.append(first)
        edited = notice('a', now=T1, title='Synthetic revised notice', description='Café — synthetic evidence.')
        edited['observed_first_at'] = T0
        second = next_snapshot(first, records=[edited, notice('c', now=T1)])
        self.store.append(second)
        return first, second

    def test_add_edit_removal_have_reconstructable_before_after(self):
        _, current = self.changed()
        view = project_history(self.store, 'yose')
        changes = view['history']['observations'][0]['changes']
        self.assertEqual([c['kind'] for c in changes], ['edited', 'removed', 'added'])
        self.assertEqual(changes[0]['after']['description'], 'Café — synthetic evidence.')
        self.assertEqual(changes[0]['before']['title'], 'Synthetic facility notice')
        self.assertIsNone(changes[1]['after']); self.assertIsNone(changes[2]['before'])
        self.assertEqual(view['snapshot'], current)
        self.assertEqual(view['history']['snapshot_hash'], digest(current))
        self.assertNotIn('reopened', json.dumps(view))

    def test_failed_head_retains_last_good_but_has_no_semantic_changes(self):
        _, old = self.changed()
        failed = next_snapshot(old, now=T2, status='failed'); identifier = self.store.append(failed)
        view = project_history(self.store, 'yose')
        self.assertEqual(view['history']['head_observation_id'], identifier)
        self.assertEqual(view['snapshot']['last_successful_fetch_at'], T1)
        self.assertEqual(view['history']['observations'][0]['collection_status'], 'failed')
        self.assertEqual(view['history']['observations'][0]['changes'], [])
        self.assertEqual(view['history']['observations'][1]['change_count'], 3)

    def test_quarantine_is_distinct_and_not_a_success(self):
        old = snapshot(); self.store.append(old)
        self.store.append(next_snapshot(old, status='quarantined'))
        view = project_history(self.store, 'yose')
        self.assertEqual(view['snapshot']['collection_status'], 'quarantined')
        self.assertEqual(view['history']['observations'][0]['comparison'], 'not_compared')

    def test_bounded_window_discloses_omitted_observations_and_changes(self):
        _, old = self.changed(); self.store.append(next_snapshot(old, now=T2))
        history = project_history(self.store, 'yose', limit=1)['history']
        self.assertEqual(len(history['observations']), 1)
        self.assertEqual(history['omitted_observations'], 2)
        self.assertEqual(history['total_changes'], 3)
        self.assertEqual(history['omitted_changes'], 3)
        self.assertEqual(history['observations'][0]['sequence'], 3)

    def test_change_limit_is_explicit(self):
        old = snapshot(records=[]); self.store.append(old)
        self.store.append(next_snapshot(old, records=[notice(f'x{i:03}', now=T1) for i in range(101)]))
        history = project_history(self.store, 'yose')['history']
        latest = history['observations'][0]
        self.assertEqual(latest['change_count'], 101)
        self.assertEqual(len(latest['changes']), 100)
        self.assertEqual(latest['omitted_changes'], 1)
        self.assertEqual(history['omitted_changes'], 1)

    def test_invalid_limits_refuse_before_archive_read(self):
        for limit in (0, -1, 21, True, '3'):
            with self.subTest(limit=limit), patch.object(self.store, 'read') as read:
                with self.assertRaises(HistoryError): project_history(self.store, 'yose', limit=limit)
                read.assert_not_called()

    def test_corrupt_evidence_cannot_be_projected(self):
        self.store.append(snapshot())
        next((self.root/'evidence').glob('*.json')).write_text('{}')
        with self.assertRaises(HistoryError): project_history(self.store, 'yose')

    def test_pending_or_orphan_files_never_enter_projection(self):
        self.store.append(snapshot())
        before = project_history(self.store, 'yose')
        (self.root/'pending.json').write_text('{"secret":"synthetic-not-for-visitors"}')
        self.assertEqual(project_history(self.store, 'yose'), before)

    def test_one_verified_read_binds_snapshot_and_history(self):
        self.changed()
        with patch.object(self.store, 'read', wraps=self.store.read) as read:
            result = project_history(self.store, 'yose')
            read.assert_called_once_with('yose')
        self.assertEqual(result['snapshot']['last_checked_at'], result['history']['observations'][0]['checked_at'])
        self.assertIsNone(result['snapshot']['published_at'])

    def test_repeated_projection_leaves_archive_unchanged(self):
        self.changed()
        files = lambda: {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        before = files(); one = project_history(self.store, 'yose'); two = project_history(self.store, 'yose')
        self.assertEqual(one, two); self.assertEqual(files(), before)
        one['snapshot']['records'].clear()
        self.assertTrue(project_history(self.store, 'yose')['snapshot']['records'])

    def test_only_public_projection_fields_are_selected(self):
        self.changed(); text = json.dumps(project_history(self.store, 'yose'))
        for forbidden in ('record_refs', 'previous_id', 'writer.lock', str(self.root), 'pending_receipt'):
            self.assertNotIn(forbidden, text)

    def test_oversize_projection_refuses_instead_of_silently_dropping_text(self):
        self.changed()
        with patch('tracker.history_projection.MAX_PROJECTION_BYTES', 100):
            with self.assertRaisesRegex(HistoryError, 'projection_too_large'):
                project_history(self.store, 'yose')

if __name__ == '__main__': unittest.main()

class FixtureTests(unittest.TestCase):
    def test_shared_fixture_is_reproducible_from_real_archive(self):
        from history_preview_fixture import make_fixture
        fixture = Path(__file__).parent/'fixtures'/'history-preview.json'
        self.assertEqual(json.loads(fixture.read_text()), make_fixture())
