"""Bounded synthetic collector/archive output for the cross-language URL regression."""
from __future__ import annotations

import copy
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from staging_fixtures import T0, T1, T2, T3, feed, raw, snapshot
from tracker.history_model import SEMANTIC_FIELDS, canonical
from tracker.history_store import HistoryStore
from tracker.preview import make_bundle
from tracker.staging import StagingCollector

SAFE_URLS = [
    'https://www.nps.gov/yose/synthetic/',
    'https://www.nps.gov/subjects/synthetic/',
    'https://go.nps.gov/synthetic/',
    'https://inciweb.wildfire.gov/incident/synthetic/',
    'https://example.org/synthetic/directory/?view=summary#details',
    'https://example.org/synthetic/caf%C3%A9/',
    'https://example.org/synthetic/encoded-directory%2F',
]
EDITED_URL = 'https://www.nps.gov/yose/synthetic-changed/'
UNSAFE_URLS = [
    'https://example.org/synthetic/../directory/',
    'https://example.org/synthetic/%2e%2e/directory/',
    'https://example.org/synthetic/./directory/',
    'https://example.org/synthetic//directory/',
    'https://example.org//directory/',
    'https://example.org/synthetic/directory//',
    'https://example.org/synthetic%2f/directory/',
    'https://example.org/%2Fdirectory/',
    'https://example.org/synthetic\\directory/',
    'https://example.org/synthetic%5cdirectory/',
]


def make_fixture():
    with tempfile.TemporaryDirectory(prefix='notice-url-pipeline-') as folder:
        stage = StagingCollector(Path(folder) / 'stage')
        rows = [raw(f'directory-{index}', url=url, description='Synthetic café — directory URL fixture only.')
                for index, url in enumerate(SAFE_URLS)]
        bundles = {}
        previous = None
        for name, at in [('baseline', T0), ('unchanged', T1), ('edited', T2)]:
            if name == 'edited':
                rows = copy.deepcopy(rows)
                rows[0]['url'] = EDITED_URL
            collected = snapshot(at=at, previous=previous, records=rows)
            assert collected['collection_status'] == 'success', name
            summary = stage.collect('yose', at, lambda start: feed(rows))
            assert summary['collection_status'] == 'success', name
            # A fresh reader must replay the immutable objects to the exact collector output.
            entries = HistoryStore(stage.archive.root).read('yose')
            assert entries[-1]['snapshot'] == collected
            previous = collected
            bundles[name] = make_bundle(stage.archive, data_kind='synthetic')
            if name == 'baseline':
                original_evidence = {
                    path: (path.read_bytes(), path.stat().st_mtime_ns)
                    for path in (stage.archive.root / 'evidence').glob('*.json')
                }

        def failed(_start):
            raise TimeoutError('synthetic transport failure')

        attempts = [stage.collect('yose', T3, failed)]
        for index, url in enumerate(UNSAFE_URLS):
            at = (datetime(2026, 9, 29, tzinfo=timezone.utc) + timedelta(hours=index)).isoformat().replace('+00:00', 'Z')
            rejected = copy.deepcopy(rows)
            rejected[0]['url'] = url
            summary = stage.collect('yose', at, lambda start: feed(rejected))
            assert summary['collection_status'] == 'quarantined'
            attempts.append(summary)
        entries = HistoryStore(stage.archive.root).read('yose')
        assert entries[-1]['snapshot']['records'] == previous['records']
        assert entries[-1]['snapshot']['last_successful_fetch_at'] == T2
        assert all(entry['changes'] == [] for entry in entries[3:])
        assert all((path.read_bytes(), path.stat().st_mtime_ns) == value
                   for path, value in original_evidence.items())
        assert not (stage.root / 'pending' / 'yose.json').exists()

        # Export only the seven original and one edited synthetic evidence objects.
        evidence = []
        for path in sorted((stage.archive.root / 'evidence').glob('*.json')):
            data = path.read_bytes()
            evidence.append({'content_hash': path.stem, 'canonical': data.decode('utf-8')})
        assert len(evidence) == len(SAFE_URLS) + 1
        for record in previous['records']:
            data = (stage.archive.root / 'evidence' / f"{record['content_hash']}.json").read_bytes()
            assert data == canonical({key: record[key] for key in SEMANTIC_FIELDS})
        bundles['degraded'] = make_bundle(stage.archive, data_kind='synthetic')
        result = {'purpose': 'SYNTHETIC TEST DATA — NOT PARK CONDITIONS',
                  'safe_urls': SAFE_URLS, 'edited_url': EDITED_URL, 'unsafe_urls': UNSAFE_URLS,
                  'bundles': bundles, 'evidence': evidence, 'attempts': attempts,
                  'canonical_bundle': canonical(bundles['degraded']).decode('utf-8')}
        assert len(canonical(result)) < 128 * 1024
        return result


if __name__ == '__main__':
    # Only this disposable subprocess owns its external synthetic archive.
    os.umask(0o077)
    with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network forbidden')):
        sys.stdout.buffer.write(canonical(make_fixture()))
