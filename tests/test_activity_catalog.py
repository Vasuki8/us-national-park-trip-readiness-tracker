"""Synthetic reviewed minimal catalog contracts; no source or operator reads."""
import copy
import hashlib
import importlib
import unittest

from tracker.activity_public import (ActivityPublicError, project_checkpoint,
                                     validate_public_activities, validate_activity_rights)
from tracker.park_activities import collect_activities, initial_activities, PILOT_CODES
from test_activity_checkpoints import checkpoint_fixture, bind, encoded
from test_activity_public import POLICY, public_fixture
from test_park_activities import T0, T1, rehash, activity, page


def dispositions_fixture(checkpoint, reviewed_at=T1):
    return {'schema_version': 1, 'purpose': 'private_activity_catalog_dispositions',
            'checkpoint_id': checkpoint['checkpoint_id'], 'reviewed_at': reviewed_at,
            'records': [{'park_code': s['park_code'], 'activity_id': r['id'],
                         'source_content_hash': r['content_hash'], 'decision': 'selected',
                         'categories': 'published'} for s in checkpoint['inventories'] for r in s['records']]}


def catalog_rights_fixture(dataset, reviewed_at=T1):
    return {'schema_version': 2, 'purpose': 'public_park_activity_text_rights',
            'reviewed_at': reviewed_at, 'review_method': 'official_nps_policy_and_exact_activity_review',
            'policy': copy.deepcopy(POLICY), 'projection_hash': hashlib.sha256(encoded(dataset)).hexdigest(),
            'records': [{'park_code': s['park_code'], 'activity_id': r['id'],
                         'source_url': s['source_url'], 'source_content_hash': r['source_content_hash'],
                         'view_hash': r['view_hash'], 'classification': 'nps_government_text',
                         'use_scope': 'activity_catalog_title_url_and_optional_categories',
                         'third_party_material_reproduced': False, 'nps_marks_reproduced': False,
                         'media_reproduced': False} for s in dataset['inventories'] for r in s['records']]}


def rehash_view(record):
    record['view_hash'] = hashlib.sha256(encoded({k: v for k, v in record.items()
                                               if k not in ('view_hash', 'hash_scope')})).hexdigest()


class ActivityCatalogTests(unittest.TestCase):
    def adapter(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.activity_catalog'),
                             'The minimal reviewed catalog contract is absent.')
        return importlib.import_module('tracker.activity_catalog')

    def test_private_prose_and_metadata_never_enter_catalog_but_original_hash_does(self):
        model = self.adapter()
        checkpoint = checkpoint_fixture()
        original = checkpoint['inventories'][0]['records'][0]
        original.update(description='QUOTATION-CONTACT-TRACKING', credit='PRIVATE-CREDIT')
        rehash(original)
        bind(checkpoint)
        plan = dispositions_fixture(checkpoint)
        plan['records'][1].update(decision='withheld', categories='withheld')
        result = model.project_catalog(checkpoint, plan)
        self.assertEqual(result['schema_version'], 2)
        self.assertEqual(len(result['inventories'][1]['source_records']), 1)
        self.assertEqual(result['inventories'][1]['records'], [])
        source = result['inventories'][0]['source_records'][0]
        self.assertEqual(source, {'id': 'synthetic-a', 'content_hash': original['content_hash'],
            'hash_scope': 'normalized_record', 'observed_first_at': T0,
            'observed_changed_at': T0, 'publication_status': 'selected'})
        record = result['inventories'][0]['records'][0]
        self.assertEqual(set(record), {'id', 'park_code', 'title', 'url', 'activity_categories',
            'category_scope', 'geographic_relationship', 'responsible_agency', 'difficulty',
            'permit_required', 'availability_status', 'source_updated_at', 'observed_first_at',
            'observed_changed_at', 'source_content_hash', 'view_hash', 'hash_scope'})
        self.assertEqual(record['source_content_hash'], original['content_hash'])
        self.assertEqual(record['availability_status'], 'not_verified')
        expected_hash = hashlib.sha256(encoded({k: v for k, v in record.items()
                                               if k not in ('view_hash', 'hash_scope')})).hexdigest()
        self.assertEqual(record['view_hash'], expected_hash)
        for marker in (b'QUOTATION', b'CONTACT', b'TRACKING', b'PRIVATE-CREDIT', b'long_description', b'related_parks'):
            self.assertNotIn(marker, encoded(result))
        self.assertEqual(project_checkpoint(checkpoint), public_fixture(checkpoint))
        self.assertEqual(project_checkpoint(checkpoint, dispositions=plan), result)
        self.assertEqual(validate_public_activities(result), result)
        result['inventories'][0]['records'][0]['title'] = 'caller mutation'
        self.assertEqual(original['title'], 'Synthetic activity')

    def test_dispositions_require_every_original_in_order_exact_hash_and_explicit_decision(self):
        model = self.adapter()
        checkpoint = checkpoint_fixture()
        changes = [lambda d: d['records'].pop(), lambda d: d['records'].reverse(),
            lambda d: d['records'].__setitem__(1, copy.deepcopy(d['records'][0])),
            lambda d: d['records'][0].update(source_content_hash='0'*64),
            lambda d: d['records'][0].update(decision='guessed'),
            lambda d: d['records'][0].update(decision='withheld'),
            lambda d: d.update(checkpoint_id='0'*64), lambda d: d.update(reviewed_at='2026-10-03T09:59:59.999999Z'),
            lambda d: d.update(reason='private explanation'),
            lambda d: d['records'][0].update(categories='omitted')]
        for change in changes:
            plan = dispositions_fixture(checkpoint)
            change(plan)
            with self.subTest(change=change), self.assertRaises(ActivityPublicError):
                model.validate_dispositions(plan, checkpoint)
        plan = dispositions_fixture(checkpoint, '2026-10-03T06:00:00-04:00')
        self.assertEqual(model.validate_dispositions(plan, checkpoint), plan)
        detached = model.validate_dispositions(plan, checkpoint)
        detached['records'][0]['decision'] = 'withheld'
        self.assertEqual(plan['records'][0]['decision'], 'selected')

    def test_published_null_empty_and_withheld_category_scopes_are_distinct(self):
        model = self.adapter()
        checkpoint = checkpoint_fixture()
        for inventory, categories in zip(checkpoint['inventories'], (None, [])):
            inventory['records'][0]['activity_categories'] = categories
            rehash(inventory['records'][0])
        bind(checkpoint)
        plan = dispositions_fixture(checkpoint)
        plan['records'][2]['categories'] = 'withheld'
        result = model.project_catalog(checkpoint, plan)
        self.assertIsNone(result['inventories'][0]['records'][0]['activity_categories'])
        self.assertEqual(result['inventories'][1]['records'][0]['activity_categories'], [])
        self.assertIsNone(result['inventories'][2]['records'][0]['activity_categories'])
        self.assertEqual(result['inventories'][2]['records'][0]['category_scope'], 'withheld')
        result['inventories'][2]['records'][0]['activity_categories'] = []
        rehash_view(result['inventories'][2]['records'][0])
        with self.assertRaises(ActivityPublicError):
            model.validate_catalog(result)

    def test_unpublishable_source_title_category_or_link_needs_explicit_withholding(self):
        model = self.adapter()
        cases = [('title', '<b>unresolved</b>'), ('title', 'control\u0085'), ('title', 'x'*1025),
                 ('url', 'https://www.nps.gov/yose/index.htm?contact=synthetic'),
                 ('url', 'https://www.nps.gov/thingstodo/synthetic.htm#fragment')]
        for field, text in cases:
            checkpoint = checkpoint_fixture()
            checkpoint['inventories'][0]['records'][0][field] = text
            rehash(checkpoint['inventories'][0]['records'][0])
            bind(checkpoint)
            plan = dispositions_fixture(checkpoint)
            with self.subTest(field=field, text=text), self.assertRaises(ActivityPublicError):
                model.project_catalog(checkpoint, plan)
            plan['records'][0].update(decision='withheld', categories='withheld')
            self.assertEqual(model.project_catalog(checkpoint, plan)['inventories'][0]['records'], [])
        checkpoint = checkpoint_fixture()
        checkpoint['inventories'][0]['records'][0]['activity_categories'][0]['name'] = '<b>category</b>'
        rehash(checkpoint['inventories'][0]['records'][0])
        bind(checkpoint)
        plan = dispositions_fixture(checkpoint)
        with self.assertRaises(ActivityPublicError):
            model.project_catalog(checkpoint, plan)
        plan['records'][0]['categories'] = 'withheld'
        self.assertIsNone(model.project_catalog(checkpoint, plan)['inventories'][0]['records'][0]['activity_categories'])
        checkpoint = checkpoint_fixture()
        record = checkpoint['inventories'][0]['records'][0]
        record['related_parks'] = sorted([*record['related_parks'], {
            **record['related_parks'][0], 'park_code': 'romo', 'url': 'https://www.nps.gov/romo/'}],
            key=lambda relation: relation['park_code'])
        record['url'] = 'https://www.nps.gov/romo/synthetic.htm'
        rehash(record)
        bind(checkpoint)
        plan = dispositions_fixture(checkpoint)
        with self.assertRaises(ActivityPublicError):
            model.project_catalog(checkpoint, plan)
        plan['records'][0].update(decision='withheld', categories='withheld')
        self.assertEqual(model.project_catalog(checkpoint, plan)['inventories'][0]['records'], [])

    def test_catalog_refuses_source_view_clock_scope_order_or_selection_tampering(self):
        model = self.adapter()
        checkpoint = checkpoint_fixture()
        baseline = model.project_catalog(checkpoint, dispositions_fixture(checkpoint))
        changes = [lambda d: d['inventories'].reverse(), lambda d: d['inventories'][0]['records'].clear(),
            lambda d: d['inventories'][0]['source_records'].clear(),
            lambda d: d['inventories'][0]['source_records'][0].update(publication_status='withheld'),
            lambda d: d['inventories'][0]['source_records'][0].update(content_hash='0'*64),
            lambda d: d['inventories'][0]['records'][0].update(title='unbound'),
            lambda d: d['inventories'][0]['records'][0].update(source_content_hash='0'*64),
            lambda d: d['inventories'][0]['source_records'][0].update(observed_changed_at=T1),
            lambda d: d['inventories'][0].update(last_successful_fetch_at=None),
            lambda d: d['inventories'][0]['records'][0].update(description='unreviewed')]
        for change in changes:
            result = copy.deepcopy(baseline)
            change(result)
            with self.subTest(change=change), self.assertRaises(ActivityPublicError):
                model.validate_catalog(result)
        record = baseline['inventories'][0]['records'][0]
        for field, invalid in [('permit_required', False), ('geographic_relationship', 'inside_park'),
                               ('availability_status', 'available'), ('url', 'https://www.nps.gov/romo/index.htm')]:
            value = copy.deepcopy(baseline)
            value['inventories'][0]['records'][0][field] = invalid
            rehash_view(value['inventories'][0]['records'][0])
            with self.subTest(field=field), self.assertRaises(ActivityPublicError):
                model.validate_catalog(value)

    def test_degraded_and_empty_successful_baselines_keep_source_clocks_and_rights_review_scope(self):
        model = self.adapter()
        checkpoint = checkpoint_fixture(T1)
        snapshot = checkpoint['inventories'][0]
        snapshot.update(collection_status='failed', coverage_status='incomplete',
                        error_code='provider_request_failed', last_successful_fetch_at=T0)
        snapshot['records'][0].update(observed_first_at=T0, observed_changed_at=T0)
        checkpoint['inventories'][4]['records'] = []
        bind(checkpoint)
        result = model.project_catalog(checkpoint, dispositions_fixture(checkpoint))
        self.assertEqual(result['inventories'][0]['last_successful_fetch_at'], T0)
        self.assertEqual(result['inventories'][4]['source_records'], [])
        rights = catalog_rights_fixture(result, T0)
        with self.assertRaises(ActivityPublicError):
            model.validate_catalog_rights(rights, result)
        rights['reviewed_at'] = T1
        self.assertEqual(validate_activity_rights(rights, result), rights)

    def test_rights_bind_every_selected_view_and_entire_projection_including_withheld(self):
        model = self.adapter()
        checkpoint = checkpoint_fixture()
        plan = dispositions_fixture(checkpoint)
        plan['records'][0].update(decision='withheld', categories='withheld')
        result = model.project_catalog(checkpoint, plan)
        rights = catalog_rights_fixture(result)
        self.assertEqual(len(model.validate_catalog_rights(rights, result)['records']), 4)
        changes = [lambda d: d['records'].pop(), lambda d: d['records'].reverse(),
            lambda d: d.update(projection_hash='0'*64),
            lambda d: d['records'][0].update(source_content_hash='0'*64),
            lambda d: d['records'][0].update(view_hash='0'*64),
            lambda d: d['records'][0].update(use_scope='normalized_activity_text_and_metadata'),
            lambda d: d['records'][0].update(media_reproduced=True),
            lambda d: d['policy'].update(nps_marks_allowed=0)]
        for change in changes:
            invalid = copy.deepcopy(rights)
            change(invalid)
            with self.subTest(change=change), self.assertRaises(ActivityPublicError):
                model.validate_catalog_rights(invalid, result)
        changed = copy.deepcopy(result)
        changed['inventories'][0]['source_records'][0]['content_hash'] = '0'*64
        with self.assertRaises(ActivityPublicError):
            model.validate_catalog_rights(rights, changed)
        changed = model.validate_catalog_rights(rights, result)
        changed['records'].clear()
        self.assertEqual(len(rights['records']), 4)

    def test_unicode_scalar_bound_sorting_and_microsecond_clock_boundary(self):
        model = self.adapter()
        checkpoint = checkpoint_fixture()
        record = checkpoint['inventories'][0]['records'][0]
        record.update(title='🏞'*1024, activity_categories=[{'id': '\ue000', 'name': 'é'},
            {'id': '🏞', 'name': 'a'}])
        rehash(record)
        bind(checkpoint)
        result = model.project_catalog(checkpoint, dispositions_fixture(checkpoint))
        self.assertEqual(result['inventories'][0]['records'][0]['title'], '🏞'*1024)
        value = copy.deepcopy(result)
        value['inventories'][0]['records'][0]['title'] += '🏞'
        rehash_view(value['inventories'][0]['records'][0])
        with self.assertRaises(ActivityPublicError):
            model.validate_catalog(value)

        value = copy.deepcopy(result)
        value['inventories'][0]['source_records'][0]['observed_changed_at'] = '2026-10-03T10:00:00.000001Z'
        with self.assertRaises(ActivityPublicError):
            model.validate_catalog(value)

    def test_wholly_withheld_retained_sources_still_need_success_and_observation_clocks(self):
        model = self.adapter()
        checkpoint = checkpoint_fixture()
        plan = dispositions_fixture(checkpoint)
        for row in plan['records']:
            row.update(decision='withheld', categories='withheld')
        result = model.project_catalog(checkpoint, plan)
        rights = catalog_rights_fixture(result)
        self.assertEqual(model.validate_catalog_rights(rights, result)['records'], [])
        self.assertEqual(sum(len(s['source_records']) for s in result['inventories']), 5)
        changes = [lambda d: d['inventories'][0].update(last_successful_fetch_at=None),
            lambda d: d['inventories'][0]['source_records'][0].update(observed_first_at=T1),
            lambda d: d['inventories'][0].update(collection_status='failed', coverage_status='incomplete',
                                                error_code='provider_request_failed', last_successful_fetch_at=None)]
        for change in changes:
            invalid = copy.deepcopy(result)
            change(invalid)
            with self.subTest(change=change), self.assertRaises(ActivityPublicError):
                model.validate_catalog(invalid)
        rights['reviewed_at'] = '2026-10-03T09:59:59.999999Z'
        with self.assertRaises(ActivityPublicError):
            model.validate_catalog_rights(rights, result)

    def test_source_and_selected_rows_remain_sorted_unique_even_with_interleaved_withholding(self):
        model = self.adapter()
        checkpoint = checkpoint_fixture()
        for code, inventory in zip(PILOT_CODES, checkpoint['inventories']):
            inventory.update(collect_activities(code, initial_activities(code), T0,
                lambda _start, code=code: page([activity(identifier=i, code=code) for i in ('c', 'a', 'b')])))
        bind(checkpoint)
        plan = dispositions_fixture(checkpoint)
        for row in plan['records']:
            if row['activity_id'] == 'b':
                row.update(decision='withheld', categories='withheld')
        result = model.project_catalog(checkpoint, plan)
        self.assertEqual([r['id'] for r in result['inventories'][0]['source_records']], ['a', 'b', 'c'])
        self.assertEqual([r['id'] for r in result['inventories'][0]['records']], ['a', 'c'])
        changes = [lambda d: d['inventories'][0]['source_records'].reverse(),
                   lambda d: d['inventories'][0]['records'].reverse(),
                   lambda d: d['inventories'][0]['source_records'].__setitem__(1, copy.deepcopy(d['inventories'][0]['source_records'][0])),
                   lambda d: d['inventories'][0]['records'].__setitem__(1, copy.deepcopy(d['inventories'][0]['records'][0]))]
        for change in changes:
            invalid = copy.deepcopy(result)
            change(invalid)
            with self.subTest(change=change), self.assertRaises(ActivityPublicError):
                model.validate_catalog(invalid)

    def test_catalog_refuses_record_inventory_and_scope_limits_without_trimming(self):
        model = self.adapter()
        checkpoint = checkpoint_fixture()
        result = model.project_catalog(checkpoint, dispositions_fixture(checkpoint))
        invalid = copy.deepcopy(result)
        record = invalid['inventories'][0]['records'][0]
        record['activity_categories'] = [{'id': f'{i:04d}', 'name': 'x'*1024} for i in range(300)]
        rehash_view(record)
        with self.assertRaises(ActivityPublicError):
            model.validate_catalog(invalid)
        invalid = copy.deepcopy(result)
        invalid['inventories'][0]['records'].clear()
        template = invalid['inventories'][0]['source_records'][0]
        invalid['inventories'][0]['source_records'] = [{**template, 'id': f'{i:04d}',
                                                      'publication_status': 'withheld'} for i in range(5001)]
        with self.assertRaises(ActivityPublicError):
            model.validate_catalog(invalid)
        invalid = copy.deepcopy(result)
        invalid['inventories'].pop()
        with self.assertRaises(ActivityPublicError):
            model.validate_catalog(invalid)
        invalid = copy.deepcopy(result)
        inventory = invalid['inventories'][0]
        source_template = inventory['source_records'][0]
        record_template = inventory['records'][0]
        # Each view is below 256 KiB, but their complete snapshot exceeds 8 MiB.
        inventory['source_records'] = []
        inventory['records'] = []
        for index in range(85):
            identifier = f'{index:04d}'
            inventory['source_records'].append({**source_template, 'id': identifier})
            record = {**record_template, 'id': identifier,
                      'activity_categories': [{'id': f'{i:04d}', 'name': 'x'*1024} for i in range(100)]}
            rehash_view(record)
            inventory['records'].append(record)
        with self.assertRaises(ActivityPublicError):
            model.validate_catalog(invalid)


if __name__ == '__main__':
    unittest.main()
