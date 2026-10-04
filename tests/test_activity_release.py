"""Synthetic exact activity review, private recovery and paired promotion only."""
import copy
import importlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tracker.park_activities import PILOT_CODES, collect_activities, initial_activities
from test_activity_checkpoints import bind, checkpoint_fixture, encoded
from test_park_activities import T0, T1, T2, activity, page, rehash

REVIEWED = '2026-10-03T13:00:00Z'
APPROVED = '2026-10-03T14:00:00Z'
PUBLIC_FILES = ('data/park-activities.json', 'data/activity-source-rights.json')


def projection(checkpoint):
    return {'schema_version': 1, 'purpose': 'public_park_activities',
            'inventories': copy.deepcopy(checkpoint['inventories'])}


def rights_fixture(dataset, reviewed_at=REVIEWED):
    return {'schema_version': 1, 'purpose': 'public_park_activity_text_rights',
            'reviewed_at': reviewed_at,
            'review_method': 'official_nps_policy_and_exact_activity_review',
            'policy': {
                'ownership_url': 'https://www.nps.gov/aboutus/disclaimer.htm',
                'marks_url': 'https://www.nps.gov/subjects/partnerships/arrowhead-requests.htm?fullweb=1',
                'commercial_notice': 'No protection is claimed in original U.S. Government works.',
                'third_party_material_allowed': False, 'nps_marks_allowed': False,
                'raw_private_captures_public': False},
            'records': [{'park_code': inventory['park_code'], 'activity_id': record['id'],
                         'source_url': inventory['source_url'], 'content_hash': record['content_hash'],
                         'classification': 'nps_government_text',
                         'use_scope': 'normalized_activity_text_and_metadata',
                         'third_party_material_reproduced': False, 'nps_marks_reproduced': False,
                         'media_reproduced': False}
                        for inventory in dataset['inventories'] for record in inventory['records']]}


def release_fixture(model, checkpoint=None):
    checkpoint = checkpoint_fixture() if checkpoint is None else checkpoint
    return model.build_release_bundle(checkpoint, rights_fixture(projection(checkpoint)), APPROVED)


def advanced_checkpoint(previous, now=T1, *, raw_by_code=None, failed=False):
    def fetch(code):
        if failed:
            def refuse(_start):
                raise TimeoutError('Synthetic private error')
            return refuse
        raw = [activity(code=code)] if raw_by_code is None else raw_by_code[code]
        return lambda _start: page(raw, limit=max(50, len(raw)))
    return bind({'schema_version': 1, 'purpose': 'private_park_activity_checkpoint',
                 'parent_checkpoint_id': previous['checkpoint_id'], 'checked_at': now,
                 'inventories': [collect_activities(code, inventory, now, fetch(code))
                                for code, inventory in zip(PILOT_CODES, previous['inventories'])]})


def current_pair(bundle, *, newline=True):
    suffix = b'\n' if newline else b''
    return dict(zip(PUBLIC_FILES, (encoded(bundle['public_activities']) + suffix,
                                  encoded(bundle['rights']) + suffix)))


class ActivityReleaseModelTests(unittest.TestCase):
    def adapter(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.activity_release'),
                             'The reviewed activity release contract is not implemented.')
        return importlib.import_module('tracker.activity_release')

    def test_bundle_binds_complete_checkpoint_projection_rights_and_approval(self):
        model = self.adapter()
        checkpoint = checkpoint_fixture()
        bundle = release_fixture(model, checkpoint)
        self.assertEqual(set(bundle), {'schema_version', 'purpose', 'checkpoint',
                                      'public_activities', 'rights', 'approval', 'bundle_id'})
        self.assertEqual(bundle['purpose'], 'private_reviewed_park_activities')
        self.assertEqual(bundle['checkpoint'], checkpoint)
        self.assertEqual(bundle['public_activities'], projection(checkpoint))
        self.assertEqual(model.validate_release_bundle(bundle), bundle)
        self.assertEqual(len(bundle['rights']['records']), 5)  # Repeated ID in five parks.
        self.assertEqual(bundle['approval']['decision'], 'approved')
        self.assertEqual(bundle['approval']['checkpoint_id'], checkpoint['checkpoint_id'])
        bundle['checkpoint']['inventories'][0]['records'][0]['credit'] = 'Caller mutation'
        self.assertNotEqual(bundle['checkpoint'], checkpoint)

    def test_tampered_envelopes_remain_refused_after_outer_rehash(self):
        model = self.adapter()
        bundle = release_fixture(model)
        def changed_lineage(value):
            value['checkpoint']['parent_checkpoint_id'] = '0' * 64
            bind(value['checkpoint'])  # Valid checkpoint still disagrees with the approval binding.
        changes = [
            changed_lineage,
            lambda b: b['public_activities']['inventories'][0]['records'][0].update(credit='Altered'),
            lambda b: b['rights']['records'][0].update(content_hash='0' * 64),
            lambda b: b['approval'].update(projection_hash='0' * 64),
            lambda b: b.update(extra='private text'),
        ]
        for change in changes:
            candidate = copy.deepcopy(bundle)
            change(candidate)
            candidate['bundle_id'] = model.activity_digest(
                {k: v for k, v in candidate.items() if k != 'bundle_id'}, max_bytes=model.MAX_BUNDLE_BYTES)
            with self.subTest(change=change), self.assertRaises(model.ActivityReleaseError):
                model.validate_release_bundle(candidate)
        bundle['bundle_id'] = '0' * 64
        with self.assertRaises(model.ActivityReleaseError):
            model.validate_release_bundle(bundle)

    def test_valid_later_projection_requires_a_new_full_projection_approval_hash(self):
        model = self.adapter()
        candidate = release_fixture(model)
        later = advanced_checkpoint(candidate['checkpoint'])
        candidate['checkpoint'] = later
        candidate['public_activities'] = projection(later)
        candidate['approval']['checkpoint_id'] = later['checkpoint_id']
        candidate['bundle_id'] = model.activity_digest(
            {k: v for k, v in candidate.items() if k != 'bundle_id'}, max_bytes=model.MAX_BUNDLE_BYTES)
        # Record semantics and rights stay the same; every refreshed clock is still reviewed.
        with self.assertRaises(model.ActivityReleaseError):
            model.validate_release_bundle(candidate)

    def test_approval_requires_exact_bindings_and_time_after_review(self):
        model = self.adapter()
        bundle = release_fixture(model)
        for field, value in [('decision', 'pending'), ('approved_at', T0),
                             ('checkpoint_id', '0' * 64), ('rights_hash', '0' * 64),
                             ('projection_hash', '0' * 64)]:
            candidate = copy.deepcopy(bundle)
            candidate['approval'][field] = value
            candidate['bundle_id'] = model.activity_digest(
                {k: v for k, v in candidate.items() if k != 'bundle_id'}, max_bytes=model.MAX_BUNDLE_BYTES)
            with self.subTest(field=field), self.assertRaises(model.ActivityReleaseError):
                model.validate_release_bundle(candidate)
        with self.assertRaises(model.ActivityReleaseError):
            model.build_release_bundle(checkpoint_fixture(), bundle['rights'], T0)

    def test_reviewed_bundle_preserves_confirmed_empty_and_degraded_state(self):
        model = self.adapter()
        empty = checkpoint_fixture()
        empty['inventories'][0] = collect_activities('yose', initial_activities('yose'), T0,
                                                    lambda _start: page([]))
        bind(empty)
        failed = advanced_checkpoint(empty, failed=True)
        bundle = release_fixture(model, failed)
        self.assertEqual(bundle['public_activities']['inventories'], failed['inventories'])
        self.assertEqual(bundle['public_activities']['inventories'][0]['records'], [])
        self.assertEqual(bundle['public_activities']['inventories'][0]['last_successful_fetch_at'], T0)
        self.assertEqual(len(bundle['rights']['records']), 4)

    def test_fixed_pair_and_exact_canonical_base_required(self):
        model = self.adapter()
        bundle = release_fixture(model)
        absent = dict.fromkeys(PUBLIC_FILES)
        result = model.build_promotion(bundle, absent)
        self.assertEqual(result['patch'].count(b'diff --git '), 2)
        self.assertNotIn(b'parent_checkpoint_id', result['patch'])
        self.assertNotIn(b'private_reviewed_park_activities', result['patch'])
        malformed = [dict.fromkeys(PUBLIC_FILES, b'{}'), {PUBLIC_FILES[0]: None},
                     {**absent, PUBLIC_FILES[0]: current_pair(bundle)[PUBLIC_FILES[0]]},
                     {**current_pair(bundle), PUBLIC_FILES[0]: encoded(bundle['public_activities']) + b'\r\n'},
                     {**current_pair(bundle), PUBLIC_FILES[1]: b'{"purpose":1,"purpose":2}'},
                     {**current_pair(bundle), PUBLIC_FILES[0]: b'[]'},
                     {**current_pair(bundle), PUBLIC_FILES[0]: b'\xff'}]
        for base in malformed:
            with self.subTest(base=base), self.assertRaises(model.ActivityReleaseError):
                model.build_promotion(bundle, base)

    def test_identity_binds_bundle_base_newline_and_patch(self):
        model = self.adapter()
        bundle = release_fixture(model)
        initial = model.build_promotion(bundle, dict.fromkeys(PUBLIC_FILES))
        final_lf = model.build_promotion(bundle, current_pair(bundle))
        no_lf = model.build_promotion(bundle, current_pair(bundle, newline=False))
        self.assertNotEqual(final_lf['receipt']['candidate_id'], no_lf['receipt']['candidate_id'])
        self.assertNotEqual(initial['receipt']['candidate_id'], final_lf['receipt']['candidate_id'])
        self.assertEqual(set(initial['receipt']['base_hashes']), set(PUBLIC_FILES))
        self.assertTrue(all(v is None for v in initial['receipt']['base_hashes'].values()))

    def test_same_attempt_requires_entire_inventory_and_rewinds_refused(self):
        model = self.adapter()
        baseline = release_fixture(model)
        for mutate in (lambda cp: cp['inventories'][0]['records'][0].update(credit='Changed credit'),
                       lambda cp: cp['inventories'][0]['records'][0].update(observed_first_at='2026-10-03T09:00:00Z'),
                       lambda cp: cp['inventories'][0].update(collection_status='failed',
                           coverage_status='incomplete', error_code='provider_request_failed')):
            checkpoint = checkpoint_fixture()
            mutate(checkpoint)
            rehash(checkpoint['inventories'][0]['records'][0])
            candidate = release_fixture(model, bind(checkpoint))
            with self.assertRaises(model.ActivityReleaseError):
                model.build_promotion(candidate, current_pair(baseline))
        later = release_fixture(model, advanced_checkpoint(checkpoint_fixture()))
        with self.assertRaises(model.ActivityReleaseError):
            model.build_promotion(baseline, current_pair(later))
        same_instant = checkpoint_fixture('2026-10-03T06:00:00-04:00')
        with self.assertRaises(model.ActivityReleaseError):
            model.build_promotion(release_fixture(model, same_instant), current_pair(baseline))

    def test_retained_first_and_unchanged_changed_observation_are_preserved(self):
        model = self.adapter()
        baseline = release_fixture(model)
        good = advanced_checkpoint(checkpoint_fixture())
        model.build_promotion(release_fixture(model, good), current_pair(baseline))
        for field, value in [('observed_first_at', '2026-10-03T09:00:00Z'),
                             ('observed_changed_at', T1)]:
            checkpoint = copy.deepcopy(good)
            checkpoint['inventories'][0]['records'][0][field] = value
            candidate = release_fixture(model, bind(checkpoint))
            with self.subTest(field=field), self.assertRaises(model.ActivityReleaseError):
                model.build_promotion(candidate, current_pair(baseline))

    def test_fork_cannot_hide_changes_or_new_ids_observed_before_public_success(self):
        model = self.adapter()
        first = checkpoint_fixture()
        public = advanced_checkpoint(first, T1)
        for replaced in (False, True):
            raws = {code: [activity('new' if replaced else 'synthetic-a', code=code,
                                   title='Synthetic changed title')] for code in PILOT_CODES}
            fork = advanced_checkpoint(first, '2026-10-03T10:30:00Z', raw_by_code=raws)
            later = advanced_checkpoint(fork, T2, raw_by_code=raws)
            with self.subTest(replaced=replaced), self.assertRaises(model.ActivityReleaseError):
                model.build_promotion(release_fixture(model, later), current_pair(release_fixture(model, public)))
            after_public = advanced_checkpoint(public, '2026-10-03T11:30:00Z', raw_by_code=raws)
            valid = advanced_checkpoint(after_public, T2, raw_by_code=raws)
            model.build_promotion(release_fixture(model, valid), current_pair(release_fixture(model, public)))

    def test_degraded_promotion_preserves_exact_public_last_good_success(self):
        model = self.adapter()
        first = checkpoint_fixture()
        baseline = release_fixture(model, first)
        degraded = advanced_checkpoint(first, failed=True)
        model.build_promotion(release_fixture(model, degraded), current_pair(baseline))
        intermediate = advanced_checkpoint(first)
        unsupported = advanced_checkpoint(intermediate, T2, failed=True)
        with self.assertRaises(model.ActivityReleaseError):
            model.build_promotion(release_fixture(model, unsupported), current_pair(baseline))
        changed = copy.deepcopy(degraded)
        changed['inventories'][0]['records'][0]['credit'] = 'Altered last-good evidence'
        rehash(changed['inventories'][0]['records'][0])
        with self.assertRaises(model.ActivityReleaseError):
            model.build_promotion(release_fixture(model, bind(changed)), current_pair(baseline))

    def test_public_half_drop_guard_applies_to_valid_private_fork(self):
        model = self.adapter()
        baseline = checkpoint_fixture()
        for inventory in baseline['inventories']:
            inventory['records'] = [copy.deepcopy(inventory['records'][0]) for _ in range(5)]
            for i, record in enumerate(inventory['records']):
                record['id'] = f'synthetic-{i}'
                rehash(record)
        bind(baseline)
        for count in (0, 2, 3):
            candidate = checkpoint_fixture(T1)
            for before, after in zip(baseline['inventories'], candidate['inventories']):
                after['records'] = copy.deepcopy(before['records'][:count])
            bind(candidate)  # Self-contained valid fork; no public replay proof.
            if count < 3:
                with self.subTest(count=count), self.assertRaises(model.ActivityReleaseError):
                    model.build_promotion(release_fixture(model, candidate), current_pair(release_fixture(model, baseline)))
            else:
                model.build_promotion(release_fixture(model, candidate), current_pair(release_fixture(model, baseline)))

    def test_exact_bundle_and_patch_limits_have_no_legacy_defaults(self):
        model = self.adapter()
        from tracker.activity_checkpoints import MAX_CHECKPOINT_BYTES
        from tracker.activity_public import MAX_PUBLIC_BYTES, MAX_RIGHTS_BYTES
        self.assertEqual(model.MAX_BUNDLE_BYTES, MAX_CHECKPOINT_BYTES + MAX_PUBLIC_BYTES + MAX_RIGHTS_BYTES + 65536)
        self.assertEqual(model.MAX_PATCH_BYTES, 2 * (MAX_PUBLIC_BYTES + MAX_RIGHTS_BYTES + 2) + 65536)
        checkpoint = checkpoint_fixture()
        bundle = release_fixture(model, checkpoint)
        with patch.object(model, 'MAX_BUNDLE_BYTES', len(encoded(bundle))):
            model.validate_release_bundle(bundle)
        with patch.object(model, 'MAX_BUNDLE_BYTES', len(encoded(bundle)) - 1):
            with self.assertRaises(model.ActivityReleaseError):
                model.validate_release_bundle(bundle)
        result = model.build_promotion(bundle, dict.fromkeys(PUBLIC_FILES))
        with patch.object(model, 'MAX_PATCH_BYTES', len(result['patch'])):
            model.build_promotion(bundle, dict.fromkeys(PUBLIC_FILES))
        with patch.object(model, 'MAX_PATCH_BYTES', len(result['patch']) - 1):
            with self.assertRaises(model.ActivityReleaseError):
                model.build_promotion(bundle, dict.fromkeys(PUBLIC_FILES))


@unittest.skipUnless(os.name == 'posix', 'Private activity releases require POSIX.')
class ActivityReleaseStorageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.root.chmod(0o700)
        self.repo = self.root / 'synthetic-repo'
        (self.repo / 'data').mkdir(parents=True)
        self.output = self.root / 'reviewed.json'

    def adapter(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.activity_release'))
        return importlib.import_module('tracker.activity_release')

    def write(self, value, name):
        path = self.root / name
        path.write_bytes(encoded(value))
        path.chmod(0o600)
        return path

    def inputs(self, model, *, checkpoint=None, checkpoint_name='checkpoint.json', rights_name='rights.json'):
        checkpoint = checkpoint_fixture() if checkpoint is None else checkpoint
        return (self.write(checkpoint, checkpoint_name),
                self.write(rights_fixture(projection(checkpoint)), rights_name))

    def bundle_path(self, model):
        return self.write(release_fixture(model), 'bundle.json')

    def test_explicit_approval_verify_and_fresh_restore_preserve_private_bytes(self):
        model = self.adapter()
        checkpoint, rights = self.inputs(model)
        before = checkpoint.read_bytes(), rights.read_bytes()
        for approval in (False, 1, None):
            with self.subTest(approval=approval), self.assertRaises(model.ActivityReleaseError):
                model.create_release_bundle(checkpoint, rights, self.output, APPROVED, approve=approval)
            self.assertFalse(self.output.exists())
            self.assertFalse(Path(str(self.output) + '.lock').exists())
        bundle = model.create_release_bundle(checkpoint, rights, self.output, APPROVED, approve=True)
        self.assertEqual(model.verify_release_bundle(self.output), bundle)
        self.assertEqual(self.output.read_bytes(), encoded(bundle))
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.output.stat().st_nlink, 1)
        with self.assertRaises(model.ActivityReleaseError):
            model.create_release_bundle(checkpoint, rights, self.output, APPROVED, approve=True)
        restored = self.root / 'restored.json'
        self.assertEqual(model.restore_release_bundle(self.output, restored), bundle)
        self.assertEqual(restored.read_bytes(), self.output.read_bytes())
        self.assertEqual((checkpoint.read_bytes(), rights.read_bytes()), before)
        with self.assertRaises(model.ActivityReleaseError):
            model.restore_release_bundle(self.output, restored)

    def test_checkpoint_and_rights_cannot_alias_destination_or_lock(self):
        model = self.adapter()
        for source_kind in ('checkpoint', 'rights'):
            for lock in (False, True):
                name = f'{source_kind}-{lock}.json'
                output = self.root / name
                source_name = name + '.lock' if lock else name
                cp_name = source_name if source_kind == 'checkpoint' else f'cp-{source_kind}-{lock}.json'
                rights_name = source_name if source_kind == 'rights' else f'rights-{source_kind}-{lock}.json'
                checkpoint, rights = self.inputs(model, checkpoint_name=cp_name, rights_name=rights_name)
                before = {checkpoint: checkpoint.read_bytes(), rights: rights.read_bytes()}
                names = sorted(self.root.iterdir())
                with self.subTest(source_kind=source_kind, lock=lock), self.assertRaises(model.ActivityReleaseError):
                    model.create_release_bundle(checkpoint, rights, output, APPROVED, approve=True)
                self.assertEqual(sorted(self.root.iterdir()), names)
                for source, data in before.items():
                    self.assertEqual(source.read_bytes(), data)

    def test_invalid_rights_size_and_bundle_bounds_refuse_before_locks(self):
        model = self.adapter()
        checkpoint, rights = self.inputs(model)
        manifest = json.loads(rights.read_text())
        manifest['records'].pop()
        rights.write_bytes(encoded(manifest))
        names = sorted(self.root.iterdir())
        with self.assertRaises(model.ActivityReleaseError):
            model.create_release_bundle(checkpoint, rights, self.output, APPROVED, approve=True)
        self.assertEqual(sorted(self.root.iterdir()), names)
        rights.write_bytes(encoded(rights_fixture(projection(checkpoint_fixture()))))
        with patch.object(model, 'MAX_BUNDLE_BYTES', 100), self.assertRaises(model.ActivityReleaseError):
            model.create_release_bundle(checkpoint, rights, self.output, APPROVED, approve=True)
        self.assertEqual(sorted(self.root.iterdir()), names)
        with patch.object(model, 'MAX_RIGHTS_BYTES', 100), self.assertRaises(model.ActivityReleaseError):
            model.create_release_bundle(checkpoint, rights, self.output, APPROVED, approve=True)
        self.assertEqual(sorted(self.root.iterdir()), names)

    def test_insecure_nonregular_hardlink_and_symlink_inputs_refused(self):
        model = self.adapter()
        for kind in ('checkpoint', 'rights'):
            checkpoint, rights = self.inputs(model, checkpoint_name=f'{kind}-cp.json', rights_name=f'{kind}-rights.json')
            source = checkpoint if kind == 'checkpoint' else rights
            source.chmod(0o644)
            with self.subTest(kind=kind), self.assertRaises(model.ActivityReleaseError):
                model.create_release_bundle(checkpoint, rights, self.output, APPROVED, approve=True)
            source.chmod(0o600)
            link = self.root / f'{kind}-hardlink'
            os.link(source, link)
            with self.assertRaises(model.ActivityReleaseError):
                model.create_release_bundle(checkpoint, rights, self.output, APPROVED, approve=True)
            link.unlink()
            symlink = self.root / f'{kind}-symlink'
            symlink.symlink_to(source)
            arguments = (symlink, rights) if kind == 'checkpoint' else (checkpoint, symlink)
            with self.assertRaises(model.ActivityReleaseError):
                model.create_release_bundle(*arguments, self.output, APPROVED, approve=True)
        directory = self.root / 'input-directory'
        directory.mkdir(mode=0o700)
        with self.assertRaises(model.ActivityReleaseError):
            model.verify_release_bundle(directory)
        self.assertFalse(self.output.exists())

    def test_private_parent_checkout_alias_and_relative_paths_refused(self):
        model = self.adapter()
        source = self.bundle_path(model)
        self.root.chmod(0o755)
        with self.assertRaises(model.ActivityReleaseError):
            model.restore_release_bundle(source, self.output)
        self.root.chmod(0o700)
        from tracker.entry_review_io import REPO_ROOT
        for output in (Path('relative.json'), REPO_ROOT / 'ignored-private.json',
                       Path('//' + str(REPO_ROOT).lstrip('/')) / 'ignored-private.json',
                       self.root / 'missing' / 'out.json', self.root / '..' / 'traversal.json'):
            with self.subTest(output=output), self.assertRaises(model.ActivityReleaseError):
                model.restore_release_bundle(source, output)

    def test_exclusive_lock_is_never_stolen_and_output_not_overwritten(self):
        model = self.adapter()
        source = self.bundle_path(model)
        lock = self.root / 'reviewed.json.lock'
        lock.write_bytes(b'Synthetic active writer')
        lock.chmod(0o600)
        with self.assertRaises(model.ActivityReleaseError):
            model.restore_release_bundle(source, self.output)
        self.assertEqual(lock.read_bytes(), b'Synthetic active writer')
        self.assertFalse(self.output.exists())
        lock.unlink()
        with model.locked_private_output(self.output, source):
            with self.assertRaises(model.ActivityReleaseError):
                model.restore_release_bundle(source, self.output)
        self.assertFalse(lock.exists())

    def test_inode_changed_bundle_or_patch_refused(self):
        model = self.adapter()
        source = self.bundle_path(model)
        with patch('tracker.entry_review_io.os.fstat', return_value=SimpleNamespace(st_dev=-1, st_ino=-1)):
            with self.assertRaises(model.ActivityReleaseError):
                model.verify_release_bundle(source)
        output = self.root / 'promotion.patch'
        receipt = model.prepare_promotion(source, output, root=self.repo)
        # Verify the bundle normally, then simulate an inode swap in the patch reader.
        real_verify = model.verify_release_bundle
        with patch.object(model, 'verify_release_bundle', return_value=real_verify(source)), \
             patch.object(model.os, 'fstat', return_value=SimpleNamespace(st_dev=-1, st_ino=-1)):
            with self.assertRaises(model.ActivityReleaseError):
                model.check_promotion(source, output, receipt['candidate_id'], root=self.repo)

    def test_precommit_error_cleans_files_postcommit_interruption_preserves_output(self):
        model = self.adapter()
        checkpoint, rights = self.inputs(model)
        names = sorted(self.root.iterdir())
        with patch('tracker.private_checkpoint_io.os.link', side_effect=OSError('Synthetic private filesystem error')):
            with self.assertRaises(model.ActivityReleaseError):
                model.create_release_bundle(checkpoint, rights, self.output, APPROVED, approve=True)
        self.assertEqual(sorted(self.root.iterdir()), names)
        with patch('tracker.private_checkpoint_io.sync_private_directory', side_effect=KeyboardInterrupt('Synthetic private sync')):
            with self.assertRaises(KeyboardInterrupt):
                model.create_release_bundle(checkpoint, rights, self.output, APPROVED, approve=True)
        self.assertEqual(model.verify_release_bundle(self.output), release_fixture(model))
        self.assertFalse(Path(str(self.output) + '.lock').exists())

    def test_cleanup_failure_preserves_multilink_output_for_operator_inspection(self):
        model = self.adapter()
        source = self.bundle_path(model)
        original_unlink = Path.unlink
        def interrupted_unlink(path, *args, **kwargs):
            if path.name.startswith('.checkpoint-'):
                raise OSError('Synthetic private cleanup error')
            return original_unlink(path, *args, **kwargs)
        with patch.object(Path, 'unlink', interrupted_unlink), self.assertRaises(model.ActivityReleaseError):
            model.restore_release_bundle(source, self.output)
        self.assertEqual(self.output.read_bytes(), source.read_bytes())
        self.assertEqual(self.output.stat().st_nlink, 2)
        with self.assertRaises(model.ActivityReleaseError):
            model.verify_release_bundle(self.output)
        self.assertFalse(Path(str(self.output) + '.lock').exists())
        self.assertEqual(len(list(self.root.glob('.checkpoint-*.tmp'))), 1)

    def test_prepare_check_is_read_only_and_detects_patch_base_and_bundle_tampering(self):
        model = self.adapter()
        source = self.bundle_path(model)
        output = self.root / 'promotion.patch'
        receipt = model.prepare_promotion(source, output, root=self.repo)
        original = output.read_bytes()
        self.assertEqual(model.check_promotion(source, output, receipt['candidate_id'], root=self.repo), receipt)
        self.assertEqual(list((self.repo / 'data').iterdir()), [])
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        for candidate_id in ('0' * 64, 'private invalid text'):
            with self.assertRaises(model.ActivityReleaseError):
                model.check_promotion(source, output, candidate_id, root=self.repo)
        output.write_bytes(original + b'\n')
        with self.assertRaises(model.ActivityReleaseError):
            model.check_promotion(source, output, receipt['candidate_id'], root=self.repo)
        output.write_bytes(original)
        (self.repo / PUBLIC_FILES[0]).write_bytes(encoded(release_fixture(model)['public_activities']))
        with self.assertRaises(model.ActivityReleaseError):
            model.check_promotion(source, output, receipt['candidate_id'], root=self.repo)
        (self.repo / PUBLIC_FILES[1]).write_bytes(encoded(release_fixture(model)['rights']))
        with self.assertRaises(model.ActivityReleaseError):
            model.check_promotion(source, output, receipt['candidate_id'], root=self.repo)
        alternate = release_fixture(model)
        alternate['approval']['approved_at'] = '2026-10-03T15:00:00Z'
        alternate['bundle_id'] = model.activity_digest(
            {k: v for k, v in alternate.items() if k != 'bundle_id'}, max_bytes=model.MAX_BUNDLE_BYTES)
        source.write_bytes(encoded(alternate))
        with self.assertRaises(model.ActivityReleaseError):
            model.check_promotion(source, output, receipt['candidate_id'], root=self.repo)

    def test_public_newline_change_invalidates_fresh_candidate(self):
        model = self.adapter()
        bundle = release_fixture(model)
        for name, data in current_pair(bundle, newline=False).items():
            (self.repo / name).write_bytes(data)
        source = self.bundle_path(model)
        output = self.root / 'promotion.patch'
        receipt = model.prepare_promotion(source, output, root=self.repo)
        changed = self.repo / PUBLIC_FILES[0]
        changed.write_bytes(changed.read_bytes() + b'\n')
        with self.assertRaises(model.ActivityReleaseError):
            model.check_promotion(source, output, receipt['candidate_id'], root=self.repo)

    def test_patch_read_limit_and_permissions_refused(self):
        model = self.adapter()
        source = self.bundle_path(model)
        output = self.root / 'promotion.patch'
        receipt = model.prepare_promotion(source, output, root=self.repo)
        output.chmod(0o644)
        with self.assertRaises(model.ActivityReleaseError):
            model.check_promotion(source, output, receipt['candidate_id'], root=self.repo)
        output.chmod(0o600)
        # Hold regeneration fixed to exercise the independent on-disk patch read bound.
        candidate = {'receipt': receipt, 'patch': output.read_bytes()}
        with patch.object(model, 'build_promotion', return_value=candidate), \
             patch.object(model, 'MAX_PATCH_BYTES', output.stat().st_size - 1), \
             self.assertRaises(model.ActivityReleaseError):
            model.check_promotion(source, output, receipt['candidate_id'], root=self.repo)

    def test_restore_and_patch_source_lock_collisions_preserve_inputs(self):
        model = self.adapter()
        for operation in (model.restore_release_bundle, model.prepare_promotion):
            for collision in ('destination', 'lock'):
                output = self.root / f'{operation.__name__}-{collision}.json'
                source = self.write(release_fixture(model), output.name + ('.lock' if collision == 'lock' else ''))
                before = source.read_bytes(), source.stat().st_mtime_ns
                arguments = {'root': self.repo} if operation == model.prepare_promotion else {}
                with self.subTest(operation=operation.__name__, collision=collision), \
                     self.assertRaises(model.ActivityReleaseError):
                    operation(source, output, **arguments)
                self.assertEqual((source.read_bytes(), source.stat().st_mtime_ns), before)

    def test_prepare_rejects_public_symlink_and_incomplete_pair_before_output_lock(self):
        model = self.adapter()
        source = self.bundle_path(model)
        output = self.root / 'promotion.patch'
        public = self.repo / PUBLIC_FILES[0]
        public.symlink_to(source)
        with self.assertRaises(model.ActivityReleaseError):
            model.prepare_promotion(source, output, root=self.repo)
        public.unlink()
        public.mkdir()
        with self.assertRaises(model.ActivityReleaseError):
            model.prepare_promotion(source, output, root=self.repo)
        public.rmdir()
        public.write_bytes(encoded(release_fixture(model)['public_activities']))
        with self.assertRaises(model.ActivityReleaseError):
            model.prepare_promotion(source, output, root=self.repo)
        self.assertFalse(output.exists())
        self.assertFalse(Path(str(output) + '.lock').exists())

    def test_real_git_initial_and_replacement_patch_apply_in_synthetic_private_repo(self):
        model = self.adapter()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True, capture_output=True)
        first = release_fixture(model)
        source = self.write(first, 'first.json')
        output = self.root / 'first.patch'
        receipt = model.prepare_promotion(source, output, root=self.repo)
        model.check_promotion(source, output, receipt['candidate_id'], root=self.repo)
        for command in (['git', 'apply', '--check', str(output)], ['git', 'apply', str(output)]):
            subprocess.run(command, cwd=self.repo, check=True, capture_output=True)
        self.assertEqual({name: (self.repo / name).read_bytes() for name in PUBLIC_FILES}, current_pair(first))
        # A valid no-final-LF base exercises the patch's no-newline marker.
        for name, data in current_pair(first, newline=False).items():
            (self.repo / name).write_bytes(data)
        second = release_fixture(model, advanced_checkpoint(checkpoint_fixture()))
        second_source = self.write(second, 'second.json')
        second_output = self.root / 'second.patch'
        receipt = model.prepare_promotion(second_source, second_output, root=self.repo)
        self.assertIn(b'\\ No newline at end of file\n', second_output.read_bytes())
        model.check_promotion(second_source, second_output, receipt['candidate_id'], root=self.repo)
        for command in (['git', 'apply', '--check', str(second_output)], ['git', 'apply', str(second_output)]):
            subprocess.run(command, cwd=self.repo, check=True, capture_output=True)
        self.assertEqual({name: (self.repo / name).read_bytes() for name in PUBLIC_FILES}, current_pair(second))

    def test_large_batch_over_legacy_limits_encodes_verifies_restores_and_replaces(self):
        model = self.adapter()
        large = checkpoint_fixture()
        for code, inventory in zip(PILOT_CODES, large['inventories']):
            raw = [activity(f'synthetic-{i:02}', code=code, shortDescription='s' * 60000,
                            longDescription='l' * 65536) for i in range(18)]
            large['inventories'][PILOT_CODES.index(code)] = collect_activities(
                code, initial_activities(code), T0, lambda _start, raw=raw: page(raw))
        bind(large)
        checkpoint, rights = self.inputs(model, checkpoint=large)
        self.assertGreater(checkpoint.stat().st_size, 10 * 1024 * 1024)
        bundle = model.create_release_bundle(checkpoint, rights, self.output, APPROVED, approve=True)
        self.assertGreater(self.output.stat().st_size, 20 * 1024 * 1024)
        self.assertEqual(model.verify_release_bundle(self.output)['bundle_id'], bundle['bundle_id'])
        restored = self.root / 'restored-large.json'
        model.restore_release_bundle(self.output, restored)
        self.assertEqual(restored.read_bytes(), self.output.read_bytes())
        replacement = copy.deepcopy(large)
        replacement['checked_at'] = T1
        replacement['parent_checkpoint_id'] = large['checkpoint_id']
        for inventory in replacement['inventories']:
            inventory.update(last_checked_at=T1, last_successful_fetch_at=T1)
        second = release_fixture(model, bind(replacement))
        for name, data in current_pair(bundle).items():
            (self.repo / name).write_bytes(data)
        second_source = self.write(second, 'second-large.json')
        output = self.root / 'large.patch'
        receipt = model.prepare_promotion(second_source, output, root=self.repo)
        self.assertGreater(output.stat().st_size, 20 * 1024 * 1024)
        self.assertEqual(model.check_promotion(second_source, output, receipt['candidate_id'], root=self.repo), receipt)

    def test_offline_operations_never_read_credentials_or_request_sources(self):
        model = self.adapter()
        checkpoint, rights = self.inputs(model)
        with patch.object(os.environ, 'get', side_effect=AssertionError('Offline key access')), \
             patch('urllib.request.urlopen', side_effect=AssertionError('Offline network access')):
            model.create_release_bundle(checkpoint, rights, self.output, APPROVED, approve=True)
            model.verify_release_bundle(self.output)
            model.restore_release_bundle(self.output, self.root / 'restored.json')
            receipt = model.prepare_promotion(self.output, self.root / 'promotion.patch', root=self.repo)
            model.check_promotion(self.output, self.root / 'promotion.patch', receipt['candidate_id'], root=self.repo)

    def test_cli_sanitizes_errors_disables_abbreviations_and_metadata_reports(self):
        model = self.adapter()
        for arguments in (['verify', '--bundle', '/private/SECRET-source-text.json'],
                          ['verify', '--bun', '/private/SECRET-source-text.json'],
                          ['SECRET-argument'], []):
            output = io.StringIO()
            with redirect_stdout(output):
                status = model.main(arguments)
            self.assertEqual(status, 2)
            self.assertNotIn('SECRET', output.getvalue())
            report = json.loads(output.getvalue())
            self.assertEqual(report['error_code'], 'activity_release_refused')
            for field in ('approval_performed', 'publication_performed', 'site_data_written', 'network_attempted'):
                self.assertIs(report[field], False)
        source = self.bundle_path(model)
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(model.main(['verify', '--bundle', str(source)]), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report['bundle_id'], release_fixture(model)['bundle_id'])
        self.assertEqual(report['park_count'], 5)
        self.assertNotIn(str(self.root), output.getvalue())
        self.assertNotIn('Synthetic', output.getvalue())
        interrupted = io.StringIO()
        with patch.object(model, 'verify_release_bundle', side_effect=KeyboardInterrupt('SECRET interruption')), \
             redirect_stdout(interrupted):
            self.assertEqual(model.main(['verify', '--bundle', str(source)]), 2)
        self.assertEqual(json.loads(interrupted.getvalue())['error_code'], 'activity_release_interrupted')
        self.assertNotIn('SECRET', interrupted.getvalue())

    def test_cli_approval_requires_flag_and_reports_only_successful_decision(self):
        model = self.adapter()
        checkpoint, rights = self.inputs(model)
        arguments = ['approve', '--checkpoint', str(checkpoint), '--rights', str(rights), '--output', str(self.output)]
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(model.main(arguments), 2)
        self.assertIs(json.loads(output.getvalue())['approval_performed'], False)
        self.assertFalse(self.output.exists())
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(model.main(arguments + ['--approve']), 0)
        report = json.loads(output.getvalue())
        self.assertIs(report['approval_performed'], True)
        self.assertEqual(report['bundle_id'], model.verify_release_bundle(self.output)['bundle_id'])
        for field in ('network_attempted', 'publication_performed', 'site_data_written'):
            self.assertIs(report[field], False)
        self.assertNotIn(str(self.root), output.getvalue())
        self.assertNotIn('Synthetic', output.getvalue())

    def test_cli_postinstall_interruption_reports_refusal_without_losing_output(self):
        model = self.adapter()
        checkpoint, rights = self.inputs(model)
        output = io.StringIO()
        with patch('tracker.private_checkpoint_io.sync_private_directory', side_effect=KeyboardInterrupt('SECRET sync')), \
             redirect_stdout(output):
            status = model.main(['approve', '--approve', '--checkpoint', str(checkpoint),
                                 '--rights', str(rights), '--output', str(self.output)])
        self.assertEqual(status, 2)
        report = json.loads(output.getvalue())
        self.assertIs(report['approval_performed'], False)
        self.assertEqual(report['error_code'], 'activity_release_interrupted')
        self.assertEqual(model.verify_release_bundle(self.output)['checkpoint'], checkpoint_fixture())
        self.assertNotIn('SECRET', output.getvalue())


if __name__ == '__main__':
    unittest.main()
