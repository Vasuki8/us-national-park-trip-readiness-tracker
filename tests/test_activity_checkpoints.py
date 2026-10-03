"""Synthetic immutable all-five activity checkpoint and recovery contracts."""
import copy
import hashlib
import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tracker.park_activities import PILOT_CODES, collect_activities, initial_activities
from test_park_activities import T0, T1, activity, page, rehash


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def bind(value):
    core = {key: item for key, item in value.items() if key != 'checkpoint_id'}
    value['checkpoint_id'] = hashlib.sha256(encoded(core)).hexdigest()
    return value


def checkpoint_fixture(now=T0):
    return bind({'schema_version': 1, 'purpose': 'private_park_activity_checkpoint',
                 'parent_checkpoint_id': None, 'checked_at': now,
                 'inventories': [collect_activities(code, initial_activities(code), now,
                     lambda _start, code=code: page([activity(code=code)])) for code in PILOT_CODES]})


@unittest.skipUnless(os.name == 'posix', 'Private checkpoint storage requires POSIX.')
class ActivityCheckpointTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.root.chmod(0o700)
        self.output = self.root / 'checkpoint.json'

    def adapter(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.activity_checkpoints'),
                             'The private activity checkpoint lifecycle is absent.')
        return importlib.import_module('tracker.activity_checkpoints')

    def write(self, value, name='previous.json'):
        source = self.root / name
        source.write_bytes(encoded(value))
        source.chmod(0o600)
        return source

    def collect(self, module=None, *, previous=None, now=T0, fetch_for=None, output=None):
        module = module or self.adapter()
        factory = fetch_for or (lambda code: lambda _start: page([activity(code=code)]))
        return module.collect_checkpoint(output or self.output, previous, now, factory)

    def test_complete_checkpoint_has_pilot_order_exact_hash_and_private_canonical_bytes(self):
        module = self.adapter()
        checkpoint = self.collect(module)
        self.assertEqual(checkpoint, checkpoint_fixture())
        self.assertEqual(self.output.read_bytes(), encoded(checkpoint))
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.output.stat().st_nlink, 1)
        self.assertEqual(module.verify_checkpoint(self.output), checkpoint)
        self.assertEqual(list(self.root.iterdir()), [self.output])
        self.assertNotIn('images', self.output.read_text())

    def test_later_attempt_binds_parent_without_mutating_source_or_observation_clocks(self):
        module = self.adapter()
        prior = checkpoint_fixture()
        source = self.write(prior)
        before = source.read_bytes(), source.stat().st_mtime_ns
        checkpoint = self.collect(module, previous=source, now=T1)
        self.assertEqual(checkpoint['parent_checkpoint_id'], prior['checkpoint_id'])
        for old, new in zip(prior['inventories'], checkpoint['inventories']):
            self.assertEqual(new['records'], old['records'])
            self.assertEqual(new['last_successful_fetch_at'], T1)
        self.assertEqual((source.read_bytes(), source.stat().st_mtime_ns), before)

    def test_failed_and_refused_later_pages_discard_partial_candidates_and_retain_each_baseline(self):
        module = self.adapter()
        prior = checkpoint_fixture()
        source = self.write(prior)
        offsets = []
        def factory(code):
            def fetch(start):
                offsets.append((code, start))
                if code in ('romo', 'zion'):
                    if start == 0:
                        return page([activity('partial', code=code)], total=2)
                    if code == 'romo':
                        raise TimeoutError('private exception')
                    return page([], total=2, start=start)
                return page([activity(code=code)])
            return fetch
        checkpoint = self.collect(module, previous=source, now=T1, fetch_for=factory)
        self.assertEqual([item['collection_status'] for item in checkpoint['inventories']],
                         ['success', 'failed', 'success', 'quarantined', 'success'])
        for index in (1, 3):
            retained = checkpoint['inventories'][index]
            self.assertEqual(retained['records'], prior['inventories'][index]['records'])
            self.assertEqual(retained['last_successful_fetch_at'], T0)
            self.assertEqual(retained['last_checked_at'], T1)
        self.assertIn(('romo', 1), offsets)
        self.assertIn(('zion', 1), offsets)
        self.assertNotIn('private exception', self.output.read_text())
        self.assertNotIn('partial', self.output.read_text())

    def test_initial_failed_attempt_has_no_success_or_invented_records(self):
        module = self.adapter()
        def factory(_code):
            def fetch(_start):
                raise OSError('private transport error')
            return fetch
        checkpoint = self.collect(module, fetch_for=factory)
        self.assertTrue(all(item['collection_status'] == 'failed' and not item['records']
                            and item['last_successful_fetch_at'] is None
                            for item in checkpoint['inventories']))

    def test_rehashed_malformed_schema_scope_state_source_and_clocks_are_refused(self):
        module = self.adapter()
        valid = checkpoint_fixture()
        mutations = [lambda v: v.update(schema_version=True),
                     lambda v: v.update(purpose='private_park_profile_checkpoint'),
                     lambda v: v.update(extra='private'),
                     lambda v: v.update(parent_checkpoint_id='bad'),
                     lambda v: v.update(inventories=v['inventories'][:-1]),
                     lambda v: v['inventories'].reverse(),
                     lambda v: v['inventories'].__setitem__(1, copy.deepcopy(v['inventories'][0])),
                     lambda v: v['inventories'].__setitem__(0, initial_activities('yose')),
                     lambda v: v['inventories'][0].update(last_checked_at=T1),
                     lambda v: v['inventories'][0].update(provider='Other'),
                     lambda v: v['inventories'][0].update(source_url='https://example.invalid'),
                     lambda v: v['inventories'][0].update(published_at=T0),
                     lambda v: v['inventories'][0]['records'][0].update(observed_changed_at=T1),
                     lambda v: v['inventories'][0]['records'][0].update(content_hash='0' * 64)]
        for mutate in mutations:
            candidate = copy.deepcopy(valid)
            mutate(candidate)
            bind(candidate)
            with self.subTest(mutation=mutate), self.assertRaises(module.ActivityCheckpointError):
                module.validate_checkpoint(candidate)
        candidate = copy.deepcopy(valid)
        candidate['checkpoint_id'] = '0' * 64
        with self.assertRaises(module.ActivityCheckpointError):
            module.validate_checkpoint(candidate)
        value = copy.deepcopy(valid)
        value['parent_checkpoint_id'] = value['checkpoint_id']
        with self.assertRaises(module.ActivityCheckpointError):
            module.validate_checkpoint(value)

    def test_validation_is_defensive_and_parent_is_only_a_reference(self):
        module = self.adapter()
        value = checkpoint_fixture()
        value['parent_checkpoint_id'] = 'a' * 64
        bind(value)
        source = self.write(value)
        checked = module.verify_checkpoint(source)
        checked['inventories'][0]['records'][0]['related_parks'].clear()
        self.assertEqual(len(value['inventories'][0]['records'][0]['related_parks']), 1)
        self.assertEqual(module.verify_checkpoint(source), value)

    def test_corrupt_previous_or_invalid_clock_refuses_before_factory_and_lock(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture())
        for now in (T0, '2026-10-03T06:00:00-04:00', '2026-10-03T09:00:00Z', 'invalid'):
            with self.subTest(now=now), self.assertRaises(module.ActivityCheckpointError):
                self.collect(module, previous=source, now=now,
                             fetch_for=lambda _code: self.fail('Invalid clock invoked factory.'))
        source.write_bytes(b'{')
        with self.assertRaises(module.ActivityCheckpointError):
            self.collect(module, previous=source, now=T1,
                         fetch_for=lambda _code: self.fail('Corrupt baseline invoked factory.'))
        self.assertEqual(list(self.root.iterdir()), [source])

    def test_last_park_failure_capacity_refuses_before_any_factory_or_output_lock(self):
        module = self.adapter()
        activity_module = importlib.import_module('tracker.park_activities')
        prior = checkpoint_fixture()
        prior['inventories'][-1] = collect_activities('grca', initial_activities('grca'), T0,
            lambda _start: page([activity(code='grca', shortDescription='x' * 4000)]))
        bind(prior)
        source = self.write(prior)
        maximum = max(len(encoded(item)) for item in prior['inventories'])
        with patch.object(activity_module, 'MAX_SNAPSHOT_BYTES', maximum):
            with patch.object(os, 'open', wraps=os.open) as opening:
                with self.assertRaises(module.ActivityCheckpointError):
                    self.collect(module, previous=source, now=T1,
                                 fetch_for=lambda _code: self.fail('Capacity refusal invoked factory.'))
        self.assertFalse(any(call.args[1] & os.O_CREAT for call in opening.call_args_list))
        self.assertEqual(list(self.root.iterdir()), [source])
        self.assertEqual(source.read_bytes(), encoded(prior))

    def test_callback_mutation_of_source_file_and_previous_provider_payload_cannot_rewrite_baselines(self):
        module = self.adapter()
        prior = checkpoint_fixture()
        source = self.write(prior)
        first_payload = page([activity()])
        def factory(code):
            if code == 'yose':
                source.write_bytes(b'changed externally after preflight')
                return lambda _start: first_payload
            first_payload['data'][0]['relatedParks'].clear()
            first_payload['data'][0]['title'] = 'mutated source payload'
            def fail(_start):
                raise TimeoutError('private')
            return fail
        checkpoint = self.collect(module, previous=source, now=T1, fetch_for=factory)
        self.assertEqual(checkpoint['parent_checkpoint_id'], prior['checkpoint_id'])
        self.assertEqual(checkpoint['inventories'][0]['records'], prior['inventories'][0]['records'])
        for index in range(1, 5):
            self.assertEqual(checkpoint['inventories'][index]['records'], prior['inventories'][index]['records'])

    def test_batch_above_eight_and_ten_mib_verifies_restores_and_exports_without_narrowing_park_bound(self):
        module = self.adapter()
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
            self.assertLess(len(encoded(inventory)), 8 * 1024 * 1024)
        bind(value)
        self.assertGreater(len(encoded(value)), 10 * 1024 * 1024)
        source = self.write(value)
        self.assertEqual(module.verify_checkpoint(source), value)
        self.assertEqual(module.restore_checkpoint(source, self.output), value)
        candidate = module.export_review_candidate(source, self.root / 'review.json')
        self.assertEqual(candidate['checkpoint'], value)

    def test_exact_checkpoint_bound_is_accepted_and_one_byte_over_refuses(self):
        module = self.adapter()
        value = checkpoint_fixture()
        size = len(encoded(value))
        with patch.object(module, 'MAX_CHECKPOINT_BYTES', size):
            self.assertEqual(module.validate_checkpoint(value), value)
        with patch.object(module, 'MAX_CHECKPOINT_BYTES', size - 1):
            with self.assertRaises(module.ActivityCheckpointError):
                module.validate_checkpoint(value)

    def test_private_input_permissions_hardlinks_fifo_duplicate_json_and_nonfinite_refuse(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture())
        source.chmod(0o644)
        with self.assertRaises(module.ActivityCheckpointError):
            module.verify_checkpoint(source)
        source.chmod(0o600)
        link = self.root / 'linked.json'
        os.link(source, link)
        with self.assertRaises(module.ActivityCheckpointError):
            module.verify_checkpoint(source)
        link.unlink()
        fifo = self.root / 'fifo'
        os.mkfifo(fifo, 0o600)
        with self.assertRaises(module.ActivityCheckpointError):
            module.verify_checkpoint(fifo)
        for raw in (b'{', b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff'):
            source.write_bytes(raw)
            with self.subTest(raw=raw), self.assertRaises(module.ActivityCheckpointError):
                module.verify_checkpoint(source)

    def test_unsafe_output_insecure_parent_and_existing_output_precede_factory(self):
        module = self.adapter()
        repo = Path(__file__).resolve().parents[1]
        symlink = self.root / 'alias'
        symlink.symlink_to(self.root, target_is_directory=True)
        for output in (Path('relative'), self.root / '..' / 'escaped', repo / 'ignored.json',
                       Path('//' + str(repo).lstrip('/')) / 'file', repo.parent / 'file',
                       self.root / 'missing' / 'file', symlink / 'file'):
            with self.subTest(output=output), self.assertRaises(module.ActivityCheckpointError):
                self.collect(module, output=output,
                             fetch_for=lambda _code: self.fail('Unsafe output invoked factory.'))
        self.root.chmod(0o755)
        with self.assertRaises(module.ActivityCheckpointError):
            self.collect(module, fetch_for=lambda _code: self.fail('Insecure parent invoked factory.'))
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o755)
        self.root.chmod(0o700)
        self.output.write_bytes(b'keep')
        self.output.chmod(0o600)
        with self.assertRaises(module.ActivityCheckpointError):
            self.collect(module, fetch_for=lambda _code: self.fail('Existing output invoked factory.'))
        self.assertEqual(self.output.read_bytes(), b'keep')

    def test_competing_output_lock_refuses_factory_and_different_outputs_can_branch(self):
        module = self.adapter()
        prior = checkpoint_fixture()
        source = self.write(prior)
        def factory(code):
            if code == 'yose':
                with self.assertRaises(module.ActivityCheckpointError):
                    self.collect(module, previous=source, now=T1,
                        fetch_for=lambda _code: self.fail('Competing writer invoked factory.'))
            return lambda _start: page([activity(code=code)])
        first = self.collect(module, previous=source, now=T1, fetch_for=factory)
        second = self.collect(module, previous=source, now=T1, output=self.root / 'branch.json')
        self.assertEqual(first, second)

    def test_source_output_and_lock_collision_never_changes_source(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture(), name='checkpoint.json.lock')
        before = source.read_bytes()
        with self.assertRaises(module.ActivityCheckpointError):
            self.collect(module, previous=source, now=T1)
        with self.assertRaises(module.ActivityCheckpointError):
            module.restore_checkpoint(source, source)
        self.assertEqual(source.read_bytes(), before)

    def test_programming_error_and_keyboard_interrupt_leave_no_preinstall_output(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture())
        before = source.read_bytes()
        for error in (RuntimeError('private programming text'), KeyboardInterrupt('private interruption')):
            calls = []
            def factory(code):
                calls.append(code)
                if code == 'yell':
                    raise error
                return lambda _start: page([activity(code=code)])
            with self.subTest(error=type(error)), self.assertRaises(type(error)):
                self.collect(module, previous=source, now=T1, fetch_for=factory)
            self.assertEqual(calls, ['yose', 'romo', 'yell'])
            self.assertEqual(list(self.root.iterdir()), [source])
            self.assertEqual(source.read_bytes(), before)

    def test_precommit_storage_error_cleans_new_files_and_postcommit_failure_keeps_verifiable_output(self):
        module = self.adapter()
        storage = importlib.import_module('tracker.private_checkpoint_io')
        with patch.object(storage.os, 'link', side_effect=OSError('private filesystem error')):
            with self.assertRaises(OSError):
                self.collect(module)
        self.assertEqual(list(self.root.iterdir()), [])
        with patch.object(storage, 'sync_private_directory', side_effect=KeyboardInterrupt('private sync')):
            with self.assertRaises(KeyboardInterrupt):
                self.collect(module)
        self.assertEqual(module.verify_checkpoint(self.output), checkpoint_fixture())
        self.assertEqual(list(self.root.iterdir()), [self.output])

    def test_postcommit_temporary_cleanup_failure_preserves_multilink_evidence_for_operator_review(self):
        module = self.adapter()
        original_unlink = Path.unlink
        def interrupted_unlink(path, *args, **kwargs):
            if path.name.startswith('.checkpoint-'):
                raise OSError('private cleanup failure')
            return original_unlink(path, *args, **kwargs)
        with patch.object(Path, 'unlink', interrupted_unlink):
            with self.assertRaises(OSError):
                self.collect(module)
        self.assertEqual(self.output.read_bytes(), encoded(checkpoint_fixture()))
        self.assertEqual(self.output.stat().st_nlink, 2)
        with self.assertRaises(module.ActivityCheckpointError):
            module.verify_checkpoint(self.output)
        self.assertFalse(Path(str(self.output) + '.lock').exists())
        self.assertEqual(len(list(self.root.glob('.checkpoint-*.tmp'))), 1)

    def test_restore_preserves_exact_bytes_clocks_source_and_refuses_overwrite(self):
        module = self.adapter()
        value = checkpoint_fixture()
        source = self.write(value)
        before = source.read_bytes(), source.stat().st_mtime_ns
        self.assertEqual(module.restore_checkpoint(source, self.output), value)
        self.assertEqual(self.output.read_bytes(), source.read_bytes())
        self.assertEqual((source.read_bytes(), source.stat().st_mtime_ns), before)
        with self.assertRaises(module.ActivityCheckpointError):
            module.restore_checkpoint(source, self.output)

    def test_review_export_preserves_degraded_checkpoint_without_approval_or_rights_claim(self):
        module = self.adapter()
        value = checkpoint_fixture()
        original = value['inventories'][0]
        def failed(_start):
            raise TimeoutError('private')
        value['inventories'][0] = collect_activities('yose', original, T1, failed)
        for inventory in value['inventories'][1:]:
            inventory['last_checked_at'] = T1
            inventory['last_successful_fetch_at'] = T1
        value['checked_at'] = T1
        bind(value)
        source = self.write(value)
        candidate = module.export_review_candidate(source, self.output)
        self.assertEqual(candidate['purpose'], 'private_park_activity_review_candidate')
        self.assertEqual(candidate['checkpoint'], value)
        self.assertEqual(candidate['checkpoint_id'], value['checkpoint_id'])
        self.assertEqual(candidate['source_rights_status'], 'not_checked')
        for field in ('approval_performed', 'publication_performed', 'site_data_written'):
            self.assertIs(candidate[field], False)
        self.assertEqual(self.output.read_bytes(), encoded(candidate))

    def test_review_capacity_refusal_precedes_output_lock_or_temporary(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture())
        with patch.object(module, 'MAX_REVIEW_BYTES', len(source.read_bytes())):
            with self.assertRaises(module.ActivityCheckpointError):
                module.export_review_candidate(source, self.output)
        self.assertEqual(list(self.root.iterdir()), [source])

    def test_offline_verify_restore_and_export_ignore_environment(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture())
        with patch.object(os.environ, 'get', side_effect=AssertionError('Offline key access')):
            module.verify_checkpoint(source)
            module.restore_checkpoint(source, self.output)
            module.export_review_candidate(source, self.root / 'review.json')


if __name__ == '__main__':
    unittest.main()
