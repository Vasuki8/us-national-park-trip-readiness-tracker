"""Exact synthetic activity text-rights and bounded public-file contracts."""
import copy
import hashlib
import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tracker.park_activities import (PILOT_CODES, ActivityCollectionError,
                                    collect_activities, initial_activities)
from test_activity_checkpoints import checkpoint_fixture, bind, encoded
from test_park_activities import T0, T1, activity, page, rehash

POLICY = {
    'ownership_url': 'https://www.nps.gov/aboutus/disclaimer.htm',
    'marks_url': 'https://www.nps.gov/subjects/partnerships/arrowhead-requests.htm?fullweb=1',
    'commercial_notice': 'No protection is claimed in original U.S. Government works.',
    'third_party_material_allowed': False, 'nps_marks_allowed': False,
    'raw_private_captures_public': False,
}


def public_fixture(checkpoint=None):
    value = checkpoint_fixture() if checkpoint is None else checkpoint
    return {'schema_version': 1, 'purpose': 'public_park_activities',
            'inventories': copy.deepcopy(value['inventories'])}


def rights_fixture(dataset, reviewed_at=T1):
    return {'schema_version': 1, 'purpose': 'public_park_activity_text_rights',
            'reviewed_at': reviewed_at,
            'review_method': 'official_nps_policy_and_exact_activity_review',
            'policy': copy.deepcopy(POLICY),
            'records': [{'park_code': s['park_code'], 'activity_id': r['id'],
                         'source_url': s['source_url'], 'content_hash': r['content_hash'],
                         'classification': 'nps_government_text',
                         'use_scope': 'normalized_activity_text_and_metadata',
                         'third_party_material_reproduced': False,
                         'nps_marks_reproduced': False, 'media_reproduced': False}
                        for s in dataset['inventories'] for r in s['records']]}


def large_checkpoint():
    value = checkpoint_fixture()
    for inventory in value['inventories']:
        template = inventory['records'][0]
        template['description'] = 'x' * 50000
        records = []
        for number in range(44):
            record = copy.deepcopy(template)
            record['id'] = f'large-{number:03d}'
            rehash(record)
            records.append(record)
        inventory['records'] = records
    return bind(value)


class ActivityPublicTests(unittest.TestCase):
    def adapter(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.activity_public'),
                             'The exact public activity contract is absent.')
        return importlib.import_module('tracker.activity_public')

    def test_projection_preserves_complete_records_clocks_and_isolated_copies(self):
        model = self.adapter()
        checkpoint = checkpoint_fixture()
        projected = model.project_checkpoint(checkpoint)
        self.assertEqual(projected, public_fixture(checkpoint))
        self.assertNotIn('checkpoint_id', projected)
        self.assertNotIn('parent_checkpoint_id', projected)
        record = projected['inventories'][0]['records'][0]
        self.assertEqual(record['geographic_relationship'], 'unconfirmed')
        self.assertIsNone(record['permit_required'])
        self.assertFalse(record['fees_apply'])
        record['description'] = 'caller changed result'
        self.assertNotEqual(projected, public_fixture(checkpoint))

    def test_never_successful_refused_but_confirmed_empty_inventories_valid(self):
        model = self.adapter()
        empty = public_fixture()
        for code, inventory in zip(PILOT_CODES, empty['inventories']):
            inventory.update(collect_activities(code, initial_activities(code), T0,
                                               lambda start: page([], total=0)))
        self.assertEqual(model.validate_public_activities(empty), empty)
        self.assertEqual(model.validate_activity_rights(rights_fixture(empty), empty)['records'], [])
        def failed(_):
            raise ActivityCollectionError('private provider text')
        empty['inventories'][4] = collect_activities('grca', initial_activities('grca'), T0, failed)
        with self.assertRaises(model.ActivityPublicError):
            model.validate_public_activities(empty)

    def test_degraded_retained_state_and_null_empty_fields_survive(self):
        model = self.adapter()
        data = public_fixture()
        for snapshot, status in zip(data['inventories'], ('failed', 'quarantined')):
            snapshot.update(collection_status=status, coverage_status='incomplete', last_checked_at=T1,
                            error_code='provider_request_failed' if status == 'failed' else 'response_requires_review')
        for snapshot in data['inventories'][2:]:
            snapshot['last_checked_at'] = snapshot['last_successful_fetch_at'] = T1
        record = data['inventories'][0]['records'][0]
        record.update(description=None, long_description='', seasons=None, times_of_day=[],
                      activity_categories=[], pets_permitted=None)
        rehash(record)
        self.assertEqual(model.validate_public_activities(data), data)
        self.assertEqual(model.validate_activity_rights(rights_fixture(data), data), rights_fixture(data))

    def test_exact_public_scope_hashes_sources_and_common_attempt_clock_required(self):
        model = self.adapter()
        changes = [lambda d: d.update(checkpoint_id='0'*64),
                   lambda d: d['inventories'].reverse(), lambda d: d['inventories'].pop(),
                   lambda d: d['inventories'][1].update(last_checked_at=T1, last_successful_fetch_at=T1),
                   lambda d: d['inventories'][0].update(source_url='https://example.invalid/'),
                   lambda d: d['inventories'][0]['records'][0].update(credit='unbound change'),
                   lambda d: d['inventories'][0].update(published_at=T0)]
        for change in changes:
            data = public_fixture()
            change(data)
            with self.subTest(change=change), self.assertRaises(model.ActivityPublicError):
                model.validate_public_activities(data)

    def test_rights_cover_cross_park_repeated_ids_once_each(self):
        model = self.adapter()
        data = public_fixture()
        rights = rights_fixture(data)
        self.assertEqual(len(set(row['activity_id'] for row in rights['records'])), 1)
        self.assertEqual(model.validate_activity_rights(rights, data), rights)
        result = model.validate_activity_rights(rights, data)
        result['records'][0]['activity_id'] = 'caller changed copy'
        self.assertNotEqual(result, rights)

    def test_rights_require_exact_all_strings_hash_scope_and_flags(self):
        model = self.adapter()
        data = public_fixture()
        for field, value in [('activity_id', 'other'), ('park_code', 'grca'),
                             ('source_url', 'https://www.nps.gov/yose/'), ('content_hash', '0'*64),
                             ('classification', 'third_party'), ('use_scope', 'normalized_profile_text_and_category_names'),
                             ('media_reproduced', True), ('nps_marks_reproduced', 0),
                             ('third_party_material_reproduced', True)]:
            rights = rights_fixture(data)
            rights['records'][0][field] = value
            with self.subTest(field=field), self.assertRaises(model.ActivityPublicError):
                model.validate_activity_rights(rights, data)
        data['inventories'][0]['records'][0]['credit'] = 'changed reviewed credit'
        rehash(data['inventories'][0]['records'][0])
        with self.assertRaises(model.ActivityPublicError):
            model.validate_activity_rights(rights_fixture(public_fixture()), data)

    def test_omitted_extra_reordered_duplicate_rights_and_profile_manifest_refused(self):
        model = self.adapter()
        data = public_fixture()
        changes = [lambda r: r['records'].pop(), lambda r: r['records'].append(copy.deepcopy(r['records'][0])),
                   lambda r: r['records'].reverse(), lambda r: r['records'].__setitem__(1, copy.deepcopy(r['records'][0])),
                   lambda r: r.update(purpose='public_park_profile_text_rights'),
                   lambda r: r.update(review_method='official_nps_policy_and_exact_profile_review'),
                   lambda r: r['policy'].update(third_party_material_allowed=0),
                   lambda r: r.update(private_review='not permitted')]
        for change in changes:
            rights = rights_fixture(data)
            change(rights)
            with self.subTest(change=change), self.assertRaises(model.ActivityPublicError):
                model.validate_activity_rights(rights, data)

    def test_review_clock_covers_empty_inventory_and_exact_microsecond_attempt(self):
        model = self.adapter()
        data = public_fixture()
        for snapshot in data['inventories']:
            snapshot['last_checked_at'] = snapshot['last_successful_fetch_at'] = '2026-10-03T10:00:00.000001Z'
        data['inventories'][4]['records'] = []
        with self.assertRaises(model.ActivityPublicError):
            model.validate_activity_rights(rights_fixture(data, T0), data)
        self.assertEqual(model.validate_activity_rights(rights_fixture(data, '2026-10-03T06:00:00.000001-04:00'), data)['records'],
                         rights_fixture(data)['records'])

    def test_canonical_hash_parsing_and_explicit_bounds_preserve_legacy_defaults(self):
        model = self.adapter()
        value = {'text': 'Synthetic café 🏞', 'ids': ['\ue000', '\U00010000']}
        raw = encoded(value)
        self.assertEqual(model.canonical_activity_json(value, max_bytes=len(raw)), raw)
        self.assertEqual(model.activity_digest(value, max_bytes=len(raw)), hashlib.sha256(raw).hexdigest())
        self.assertEqual(model.parse_activity_json(raw, max_bytes=len(raw)), value)
        for call in (model.canonical_activity_json, model.activity_digest):
            with self.assertRaises(model.ActivityPublicError):
                call(value, max_bytes=len(raw)-1)
        with self.assertRaises(model.ActivityPublicError):
            model.parse_activity_json(raw, max_bytes=len(raw)-1)
        for limit in (0, -1, True, '100', 1.5):
            with self.subTest(limit=limit), self.assertRaises(model.ActivityPublicError):
                model.parse_activity_json(raw, max_bytes=limit)

    def test_strict_parser_refuses_duplicate_nonfinite_overflow_utf8_and_surrogates(self):
        model = self.adapter()
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}', b'\xff',
                    b'{"x":"\\ud800"}', b'['*10000+b']'*10000):
            with self.subTest(raw=raw[:50]), self.assertRaises(model.ActivityPublicError):
                model.parse_activity_json(raw, max_bytes=100000)

    def test_large_projection_hashes_and_pair_read_beyond_eight_and_ten_mib(self):
        model = self.adapter()
        checkpoint = large_checkpoint()
        data = model.project_checkpoint(checkpoint)
        raw = encoded(data)
        self.assertGreater(len(raw), 10*1024*1024)
        self.assertEqual(model.activity_digest(data), hashlib.sha256(raw).hexdigest())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_pair(root, data)
            pair = model.read_public_activity_pair(root)
            self.assertEqual(pair['dataset'], data)
            self.assertEqual(pair['current'][model.PUBLIC_FILES[0]], raw+b'\n')

    def test_public_and_rights_exact_bounds_or_one_byte_over(self):
        model = self.adapter()
        data, rights = public_fixture(), rights_fixture(public_fixture())
        for name, value, validate in [('MAX_PUBLIC_BYTES', data, lambda: model.validate_public_activities(data)),
                                      ('MAX_RIGHTS_BYTES', rights, lambda: model.validate_activity_rights(rights, data))]:
            size = len(encoded(value))
            with patch.object(model, name, size):
                self.assertEqual(validate(), value)
            with patch.object(model, name, size-1), self.assertRaises(model.ActivityPublicError):
                validate()

    def write_pair(self, root, data=None, *, newline=True):
        data = public_fixture() if data is None else data
        folder = root/'data'
        folder.mkdir(exist_ok=True)
        for name, value in zip(('park-activities.json', 'activity-source-rights.json'), (data, rights_fixture(data))):
            (folder/name).write_bytes(encoded(value)+(b'\n' if newline else b''))

    def test_public_pair_absent_canonical_and_optional_single_newline(self):
        model = self.adapter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(model.read_public_activity_pair(root),
                             {'current': dict.fromkeys(model.PUBLIC_FILES), 'dataset': None, 'rights': None})
            for newline in (False, True):
                self.write_pair(root, newline=newline)
                pair = model.read_public_activity_pair(root)
                self.assertEqual(pair['dataset'], public_fixture())
                self.assertEqual(pair['rights'], rights_fixture(public_fixture()))

    def test_incomplete_noncanonical_duplicate_utf8_and_unknown_public_bytes_refused(self):
        model = self.adapter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_pair(root)
            target = root/model.PUBLIC_FILES[0]
            original = target.read_bytes()
            for raw in (json.dumps(public_fixture()).encode(), original+b'\n', b'\xef\xbb\xbf'+original,
                        b'\xff', original.replace(b'"schema_version":1', b'"schema_version":1,"schema_version":1', 1)):
                target.write_bytes(raw)
                with self.subTest(raw=raw[:30]), self.assertRaises(model.ActivityPublicError):
                    model.read_public_activity_pair(root)
            target.unlink()
            with self.assertRaises(model.ActivityPublicError):
                model.read_public_activity_pair(root)

    @unittest.skipUnless(os.name == 'posix', 'POSIX synthetic file types')
    def test_public_symlink_directory_and_fifo_refused_without_blocking(self):
        model = self.adapter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_pair(root)
            target = root/model.PUBLIC_FILES[0]
            saved = root/'saved.json'
            target.rename(saved)
            for install in (lambda: target.symlink_to(saved), lambda: target.mkdir(), lambda: os.mkfifo(target)):
                install()
                with self.assertRaises(model.ActivityPublicError):
                    model.read_public_activity_pair(root)
                target.rmdir() if target.is_dir() and not target.is_symlink() else target.unlink()
            target.write_bytes(saved.read_bytes())
            folder = root/'data'
            actual = root/'other-data'
            folder.rename(actual)
            folder.symlink_to(actual, target_is_directory=True)
            with self.assertRaises(model.ActivityPublicError):
                model.read_public_activity_pair(root)

    def test_public_file_exact_canonical_bound_allows_one_final_newline(self):
        model = self.adapter()
        data, rights = public_fixture(), rights_fixture(public_fixture())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_pair(root, data)
            for name, value in (('MAX_PUBLIC_BYTES', data), ('MAX_RIGHTS_BYTES', rights)):
                size = len(encoded(value))
                with patch.object(model, name, size):
                    self.assertEqual(model.read_public_activity_pair(root)['dataset'], data)
                with patch.object(model, name, size-1), self.assertRaises(model.ActivityPublicError):
                    model.read_public_activity_pair(root)

    @unittest.skipUnless(os.name == 'posix', 'POSIX synthetic open boundary')
    def test_public_replacement_between_stat_and_open_is_refused(self):
        model = self.adapter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_pair(root)
            target = root/model.PUBLIC_FILES[0]
            original = target.read_bytes()
            open_file = os.open
            def replaced(path, flags):
                if path == target:
                    target.rename(root/'original.json')
                    target.write_bytes(original)
                return open_file(path, flags)
            with patch.object(model.os, 'open', side_effect=replaced), self.assertRaises(model.ActivityPublicError) as error:
                model.read_public_activity_pair(root)
            self.assertEqual(str(error.exception), 'activity_public_input_changed')


if __name__ == '__main__':
    unittest.main()
