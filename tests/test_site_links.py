"""Exercise the real generated-site link gate with deliberately broken HTML."""
import os
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from site_links import check_site

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ('', 'parks', 'parks/yosemite', 'parks/rocky-mountain',
          'parks/yellowstone', 'parks/zion', 'parks/grand-canyon',
          'how-it-works', 'sources', 'changes', 'about', 'privacy',
          'terms', 'corrections')
BASES = ('/', '/us-national-park-trip-readiness-tracker/')


class StaticLinkGateTests(unittest.TestCase):
    def check(self, base, html, *, page='', extra=None):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            for route in ROUTES:
                target = output / route / 'index.html'
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('<main id="main"></main>', encoding='utf-8')
            (output / page / 'index.html').write_text(html, encoding='utf-8')
            (output / 'asset.js').write_text('/* fixture */', encoding='utf-8')
            (output / 'photo one.svg').write_text('<svg/>', encoding='utf-8')
            for route, content in (extra or {}).items():
                target = output / route
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding='utf-8')
            result = subprocess.run(
                ['node', '--test', '--test-isolation=none', '--test-reporter=tap',
                 '--test-name-pattern=internal page links',
                 'tests/site.test.mjs'], cwd=ROOT,
                env={**os.environ, 'SITE_TEST_OUTPUT': str(output),
                     'SITE_TEST_BASE': base},
                text=True, capture_output=True, timeout=15)
            self.assertIn('internal page links', result.stdout,
                          result.stdout + result.stderr)
            return result

    def test_missing_relative_query_and_fragment_destinations_fail(self):
        for base in BASES:
            for url in ('missing/', './missing/?view=all',
                        f'{base}missing/?view=all#main', '../missing.js?v=1'):
                with self.subTest(base=base, url=url):
                    result = self.check(base, f'<a href="{url}">Missing</a>')
                    self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_missing_local_and_cross_page_fragments_fail(self):
        for base in BASES:
            for url in ('#missing', '?view=all#missing',
                        'parks/?view=all#missing', f'{base}parks/#mis%73ing'):
                with self.subTest(base=base, url=url):
                    result = self.check(base, f'<a href="{url}">Missing</a>')
                    self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_comment_script_and_template_ids_do_not_satisfy_fragments(self):
        for hidden in ('<!-- <div id="missing"></div> -->',
                       '<script>const example = \'<div id="missing"></div>\';</script>',
                       '<template><div id="missing"></div></template>'):
            with self.subTest(hidden=hidden):
                result = self.check('/', hidden + '<a href="#missing">Missing</a>')
                self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_text_element_contents_do_not_supply_links_or_fragment_targets(self):
        for tag in ('textarea', 'title', 'iframe'):
            with self.subTest(tag=tag):
                result = self.check('/',
                    f'<{tag}><span id="missing"></span></{tag}>'
                    '<a href="#missing">Missing</a>')
                self.assertNotEqual(result.returncode, 0, result.stdout)
                result = self.check('/',
                    f'<{tag}><a href="missing/">Example</a></{tag}>')
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_old_python_parser_cannot_supply_targets_from_text_contents(self):
        # Characterize the raw/RCDATA defaults before the 3.12.14 backport.
        with tempfile.TemporaryDirectory() as temporary:
            (Path(temporary) / 'index.html').write_text(
                '<textarea><a href="missing/" id="missing">Example</a></textarea>'
                '<a href="#missing">Missing</a>', encoding='utf-8')
            with patch.object(HTMLParser, 'CDATA_CONTENT_ELEMENTS', ('script', 'style')), \
                    patch.object(HTMLParser, 'RCDATA_CONTENT_ELEMENTS', (), create=True):
                _, _, errors = check_site(temporary, '/')
            self.assertEqual(errors, ['index.html -> #missing: missing_fragment'])

    def test_project_escape_cannot_hide_in_query_relative_or_encoded_path(self):
        base = BASES[1]
        for url in ('/parks/?view=all', '../parks/',
                    f'{base}%2e%2e/parks/', f'{base}..%2fparks/'):
            with self.subTest(url=url):
                result = self.check(base, f'<a href="{url}">Escaped</a>')
                self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_valid_destinations_and_external_urls_pass_without_network(self):
        for base in BASES:
            html = f'''<main id="main"></main><h2 id="details &amp; notes"></h2>
                <a name="legacy"></a><a href="#legacy">Legacy</a>
                <template id="template-node"><span id="inert"></span></template>
                <a href="#template-node">Template element</a>
                <a href="#details%20%26%20notes">Encoded ID</a>
                <a href="?a=1&amp;b=2#main">Same page query</a>
                <a href="./?view=all#main">Relative</a><a href="#">Top</a>
                <a href="../?view=all#main">Parent</a>
                <a href=" \t../?view=all#main \r\n">Padded parent</a>
                <a href="{base}parks/?view=all#main">Absolute</a>
                <script src="../asset.js?v=1"></script>
                <img src='../photo%20one.svg?v=1'>
                <a href="https://www.nps.gov/missing/#missing">External</a>
                <a href="//www.nps.gov/missing/">Protocol relative</a>
                <a href="mailto:example@example.org">Mail</a>
                <!-- <a href="missing/">Example</a> -->
                <script>const example = '<a href="missing/">Example</a>';</script>'''
            with self.subTest(base=base):
                result = self.check(base, html, page='parks')
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_newly_emitted_pages_are_checked_without_editing_route_list(self):
        result = self.check('/', '<main id="main"></main>', extra={
            'new-page/index.html': '<a href="../missing/?view=all">Missing</a>'})
        self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_regular_files_cannot_be_requested_as_directories(self):
        for base in BASES:
            for url in ('asset.js/?v=1', 'parks/index.html/#main'):
                with self.subTest(base=base, url=url):
                    result = self.check(base, f'<a href="{url}">Broken</a>')
                    self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_unicode_whitespace_is_part_of_the_destination_path(self):
        for base in BASES:
            for url in ('parks/\u00a0', '\u00a0parks/', 'parks/\u2003'):
                with self.subTest(base=base, url=url):
                    result = self.check(base, f'<a href="{url}">Missing</a>')
                    self.assertNotEqual(result.returncode, 0, result.stdout)


if __name__ == '__main__':
    unittest.main()
