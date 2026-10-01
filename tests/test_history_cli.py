import contextlib
import io
import json
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from history_fixtures import T0, T1, notice, snapshot, next_snapshot
from tracker.history import main
from tracker.history_store import HistoryStore

class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/'archive'; self.input = Path(self.tmp.name)/'snapshot.json'
        self.input.write_text(json.dumps(snapshot()), encoding='utf-8')

    def invoke(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), patch.object(socket, 'create_connection', side_effect=AssertionError('No network permitted')):
            code = main(list(args) + ['--archive-dir', str(self.root)])
        return code, out.getvalue(), err.getvalue()

    def test_import_is_offline_leaves_input_unchanged_and_reports_no_publication(self):
        original = self.input.read_bytes()
        code, out, err = self.invoke('record', '--snapshot', str(self.input))
        self.assertEqual(code, 0); self.assertEqual(err, '')
        report = json.loads(out)
        self.assertFalse(report['publication_performed'])
        self.assertFalse(report['site_data_written'])
        self.assertEqual(self.input.read_bytes(), original)
        self.assertEqual(report['source_collection_status'], 'success')
        self.assertNotIn('Synthetic facility', out)

    def test_empty_report_does_not_initialize_a_store(self):
        code, out, err = self.invoke('report', '--park', 'yose')
        self.assertEqual(code, 0); self.assertEqual(json.loads(out)['observation_count'], 0)
        self.assertEqual(json.loads(out)['collection_status'], 'never_checked')
        self.assertFalse(self.root.exists())

    def test_bounded_report_distinguishes_baseline_and_retained_failed_attempt(self):
        store = HistoryStore(self.root); first = snapshot(); store.append(first)
        store.append(next_snapshot(first, status='failed'))
        code, out, err = self.invoke('report', '--park', 'yose', '--limit', '1')
        self.assertEqual(code, 0)
        result = json.loads(out)
        self.assertEqual(result['observation_count'], 2)
        self.assertEqual(result['omitted_observations'], 1)
        self.assertEqual(result['observations'][0]['comparison'], 'not_compared')
        self.assertEqual(result['last_successful_fetch_at'], T0)
        self.assertEqual(result['last_checked_at'], T1)
        self.assertNotIn('Synthetic text', out)

    def test_report_does_not_call_removal_a_reopening(self):
        old = snapshot([notice('a'), notice('b')]); store = HistoryStore(self.root); store.append(old)
        store.append(next_snapshot(old, records=[old['records'][1]]))
        code, out, err = self.invoke('report', '--park', 'yose')
        self.assertEqual(code, 0)
        self.assertIn('Notice no longer present in the checked feed', out)
        self.assertNotIn('reopened', out)

    def test_bad_input_and_io_errors_are_sanitized(self):
        self.input.write_text('{"secret": "synthetic-private-key"}')
        code, out, err = self.invoke('record', '--snapshot', str(self.input))
        self.assertEqual(code, 2); self.assertEqual(out, '')
        self.assertNotIn('synthetic-private-key', err)
        self.assertFalse(self.root.exists())
        code, out, err = self.invoke('record', '--snapshot', str(self.input)+'-private-path')
        self.assertEqual(code, 2); self.assertNotIn('private-path', err)

    def test_duplicate_json_keys_and_nonfinite_json_are_rejected(self):
        for text in ['{"schema_version":1,"schema_version":2}', '{"v":NaN}']:
            self.input.write_text(text)
            code, out, err = self.invoke('record', '--snapshot', str(self.input))
            self.assertEqual(code, 2); self.assertEqual(out, '')

    def test_invalid_report_limit_is_rejected_before_reading(self):
        for limit in ['0', '-1', '101']:
            code, out, err = self.invoke('report', '--park', 'yose', '--limit', limit)
            self.assertEqual(code, 2); self.assertEqual(out, '')
            self.assertFalse(self.root.exists())

    def test_repeated_report_is_read_only(self):
        self.invoke('record', '--snapshot', str(self.input))
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.invoke('report', '--park', 'yose'); self.invoke('report', '--park', 'yose')
        after = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(after, before)

    def test_archive_cannot_target_website_or_source_directories(self):
        project = Path(__file__).resolve().parents[1]
        for folder in ('data', 'public', 'src', 'dist', '.git'):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                result = main(['report', '--park', 'yose', '--archive-dir', str(project/folder/'history')])
            self.assertEqual(result, 2)
            self.assertIn('unsafe_archive_destination', err.getvalue())

    def test_record_and_report_refuse_unlisted_checkout_or_relative_roots_before_archive_access(self):
        project = Path(__file__).resolve().parents[1]
        original = self.input.read_bytes()
        destinations = [Path('state/alert-history'), project/'state/alert-history',
                            project/'.superpowers/private-history', project/'unlisted-private-history',
                            project.parent, self.root/'..'/'other-history']
        if project.anchor == '/':
            destinations.extend([Path('/' + str(project))/'state/alert-history',
                                 Path('/' + str(project.parent))])
        for destination in destinations:
            for command in ('record', 'report'):
                with self.subTest(destination=str(destination), command=command):
                    out, err = io.StringIO(), io.StringIO()
                    selection = ['--snapshot', str(self.input)] if command == 'record' else ['--park', 'yose']
                    with patch.object(HistoryStore, 'append', return_value='a'*64) as append, \
                         patch.object(HistoryStore, 'read', return_value=[]) as read, \
                         contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                        code = main([command, *selection, '--archive-dir', str(destination)])
                    self.assertEqual(code, 2)
                    self.assertEqual(out.getvalue(), '')
                    self.assertIn('unsafe_archive_destination', err.getvalue())
                    append.assert_not_called(); read.assert_not_called()
                    self.assertNotIn(str(destination), err.getvalue())
                    self.assertEqual(self.input.read_bytes(), original)
        self.assertFalse(self.root.exists())

    def test_record_refuses_pages_output_without_writing_archive(self):
        original = self.input.read_bytes()
        for nested in (False, True):
            with self.subTest(nested=nested):
                project = Path(self.tmp.name)/f'project-{nested}'
                project.mkdir()
                output = project/'dist-pages'
                if nested:
                    output.mkdir()
                    (output/'index.html').write_text('retained public page')
                destination = output/'private-history' if nested else output
                before = {p:p.read_bytes() for p in project.rglob('*') if p.is_file()}
                out, err = io.StringIO(), io.StringIO()
                with patch('tracker.history_store.PROJECT_ROOT', project), \
                     contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    code = main(['record', '--snapshot', str(self.input),
                                 '--archive-dir', str(destination)])
                self.assertEqual(code, 2)
                self.assertEqual(out.getvalue(), '')
                self.assertIn('unsafe_archive_destination', err.getvalue())
                self.assertEqual(before, {p:p.read_bytes() for p in project.rglob('*') if p.is_file()})
                self.assertFalse(destination.exists())
                self.assertEqual(self.input.read_bytes(), original)


    def test_large_change_report_has_explicit_truncation_not_silent_loss(self):
        old = snapshot([]); store = HistoryStore(self.root); store.append(old)
        store.append(snapshot([notice(str(i), now=T1) for i in range(101)], now=T1))
        code, out, err = self.invoke('report', '--park', 'yose')
        self.assertEqual(code, 0)
        entry = json.loads(out)['observations'][0]
        self.assertEqual(len(entry['changes']), 100)
        self.assertEqual(entry['omitted_changes'], 1)
        self.assertEqual(entry['change_count'], 101)

if __name__ == '__main__': unittest.main()
