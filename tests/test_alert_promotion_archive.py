"""Synthetic full-chain continuity checks; no real capture, review or publication."""
import copy
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from promotion_archive_fixture import prepare
from tracker.alert_promotion_archive import main, verify_archive_request
from tracker.entry_review_io import ReviewStoreError
from tracker.history_model import HistoryError, canonical, digest
from tracker.history_projection import _project_entries
from tracker.history_store import HistoryStore
from tracker.preview import PILOT_CODES


def request_for(public, bundle):
    items = []
    for code, old, new in zip(PILOT_CODES, public, bundle['views']):
        item = {'park_code': code}
        for prefix, view in [('public', old), ('candidate', new)]:
            item.update({f'{prefix}_snapshot_hash': digest(view['snapshot']),
                         f'{prefix}_history_hash': digest(view['history']),
                         f'{prefix}_total_observations': view['history']['total_observations'],
                         f'{prefix}_visible_observations': len(view['history']['observations'])})
        items.append(item)
    return {'schema_version': 1, 'purpose': 'alert_archive_request', 'bundle_id': bundle['bundle_id'], 'parks': items}


class ArchivePromotionTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(); self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        mask = os.umask(0o077)
        try:
            self.archive = prepare(self.root, 'window')
        finally:
            os.umask(mask)
        self.public = json.loads((self.root/'public.json').read_text())
        self.bundle = json.loads((self.root/'bundle.json').read_text())
        self.request = request_for(self.public, self.bundle)

    def files(self):
        return {str(p.relative_to(self.archive)): p.read_bytes() for p in self.archive.rglob('*') if p.is_file()}

    def test_full_chain_verifies_hidden_public_checkpoint_without_writes(self):
        before = self.files()
        report = verify_archive_request(self.archive, self.request)
        self.assertEqual(report['verified_parks'], 5)
        self.assertEqual(report['request_hash'], digest(self.request))
        self.assertEqual(report['bundle_id'], self.bundle['bundle_id'])
        self.assertFalse(report['publication_performed'])
        self.assertEqual(self.files(), before)
        self.assertNotIn(str(self.archive), json.dumps(report))
        self.assertNotIn('Synthetic', json.dumps(report))

    def test_frozen_candidate_can_remain_an_exact_ancestor_of_an_advanced_archive(self):
        entries = HistoryStore(self.archive).read('yose')
        bundle = copy.deepcopy(self.bundle)
        bundle['views'][0] = _project_entries(entries[:23], 'yose')
        bundle['bundle_id'] = digest({k:v for k,v in bundle.items() if k != 'bundle_id'})
        self.assertEqual(verify_archive_request(self.archive, request_for(self.public, bundle))['bundle_id'], bundle['bundle_id'])

    def test_forged_public_or_candidate_hashes_cannot_supply_archive_proof(self):
        for field in ['public_snapshot_hash', 'public_history_hash', 'candidate_snapshot_hash', 'candidate_history_hash']:
            with self.subTest(field=field):
                request = copy.deepcopy(self.request); request['parks'][0][field] = 'a'*64
                with self.assertRaises(HistoryError): verify_archive_request(self.archive, request)
        request = copy.deepcopy(self.request); request['bundle_id'] = 'b'*64
        with self.assertRaises(HistoryError): verify_archive_request(self.archive, request)

    def test_missing_or_rewound_checkpoint_refuses(self):
        request = copy.deepcopy(self.request); request['parks'][0]['candidate_total_observations'] = 26
        with self.assertRaises(HistoryError): verify_archive_request(self.archive, request)
        request = copy.deepcopy(self.request); request['parks'][0]['public_total_observations'] = 26
        with self.assertRaises(HistoryError): verify_archive_request(self.archive, request)

    def test_missing_archive_is_not_initialized_by_verification(self):
        missing = self.root/'missing-archive'
        with self.assertRaises(OSError): verify_archive_request(missing, self.request)
        self.assertFalse(missing.exists())

    def test_malformed_inventory_and_counts_are_not_coerced(self):
        mutations = [lambda r: r.update(schema_version=True), lambda r: r.update(purpose='approved'),
                     lambda r: r['parks'].pop(), lambda r: r['parks'].reverse(),
                     lambda r: r['parks'][0].update(public_total_observations=True),
                     lambda r: r['parks'][0].update(candidate_visible_observations=21),
                     lambda r: r['parks'][1].update(candidate_visible_observations=1),
                     lambda r: r['parks'][0].update(private_path='synthetic-private')]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                request = copy.deepcopy(self.request); mutate(request)
                with self.assertRaises(HistoryError): verify_archive_request(self.archive, request)

    def test_corrupt_committed_object_cannot_supply_proof(self):
        evidence = next((self.archive/'evidence').glob('*.json'))
        evidence.write_bytes(b'{}')
        with self.assertRaises(HistoryError): verify_archive_request(self.archive, self.request)

    def test_private_permissions_symlinks_and_hardlinks_are_required(self):
        head = self.archive/'parks/yose/head.json'
        head.chmod(0o644)
        with self.assertRaises(ReviewStoreError): verify_archive_request(self.archive, self.request)
        head.chmod(0o600)
        alias = self.root/'alias'; alias.symlink_to(self.archive, target_is_directory=True)
        with self.assertRaises(ReviewStoreError): verify_archive_request(alias, self.request)
        alias.unlink(); os.link(head, self.root/'head-copy.json')
        with self.assertRaises(ReviewStoreError): verify_archive_request(self.archive, self.request)

    def test_cli_bounds_and_redacts_requests_without_output_on_refusal(self):
        for raw in [b'x'*16385, b'{"schema_version":1,"schema_version":1}', b'{bad', canonical({**self.request, 'private_path': str(self.archive)})]:
            out, err = io.StringIO(), io.StringIO()
            with patch('sys.stdin', SimpleNamespace(buffer=io.BytesIO(raw))), redirect_stdout(out), redirect_stderr(err):
                result = main(['--archive-dir', str(self.archive)])
            self.assertEqual(result, 2); self.assertEqual(out.getvalue(), '')
            self.assertNotIn(str(self.archive), err.getvalue()); self.assertNotIn('Synthetic', err.getvalue())

    def test_cli_emits_only_the_bound_metadata_reply(self):
        out, err = io.StringIO(), io.StringIO()
        with patch('sys.stdin', SimpleNamespace(buffer=io.BytesIO(canonical(self.request)))), redirect_stdout(out), redirect_stderr(err):
            result = main(['--archive-dir', str(self.archive)])
        self.assertEqual(result, 0); self.assertEqual(err.getvalue(), '')
        self.assertEqual(json.loads(out.getvalue())['request_hash'], digest(self.request))


if __name__ == '__main__': unittest.main()
