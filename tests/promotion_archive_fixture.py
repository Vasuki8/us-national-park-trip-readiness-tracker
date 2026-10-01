"""Disposable synthetic archive fixtures for the real offline preparer CLI."""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from history_fixtures import T0, T1, notice, snapshot, next_snapshot
from tracker.history_store import HistoryStore
from tracker.preview import make_bundle
from tracker.history_model import canonical


def prepare(root: Path, scenario: str):
    archive = root/'archive'
    store = HistoryStore(archive)
    first = snapshot([notice(str(i)) for i in range(120)]) if scenario == 'changes' else snapshot()
    if scenario == 'no-success':
        first = next_snapshot(snapshot([]), now=T0, status='failed')
        first['last_successful_fetch_at'] = None
    store.append(first)
    public = make_bundle(store)['views']
    if scenario == 'changes':
        records = [notice(str(i), now=T1, title=f'Synthetic changed notice {i}') for i in range(120)]
        for record in records:
            record['observed_first_at'] = T0
        store.append(next_snapshot(first, records=records))
    elif scenario in ('hidden-success', 'no-success'):
        retained = first
        if scenario == 'hidden-success':
            retained = next_snapshot(first, now='2026-09-28T11:00:00Z')
            store.append(retained)
        for i in range(20):
            now = (datetime(2026, 9, 28, 12, tzinfo=timezone.utc) + timedelta(hours=i)).isoformat().replace('+00:00', 'Z')
            store.append(next_snapshot(retained, now=now, status='failed' if i % 2 else 'quarantined'))
        public = make_bundle(store)['views']
        store.append(next_snapshot(retained, now='2026-09-29T08:00:00Z', status='failed'))
    else:
        for i in range(1, 25):
            now = (datetime(2026, 9, 28, 10, tzinfo=timezone.utc) + timedelta(hours=i)).isoformat().replace('+00:00', 'Z')
            store.append(next_snapshot(first, now=now, status='failed'))
    (root/'bundle.json').write_bytes(canonical(make_bundle(store)))
    (root/'bundle.json').chmod(0o600)
    (root/'public.json').write_text(json.dumps(public), encoding='utf-8')
    return archive


if __name__ == '__main__':
    os.umask(0o077)  # Separate disposable operator process; ordinary test permissions stay unchanged.
    prepare(Path(sys.argv[1]), sys.argv[2])
