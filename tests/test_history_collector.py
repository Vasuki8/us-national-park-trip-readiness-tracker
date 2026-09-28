"""Exercise the unchanged real collector against synthetic feeds, without NPS requests."""
import tempfile
import unittest
from pathlib import Path
from tracker.alerts import collect, initial_snapshot
from tracker.history_store import HistoryStore
from history_fixtures import T0, T1, T2

class CollectorHistoryTests(unittest.TestCase):
    def page(self, rows):
        return {'total': str(len(rows)), 'start': '0', 'limit': '50', 'data': rows}

    def rows(self, code='yose'):
        return [{'id': name, 'parkCode': code, 'title': 'Synthetic, not an actual notice', 'description': 'Synthetic café text only.', 'category': 'Park Closure', 'url': f'https://www.nps.gov/{code}/test.htm'} for name in ('a', 'b')]

    def test_real_collector_edit_and_removal_reconstruct_exactly(self):
        first = collect('yose', initial_snapshot('yose'), T0, lambda start: self.page(self.rows()))
        rows = self.rows()[:1]; rows[0]['title'] = 'Edited synthetic notice'
        second = collect('yose', first, T1, lambda start: self.page(rows))
        self.assertEqual(second['collection_status'], 'success')
        with tempfile.TemporaryDirectory() as folder:
            store = HistoryStore(Path(folder)); store.append(first); store.append(second)
            history = store.read('yose')
            self.assertEqual(history[0]['snapshot'], first)
            self.assertEqual(history[1]['snapshot'], second)
            self.assertEqual([c['kind'] for c in history[1]['changes']], ['edited', 'removed'])

    def test_real_collector_quarantine_and_failure_keep_the_accepted_history(self):
        first = collect('yose', initial_snapshot('yose'), T0, lambda start: self.page(self.rows()))
        quarantined = collect('yose', first, T1, lambda start: self.page([]))
        def failed(start): raise TimeoutError('Synthetic sensitive error must not persist')
        failure = collect('yose', quarantined, T2, failed)
        with tempfile.TemporaryDirectory() as folder:
            store = HistoryStore(Path(folder))
            for value in (first, quarantined, failure): store.append(value)
            history = store.read('yose')
            self.assertEqual([h['snapshot']['collection_status'] for h in history], ['success', 'quarantined', 'failed'])
            self.assertEqual(history[-1]['snapshot']['records'], first['records'])
            self.assertEqual(history[-1]['snapshot']['last_successful_fetch_at'], T0)
            self.assertEqual(history[-1]['changes'], [])
            self.assertNotIn('sensitive error', str(history))

    def test_all_five_collector_park_codes_use_separate_chains(self):
        with tempfile.TemporaryDirectory() as folder:
            store = HistoryStore(Path(folder))
            for code in ('yose', 'romo', 'yell', 'zion', 'grca'):
                result = collect(code, initial_snapshot(code), T0, lambda start: self.page(self.rows(code)))
                store.append(result)
                self.assertEqual(store.read(code)[0]['snapshot'], result)

if __name__ == '__main__': unittest.main()
