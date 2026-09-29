"""Minimized synthetic markup reproducing live NPS envelope shape, not real prose."""
import unittest
from tracker.entry_html import inspect_html, SourceExtractionError

H1 = 'Entrance Reservations'
DOC = '<!doctype html><html><head><title>Test</title></head><body><h1>Entrance Reservations</h1><p>Synthetic entry guidance.</p><details><summary>Exceptions</summary><p>Synthetic exception stays visible to comparison.</p></details></body></html>'
TRAILER = '<script src="/synthetic.js"></script><script>const example = "<p>not a live claim</p>";</script>\n</body>\n</html>'

class EnvelopeTests(unittest.TestCase):
    def test_observed_redundant_document_closing_pair_keeps_full_body_context(self):
        self.assertEqual(inspect_html(DOC + TRAILER, H1), inspect_html(DOC, H1))
    def test_redundant_pair_without_scripts_is_an_inert_envelope(self):
        self.assertEqual(inspect_html(DOC + '\n</body>\n</html>\n', H1), inspect_html(DOC, H1))
    def test_comment_and_whitespace_inside_trailer_do_not_supply_evidence(self):
        text = DOC + '<!-- <h1>untrusted</h1> -->\n' + TRAILER + '<!-- end -->'
        self.assertEqual(inspect_html(text, H1), inspect_html(DOC, H1))
    def test_text_appended_after_document_is_not_silently_discarded(self):
        with self.assertRaises(SourceExtractionError): inspect_html(DOC + 'A new exception.', H1)
    def test_elements_appended_after_document_are_not_silently_discarded(self):
        for tag in ('p','div','a','h1','iframe','template'):
            with self.subTest(tag=tag), self.assertRaises(SourceExtractionError):
                inspect_html(DOC + f'<{tag}>A new exception.</{tag}>', H1)
    def test_new_clause_between_body_and_html_end_is_not_lost(self):
        with self.assertRaises(SourceExtractionError):
            inspect_html(DOC.replace('</body></html>', '</body>New exception.</html>'), H1)
    def test_nonempty_text_after_the_redundant_closers_is_rejected(self):
        with self.assertRaises(SourceExtractionError): inspect_html(DOC + TRAILER + 'new text', H1)
    def test_visible_text_before_body_cannot_hide_a_qualification(self):
        with self.assertRaises(SourceExtractionError): inspect_html('A qualification.' + DOC, H1)
    def test_trailer_cannot_complete_truncated_or_misnested_interior_markup(self):
        for doc in (DOC.replace('</details>',''), DOC.replace('</p>','',1), DOC.replace('</body>',''), DOC.replace('</html>','')):
            with self.subTest(doc=doc), self.assertRaises(SourceExtractionError): inspect_html(doc + TRAILER, H1)
    def test_duplicate_opening_body_is_still_refused(self):
        with self.assertRaises(SourceExtractionError): inspect_html(DOC + '<body></body></html>', H1)
    def test_unpaired_or_reordered_redundant_closers_refuse(self):
        for tail in ('</body>', '</html>', '</html></body>', '</body></body></html>', '</body></html></body></html>'):
            with self.subTest(tail=tail), self.assertRaises(SourceExtractionError): inspect_html(DOC + tail, H1)
    def test_scripts_cannot_be_inserted_inside_the_redundant_closing_pair(self):
        with self.assertRaises(SourceExtractionError): inspect_html(DOC + '</body><script></script></html>', H1)
    def test_body_changes_remain_distinct_even_with_the_accepted_trailer(self):
        changed = DOC.replace('Synthetic entry guidance.', 'Synthetic revised guidance.')
        self.assertNotEqual(inspect_html(changed + TRAILER,H1),inspect_html(DOC + TRAILER,H1))
    def test_annotations_and_document_base_are_not_bypassed_by_a_trailer(self):
        for element in ('<base href="https://invalid.example">','<s>Withdrawn statement</s>'):
            with self.subTest(element=element),self.assertRaises(SourceExtractionError):
                inspect_html(DOC.replace('</body>',element+'</body>') + TRAILER,H1)
