"""Synthetic activity evidence extends release gates without publication or clocks."""
import copy
import hashlib
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tracker.entry_review_io import ReviewStoreError
from tracker.park_activities import PILOT_CODES, collect_activities, initial_activities
from tracker.release_readiness import evaluate_readiness, main
from test_park_activities import T0, T1, activity, page, rehash
from test_release_readiness import synthetic_core_ready


ROOT = Path(__file__).resolve().parents[1]
ACTIVITY_FILES = ('park-activities.json', 'activity-source-rights.json')
SELECTED_GATES = ('durable_source_review', 'storage_backup', 'source_rights')


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def bundle_fixture(*, large=False, empty=False):
    """Independent exact review fixture; every source and decision is synthetic."""
    inventories = []
    for code in PILOT_CODES:
        if empty:
            records = []
        elif large:
            records = [activity('synthetic-' + str(number).zfill(3), code=code,
                                longDescription='Synthetic ' + 'x' * 60_000)
                       for number in range(40)]
        else:
            records = [activity(code=code)]
        inventories.append(collect_activities(code, initial_activities(code), T0,
                            lambda _start, records=records: page(records)))
    checkpoint_core = {'schema_version': 1, 'purpose': 'private_park_activity_checkpoint',
                       'parent_checkpoint_id': None, 'checked_at': T0,
                       'inventories': inventories}
    checkpoint = {**checkpoint_core, 'checkpoint_id': digest(checkpoint_core)}
    public = {'schema_version': 1, 'purpose': 'public_park_activities',
              'inventories': copy.deepcopy(inventories)}
    rights = {'schema_version': 1, 'purpose': 'public_park_activity_text_rights',
              'reviewed_at': '2026-10-03T10:30:00Z',
              'review_method': 'official_nps_policy_and_exact_activity_review',
              'policy': json.loads((ROOT / 'data/source-rights.json').read_text())['policy'],
              'records': [{
                  'park_code': inventory['park_code'], 'activity_id': record['id'],
                  'source_url': inventory['source_url'], 'content_hash': record['content_hash'],
                  'classification': 'nps_government_text',
                  'use_scope': 'normalized_activity_text_and_metadata',
                  'third_party_material_reproduced': False, 'nps_marks_reproduced': False,
                  'media_reproduced': False}
                  for inventory in inventories for record in inventory['records']]}
    core = {'schema_version': 1, 'purpose': 'private_reviewed_park_activities',
            'checkpoint': checkpoint, 'public_activities': public, 'rights': rights,
            'approval': {'decision': 'approved', 'approved_at': T1,
                         'checkpoint_id': checkpoint['checkpoint_id'],
                         'projection_hash': digest(public), 'rights_hash': digest(rights)}}
    return {**core, 'bundle_id': digest(core)}


class ActivityReadinessTests(unittest.TestCase):
    def repository(self, bundle=None, *, present=True):
        temporary = tempfile.TemporaryDirectory(prefix='activity-readiness-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for name in ('data', 'src', 'public', '.github'):
            shutil.copytree(ROOT / name, root / name)
        for name in (*ACTIVITY_FILES, 'park-profiles.json', 'profile-source-rights.json'):
            (root / 'data' / name).unlink(missing_ok=True)
        bundle = bundle_fixture() if bundle is None else bundle
        if present:
            self.write_public(root, bundle['public_activities'], bundle['rights'])
        return root, bundle

    def write_public(self, root, public, rights):
        for name, value in zip(ACTIVITY_FILES, (public, rights)):
            (root / 'data' / name).write_bytes(encoded(value))

    def report(self, root, **kwargs):
        with synthetic_core_ready():
            return evaluate_readiness(root, **kwargs)

    def gate(self, report, identifier):
        return next(gate for gate in report['gates'] if gate['id'] == identifier)

    def assert_activity_blocked(self, report):
        for identifier in SELECTED_GATES:
            gate = self.gate(report, identifier)
            self.assertEqual(gate['status'], 'blocked')
            self.assertEqual(gate['reason'], 'public_activity_inventory_invalid')
            self.assertTrue(gate['blocking'])

    def test_both_absent_preserve_prior_report_even_with_unrelated_valid_bundle(self):
        root, bundle = self.repository(present=False)
        before = self.report(root)
        after = self.report(root, activity_review=bundle, activity_backup=copy.deepcopy(bundle))
        self.assertEqual(after, before)
        self.assertEqual([gate['id'] for gate in after['gates']], [
            'durable_source_review', 'nps_alert_api', 'storage_backup', 'source_rights',
            'hosting_rollback', 'indexing', 'advertising'])

    def test_public_pair_requires_its_own_exact_review_and_recovered_copy(self):
        root, _ = self.repository()
        report = self.report(root)
        review, backup, rights = [self.gate(report, identifier) for identifier in SELECTED_GATES]
        self.assertEqual((review['status'], review['reason']),
                         ('not_checked', 'activity_review_not_supplied'))
        self.assertFalse(review['evidence']['public_activities_match_review'])
        self.assertEqual((backup['status'], backup['reason']),
                         ('blocked', 'verified_activity_backup_not_supplied'))
        self.assertFalse(backup['evidence']['activity_backup_verified'])
        self.assertFalse(backup['evidence']['activity_backup_matches_review'])
        self.assertEqual(rights['status'], 'pass')
        self.assertEqual(rights['evidence']['activity_records_covered'], 5)
        self.assertFalse(report['release_ready'])

    def test_confirmed_empty_inventories_still_require_review_and_preserve_their_clocks(self):
        bundle = bundle_fixture(empty=True)
        root, bundle = self.repository(bundle)
        missing = self.report(root)
        self.assertEqual(self.gate(missing, 'durable_source_review')['status'], 'not_checked')
        self.assertEqual(self.gate(missing, 'storage_backup')['status'], 'blocked')
        reviewed = self.report(root, activity_review=bundle, activity_backup=bundle)
        self.assertTrue(reviewed['release_ready'])
        self.assertEqual(self.gate(reviewed, 'source_rights')['evidence']['activity_records_covered'], 0)
        stored = json.loads((root / 'data' / ACTIVITY_FILES[0]).read_bytes())
        self.assertEqual([inventory['last_successful_fetch_at'] for inventory in stored['inventories']],
                         [T0, T0, T0, T0, T0])
        bundle['rights']['reviewed_at'] = '2026-10-03T09:59:59Z'
        self.write_public(root, bundle['public_activities'], bundle['rights'])
        self.assert_activity_blocked(self.report(root))

    def test_matching_evidence_keeps_original_source_clocks_and_performs_no_writes_or_network(self):
        root, bundle = self.repository()
        before = {path: (path.read_bytes(), path.stat().st_mtime_ns)
                  for path in root.rglob('*') if path.is_file()}
        original = copy.deepcopy(bundle)
        with patch.object(socket, 'socket', side_effect=AssertionError('Network is forbidden')):
            report = self.report(root, activity_review=bundle, activity_backup=copy.deepcopy(bundle))
        self.assertTrue(report['release_ready'])
        for identifier in SELECTED_GATES:
            gate = self.gate(report, identifier)
            self.assertEqual(gate['status'], 'pass')
            self.assertTrue(gate['evidence']['activity_inventory_valid'])
            self.assertEqual(gate['evidence']['activity_records_total'], 5)
        self.assertTrue(self.gate(report, 'durable_source_review')['evidence']['public_activities_match_review'])
        self.assertTrue(self.gate(report, 'storage_backup')['evidence']['activity_backup_matches_review'])
        self.assertFalse(report['network_performed'])
        self.assertFalse(report['writes_performed'])
        self.assertFalse(report['deployment_performed'])
        self.assertEqual(bundle, original)
        self.assertEqual(before, {path: (path.read_bytes(), path.stat().st_mtime_ns)
                                 for path in root.rglob('*') if path.is_file()})

    def test_matching_activities_cannot_clear_any_existing_block_or_unchecked_gate(self):
        root, bundle = self.repository()
        for identifier, function in (('durable_source_review', '_durable_review'),
                                     ('storage_backup', '_backup'), ('source_rights', '_rights'),
                                     ('nps_alert_api', '_alerts')):
            for status in ('blocked', 'not_checked'):
                with self.subTest(identifier=identifier, status=status), synthetic_core_ready():
                    baseline = {'id': identifier, 'name': 'Synthetic gate', 'status': status,
                                'reason': 'existing_source_evidence_unchanged', 'blocking': True,
                                'evidence': {'original_successful_check': T0}}
                    with patch('tracker.release_readiness.' + function, return_value=baseline):
                        report = evaluate_readiness(root, activity_review=bundle, activity_backup=bundle)
                    gate = self.gate(report, identifier)
                    self.assertEqual(gate['status'], status)
                    self.assertEqual(gate['reason'], 'existing_source_evidence_unchanged')
                    self.assertEqual(gate['evidence']['original_successful_check'], T0)
                    self.assertFalse(report['release_ready'])

    def test_incomplete_and_invalid_pair_blocks_all_selected_gates_on_every_target(self):
        for name, raw in ((ACTIVITY_FILES[0], None), (ACTIVITY_FILES[1], None),
                          (ACTIVITY_FILES[0], b'{}'), (ACTIVITY_FILES[1], b'{}'),
                          (ACTIVITY_FILES[0], b'not JSON'), (ACTIVITY_FILES[1], b'\xff')):
            with self.subTest(name=name, raw=raw):
                root, bundle = self.repository()
                path = root / 'data' / name
                if raw is None:
                    path.unlink()
                else:
                    path.write_bytes(raw)
                for target in ('pilot', 'indexed', 'advertising'):
                    self.assert_activity_blocked(self.report(root, release_target=target,
                        activity_review=bundle, activity_backup=bundle))

    def test_invalid_or_incomplete_pair_blocks_even_without_private_evidence(self):
        root, _ = self.repository()
        (root / 'data' / ACTIVITY_FILES[1]).unlink()
        self.assert_activity_blocked(self.report(root))

    def test_changed_text_source_clock_or_full_rights_review_cannot_match_old_bundle(self):
        for changed in ('text', 'clock', 'rights'):
            with self.subTest(changed=changed):
                root, bundle = self.repository()
                public, rights = copy.deepcopy(bundle['public_activities']), copy.deepcopy(bundle['rights'])
                if changed == 'text':
                    record = public['inventories'][0]['records'][0]
                    record['description'] = 'Synthetic independently changed activity text.'
                    rehash(record)
                    rights['records'][0]['content_hash'] = record['content_hash']
                elif changed == 'clock':
                    for inventory in public['inventories']:
                        inventory['last_checked_at'] = '2026-10-03T10:01:00Z'
                        inventory['last_successful_fetch_at'] = '2026-10-03T10:01:00Z'
                else:
                    rights['reviewed_at'] = '2026-10-03T10:31:00Z'
                self.write_public(root, public, rights)
                report = self.report(root, activity_review=bundle, activity_backup=bundle)
                review = self.gate(report, 'durable_source_review')
                self.assertEqual((review['status'], review['reason']),
                    ('blocked', 'public_activities_differ_from_reviewed_bundle'))
                self.assertFalse(review['evidence']['public_activities_match_review'])
                self.assertFalse(self.gate(report, 'storage_backup')['evidence']['activity_backup_matches_review'])

    def test_wrong_rights_record_source_or_scope_cannot_borrow_existing_rights_pass(self):
        for field, value in (('content_hash', '0' * 64),
                             ('source_url', 'https://example.invalid/private-source'),
                             ('use_scope', 'unreviewed_media'), ('media_reproduced', True)):
            with self.subTest(field=field):
                root, bundle = self.repository()
                rights = copy.deepcopy(bundle['rights'])
                rights['records'][0][field] = value
                self.write_public(root, bundle['public_activities'], rights)
                self.assert_activity_blocked(self.report(root, activity_review=bundle, activity_backup=bundle))

    def test_missing_or_different_valid_recovery_blocks_storage_gate(self):
        root, bundle = self.repository()
        other = copy.deepcopy(bundle)
        other['approval']['approved_at'] = '2026-10-03T11:01:00Z'
        other['bundle_id'] = digest({key: value for key, value in other.items() if key != 'bundle_id'})
        for backup in (None, other):
            with self.subTest(backup_supplied=backup is not None):
                report = self.report(root, activity_review=bundle, activity_backup=backup)
                gate = self.gate(report, 'storage_backup')
                self.assertEqual(gate['status'], 'blocked')
                self.assertEqual(gate['reason'], 'verified_activity_backup_not_supplied' if backup is None
                                 else 'activity_backup_does_not_match_current_review')
                self.assertFalse(gate['evidence']['activity_backup_matches_review'])

    def test_invalid_private_evidence_is_static_refusal_even_when_public_pair_absent(self):
        for present in (False, True):
            root, bundle = self.repository(present=present)
            for field in ('activity_review', 'activity_backup'):
                values = {'activity_review': bundle, 'activity_backup': copy.deepcopy(bundle)}
                values[field] = {'secret': '/private/sentinel/secret?api_key=synthetic'}
                with self.subTest(present=present, field=field), self.assertRaisesRegex(
                        ReviewStoreError, '^invalid_release_readiness_activity_evidence$'):
                    self.report(root, **values)

    def test_public_files_allow_one_final_lf_but_refuse_noncanonical_or_duplicate_json(self):
        for kind in ('one-lf', 'two-lf', 'pretty', 'duplicate'):
            with self.subTest(kind=kind):
                root, bundle = self.repository()
                for name, key in zip(ACTIVITY_FILES, ('public_activities', 'rights')):
                    raw = encoded(bundle[key])
                    if kind == 'pretty':
                        raw = json.dumps(bundle[key], indent=2).encode()
                    elif kind == 'duplicate':
                        raw = b'{"purpose":"unreviewed",' + raw[1:]
                    else:
                        raw += b'\n' if kind == 'one-lf' else b'\n\n'
                    (root / 'data' / name).write_bytes(raw)
                report = self.report(root, activity_review=bundle, activity_backup=bundle)
                if kind == 'one-lf':
                    self.assertTrue(report['release_ready'])
                else:
                    self.assert_activity_blocked(report)

    @unittest.skipUnless(os.name == 'posix', 'Symlink fixtures require POSIX.')
    def test_symlink_public_file_or_data_directory_blocks_activity_gates(self):
        for kind in ('file', 'data'):
            with self.subTest(kind=kind):
                root, bundle = self.repository()
                path = root / 'data' / ACTIVITY_FILES[0] if kind == 'file' else root / 'data'
                retained = path.with_name('retained-' + path.name)
                path.rename(retained)
                path.symlink_to(retained, target_is_directory=kind == 'data')
                self.assert_activity_blocked(self.report(root, activity_review=bundle, activity_backup=bundle))

    @unittest.skipUnless(os.name == 'posix', 'FIFO fixtures require POSIX.')
    def test_fifo_public_input_is_refused_before_a_blocking_read(self):
        root, _ = self.repository()
        path = root / 'data' / ACTIVITY_FILES[0]
        path.unlink()
        os.mkfifo(path)
        code = ('from pathlib import Path\n'
                'from tracker.release_readiness import evaluate_readiness\n'
                'import sys\n'
                'report=evaluate_readiness(Path(sys.argv[1]))\n'
                'print(next(g["status"] for g in report["gates"] if g["id"]=="source_rights"))\n')
        result = subprocess.run([sys.executable, '-c', code, str(root)], cwd=ROOT,
                                capture_output=True, text=True, timeout=5, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'blocked\n')
        self.assertEqual(result.stderr, '')

    def test_report_omits_source_text_urls_and_private_bundle_identities(self):
        root, bundle = self.repository()
        text = json.dumps(self.report(root, activity_review=bundle, activity_backup=bundle))
        for private in ('Synthetic activity', 'Synthetic credit', 'synthetic-outside-destination',
                        bundle['bundle_id'], bundle['checkpoint']['checkpoint_id'],
                        bundle['approval']['projection_hash'], bundle['approval']['rights_hash']):
            self.assertNotIn(private, text)

    def test_cli_refuses_backup_without_review_or_copies_in_the_same_parent(self):
        for arguments in (['--activity-backup', '/private/sentinel/backup'],
                          ['--activity-review', '/private/sentinel/same',
                           '--activity-backup', '/private/sentinel/same'],
                          ['--activity-review', '/private/sentinel/review.json',
                           '--activity-backup', '/private/sentinel/backup.json']):
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = main(arguments)
            self.assertEqual(code, 2)
            self.assertEqual(out.getvalue(), '')
            self.assertEqual(err.getvalue(), 'invalid_release_readiness_arguments\n')
            self.assertNotIn('/private/sentinel', err.getvalue())

    @unittest.skipUnless(os.name == 'posix', 'Canonical private paths require POSIX.')
    def test_cli_canonical_parent_alias_cannot_claim_separate_recovery(self):
        with tempfile.TemporaryDirectory(prefix='activity-private-') as folder:
            parent = Path(folder)
            parent.chmod(0o700)
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = main(['--activity-review', str(parent / 'review.json'),
                             '--activity-backup', '/' + str(parent / 'backup.json')])
            self.assertEqual(code, 2)
            self.assertEqual(out.getvalue(), '')
            self.assertEqual(err.getvalue(), 'invalid_release_readiness_arguments\n')

    @unittest.skipUnless(os.name == 'posix', 'Private evidence requires owner-only POSIX files.')
    def test_cli_missing_malformed_insecure_or_symlink_evidence_has_fixed_refusal(self):
        root, bundle = self.repository(present=False)
        with tempfile.TemporaryDirectory(prefix='activity-private-') as folder:
            parent = Path(folder)
            parent.chmod(0o700)
            bad = parent / 'bad.json'
            bad.write_bytes(b'{')
            bad.chmod(0o600)
            insecure = parent / 'insecure.json'
            insecure.write_bytes(encoded(bundle))
            insecure.chmod(0o644)
            alias = parent / 'alias.json'
            alias.symlink_to(bad)
            for path in (bad, parent / 'missing.json', insecure, alias):
                with self.subTest(path=path.name):
                    out, err = io.StringIO(), io.StringIO()
                    with patch('tracker.release_readiness.REPO_ROOT', root), redirect_stdout(out), redirect_stderr(err):
                        code = main(['--format', 'json', '--activity-review', str(path)])
                    self.assertEqual(code, 2)
                    self.assertEqual(out.getvalue(), '')
                    self.assertEqual(err.getvalue(), 'invalid_release_readiness_activity_evidence\n')
                    self.assertNotIn(str(parent), err.getvalue())

    def cli_copies(self, root, bundle):
        with tempfile.TemporaryDirectory(prefix='activity-private-') as folder:
            parent = Path(folder)
            parent.chmod(0o700)
            paths = []
            for name in ('synthetic-review', 'synthetic-recovered'):
                directory = parent / name
                directory.mkdir(mode=0o700)
                path = directory / 'activities.json'
                path.write_bytes(encoded(bundle))
                path.chmod(0o600)
                paths.append(path)
            before = [(path.read_bytes(), path.stat().st_mtime_ns) for path in paths]
            out, err = io.StringIO(), io.StringIO()
            with patch('tracker.release_readiness.REPO_ROOT', root), patch.dict(os.environ, {}, clear=True), \
                    patch.object(socket, 'socket', side_effect=AssertionError('Network is forbidden')), \
                    redirect_stdout(out), redirect_stderr(err):
                code = main(['--format', 'json', '--activity-review', str(paths[0]),
                             '--activity-backup', str(paths[1])])
            self.assertEqual(code, 1)
            self.assertEqual(err.getvalue(), '')
            report = json.loads(out.getvalue())
            self.assertTrue(self.gate(report, 'durable_source_review')['evidence']['public_activities_match_review'])
            self.assertTrue(self.gate(report, 'storage_backup')['evidence']['activity_backup_matches_review'])
            self.assertNotIn(str(parent), out.getvalue())
            self.assertEqual(before, [(path.read_bytes(), path.stat().st_mtime_ns) for path in paths])
            self.assertEqual(sorted(path.name for path in parent.rglob('*') if path.is_file()),
                             ['activities.json', 'activities.json'])
            return report

    @unittest.skipUnless(os.name == 'posix', 'Private evidence requires owner-only POSIX files.')
    def test_cli_verifies_actual_distinct_copies_without_credentials_or_writes(self):
        root, bundle = self.repository()
        report = self.cli_copies(root, bundle)
        self.assertFalse(report['network_performed'])
        self.assertFalse(report['writes_performed'])

    @unittest.skipUnless(os.name == 'posix', 'Large private evidence requires POSIX files.')
    def test_large_valid_public_projection_and_bundle_exceed_legacy_bounds(self):
        bundle = bundle_fixture(large=True)
        self.assertGreater(len(encoded(bundle['public_activities'])), 10 * 1024 * 1024)
        self.assertGreater(len(encoded(bundle)), 8 * 1024 * 1024)
        root, bundle = self.repository(bundle)
        report = self.report(root, activity_review=bundle, activity_backup=copy.deepcopy(bundle))
        self.assertTrue(report['release_ready'])
        self.assertEqual(self.gate(report, 'source_rights')['evidence']['activity_records_covered'], 200)
        recovered = self.cli_copies(root, bundle)
        self.assertTrue(self.gate(recovered, 'durable_source_review')['evidence']['public_activities_match_review'])


if __name__ == '__main__':
    unittest.main()
