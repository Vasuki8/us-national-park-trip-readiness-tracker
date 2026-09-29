"""Build deterministic synthetic cases using the real archive and projection."""
import tempfile
from pathlib import Path
from history_fixtures import T0, T1, T2, notice, snapshot, next_snapshot
from tracker.history_projection import project_history
from tracker.history_store import HistoryStore


def make_fixture():
    with tempfile.TemporaryDirectory() as folder:
        store = HistoryStore(Path(folder)/'archive')
        cases = {'empty': project_history(store, 'yose')}
        first = snapshot([notice('a'), notice('b')]); store.append(first)
        cases['baseline'] = project_history(store, 'yose')
        edited = notice('a', now=T1, title='Synthetic changed access notice',
                        description='Café — synthetic text. <script>window.historyInjected=1</script>')
        edited['observed_first_at'] = T0
        second = next_snapshot(first, records=[edited, notice('c', now=T1, title='Synthetic added notice')])
        store.append(second)
        cases['mixed'] = project_history(store, 'yose')
        store.append(next_snapshot(second, now=T2, status='failed'))
        cases['failed'] = project_history(store, 'yose')
        cases['truncated'] = project_history(store, 'yose', limit=1)
        return {'purpose': 'SYNTHETIC TEST DATA — NOT PARK CONDITIONS', 'cases': cases}
