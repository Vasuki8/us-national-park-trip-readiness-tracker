"""Synthetic catalog approval, source continuity and private recovery contracts."""
import copy
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tracker import activity_release as model
from tracker.park_activities import PILOT_CODES, collect_activities, initial_activities
from tracker.release_readiness import _activity_publication, _gate
from test_activity_checkpoints import bind, checkpoint_fixture, encoded
from test_activity_release import (APPROVED, REVIEWED, advanced_checkpoint,
                                   current_pair, release_fixture)
from test_activity_public import POLICY
from test_park_activities import T0, T1, T2, activity, page, rehash

DISPOSITION_REVIEW = '2026-10-03T12:30:00Z'
SOURCE_FIELDS = ('id', 'content_hash', 'hash_scope', 'observed_first_at', 'observed_changed_at')


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def dispositions_fixture(checkpoint, *, withheld=(), categories='published', reviewed_at=DISPOSITION_REVIEW):
    return {'schema_version': 1, 'purpose': 'private_activity_catalog_dispositions',
            'checkpoint_id': checkpoint['checkpoint_id'], 'reviewed_at': reviewed_at,
            'records': [{'park_code': inv['park_code'], 'activity_id': row['id'],
                         'source_content_hash': row['content_hash'],
                         'decision': 'withheld' if (inv['park_code'], row['id']) in withheld else 'selected',
                         'categories': 'withheld' if (inv['park_code'], row['id']) in withheld else categories}
                        for inv in checkpoint['inventories'] for row in inv['records']]}


def catalog_fixture(checkpoint, dispositions):
    """Independent synthetic projection to expose release-layer failures first."""
    decisions = {(row['park_code'], row['activity_id']): row for row in dispositions['records']}
    inventories = []
    for inventory in checkpoint['inventories']:
        result = {key: copy.deepcopy(value) for key, value in inventory.items() if key != 'records'}
        result.update(schema_version=2, records=[], source_records=[])
        for row in inventory['records']:
            choice = decisions[inventory['park_code'], row['id']]
            result['source_records'].append({**{key: row[key] for key in SOURCE_FIELDS},
                                             'publication_status': choice['decision']})
            if choice['decision'] == 'withheld':
                continue
            record = {'id': row['id'], 'park_code': inventory['park_code'],
                      'title': row['title'], 'url': row['url'],
                      'activity_categories': copy.deepcopy(row['activity_categories'])
                      if choice['categories'] == 'published' else None,
                      'category_scope': choice['categories'], 'geographic_relationship': 'unconfirmed',
                      'responsible_agency': None, 'difficulty': None, 'permit_required': None,
                      'availability_status': 'not_verified', 'source_updated_at': None,
                      'observed_first_at': row['observed_first_at'],
                      'observed_changed_at': row['observed_changed_at'],
                      'source_content_hash': row['content_hash']}
            result['records'].append({**record, 'view_hash': digest(record), 'hash_scope': 'catalog_view'})
        inventories.append(result)
    return {'schema_version': 2, 'purpose': 'public_park_activities', 'inventories': inventories}


def rights_fixture(public, *, reviewed_at=REVIEWED):
    return {'schema_version': 2, 'purpose': 'public_park_activity_text_rights',
            'reviewed_at': reviewed_at, 'review_method': 'official_nps_policy_and_exact_activity_review',
            'policy': copy.deepcopy(POLICY), 'projection_hash': digest(public),
            'records': [{'park_code': inv['park_code'], 'activity_id': row['id'],
                         'source_url': inv['source_url'],
                         'source_content_hash': row['source_content_hash'], 'view_hash': row['view_hash'],
                         'classification': 'nps_government_text',
                         'use_scope': 'activity_catalog_title_url_and_optional_categories',
                         'third_party_material_reproduced': False, 'nps_marks_reproduced': False,
                         'media_reproduced': False}
                        for inv in public['inventories'] for row in inv['records']]}


def catalog_bundle(checkpoint=None, *, withheld=(), categories='published',
                   disposition_review=DISPOSITION_REVIEW, rights_review=REVIEWED, approved_at=APPROVED):
    checkpoint = checkpoint_fixture() if checkpoint is None else checkpoint
    plan = dispositions_fixture(checkpoint, withheld=withheld, categories=categories,
                                reviewed_at=disposition_review)
    public = catalog_fixture(checkpoint, plan)
    return model.build_release_bundle(checkpoint, rights_fixture(public, reviewed_at=rights_review),
                                      approved_at, dispositions=plan)


def rebind_bundle(bundle):
    bundle['bundle_id'] = digest({key: value for key, value in bundle.items() if key != 'bundle_id'})
    return bundle


def expanded_checkpoint(count=4):
    checkpoint = checkpoint_fixture()
    for code in PILOT_CODES:
        checkpoint['inventories'][PILOT_CODES.index(code)] = collect_activities(
            code, initial_activities(code), T0,
            lambda _start, code=code: page([activity(f'synthetic-{i}', code=code) for i in range(count)]))
    return bind(checkpoint)


class CatalogReleaseModelTests(unittest.TestCase):
    def test_optional_dispositions_select_v2_and_bind_plan_without_mutation(self):
        checkpoint = checkpoint_fixture()
        plan = dispositions_fixture(checkpoint, withheld=(('yose', 'synthetic-a'),))
        before = copy.deepcopy((checkpoint, plan))
        public = catalog_fixture(checkpoint, plan)
        rights = rights_fixture(public)
        bundle = model.build_release_bundle(checkpoint, rights, APPROVED, dispositions=plan)
        self.assertEqual(bundle['schema_version'], 2)
        self.assertEqual(bundle['dispositions'], plan)
        self.assertEqual(bundle['approval']['dispositions_hash'], digest(plan))
        self.assertEqual(bundle['public_activities'], public)
        self.assertEqual(bundle['rights'], rights)
        self.assertEqual(model.validate_release_bundle(bundle), bundle)
        self.assertEqual((checkpoint, plan), before)
        bundle['dispositions']['records'][0]['categories'] = 'caller mutation'
        self.assertEqual((checkpoint, plan), before)

    def test_absent_plan_keeps_exact_v1_bundle_and_strict_same_clock(self):
        bundle = release_fixture(model)
        self.assertEqual(bundle['schema_version'], 1)
        self.assertNotIn('dispositions', bundle)
        self.assertNotIn('dispositions_hash', bundle['approval'])
        changed = copy.deepcopy(bundle['public_activities'])
        changed['inventories'][0]['records'][0]['credit'] = 'new synthetic credit'
        rehash(changed['inventories'][0]['records'][0])
        with self.assertRaisesRegex(model.ActivityReleaseError, 'activity_promotion_same_clock_change'):
            model._advance(bundle['public_activities'], changed)

    def test_outer_rehash_does_not_authorize_plan_projection_or_approval_tampering(self):
        original = catalog_bundle(withheld=(('yose', 'synthetic-a'),))
        changes = [lambda b: b['dispositions']['records'][0].update(decision='selected', categories='published'),
                   lambda b: b['dispositions'].update(checkpoint_id='0' * 64),
                   lambda b: b['dispositions']['records'][1].update(source_content_hash='0' * 64),
                   lambda b: b['approval'].update(dispositions_hash='0' * 64),
                   lambda b: b['approval'].pop('dispositions_hash'),
                   lambda b: b['public_activities']['inventories'][1]['records'][0].update(title='Unbound title'),
                   lambda b: b['public_activities']['inventories'][0]['source_records'][0].update(content_hash='0' * 64),
                   lambda b: b['rights']['records'][0].update(view_hash='0' * 64)]
        for change in changes:
            candidate = copy.deepcopy(original)
            change(candidate)
            rebind_bundle(candidate)
            with self.subTest(change=change), self.assertRaises(model.ActivityReleaseError):
                model.validate_release_bundle(candidate)

    def test_even_rehashed_valid_catalog_cannot_diverge_from_checkpoint_projection(self):
        candidate = catalog_bundle()
        row = candidate['public_activities']['inventories'][0]['records'][0]
        row['title'] = 'Synthetic different but valid title'
        row['view_hash'] = digest({key: value for key, value in row.items() if key not in ('view_hash', 'hash_scope')})
        candidate['rights'] = rights_fixture(candidate['public_activities'])
        candidate['approval'].update(projection_hash=digest(candidate['public_activities']),
                                     rights_hash=digest(candidate['rights']))
        rebind_bundle(candidate)
        with self.assertRaisesRegex(model.ActivityReleaseError, 'activity_projection_mismatch'):
            model.validate_release_bundle(candidate)

    def test_schema_transitions_require_version_specific_approval_envelopes(self):
        for original in (release_fixture(model), catalog_bundle()):
            candidate = copy.deepcopy(original)
            candidate['schema_version'] = 3 - candidate['schema_version']
            rebind_bundle(candidate)
            with self.subTest(version=original['schema_version']), self.assertRaises(model.ActivityReleaseError):
                model.validate_release_bundle(candidate)
        for original in (release_fixture(model), catalog_bundle()):
            candidate = copy.deepcopy(original)
            candidate['rights']['schema_version'] = 3 - candidate['rights']['schema_version']
            candidate['approval']['rights_hash'] = digest(candidate['rights'])
            rebind_bundle(candidate)
            with self.assertRaises(model.ActivityReleaseError):
                model.validate_release_bundle(candidate)

    def test_review_clock_order_and_equal_microsecond_boundaries(self):
        clock = '2026-10-03T10:00:00.000001Z'
        checkpoint = checkpoint_fixture(now=clock)
        self.assertEqual(catalog_bundle(checkpoint, disposition_review=clock, rights_review=clock,
                                        approved_at=clock)['approval']['approved_at'], clock)
        earlier = '2026-10-03T10:00:00Z'
        for disposition_review, rights_review, approved in ((earlier, clock, clock),
                                                          (clock, earlier, clock),
                                                          (clock, clock, earlier)):
            with self.subTest(disposition_review=disposition_review, rights_review=rights_review, approved=approved), \
                 self.assertRaises(model.ActivityReleaseError):
                catalog_bundle(checkpoint, disposition_review=disposition_review,
                               rights_review=rights_review, approved_at=approved)

    def test_rights_review_must_follow_disposition_review_even_when_wholly_withheld(self):
        checkpoint = checkpoint_fixture()
        withheld = [(inv['park_code'], row['id']) for inv in checkpoint['inventories'] for row in inv['records']]
        with self.assertRaises(model.ActivityReleaseError):
            catalog_bundle(checkpoint, withheld=withheld, disposition_review=APPROVED, rights_review=REVIEWED)
        bundle = catalog_bundle(checkpoint, withheld=withheld)
        self.assertEqual(bundle['rights']['records'], [])
        self.assertEqual(sum(len(inv['source_records']) for inv in bundle['public_activities']['inventories']), 5)

    def test_selected_categories_can_change_at_same_source_clock_without_refresh(self):
        first = catalog_bundle()
        second = catalog_bundle(categories='withheld', disposition_review=REVIEWED,
                                rights_review=APPROVED, approved_at='2026-10-03T15:00:00Z')
        candidate = model.build_promotion(second, current_pair(first))
        self.assertNotEqual(first['bundle_id'], second['bundle_id'])
        self.assertIn(b'"category_scope":"withheld"', candidate['patch'])
        inventory = second['public_activities']['inventories'][0]
        self.assertEqual(inventory['last_checked_at'], T0)
        self.assertEqual(inventory['last_successful_fetch_at'], T0)
        self.assertEqual(inventory['source_records'][0]['observed_changed_at'], T0)

    def test_withholding_all_sources_at_same_clock_is_editorial_not_removal(self):
        first = catalog_bundle()
        withheld = [(code, 'synthetic-a') for code in PILOT_CODES]
        second = catalog_bundle(withheld=withheld)
        model.build_promotion(second, current_pair(first))
        self.assertEqual(sum(len(inv['records']) for inv in second['public_activities']['inventories']), 0)
        self.assertEqual(sum(len(inv['source_records']) for inv in second['public_activities']['inventories']), 5)

    def test_explicit_v1_v2_transitions_preserve_source_evidence(self):
        v1 = release_fixture(model)
        v2 = catalog_bundle(withheld=(('yose', 'synthetic-a'),))
        for old, new in ((v1, v2), (v2, v1)):
            with self.subTest(before=old['schema_version'], after=new['schema_version']):
                model.build_promotion(new, current_pair(old))

    def test_same_clock_source_header_and_hidden_source_changes_refused(self):
        old = catalog_bundle(withheld=(('yose', 'synthetic-a'),))
        for kind in ('record', 'header'):
            checkpoint = checkpoint_fixture()
            if kind == 'record':
                checkpoint['inventories'][0]['records'][0]['description'] = 'New withheld source text'
                rehash(checkpoint['inventories'][0]['records'][0])
            else:
                checkpoint['inventories'][0].update(collection_status='failed', coverage_status='incomplete',
                                                     error_code='provider_request_failed')
            bind(checkpoint)
            new = catalog_bundle(checkpoint, withheld=(('yose', 'synthetic-a'),))
            with self.subTest(kind=kind), self.assertRaisesRegex(model.ActivityReleaseError,
                                                                'activity_promotion_same_clock_change'):
                model.build_promotion(new, current_pair(old))

    def test_degraded_catalog_can_change_editorial_choices_but_preserves_source_clocks(self):
        first = catalog_bundle()
        failed = advanced_checkpoint(checkpoint_fixture(), failed=True)
        second = catalog_bundle(failed, withheld=(('yose', 'synthetic-a'),), categories='withheld')
        model.build_promotion(second, current_pair(first))
        inventory = second['public_activities']['inventories'][0]
        self.assertEqual((inventory['last_checked_at'], inventory['last_successful_fetch_at']), (T1, T0))
        self.assertEqual(inventory['source_records'][0]['content_hash'],
                         first['public_activities']['inventories'][0]['source_records'][0]['content_hash'])

    def test_degraded_hidden_source_hash_or_success_clock_change_refused(self):
        first = catalog_bundle(withheld=(('yose', 'synthetic-a'),))
        for kind in ('hash', 'clock'):
            checkpoint = advanced_checkpoint(checkpoint_fixture(), failed=True)
            if kind == 'hash':
                checkpoint['inventories'][0]['records'][0]['credit'] = 'Altered withheld evidence'
                rehash(checkpoint['inventories'][0]['records'][0])
            else:
                checkpoint['inventories'][0]['last_successful_fetch_at'] = '2026-10-03T10:30:00Z'
            new = catalog_bundle(bind(checkpoint), withheld=(('yose', 'synthetic-a'),))
            with self.subTest(kind=kind), self.assertRaisesRegex(model.ActivityReleaseError,
                                                                'activity_promotion_degraded_evidence_changed'):
                model.build_promotion(new, current_pair(first))

    def test_actual_source_half_drop_is_checked_when_nothing_is_published(self):
        checkpoint = expanded_checkpoint()
        withheld = [(code, f'synthetic-{i}') for code in PILOT_CODES for i in range(4)]
        first = catalog_bundle(checkpoint, withheld=withheld)
        fork = copy.deepcopy(checkpoint)
        fork['checked_at'] = T1
        for inventory in fork['inventories']:
            inventory.update(last_checked_at=T1, last_successful_fetch_at=T1)
            inventory['records'] = inventory['records'][:1]
        second = catalog_bundle(bind(fork), withheld=[(code, 'synthetic-0') for code in PILOT_CODES])
        with self.assertRaisesRegex(model.ActivityReleaseError, 'activity_promotion_inventory_drop_requires_review'):
            model.build_promotion(second, current_pair(first))

    def test_hidden_source_retained_observations_and_changes_remain_guarded(self):
        initial = checkpoint_fixture()
        first = catalog_bundle(initial, withheld=(('yose', 'synthetic-a'),))
        for kind, expected in (('first', 'activity_promotion_observation_rewind'),
                               ('unchanged', 'activity_promotion_unchanged_clock_changed'),
                               ('changed', 'activity_promotion_conflicting_observation')):
            checkpoint = advanced_checkpoint(initial)
            row = checkpoint['inventories'][0]['records'][0]
            if kind == 'first':
                row['observed_first_at'] = '2026-10-03T09:00:00Z'
            elif kind == 'unchanged':
                row['observed_changed_at'] = T1
            else:
                row['credit'] = 'Changed hidden source'
                rehash(row)
            new = catalog_bundle(bind(checkpoint), withheld=(('yose', 'synthetic-a'),))
            with self.subTest(kind=kind), self.assertRaisesRegex(model.ActivityReleaseError, expected):
                model.build_promotion(new, current_pair(first))

    def test_new_source_and_successful_changed_source_need_later_observations(self):
        initial = expanded_checkpoint(count=2)
        first = catalog_bundle(initial)
        checkpoint = advanced_checkpoint(initial, raw_by_code={code: [activity('synthetic-0', code=code),
            activity('synthetic-1', code=code, credit='New hidden credit'), activity('synthetic-2', code=code)]
            for code in PILOT_CODES})
        second = catalog_bundle(checkpoint, withheld=[(code, 'synthetic-1') for code in PILOT_CODES])
        model.build_promotion(second, current_pair(first))
        for kind in ('new', 'changed'):
            candidate = copy.deepcopy(checkpoint)
            row = candidate['inventories'][0]['records'][2 if kind == 'new' else 1]
            row['observed_changed_at'] = T0
            if kind == 'new':
                row['observed_first_at'] = T0
            new = catalog_bundle(bind(candidate))
            with self.subTest(kind=kind), self.assertRaisesRegex(model.ActivityReleaseError,
                                                                'activity_promotion_conflicting_observation'):
                model.build_promotion(new, current_pair(first))

    def test_catalog_attempt_and_success_clocks_cannot_rewind(self):
        initial = checkpoint_fixture()
        later = advanced_checkpoint(initial)
        first = catalog_bundle(later)
        with self.assertRaisesRegex(model.ActivityReleaseError, 'activity_promotion_clock_rewind'):
            model.build_promotion(catalog_bundle(initial), current_pair(first))
        failed = advanced_checkpoint(initial, now=T2, failed=True)
        with self.assertRaisesRegex(model.ActivityReleaseError, 'activity_promotion_clock_rewind'):
            model.build_promotion(catalog_bundle(failed), current_pair(first))

    def test_initial_public_patch_contains_only_catalog_and_rights_scope(self):
        checkpoint = checkpoint_fixture()
        for inventory in checkpoint['inventories']:
            inventory['records'][0]['description'] = '<p>SECRET_QUOTATION contact@example.invalid tracking-token</p>'
            inventory['records'][0]['credit'] = 'SECRET_CREDIT'
            rehash(inventory['records'][0])
        bundle = catalog_bundle(bind(checkpoint), categories='withheld')
        output = model.build_promotion(bundle, dict.fromkeys(model.PUBLIC_FILES))['patch']
        for marker in (b'SECRET_QUOTATION', b'SECRET_CREDIT', b'contact@example.invalid', b'tracking-token',
                       b'private_activity_catalog_dispositions', b'checkpoint_id', b'dispositions_hash', b'<p>'):
            self.assertNotIn(marker, output)
        self.assertEqual(output.count(b'diff --git '), 2)


@unittest.skipUnless(os.name == 'posix', 'Private lifecycle requires POSIX.')
class CatalogPrivateLifecycleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='catalog-private-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.root.chmod(0o700)
        self.repo = self.root / 'synthetic-repo'
        (self.repo / 'data').mkdir(parents=True)
        self.output = self.root / 'reviewed.json'

    def write(self, value, name):
        result = self.root / name
        result.write_bytes(encoded(value))
        result.chmod(0o600)
        return result

    def inputs(self):
        checkpoint = checkpoint_fixture()
        plan = dispositions_fixture(checkpoint, withheld=(('yose', 'synthetic-a'),))
        public = catalog_fixture(checkpoint, plan)
        return (self.write(checkpoint, 'checkpoint.json'), self.write(rights_fixture(public), 'rights.json'),
                self.write(plan, 'dispositions.json'))

    def test_approve_verify_fresh_restore_and_paired_patch_are_offline_and_private(self):
        checkpoint, rights, plan = self.inputs()
        with patch('urllib.request.urlopen', side_effect=AssertionError('Forbidden network')), \
             patch.object(os.environ, 'get', side_effect=AssertionError('Forbidden credential access')):
            bundle = model.create_release_bundle(checkpoint, rights, self.output, APPROVED,
                                                  approve=True, dispositions=plan)
            self.assertEqual(model.verify_release_bundle(self.output), bundle)
            recovery = self.root / 'fresh-recovery'
            recovery.mkdir(mode=0o700)
            restored = recovery / 'reviewed.json'
            self.assertEqual(model.restore_release_bundle(self.output, restored), bundle)
            self.assertEqual(restored.read_bytes(), self.output.read_bytes())
            patch_file = self.root / 'catalog.patch'
            receipt = model.prepare_promotion(restored, patch_file, root=self.repo)
            self.assertEqual(model.check_promotion(restored, patch_file, receipt['candidate_id'], root=self.repo), receipt)
            self.assertEqual(list((self.repo / 'data').iterdir()), [])
        for path in (self.output, restored, patch_file):
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(path.stat().st_nlink, 1)
        self.assertEqual(bundle['public_activities']['inventories'][0]['last_checked_at'], T0)

    def test_all_approval_input_output_and_lock_collisions_preserve_inputs(self):
        for kind in ('checkpoint', 'rights', 'dispositions'):
            for collision in ('output', 'lock'):
                checkpoint, rights, plan = self.inputs()
                inputs = {'checkpoint': checkpoint, 'rights': rights, 'dispositions': plan}
                source = inputs[kind]
                output = source if collision == 'output' else self.root / f'{kind}-collision.json'
                if collision == 'lock':
                    source.rename(Path(str(output) + '.lock'))
                    inputs[kind] = source = Path(str(output) + '.lock')
                before = source.read_bytes(), source.stat().st_mtime_ns
                with self.subTest(kind=kind, collision=collision), self.assertRaises(model.ActivityReleaseError):
                    model.create_release_bundle(inputs['checkpoint'], inputs['rights'], output, APPROVED,
                                                approve=True, dispositions=inputs['dispositions'])
                self.assertEqual((source.read_bytes(), source.stat().st_mtime_ns), before)
                if collision == 'lock':
                    self.assertFalse(output.exists())
                for path in self.root.iterdir():
                    if path.is_file():
                        path.unlink()

    def test_disposition_symlink_hardlink_and_public_permissions_refused(self):
        checkpoint, rights, plan = self.inputs()
        symlink = self.root / 'linked-plan.json'
        symlink.symlink_to(plan)
        hardlink = self.root / 'hardlinked-plan.json'
        for kind in ('symlink', 'hardlink', 'permissions'):
            if kind == 'hardlink':
                os.link(plan, hardlink)
            if kind == 'permissions':
                hardlink.unlink()
                plan.chmod(0o644)
            with self.subTest(kind=kind), self.assertRaises(model.ActivityReleaseError):
                model.create_release_bundle(checkpoint, rights, self.output, APPROVED,
                                            approve=True, dispositions=symlink if kind == 'symlink' else plan)
        self.assertFalse(self.output.exists())
        self.assertFalse(Path(str(self.output) + '.lock').exists())

    def test_invalid_or_stale_plan_refused_before_output_lock(self):
        checkpoint, rights, plan_path = self.inputs()
        for change in (lambda p: p['records'].pop(),
                       lambda p: p['records'].append(copy.deepcopy(p['records'][0])),
                       lambda p: p.update(checkpoint_id='0' * 64)):
            plan = dispositions_fixture(checkpoint_fixture())
            change(plan)
            plan_path.write_bytes(encoded(plan))
            with self.assertRaises(model.ActivityReleaseError):
                model.create_release_bundle(checkpoint, rights, self.output, APPROVED,
                                            approve=True, dispositions=plan_path)
            self.assertFalse(self.output.exists())
            self.assertFalse(Path(str(self.output) + '.lock').exists())

    def test_supplied_null_plan_never_silently_downgrades_to_v1(self):
        checkpoint, rights, plan = self.inputs()
        rights.write_bytes(encoded(release_fixture(model)['rights']))
        plan.write_bytes(b'null')
        with self.assertRaises(model.ActivityReleaseError):
            model.create_release_bundle(checkpoint, rights, self.output, APPROVED,
                                        approve=True, dispositions=plan)
        self.assertFalse(self.output.exists())
        self.assertFalse(Path(str(self.output) + '.lock').exists())

    def test_cli_plan_is_optional_but_approval_is_explicit_and_report_is_sanitized(self):
        checkpoint, rights, plan = self.inputs()
        arguments = ['approve', '--checkpoint', str(checkpoint), '--rights', str(rights),
                     '--dispositions', str(plan), '--output', str(self.output)]
        stream = io.StringIO()
        with redirect_stdout(stream):
            self.assertEqual(model.main(arguments), 2)
        self.assertFalse(json.loads(stream.getvalue())['approval_performed'])
        self.assertFalse(self.output.exists())
        stream = io.StringIO()
        with redirect_stdout(stream):
            self.assertEqual(model.main(arguments + ['--approve']), 0)
        report = json.loads(stream.getvalue())
        self.assertTrue(report['approval_performed'])
        self.assertEqual(model.verify_release_bundle(self.output)['schema_version'], 2)
        for marker in (str(self.root), 'Synthetic', 'synthetic-a', 'dispositions.json'):
            self.assertNotIn(marker, stream.getvalue())
        for flag in ('network_attempted', 'publication_performed', 'site_data_written'):
            self.assertFalse(report[flag])

    def test_paired_cas_recheck_detects_bundle_patch_and_raw_base_changes(self):
        bundle = catalog_bundle()
        source = self.write(bundle, 'reviewed-source.json')
        patch_file = self.root / 'promotion.patch'
        receipt = model.prepare_promotion(source, patch_file, root=self.repo)
        raw = patch_file.read_bytes()
        patch_file.write_bytes(raw + b'\n')
        with self.assertRaises(model.ActivityReleaseError):
            model.check_promotion(source, patch_file, receipt['candidate_id'], root=self.repo)
        patch_file.write_bytes(raw)
        for name, data in current_pair(bundle).items():
            (self.repo / name).write_bytes(data)
        with self.assertRaises(model.ActivityReleaseError):
            model.check_promotion(source, patch_file, receipt['candidate_id'], root=self.repo)
        for name in model.PUBLIC_FILES:
            (self.repo / name).unlink()
        altered = copy.deepcopy(bundle)
        altered['approval']['approved_at'] = '2026-10-03T15:00:00Z'
        source.write_bytes(encoded(rebind_bundle(altered)))
        with self.assertRaises(model.ActivityReleaseError):
            model.check_promotion(source, patch_file, receipt['candidate_id'], root=self.repo)

    def test_real_git_paired_initial_and_editorial_replacement_patch_apply(self):
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True, capture_output=True)
        first = catalog_bundle()
        for index, bundle in enumerate((first, catalog_bundle(withheld=(('yose', 'synthetic-a'),), categories='withheld'))):
            source = self.write(bundle, f'reviewed-{index}.json')
            patch_file = self.root / f'promotion-{index}.patch'
            receipt = model.prepare_promotion(source, patch_file, root=self.repo)
            model.check_promotion(source, patch_file, receipt['candidate_id'], root=self.repo)
            for command in (['git', 'apply', '--check', str(patch_file)], ['git', 'apply', str(patch_file)]):
                subprocess.run(command, cwd=self.repo, check=True, capture_output=True)
            self.assertEqual({name: (self.repo / name).read_bytes() for name in model.PUBLIC_FILES}, current_pair(bundle))


class CatalogReadinessTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='catalog-readiness-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'data').mkdir()

    def report(self, public_bundle, *, review=None, backup=None, original_status='pass'):
        for name, raw in current_pair(public_bundle).items():
            (self.root / name).write_bytes(raw)
        gates = [_gate(identifier, original_status, 'synthetic_core_gate', {})
                 for identifier in ('durable_source_review', 'storage_backup', 'source_rights')]
        _activity_publication(self.root, gates, review, backup)
        return {gate['id']: gate for gate in gates}

    def test_source_published_withheld_counts_and_rights_are_distinct(self):
        bundle = catalog_bundle(withheld=(('yose', 'synthetic-a'), ('romo', 'synthetic-a')))
        gates = self.report(bundle, review=bundle, backup=copy.deepcopy(bundle))
        for gate in gates.values():
            self.assertEqual(gate['status'], 'pass')
            self.assertEqual(gate['evidence']['activity_source_records_total'], 5)
            self.assertEqual(gate['evidence']['activity_records_published'], 3)
            self.assertEqual(gate['evidence']['activity_records_withheld'], 2)
        self.assertEqual(gates['source_rights']['evidence']['activity_records_covered'], 3)
        self.assertTrue(gates['durable_source_review']['evidence']['public_activities_match_review'])
        self.assertTrue(gates['storage_backup']['evidence']['activity_backup_matches_review'])

    def test_wholly_withheld_catalog_still_requires_review_and_recovery(self):
        bundle = catalog_bundle(withheld=[(code, 'synthetic-a') for code in PILOT_CODES])
        gates = self.report(bundle)
        self.assertEqual(gates['durable_source_review']['status'], 'not_checked')
        self.assertEqual(gates['storage_backup']['status'], 'blocked')
        self.assertEqual(gates['source_rights']['evidence']['activity_records_covered'], 0)
        self.assertEqual(gates['source_rights']['evidence']['activity_records_withheld'], 5)

    def test_changed_disposition_and_rights_review_cannot_match_old_evidence(self):
        first = catalog_bundle()
        second = catalog_bundle(categories='withheld')
        gates = self.report(second, review=first, backup=first)
        self.assertEqual(gates['durable_source_review']['status'], 'blocked')
        self.assertEqual(gates['storage_backup']['status'], 'blocked')
        gates = self.report(second, review=second, backup=first)
        self.assertEqual(gates['storage_backup']['status'], 'blocked')

    def test_matching_catalog_evidence_cannot_clear_existing_blockers(self):
        bundle = catalog_bundle()
        for status in ('blocked', 'not_checked'):
            gates = self.report(bundle, review=bundle, backup=bundle, original_status=status)
            for gate in gates.values():
                self.assertEqual(gate['status'], status)
                self.assertEqual(gate['reason'], 'synthetic_core_gate')


if __name__ == '__main__':
    unittest.main()
