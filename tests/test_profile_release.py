"""Synthetic profile text review and paired publication preparation only."""
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
from unittest.mock import patch

from tracker.history_model import canonical, digest
from test_profile_checkpoints import checkpoint_fixture, NOW, LATER

REVIEWED = '2026-10-03T13:00:00Z'
APPROVED = '2026-10-03T14:00:00Z'


def rights_fixture(dataset, reviewed_at=REVIEWED):
    return {'schema_version': 1, 'purpose': 'public_park_profile_text_rights',
            'reviewed_at': reviewed_at,
            'review_method': 'official_nps_policy_and_exact_profile_review',
            'policy': {
                'ownership_url': 'https://www.nps.gov/aboutus/disclaimer.htm',
                'marks_url': 'https://www.nps.gov/subjects/partnerships/arrowhead-requests.htm?fullweb=1',
                'commercial_notice': 'No protection is claimed in original U.S. Government works.',
                'third_party_material_allowed': False, 'nps_marks_allowed': False,
                'raw_private_captures_public': False},
            'records': [{'park_code': row['park_code'], 'profile_id': row['profile']['id'],
                         'source_url': row['source_url'], 'content_hash': row['profile']['content_hash'],
                         'classification': 'nps_government_text',
                         'use_scope': 'normalized_profile_text_and_category_names',
                         'third_party_material_reproduced': False, 'nps_marks_reproduced': False,
                         'media_reproduced': False} for row in dataset['profiles']]}


def release_fixture(now=NOW):
    from tracker.profile_release import project_checkpoint, build_release_bundle
    checkpoint = checkpoint_fixture(now)
    return build_release_bundle(checkpoint, rights_fixture(project_checkpoint(checkpoint)), APPROVED)


class ProfileReleaseModelTests(unittest.TestCase):
    def adapter(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.profile_release'),
                             'The reviewed public-profile contract is not implemented.')
        return importlib.import_module('tracker.profile_release')

    def test_projection_excludes_private_lineage_and_preserves_clocks(self):
        model = self.adapter()
        checkpoint = checkpoint_fixture()
        projected = model.project_checkpoint(checkpoint)
        self.assertEqual(set(projected), {'schema_version', 'purpose', 'profiles'})
        self.assertEqual(projected['profiles'], checkpoint['profiles'])
        projected['profiles'][0]['profile']['description'] = 'caller mutation'
        self.assertNotEqual(projected['profiles'], checkpoint['profiles'])

    def test_never_observed_profile_cannot_be_published(self):
        model = self.adapter()
        from tracker.park_profiles import collect_profile, initial_profile, ProfileCollectionError
        checkpoint = checkpoint_fixture()
        def failed(_):
            raise ProfileCollectionError('private error')
        checkpoint['profiles'][0] = collect_profile('yose', initial_profile('yose'), NOW, failed)
        checkpoint['checkpoint_id'] = digest({k: v for k, v in checkpoint.items() if k != 'checkpoint_id'})
        with self.assertRaises(model.ProfileReleaseError):
            model.project_checkpoint(checkpoint)

    def test_rights_bind_exact_source_record_hash_and_new_text_use(self):
        model = self.adapter()
        dataset = model.project_checkpoint(checkpoint_fixture())
        manifest = rights_fixture(dataset)
        self.assertEqual(model.validate_profile_rights(manifest, dataset), manifest)
        for field, value in [('content_hash', '0'*64), ('source_url', 'https://example.invalid/'),
                             ('use_scope', 'short_text_excerpt_and_original_summary'),
                             ('media_reproduced', True), ('profile_id', 'other'), ('park_code', 'romo')]:
            candidate = copy.deepcopy(manifest)
            candidate['records'][0][field] = value
            with self.subTest(field=field), self.assertRaises(model.ProfileReleaseError):
                model.validate_profile_rights(candidate, dataset)

    def test_rights_review_cannot_predate_collection(self):
        model = self.adapter()
        dataset = model.project_checkpoint(checkpoint_fixture())
        with self.assertRaises(model.ProfileReleaseError):
            model.validate_profile_rights(rights_fixture(dataset, '2026-10-01T12:00:00Z'), dataset)

    def test_bundle_binds_full_projection_rights_and_checkpoint(self):
        model = self.adapter()
        bundle = release_fixture()
        self.assertEqual(model.validate_release_bundle(bundle), bundle)
        for field in ['checkpoint', 'public_profiles', 'rights', 'approval']:
            candidate = copy.deepcopy(bundle)
            if field == 'checkpoint':
                candidate[field]['parent_checkpoint_id'] = '0'*64
            elif field == 'public_profiles':
                candidate[field]['profiles'][0]['last_checked_at'] = LATER
            elif field == 'rights':
                candidate[field]['reviewed_at'] = APPROVED
            else:
                candidate[field]['projection_hash'] = '0'*64
            candidate['bundle_id'] = digest({k: v for k, v in candidate.items() if k != 'bundle_id'})
            with self.subTest(field=field), self.assertRaises(model.ProfileReleaseError):
                model.validate_release_bundle(candidate)

    def test_approval_requires_later_review_clock_and_explicit_decision(self):
        model = self.adapter()
        bundle = release_fixture()
        for field, value in [('decision', 'pending'), ('approved_at', NOW),
                             ('checkpoint_id', '0'*64), ('rights_hash', '0'*64)]:
            candidate = copy.deepcopy(bundle)
            candidate['approval'][field] = value
            candidate['bundle_id'] = digest({k: v for k, v in candidate.items() if k != 'bundle_id'})
            with self.subTest(field=field), self.assertRaises(model.ProfileReleaseError):
                model.validate_release_bundle(candidate)

    def test_public_pair_rejects_extra_private_fields_and_nonpilot_scope(self):
        model = self.adapter()
        dataset = model.project_checkpoint(checkpoint_fixture())
        for change in [lambda d: d.update(checkpoint_id='0'*64),
                       lambda d: d['profiles'].reverse(),
                       lambda d: d['profiles'].pop(),
                       lambda d: d['profiles'][0].update(published_at=NOW)]:
            candidate = copy.deepcopy(dataset)
            change(candidate)
            with self.assertRaises(model.ProfileReleaseError):
                model.validate_public_profiles(candidate)

    def test_changed_or_replaced_profile_cannot_predate_public_confirmation(self):
        model = self.adapter()
        from tracker.park_profiles import collect_profile, initial_profile
        from test_profile_checkpoints import payload
        for replaced in (False, True):
            with self.subTest(replaced=replaced):
                base = collect_profile('yose', initial_profile('yose'), '2026-10-02T09:00:00Z',
                                       lambda _: payload('yose', 'A'))
                public = collect_profile('yose', base, '2026-10-02T10:00:00Z',
                                         lambda _: payload('yose', 'A'))
                def branch_payload(_):
                    result = payload('yose', 'B')
                    if replaced:
                        result['data'][0]['id'] = 'replacement-profile'
                    return result
                branch = collect_profile('yose', base, '2026-10-02T09:30:00Z', branch_payload)
                new = collect_profile('yose', branch, '2026-10-02T11:00:00Z', branch_payload)
                with self.assertRaises(model.ProfileReleaseError):
                    model._advance({'profiles': [public]}, {'profiles': [new]})
                later_branch = collect_profile('yose', public, '2026-10-02T10:30:00Z', branch_payload)
                valid = collect_profile('yose', later_branch, '2026-10-02T11:00:00Z', branch_payload)
                model._advance({'profiles': [public]}, {'profiles': [valid]})


@unittest.skipUnless(os.name == 'posix', 'Private profile releases require POSIX.')
class ProfileReleaseStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root.chmod(0o700)
        self.repo = self.root/'repo'
        (self.repo/'data').mkdir(parents=True)

    def adapter(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.profile_release'))
        return importlib.import_module('tracker.profile_release')

    def write(self, value, name):
        path = self.root/name
        path.write_bytes(canonical(value))
        path.chmod(0o600)
        return path

    def bundle_path(self):
        return self.write(release_fixture(), 'bundle.json')

    def test_explicit_approval_then_immutable_verify_restore(self):
        model = self.adapter()
        checkpoint = checkpoint_fixture()
        cp = self.write(checkpoint, 'checkpoint.json')
        rights = self.write(rights_fixture(model.project_checkpoint(checkpoint)), 'rights.json')
        output = self.root/'reviewed.json'
        with self.assertRaises(model.ProfileReleaseError):
            model.create_release_bundle(cp, rights, output, APPROVED)
        self.assertFalse(output.exists())
        bundle = model.create_release_bundle(cp, rights, output, APPROVED, approve=True)
        self.assertEqual(model.verify_release_bundle(output), bundle)
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        with self.assertRaises(Exception):
            model.create_release_bundle(cp, rights, output, APPROVED, approve=True)
        recovery = self.root/'recovered.json'
        self.assertEqual(model.restore_release_bundle(output, recovery), bundle)
        self.assertEqual(output.read_bytes(), recovery.read_bytes())

    def test_insecure_rights_and_checkpoint_inputs_refused_before_output(self):
        model = self.adapter()
        cp = self.write(checkpoint_fixture(), 'cp.json')
        rights = self.write(rights_fixture(model.project_checkpoint(checkpoint_fixture())), 'rights.json')
        rights.chmod(0o644)
        with self.assertRaises(Exception):
            model.create_release_bundle(cp, rights, self.root/'out.json', APPROVED, approve=True)
        self.assertFalse((self.root/'out.json').exists())
        self.assertFalse((self.root/'out.json.lock').exists())

    def test_prepare_and_check_bind_absent_public_pair_and_exact_patch_bytes(self):
        model = self.adapter()
        bundle = self.bundle_path()
        output = self.root/'candidate.patch'
        receipt = model.prepare_promotion(bundle, output, root=self.repo)
        data = output.read_bytes()
        self.assertEqual(data.count(b'diff --git '), 2)
        self.assertIn(b'--- /dev/null', data)
        self.assertNotIn(b'parent_checkpoint_id', data)
        self.assertNotIn(b'private_reviewed_park_profiles', data)
        self.assertEqual(model.check_promotion(bundle, output, receipt['candidate_id'], root=self.repo), receipt)
        self.assertFalse((self.repo/'data/park-profiles.json').exists())
        output.write_bytes(data + b'\n')
        with self.assertRaises(model.ProfileReleaseError):
            model.check_promotion(bundle, output, receipt['candidate_id'], root=self.repo)

    def test_changed_or_unpaired_base_and_wrong_candidate_refused(self):
        model = self.adapter()
        bundle = self.bundle_path()
        output = self.root/'candidate.patch'
        receipt = model.prepare_promotion(bundle, output, root=self.repo)
        with self.assertRaises(model.ProfileReleaseError):
            model.check_promotion(bundle, output, '0'*64, root=self.repo)
        (self.repo/'data/park-profiles.json').write_bytes(canonical(release_fixture()['public_profiles']))
        with self.assertRaises(model.ProfileReleaseError):
            model.check_promotion(bundle, output, receipt['candidate_id'], root=self.repo)

    def test_complete_base_byte_changes_are_bound_even_when_json_equivalent(self):
        model = self.adapter()
        bundle = release_fixture()
        for name, value in [('park-profiles.json', bundle['public_profiles']),
                            ('profile-source-rights.json', bundle['rights'])]:
            (self.repo/'data'/name).write_bytes(canonical(value))
        bp = self.bundle_path()
        output = self.root/'candidate.patch'
        receipt = model.prepare_promotion(bp, output, root=self.repo)
        base = self.repo/'data/park-profiles.json'
        base.write_bytes(base.read_bytes()+b'\n')
        with self.assertRaises(model.ProfileReleaseError):
            model.check_promotion(bp, output, receipt['candidate_id'], root=self.repo)

    def test_prepared_new_and_replacement_patches_apply_exact_public_pair(self):
        model = self.adapter()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True, capture_output=True)
        bundle = self.bundle_path()
        for name in ('new.patch', 'replacement.patch'):
            output = self.root/name
            model.prepare_promotion(bundle, output, root=self.repo)
            subprocess.run(['git', 'apply', '--check', str(output)], cwd=self.repo,
                           check=True, capture_output=True)
            subprocess.run(['git', 'apply', str(output)], cwd=self.repo,
                           check=True, capture_output=True)
            value = release_fixture()
            self.assertEqual((self.repo/'data/park-profiles.json').read_bytes(),
                             canonical(value['public_profiles'])+b'\n')
            self.assertEqual((self.repo/'data/profile-source-rights.json').read_bytes(),
                             canonical(value['rights'])+b'\n')

    def test_degraded_retained_evidence_can_advance_attempt_without_refreshing_success(self):
        model = self.adapter()
        from tracker.park_profiles import collect_profile, ProfileCollectionError
        old = release_fixture()
        def failed(_):
            raise ProfileCollectionError('private transport reason')
        cp = checkpoint_fixture()
        cp['profiles'] = [collect_profile(row['park_code'], row, LATER, failed) for row in cp['profiles']]
        cp['checked_at'] = LATER
        cp['checkpoint_id'] = digest({k:v for k,v in cp.items() if k != 'checkpoint_id'})
        bundle = model.build_release_bundle(cp, rights_fixture(model.project_checkpoint(cp)), APPROVED)
        current = {'data/park-profiles.json': canonical(old['public_profiles']),
                   'data/profile-source-rights.json': canonical(old['rights'])}
        candidate = model.build_promotion(bundle, current)
        self.assertIn(b'provider_request_failed', candidate['patch'])
        self.assertEqual(bundle['public_profiles']['profiles'][0]['last_successful_fetch_at'], NOW)

    def test_clock_rewind_and_changed_degraded_profile_refused(self):
        model = self.adapter()
        old, newer = release_fixture(), release_fixture(LATER)
        current = {'data/park-profiles.json': canonical(newer['public_profiles']),
                   'data/profile-source-rights.json': canonical(newer['rights'])}
        with self.assertRaises(model.ProfileReleaseError):
            model.build_promotion(old, current)
        from tracker.park_profiles import collect_profile, ProfileCollectionError
        def failed(_):
            raise ProfileCollectionError('do not leak')
        cp = checkpoint_fixture(LATER)
        cp['profiles'] = [collect_profile(row['park_code'], row, APPROVED, failed) for row in cp['profiles']]
        cp['checked_at'] = APPROVED
        cp['checkpoint_id'] = digest({k:v for k,v in cp.items() if k != 'checkpoint_id'})
        candidate = model.build_release_bundle(cp, rights_fixture(model.project_checkpoint(cp), APPROVED), APPROVED)
        previous = {'data/park-profiles.json': canonical(old['public_profiles']),
                    'data/profile-source-rights.json': canonical(old['rights'])}
        with self.assertRaises(model.ProfileReleaseError):
            model.build_promotion(candidate, previous)

    def test_cli_static_failure_never_echoes_paths_or_arguments(self):
        model = self.adapter()
        stream = io.StringIO()
        with redirect_stdout(stream):
            self.assertEqual(model.main(['verify', '--secret', 'synthetic-private-value']), 2)
        self.assertNotIn('synthetic-private-value', stream.getvalue())
        self.assertFalse(json.loads(stream.getvalue())['network_attempted'])

    def test_cli_interruption_reports_safely(self):
        model = self.adapter()
        stream = io.StringIO()
        with patch.object(model, 'verify_release_bundle', side_effect=KeyboardInterrupt), redirect_stdout(stream):
            self.assertEqual(model.main(['verify', '--bundle', str(self.root/'private')]), 2)
        self.assertEqual(json.loads(stream.getvalue())['error_code'], 'profile_release_interrupted')

    def test_export_size_is_checked_before_output_lock(self):
        model = self.adapter()
        cp = self.write(checkpoint_fixture(), 'cp.json')
        rights = self.write(rights_fixture(model.project_checkpoint(checkpoint_fixture())), 'rights.json')
        with patch.object(model, 'MAX_RELEASE_BYTES', 100), self.assertRaises(model.ProfileReleaseError):
            model.create_release_bundle(cp, rights, self.root/'out.json', APPROVED, approve=True)
        self.assertFalse((self.root/'out.json.lock').exists())
