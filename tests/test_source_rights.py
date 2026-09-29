"""Source-rights evidence for the exact public NPS guidance text scope."""
import json
import re
import unittest
from pathlib import Path

from tracker.release_readiness import evaluate_readiness

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'data/source-rights.json'
NOTICE='No protection is claimed in original U.S. Government works.'
OWNERSHIP='https://www.nps.gov/aboutus/disclaimer.htm'
MARKS='https://www.nps.gov/subjects/partnerships/arrowhead-requests.htm?fullweb=1'

class SourceRightsTests(unittest.TestCase):
    def records(self):
        return json.loads((ROOT/'data/rules.json').read_text()) + json.loads((ROOT/'data/entry-notes.json').read_text())

    def manifest(self):
        return json.loads(MANIFEST.read_text())

    def test_manifest_covers_every_public_guidance_record_exactly_once(self):
        manifest=self.manifest(); records=self.records()
        self.assertEqual(manifest['schema_version'],1)
        self.assertEqual(manifest['scope'],'public_guidance_text_only')
        covered=manifest['records']
        self.assertEqual(len(covered),len(records))
        self.assertEqual(len({row['guidance_id'] for row in covered}),len(records))
        expected={(row['id'],row['evidence']['url']) for row in records}
        actual={(row['guidance_id'],row['source_url']) for row in covered}
        self.assertEqual(actual,expected)
        for row in covered:
            self.assertEqual(row['classification'],'nps_government_text')
            self.assertEqual(row['use_scope'],'short_text_excerpt_and_original_summary')
            self.assertFalse(row['third_party_material_reproduced'])
            self.assertFalse(row['nps_marks_reproduced'])
            self.assertFalse(row['media_reproduced'])

    def test_manifest_binds_official_nps_policy_and_commercial_notice(self):
        manifest=self.manifest(); policy=manifest['policy']
        self.assertEqual(policy['ownership_url'],OWNERSHIP)
        self.assertEqual(policy['marks_url'],MARKS)
        self.assertEqual(policy['commercial_notice'],NOTICE)
        self.assertFalse(policy['third_party_material_allowed'])
        self.assertFalse(policy['nps_marks_allowed'])
        self.assertFalse(policy['raw_private_captures_public'])
        self.assertRegex(manifest['reviewed_at'],r'^2026-09-29T\d{2}:\d{2}:\d{2}Z$')

    def test_footer_contains_required_commercial_government_work_notice(self):
        layout=(ROOT/'src/layouts/Layout.astro').read_text()
        self.assertIn(NOTICE,layout)
        self.assertIn('National Park Service',layout)
        self.assertIn('Not affiliated with or endorsed by the National Park Service.',layout)

    def test_public_application_contains_no_nps_marks_or_nps_hosted_media(self):
        files=[p for folder in (ROOT/'src',ROOT/'public') for p in folder.rglob('*') if p.is_file()]
        forbidden_names=re.compile(r'(?:arrowhead|nps[-_ ]?(?:logo|mark)|secondary[-_ ]mark)',re.I)
        media_ext=re.compile(r'\.(?:png|jpe?g|gif|svg|webp|avif|ico|mp4|webm|mp3|wav)$',re.I)
        for path in files:
            rel=str(path.relative_to(ROOT))
            self.assertFalse(forbidden_names.search(rel),rel)
            if media_ext.search(path.name):
                self.fail(f'Unreviewed public media asset: {rel}')
            text=path.read_text(encoding='utf-8',errors='ignore')
            self.assertIsNone(forbidden_names.search(text),rel)
            self.assertIsNone(re.search(r'<(?:img|video|audio|source)\b[^>]*\bnps\.gov\b',text,re.I),rel)

    def test_release_rights_gate_passes_only_for_complete_exact_manifest(self):
        gate=next(g for g in evaluate_readiness(ROOT)['gates'] if g['id']=='source_rights')
        self.assertEqual(gate['status'],'pass')
        self.assertEqual(gate['evidence']['covered_guidance_records'],6)
        self.assertEqual(gate['evidence']['guidance_records_total'],6)
        self.assertTrue(gate['evidence']['commercial_notice_present'])
        self.assertFalse(gate['evidence']['nps_marks_or_media_detected'])

if __name__=='__main__': unittest.main()
