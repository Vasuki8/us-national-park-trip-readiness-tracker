"""Synthetic HTML; source headings/URLs are profiles, not live DOM baselines."""
import copy
import hashlib
import json
import unittest
from datetime import datetime, timezone
from html import escape

from tracker.entry_sources import inspect_entry_sources, inspect_html, SourceExtractionError, PROFILES

T0 = '2026-09-28T19:00:00Z'
T1 = '2026-09-28T20:00:00Z'
T2 = '2026-09-28T21:00:00Z'
T3 = '2026-09-28T22:00:00Z'
NOW = datetime(2026, 9, 29, 1, tzinfo=timezone.utc)

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def inputs():
    records, captures = [], []
    for code, profile in PROFILES.items():
        selected = [f'{code} synthetic selected statement {i}.' for i in range(2 if code == 'romo' else 1)]
        for i, excerpt in enumerate(selected):
            records.append({'id': f'{code}-test-{i}', 'park_code': code, 'reviewed_at': T0,
                'review_status': 'reviewed', 'summary': 'Synthetic approved summary',
                'evidence': {'url': profile['url'], 'excerpt': excerpt,
                    'content_hash': hashlib.sha256(excerpt.encode()).hexdigest(),
                    'hash_scope': 'excerpt', 'reviewed_at': T0}})
        html = '<!doctype html><html><head><title>Test</title></head><body><h1>' + escape(profile['heading']) + '</h1>'
        html += ''.join(f'<p>{escape(x)}</p>' for x in selected)
        html += '<details><summary>Exceptions</summary><p>Existing permits need a separate review.</p></details>'
        html += f'<a href="/{code}/planyourvisit/permits.htm">Official details</a></body></html>'
        captures.append({'source_url': profile['url'], 'final_url': profile['url'],
            'checked_at': T1, 'status': 'success', 'content_type': 'text/html; charset=utf-8', 'html': html})
    return records, captures

def baseline(records, captures):
    # Explicitly synthetic operator approval, never production baseline data.
    first = inspect_entry_sources(records, captures, [], NOW)
    return [{'schema_version': 1, 'source_url': e['source_url'], 'profile_id': e['profile_id'],
             'guidance_hashes': e['guidance_hashes'], 'checked_at': e['checked_at'], 'reviewed_at': T2,
             'context': e['context'], 'context_hash': e['context_hash']}
            for e in first['sources']]

class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.records, self.captures = inputs()
        self.baselines = baseline(self.records, self.captures)
        for capture in self.captures: capture['checked_at'] = T3
    def run_batch(self):
        return inspect_entry_sources(self.records, self.captures, self.baselines, NOW)
    def test_reviewed_context_and_all_six_binding_hashes_match(self):
        result = self.run_batch()
        self.assertEqual(len(result['observations']), 6)
        self.assertEqual([o['status'] for o in result['observations']], ['observed'] * 6)
        self.assertEqual([o['guidance_hash'] for o in result['observations']], [digest(r) for r in self.records])
        self.assertFalse(result['network_performed']); self.assertFalse(result['publication_performed'])
    def test_no_baseline_is_not_matching_even_with_original_excerpt_present(self):
        result = inspect_entry_sources(self.records, self.captures, [], NOW)
        self.assertTrue(all(o['status'] == 'failed' and o['excerpt'] is None for o in result['observations']))
        self.assertEqual({s['reason'] for s in result['sources']}, {'context_not_reviewed'})
        self.assertTrue(all(s['context'] for s in result['sources']))
    def test_new_exception_outside_quote_requires_review_and_retains_before_after(self):
        self.captures[0]['html'] = self.captures[0]['html'].replace('</body>', '<p>Except: a new synthetic reservation requirement applies.</p></body>')
        result = self.run_batch()
        self.assertEqual(result['sources'][0]['reason'], 'context_changed')
        self.assertEqual(result['observations'][0]['status'], 'failed')
        self.assertIn('new synthetic', result['sources'][0]['context']['text'])
        self.assertNotIn('new synthetic', result['sources'][0]['baseline_context']['text'])
    def test_collapsed_hidden_and_later_sections_are_not_discarded(self):
        self.captures[1]['html'] = self.captures[1]['html'].replace('</details>', '<p hidden aria-hidden="true">Different camping exception.</p></details>')
        result = self.run_batch()
        self.assertEqual(result['sources'][1]['reason'], 'context_changed')
        self.assertEqual([o['status'] for o in result['observations'][1:3]], ['failed', 'failed'])
    def test_link_target_only_change_is_not_lost(self):
        self.captures[0]['html'] = self.captures[0]['html'].replace('permits.htm', 'changed-permits.htm')
        self.assertEqual(self.run_batch()['sources'][0]['reason'], 'context_changed')
    def test_whitespace_and_inline_emphasis_do_not_create_a_context_change(self):
        c = self.captures[0]
        c['html'] = c['html'].replace('synthetic selected', 'synthetic\n  <em>selected</em>').replace('separate review', 'separate&nbsp;review')
        self.assertEqual(self.run_batch()['observations'][0]['status'], 'observed')
    def test_text_in_script_style_and_comments_does_not_establish_excerpt(self):
        for wrapper in ['<script>{}</script>', '<style>{}</style>', '<!-- {} -->']:
            with self.subTest(wrapper=wrapper):
                captures = copy.deepcopy(self.captures)
                quote = self.records[0]['evidence']['excerpt']
                captures[0]['html'] = captures[0]['html'].replace(f'<p>{quote}</p>', wrapper.format(quote))
                result = inspect_entry_sources(self.records, captures, self.baselines, NOW)
                self.assertEqual(result['observations'][0]['status'], 'missing')
    def test_duplicate_excerpt_is_ambiguous_not_first_match(self):
        c = self.captures[0]; c['html'] = c['html'].replace('</body>', '<p>'+self.records[0]['evidence']['excerpt']+'</p></body>')
        result = self.run_batch()
        self.assertEqual(result['observations'][0]['status'], 'failed')
        self.assertEqual(result['sources'][0]['reason'], 'excerpt_ambiguous')
    def test_missing_or_duplicate_expected_heading_refuses(self):
        for replacement in ['<h2>Changed title</h2>', '<h1>Entrance Reservations</h1><h1>Entrance Reservations</h1>']:
            captures = copy.deepcopy(self.captures)
            captures[0]['html'] = captures[0]['html'].replace('<h1>Entrance Reservations</h1>', replacement)
            result = inspect_entry_sources(self.records, captures, self.baselines, NOW)
            self.assertEqual(result['sources'][0]['reason'], 'heading_ambiguous')
            self.assertEqual(result['observations'][0]['status'], 'failed')
    def test_truncated_duplicate_and_missing_body_refuse(self):
        for html in ['<body><p>truncated', '<body>one</body><body>two</body>', '<div>not a document</div>']:
            with self.subTest(html=html):
                captures = copy.deepcopy(self.captures); captures[0]['html'] = html
                self.assertEqual(inspect_entry_sources(self.records, captures, self.baselines, NOW)['observations'][0]['status'], 'failed')
    def test_fake_complete_document_inside_comment_does_not_count(self):
        with self.assertRaises(SourceExtractionError): inspect_html('<!-- <body>Hi</body> -->', 'Entrance Reservations')
    def test_html_parser_handles_entities_without_interpreting_markup(self):
        scope = inspect_html('<body><h1>Permits &amp; Reservations</h1><p>Caf&eacute; &lt;script&gt;not code&lt;/script&gt;</p></body>', 'Permits & Reservations')
        self.assertIn('Café <script>not code</script>', scope['text'])
    def test_failed_capture_records_no_content_and_does_not_borrow_prior_success(self):
        c = self.captures[0]; c.update(status='failed', html=None, content_type=None, final_url=None)
        result = self.run_batch()
        self.assertEqual(result['sources'][0]['reason'], 'capture_failed')
        self.assertIsNone(result['sources'][0]['context'])
        self.assertEqual(result['observations'][0]['status'], 'failed')
        self.assertEqual(result['observations'][0]['checked_at'], T3)
    def test_cross_park_redirect_mime_and_unexpected_payloads_refuse(self):
        for change in [{'final_url': self.captures[1]['source_url']}, {'content_type':'application/json'}, {'headers':{'Authorization':'private'}}, {'status':'failed'}]:
            captures = copy.deepcopy(self.captures); captures[0].update(change)
            with self.subTest(change=change), self.assertRaises(SourceExtractionError):
                inspect_entry_sources(self.records, captures, self.baselines, NOW)
    def test_complete_source_inventory_required_no_missing_duplicate_unknown(self):
        for captures in [self.captures[:-1], self.captures+[self.captures[0]], [self.captures[0]]*5]:
            with self.assertRaises(SourceExtractionError): inspect_entry_sources(self.records, captures, self.baselines, NOW)
    def test_revised_guidance_cannot_reuse_old_context_approval(self):
        self.records[0]['summary'] = 'Revised approved rule'
        with self.assertRaisesRegex(SourceExtractionError, 'baseline_revision_mismatch'): self.run_batch()
    def test_baseline_clock_and_hash_tampering_refuse(self):
        for key, value in [('reviewed_at','2099-01-01T00:00:00Z'), ('context_hash','0'*64), ('profile_id','unrecognized'), ('checked_at',T3)]:
            baselines = copy.deepcopy(self.baselines); baselines[0][key] = value
            with self.subTest(key=key), self.assertRaises(SourceExtractionError):
                inspect_entry_sources(self.records, self.captures, baselines, NOW)
    def test_a_short_excerpt_cannot_be_supplied_as_whole_context(self):
        b = self.baselines[0]; b['context']['text'] = self.records[0]['evidence']['excerpt']; b['context_hash'] = digest(b['context'])
        with self.assertRaises(SourceExtractionError): self.run_batch()
    def test_baseline_context_not_mutated_or_automatically_approved(self):
        old = copy.deepcopy((self.records, self.captures, self.baselines))
        result = self.run_batch(); result['sources'][0]['context']['text'] = 'mutated result'
        self.assertEqual((self.records, self.captures, self.baselines), old)
    def test_invalid_future_backwards_and_naive_clocks_refuse(self):
        for time in ['0000-01-01T00:00:00Z','2026-02-30T00:00:00Z','2099-01-01T00:00:00Z',T0,'2026-09-28T21:00:00','2026-09-28T21:00:00+00:00']:
            captures = copy.deepcopy(self.captures); captures[0]['checked_at'] = time
            with self.subTest(time=time), self.assertRaises(SourceExtractionError):
                inspect_entry_sources(self.records, captures, self.baselines, NOW)
    def test_capture_older_than_context_approval_cannot_replay(self):
        self.captures[0]['checked_at'] = T1
        with self.assertRaises(SourceExtractionError): self.run_batch()
    def test_unknown_baseline_fields_and_duplicate_sources_refuse(self):
        for baselines in [self.baselines+[self.baselines[0]], [{**self.baselines[0], 'approved':True}]+self.baselines[1:]]:
            with self.assertRaises(SourceExtractionError): inspect_entry_sources(self.records, self.captures, baselines, NOW)
    def test_bounds_refuse_instead_of_truncating(self):
        for html in ['<body>'+'x'*1_048_577+'</body>', '<body>'+'<div>'*129+'x'+'</div>'*129+'</body>', '<body><h1>Entrance Reservations</h1><p>'+'x'*65_537+'</p></body>']:
            with self.assertRaises(SourceExtractionError): inspect_html(html, 'Entrance Reservations')
    def test_controls_surrogates_and_null_input_refuse(self):
        for html in [None, '<body>\ud800</body>', '<body>\x00</body>','<body>\u202e</body>']:
            with self.assertRaises(SourceExtractionError): inspect_html(html, 'Entrance Reservations')
    def test_diagnostics_do_not_echo_raw_input(self):
        self.captures[0]['final_url'] = 'https://example.test/private-secret'
        with self.assertRaises(SourceExtractionError) as caught: self.run_batch()
        self.assertNotIn('private-secret', str(caught.exception))
    def test_expected_profile_urls_and_headings_are_explicit(self):
        self.assertEqual(set(PROFILES), {'yose','romo','yell','zion','grca'})
        self.assertEqual(PROFILES['grca']['heading'], 'Grand Canyon National Park Operations Update')
    def test_block_boundaries_cannot_join_a_different_sentence_into_approved_quote(self):
        c = self.captures[0]; c['html'] = c['html'].replace('selected statement', 'selected</p><p>statement')
        result = self.run_batch()
        self.assertEqual(result['observations'][0]['status'], 'failed')
    def test_base_element_cannot_silently_retarget_unchanged_links(self):
        c = self.captures[0]; c['html'] = c['html'].replace('<head>', '<head><base href="https://different.example/">')
        self.assertEqual(self.run_batch()['observations'][0]['status'], 'failed')
    def test_deleted_text_is_not_reused_as_an_unchanged_live_claim(self):
        quote = self.records[0]['evidence']['excerpt']
        c = self.captures[0]; c['html'] = c['html'].replace(quote, '<del>'+quote+'</del>')
        self.assertEqual(self.run_batch()['observations'][0]['status'], 'failed')
    def test_body_only_does_not_accept_heading_copied_from_head(self):
        with self.assertRaises(SourceExtractionError):
            inspect_html('<head><h1>Entrance Reservations</h1></head><body>no title</body>', 'Entrance Reservations')

if __name__ == '__main__': unittest.main()
