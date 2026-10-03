"""Synthetic immutable profile checkpoints; temporary POSIX storage only."""
import copy
import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tracker.history_model import canonical, digest
from tracker.park_profiles import PILOT_CODES, ProfileCollectionError, collect_profile, initial_profile

NOW = '2026-10-02T12:00:00Z'
LATER = '2026-10-03T12:00:00Z'


def payload(code, description='Synthetic introduction'):
    return {'total': '1', 'start': '0', 'data': [{
        'id': f'profile-{code}', 'parkCode': code, 'fullName': f'Synthetic {code}',
        'url': f'https://www.nps.gov/{code}/index.htm', 'description': description,
        'weatherInfo': 'Synthetic seasonal context', 'activities': [],
        'images': [{'url': 'https://example.invalid/private-image'}],
    }]}


def checkpoint_fixture(now=NOW):
    core = {'schema_version': 1, 'purpose': 'private_park_profile_checkpoint',
            'parent_checkpoint_id': None, 'checked_at': now,
            'profiles': [collect_profile(code, initial_profile(code), now,
                                        lambda _start, code=code: payload(code)) for code in PILOT_CODES]}
    return {**core, 'checkpoint_id': digest(core)}


@unittest.skipUnless(os.name == 'posix', 'Owner-only private tools require POSIX.')
class ProfileCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root.chmod(0o700)
        self.output = self.root / 'checkpoint.json'

    def adapter(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.profile_checkpoints'),
                             'The private checkpoint lifecycle is not implemented.')
        return importlib.import_module('tracker.profile_checkpoints')

    def write(self, value, name='previous.json'):
        path = self.root / name
        path.write_bytes(canonical(value))
        path.chmod(0o600)
        return path

    def collect(self, module=None, *, previous=None, now=NOW, fetch_for=None, output=None):
        module = module or self.adapter()
        fetch_for = fetch_for or (lambda code: lambda _start: payload(code))
        return module.collect_checkpoint(output or self.output, previous, now, fetch_for)

    def test_all_five_checkpoint_is_private_canonical_and_source_specific(self):
        module = self.adapter()
        result = self.collect(module)
        self.assertEqual(result, checkpoint_fixture())
        self.assertEqual(self.output.read_bytes(), canonical(result))
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.output.stat().st_nlink, 1)
        self.assertEqual(module.verify_checkpoint(self.output), result)
        self.assertEqual(set(p.name for p in self.root.iterdir()), {'checkpoint.json'})
        self.assertNotIn('images', self.output.read_text())

    def test_new_checkpoint_preserves_baseline_and_binds_parent(self):
        module = self.adapter()
        prior = checkpoint_fixture()
        source = self.write(prior)
        before = (source.read_bytes(), source.stat().st_mtime_ns)
        result = self.collect(module, previous=source, now=LATER)
        self.assertEqual(result['parent_checkpoint_id'], prior['checkpoint_id'])
        self.assertEqual(result['checked_at'], LATER)
        for old, new in zip(prior['profiles'], result['profiles']):
            self.assertEqual(new['profile'], old['profile'])
            self.assertEqual(new['last_successful_fetch_at'], LATER)
        self.assertEqual((source.read_bytes(), source.stat().st_mtime_ns), before)

    def test_failure_and_quarantine_retain_each_parks_last_good_evidence(self):
        module = self.adapter()
        prior = checkpoint_fixture()
        source = self.write(prior)
        def fetch_for(code):
            def fetch(_start):
                if code == 'romo':
                    raise ProfileCollectionError('untrusted body and key')
                return {'total': '0', 'start': '0', 'data': []} if code == 'zion' else payload(code)
            return fetch
        result = self.collect(module, previous=source, now=LATER, fetch_for=fetch_for)
        self.assertEqual([p['collection_status'] for p in result['profiles']],
                         ['success', 'failed', 'success', 'quarantined', 'success'])
        for index in (1, 3):
            self.assertEqual(result['profiles'][index]['profile'], prior['profiles'][index]['profile'])
            self.assertEqual(result['profiles'][index]['last_successful_fetch_at'], NOW)
        self.assertNotIn('untrusted body', self.output.read_text())

    def test_first_failed_run_does_not_invent_profile_or_success(self):
        module = self.adapter()
        def failed(_code):
            def fetch(_start):
                raise TimeoutError('private exception')
            return fetch
        result = self.collect(module, fetch_for=failed)
        for item in result['profiles']:
            self.assertEqual(item['collection_status'], 'failed')
            self.assertIsNone(item['profile'])
            self.assertIsNone(item['last_successful_fetch_at'])

    def test_validate_returns_copy(self):
        module = self.adapter()
        value = checkpoint_fixture()
        result = module.validate_checkpoint(value)
        result['profiles'][0]['profile']['description'] = 'Changed locally'
        self.assertEqual(value['profiles'][0]['profile']['description'], 'Synthetic introduction')

    def test_checkpoint_hash_and_full_schema_are_checked(self):
        module = self.adapter()
        valid = checkpoint_fixture()
        mutations = [lambda v: v.update(checkpoint_id='0' * 64),
                     lambda v: v.update(extra='private'),
                     lambda v: v.update(schema_version=True),
                     lambda v: v.update(purpose='public_profiles'),
                     lambda v: v.update(parent_checkpoint_id='bad'),
                     lambda v: v.update(parent_checkpoint_id=v['checkpoint_id']),
                     lambda v: v.update(profiles=v['profiles'][:-1]),
                     lambda v: v['profiles'].reverse(),
                     lambda v: v['profiles'].__setitem__(1, copy.deepcopy(v['profiles'][0])),
                     lambda v: v['profiles'][0].update(last_checked_at=LATER),
                     lambda v: v['profiles'][0]['profile'].update(content_hash='0' * 64),
                     lambda v: v['profiles'][0].update(published_at=NOW)]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                value = copy.deepcopy(valid)
                mutate(value)
                with self.assertRaises(module.ProfileCheckpointError):
                    module.validate_checkpoint(value)

    def test_rehashed_unattempted_or_cross_clock_snapshot_is_refused(self):
        module = self.adapter()
        for replacement in (initial_profile('yose'), checkpoint_fixture(LATER)['profiles'][0]):
            value = checkpoint_fixture()
            value['profiles'][0] = replacement
            value['checkpoint_id'] = digest({k: v for k, v in value.items() if k != 'checkpoint_id'})
            with self.assertRaises(module.ProfileCheckpointError):
                module.validate_checkpoint(value)

    def test_invalid_previous_checkpoint_refuses_before_fetch_and_output(self):
        module = self.adapter()
        value = checkpoint_fixture()
        value['profiles'][0]['profile']['description'] = 'Corruption'
        source = self.write(value)
        with self.assertRaises(module.ProfileCheckpointError):
            self.collect(module, previous=source, now=LATER,
                         fetch_for=lambda _code: self.fail('Invalid evidence must precede requests'))
        self.assertFalse(self.output.exists())
        self.assertFalse(Path(str(self.output) + '.lock').exists())

    def test_equal_rewound_invalid_or_future_previous_clock_precedes_fetch(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture())
        for now in (NOW, '2026-10-02T08:00:00-04:00', '2026-10-01T12:00:00Z', 'invalid'):
            with self.subTest(now=now):
                with self.assertRaises(module.ProfileCheckpointError):
                    self.collect(module, previous=source, now=now,
                                 fetch_for=lambda _code: self.fail('Clock refusal must precede fetch'))
                self.assertFalse(self.output.exists())

    def test_destination_boundaries_refuse_before_fetch(self):
        module = self.adapter()
        repo = Path(__file__).resolve().parents[1]
        alias = Path('//' + str(repo).lstrip('/')) / 'ignored-profile.json'
        bad = [Path('relative.json'), self.root / '..' / 'escaped.json',
               repo / 'data' / 'profile.json', repo.parent / 'profile.json', alias,
               self.root / 'missing' / 'profile.json']
        for destination in bad:
            with self.subTest(destination=destination):
                with self.assertRaises(module.ProfileCheckpointError):
                    self.collect(module, output=destination,
                                 fetch_for=lambda _code: self.fail('Unsafe destination fetched'))

    def test_insecure_parent_is_never_repaired(self):
        module = self.adapter()
        self.root.chmod(0o755)
        with self.assertRaises(module.ProfileCheckpointError):
            self.collect(module, fetch_for=lambda _code: self.fail('Insecure parent fetched'))
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o755)
        self.assertFalse(self.output.exists())

    def test_symlink_ancestry_is_refused(self):
        module = self.adapter()
        alias = self.root / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(module.ProfileCheckpointError):
            self.collect(module, output=alias / 'new.json')

    def test_insecure_hardlinked_and_nonregular_inputs_are_refused(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture())
        source.chmod(0o644)
        with self.assertRaises(module.ProfileCheckpointError):
            module.verify_checkpoint(source)
        source.chmod(0o600)
        link = self.root / 'linked.json'
        os.link(source, link)
        with self.assertRaises(module.ProfileCheckpointError):
            module.verify_checkpoint(source)
        link.unlink()
        fifo = self.root / 'fifo'
        os.mkfifo(fifo, 0o600)
        with self.assertRaises(module.ProfileCheckpointError):
            module.verify_checkpoint(fifo)

    def test_input_parent_must_be_private(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture())
        self.root.chmod(0o755)
        with self.assertRaises(module.ProfileCheckpointError):
            module.verify_checkpoint(source)

    def test_corrupt_duplicate_nonfinite_and_oversized_json_refused(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture())
        for raw in (b'{', b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff', b' ' * (8 * 1024 * 1024 + 1)):
            with self.subTest(size=len(raw)):
                source.write_bytes(raw)
                with self.assertRaises(module.ProfileCheckpointError):
                    module.verify_checkpoint(source)

    def test_existing_output_prevents_fetch_and_preserves_bytes(self):
        module = self.adapter()
        self.output.write_bytes(b'keep this evidence')
        self.output.chmod(0o600)
        with self.assertRaises(module.ProfileCheckpointError):
            self.collect(module, fetch_for=lambda _code: self.fail('Existing output fetched'))
        self.assertEqual(self.output.read_bytes(), b'keep this evidence')

    def test_existing_lock_is_not_stolen(self):
        module = self.adapter()
        lock = Path(str(self.output) + '.lock')
        lock.write_bytes(b'other writer')
        lock.chmod(0o600)
        with self.assertRaises(module.ProfileCheckpointError):
            self.collect(module, fetch_for=lambda _code: self.fail('Locked output fetched'))
        self.assertEqual(lock.read_bytes(), b'other writer')

    def test_source_destination_and_lock_collision_is_refused(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture(), name='checkpoint.json.lock')
        before = source.read_bytes()
        with self.assertRaises(module.ProfileCheckpointError):
            self.collect(module, previous=source, now=LATER)
        self.assertEqual(source.read_bytes(), before)
        with self.assertRaises(module.ProfileCheckpointError):
            module.restore_checkpoint(source, source)

    def test_programming_interruption_keeps_previous_without_completed_output(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture())
        before = source.read_bytes()
        calls = []
        def fetch_for(code):
            calls.append(code)
            if code == 'yell':
                raise RuntimeError('programming error with private text')
            return lambda _start: payload(code)
        with self.assertRaises(RuntimeError):
            self.collect(module, previous=source, now=LATER, fetch_for=fetch_for)
        self.assertEqual(calls, ['yose', 'romo', 'yell'])
        self.assertEqual(source.read_bytes(), before)
        self.assertFalse(self.output.exists())
        self.assertEqual(set(p.name for p in self.root.iterdir()), {'previous.json'})

    def test_competing_same_output_cannot_fetch(self):
        module = self.adapter()
        def fetch_for(code):
            if code == 'yose':
                with self.assertRaises(module.ProfileCheckpointError):
                    self.collect(module, fetch_for=lambda _code: self.fail('Competing writer fetched'))
            return lambda _start: payload(code)
        self.collect(module, fetch_for=fetch_for)
        self.assertEqual(module.verify_checkpoint(self.output), checkpoint_fixture())

    def test_different_outputs_can_fork_from_same_explicit_parent(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture())
        first = self.collect(module, previous=source, now=LATER)
        second = self.collect(module, previous=source, now=LATER, output=self.root / 'fork.json')
        self.assertEqual(first, second)

    def test_preinstall_error_does_not_leave_output_or_temp(self):
        module = self.adapter()
        with patch.object(module.os, 'link', side_effect=OSError('private filesystem text')):
            with self.assertRaises(OSError):
                self.collect(module)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_postinstall_sync_failure_preserves_verifiable_checkpoint(self):
        module = self.adapter()
        with patch.object(module, '_sync_directory', side_effect=OSError('sync failed')):
            with self.assertRaises(OSError):
                self.collect(module)
        self.assertEqual(module.verify_checkpoint(self.output), checkpoint_fixture())

    def test_restore_is_verified_fresh_private_and_source_unchanged(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture())
        before = (source.read_bytes(), source.stat().st_mtime_ns)
        restored = module.restore_checkpoint(source, self.output)
        self.assertEqual(restored, checkpoint_fixture())
        self.assertEqual(self.output.read_bytes(), source.read_bytes())
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)
        self.assertEqual((source.read_bytes(), source.stat().st_mtime_ns), before)
        with self.assertRaises(module.ProfileCheckpointError):
            module.restore_checkpoint(source, self.output)

    def test_export_is_private_unapproved_and_preserves_degraded_evidence(self):
        module = self.adapter()
        value = checkpoint_fixture()
        prior = value['profiles'][0]
        failed = collect_profile('yose', prior, NOW, lambda _start: {'total': 0, 'start': 0, 'data': []})
        value['profiles'][0] = failed
        value['checkpoint_id'] = digest({k: v for k, v in value.items() if k != 'checkpoint_id'})
        source = self.write(value)
        result = module.export_review_candidate(source, self.output)
        self.assertEqual(result['checkpoint'], value)
        self.assertEqual(result['checkpoint_id'], value['checkpoint_id'])
        self.assertEqual(result['purpose'], 'private_park_profile_review_candidate')
        self.assertEqual(result['source_rights_status'], 'not_checked')
        for field in ('approval_performed', 'publication_performed', 'site_data_written'):
            self.assertIs(result[field], False)
        self.assertIsNone(result['checkpoint']['profiles'][0]['published_at'])
        self.assertEqual(json.loads(self.output.read_bytes()), result)
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)

    def test_offline_operations_do_not_access_environment(self):
        module = self.adapter()
        source = self.write(checkpoint_fixture())
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(module.verify_checkpoint(source), checkpoint_fixture())
            module.restore_checkpoint(source, self.output)
            module.export_review_candidate(source, self.root / 'review.json')

    def test_oversized_review_envelope_refuses_before_creating_lock_or_temporary(self):
        module = self.adapter()
        value = checkpoint_fixture()
        source = self.write(value)
        with patch.object(module, 'MAX_CHECKPOINT_BYTES', len(canonical(value))):
            with patch.object(module.os, 'open', wraps=os.open) as opening:
                with self.assertRaises(module.ProfileCheckpointError):
                    module.export_review_candidate(source, self.output)
        self.assertFalse(any(call.args[1] & os.O_CREAT for call in opening.call_args_list))
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
