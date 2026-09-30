"""Source-rights evidence for the exact public NPS guidance text scope."""
import copy
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from tracker.release_readiness import evaluate_readiness, _rights

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'data/source-rights.json'
NOTICE='No protection is claimed in original U.S. Government works.'
OWNERSHIP='https://www.nps.gov/aboutus/disclaimer.htm'
MARKS='https://www.nps.gov/subjects/partnerships/arrowhead-requests.htm?fullweb=1'

class SourceRightsTests(unittest.TestCase):
    def private_repository(self):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        root=Path(folder.name)
        for name in ('data','src','public','.github'):
            shutil.copytree(ROOT/name,root/name)
        return root,root/'src/layouts/Layout.astro'

    def assert_notice_blocked(self, root, layout, source):
        layout.write_text(source)
        gate=_rights(root)
        self.assertEqual(gate['status'],'blocked')
        self.assertEqual(gate['reason'],'commercial_government_work_notice_missing')
        self.assertFalse(gate['evidence']['commercial_notice_present'])

    def records(self):
        return json.loads((ROOT/'data/rules.json').read_text()) + json.loads((ROOT/'data/entry-notes.json').read_text())

    def manifest(self):
        return json.loads(MANIFEST.read_text())

    def write_guidance(self, root, rules, notes, manifest):
        for name,value in (('rules.json',rules),('entry-notes.json',notes),('source-rights.json',manifest)):
            (root/'data'/name).write_text(json.dumps(value))

    def assert_inventory_blocked(self, root):
        gate=_rights(root)
        self.assertEqual(gate['status'],'blocked')
        self.assertEqual(gate['reason'],'public_guidance_inventory_invalid')
        self.assertEqual(gate['evidence']['covered_guidance_records'],0)

    def test_empty_guidance_and_empty_manifest_cannot_pass_rights_gate(self):
        root,_=self.private_repository(); manifest=self.manifest()
        manifest['records']=[]
        self.write_guidance(root,[],[],manifest)
        self.assert_inventory_blocked(root)

    def test_duplicate_guidance_ids_cannot_be_collapsed_into_rights_coverage(self):
        root,_=self.private_repository()
        original_rules=json.loads((root/'data/rules.json').read_text())
        original_notes=json.loads((root/'data/entry-notes.json').read_text())
        for kind in ('identical','revised','across_files','different_source'):
            with self.subTest(kind=kind):
                rules=copy.deepcopy(original_rules); notes=copy.deepcopy(original_notes)
                manifest=self.manifest(); extra=copy.deepcopy(rules[0])
                if kind=='revised': extra['summary']='Conflicting duplicate guidance.'
                if kind=='different_source':
                    extra['park_code']=notes[0]['park_code']
                    extra['evidence']['url']=notes[0]['evidence']['url']
                    entry=copy.deepcopy(next(r for r in manifest['records'] if r['guidance_id']==extra['id']))
                    entry['source_url']=extra['evidence']['url']; manifest['records'].append(entry)
                (notes if kind=='across_files' else rules).append(extra)
                self.write_guidance(root,rules,notes,manifest)
                self.assert_inventory_blocked(root)

    def test_guidance_must_bind_valid_ids_and_parks_to_fixed_official_sources(self):
        root,_=self.private_repository()
        original_rules=json.loads((root/'data/rules.json').read_text())
        notes=json.loads((root/'data/entry-notes.json').read_text())
        for field,value in (
            ('source','https://example.com/unreviewed-source'),
            ('source',notes[0]['evidence']['url']),
            ('park','unknown'),('park',notes[0]['park_code']),
            ('id',''),('id',None),('id','Invalid ID'),
        ):
            with self.subTest(field=field,value=value):
                rules=copy.deepcopy(original_rules); manifest=self.manifest()
                identifier=rules[0]['id']
                if field=='source': rules[0]['evidence']['url']=value
                elif field=='park': rules[0]['park_code']=value
                else: rules[0]['id']=value
                for row in manifest['records']:
                    if row['guidance_id']==identifier:
                        row['guidance_id']=rules[0]['id']; row['source_url']=rules[0]['evidence']['url']
                self.write_guidance(root,rules,notes,manifest)
                self.assert_inventory_blocked(root)

    def test_missing_pilot_source_cannot_pass_a_reduced_rights_manifest(self):
        root,_=self.private_repository(); original=self.records()
        for code in ('yose','romo','yell','zion','grca'):
            with self.subTest(park=code):
                removed={row['id'] for row in original if row['park_code']==code}
                rules=[row for row in json.loads((ROOT/'data/rules.json').read_text()) if row['id'] not in removed]
                notes=[row for row in json.loads((ROOT/'data/entry-notes.json').read_text()) if row['id'] not in removed]
                manifest=self.manifest()
                manifest['records']=[row for row in manifest['records'] if row['guidance_id'] not in removed]
                self.write_guidance(root,rules,notes,manifest)
                self.assert_inventory_blocked(root)

    def test_invalid_rights_inventory_blocks_all_targets_without_mutating_inputs(self):
        root,_=self.private_repository(); manifest=self.manifest(); manifest['records']=[]
        self.write_guidance(root,[],[],manifest)
        before={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
        for target in ('pilot','indexed','advertising'):
            with self.subTest(target=target):
                report=evaluate_readiness(root,release_target=target)
                gate=next(g for g in report['gates'] if g['id']=='source_rights')
                self.assertEqual(gate['status'],'blocked')
                self.assertTrue(gate['required']); self.assertTrue(gate['blocking'])
                self.assertFalse(report['release_ready'])
                self.assertFalse(report['network_performed']); self.assertFalse(report['writes_performed'])
        self.assertEqual(before,{p:p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_rights_inventory_accepts_record_and_manifest_reordering(self):
        root,_=self.private_repository()
        rules=json.loads((root/'data/rules.json').read_text())
        notes=json.loads((root/'data/entry-notes.json').read_text()); manifest=self.manifest()
        self.write_guidance(root,list(reversed(rules)),list(reversed(notes)),
                            {**manifest,'records':list(reversed(manifest['records']))})
        gate=_rights(root)
        self.assertEqual(gate['status'],'pass')
        self.assertEqual(gate['evidence']['guidance_records_total'],6)
        self.assertEqual(gate['evidence']['covered_guidance_records'],6)

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
            self.assertIsNone(re.search(r'<(?:img|video|audio|source)\b[^>]*\bnps\.gov\b',text,re.I),rel)

    def test_release_rights_gate_passes_only_for_complete_exact_manifest(self):
        gate=next(g for g in evaluate_readiness(ROOT)['gates'] if g['id']=='source_rights')
        self.assertEqual(gate['status'],'pass')
        self.assertEqual(gate['evidence']['covered_guidance_records'],6)
        self.assertEqual(gate['evidence']['guidance_records_total'],6)
        self.assertTrue(gate['evidence']['commercial_notice_present'])
        self.assertFalse(gate['evidence']['nps_marks_or_media_detected'])

    def test_notice_in_source_only_contexts_does_not_satisfy_rights_gate(self):
        root,layout=self.private_repository(); original=layout.read_text()
        for label,replacement in [
            ('html_comment','<!-- '+NOTICE+' -->'),
            ('script','<script>'+repr(NOTICE)+'</script>'),
            ('style','<style>/* '+NOTICE+' */</style>'),
            ('template','<template>'+NOTICE+'</template>'),
            ('noscript','<noscript>'+NOTICE+'</noscript>'),
            ('textarea','<textarea>'+NOTICE+'</textarea>'),
            ('attribute','<span data-notice="'+NOTICE+'"></span>'),
        ]:
            with self.subTest(context=label):
                self.assert_notice_blocked(root,layout,original.replace(NOTICE,replacement))
        for prefix in ('// '+NOTICE, 'const notice = '+repr(NOTICE)+';'):
            with self.subTest(context='frontmatter',prefix=prefix):
                source=original.replace(NOTICE,'').replace('---\n','---\n'+prefix+'\n',1)
                self.assert_notice_blocked(root,layout,source)

    def test_notice_outside_literal_body_footer_does_not_satisfy_rights_gate(self):
        root,layout=self.private_repository(); original=layout.read_text()
        empty=original.replace(NOTICE,'')
        sources=[
            empty.replace('<main ', '<p>'+NOTICE+'</p><main ',1),
            empty.replace('</head>', '<title>'+NOTICE+'</title></head>'),
            original.replace('<footer ', '<section ').replace('</footer>','</section>'),
            original.replace('<footer ', '<div><footer ').replace('</footer>','</footer></div>'),
        ]
        for source in sources:
            with self.subTest(source=source):
                self.assert_notice_blocked(root,layout,source)

    def test_conditional_or_component_notices_require_review(self):
        root,layout=self.private_repository(); original=layout.read_text()
        sources=[
            original.replace('<footer ','{false && <footer ').replace('</footer>','</footer>}'),
            original.replace(NOTICE,'{false && <span>'+NOTICE+'</span>}'),
            original.replace(NOTICE,'{/* '+NOTICE+' */}'),
            original.replace('<footer ','<Footer ').replace('</footer>','</Footer>'),
            original.replace(NOTICE,'<Conditional>'+NOTICE+'</Conditional>'),
            original.replace('<footer ','{false && <><span>{"}"}</span><footer ').replace('</footer>','</footer></>}'),
        ]
        for source in sources:
            with self.subTest(source=source):
                self.assert_notice_blocked(root,layout,source)

    def test_explicitly_hidden_notice_or_ancestor_does_not_satisfy_rights_gate(self):
        root,layout=self.private_repository(); original=layout.read_text()
        sources=[original.replace(NOTICE,'<span '+attrs+'>'+NOTICE+'</span>') for attrs in (
            'hidden','hidden="false"','aria-hidden="true"','inert',
            'style="display:none"','style="visibility:hidden"','style="opacity:0"')]
        sources += [original.replace('<'+tag, '<'+tag+' hidden',1) for tag in ('html','body','footer')]
        sources.append(original.replace('Government works','<span hidden>Government works</span>'))
        for source in sources:
            with self.subTest(source=source):
                self.assert_notice_blocked(root,layout,source)

    def test_dynamic_content_or_attributes_on_notice_ancestors_require_review(self):
        root,layout=self.private_repository(); original=layout.read_text()
        sources=[original.replace(NOTICE,'<span '+attrs+'>'+NOTICE+'</span>') for attrs in (
            'set:html={""}','set:text={""}','{...props}','hidden={false}',
            'class:list={{hidden:true}}','class="small" class="hidden"')]
        sources.append(original.replace('<body>', '<body set:html={""}>'))
        for source in sources:
            with self.subTest(source=source):
                self.assert_notice_blocked(root,layout,source)

    def test_unclosed_or_duplicate_footer_cannot_prove_public_notice(self):
        root,layout=self.private_repository(); original=layout.read_text()
        sources=[
            original.replace('</footer>',''),
            original.replace('</footer>','</div>'),
            original.replace('</body>','<footer>'+NOTICE+'</footer></body>'),
            original.replace(NOTICE,'<footer>'+NOTICE+'</footer>'),
        ]
        for source in sources:
            with self.subTest(source=source):
                self.assert_notice_blocked(root,layout,source)

    def test_literal_footer_notice_accepts_text_formatting_and_entities(self):
        root,layout=self.private_repository(); original=layout.read_text()
        for replacement in (
            NOTICE,
            'No protection is claimed in original <strong>U.S. Government works.</strong>',
            'No protection\n is claimed in original U.S. Government works&#46;',
            'No protection <!-- explanatory comment -->is claimed in original U.S. Government works.',
        ):
            with self.subTest(replacement=replacement):
                layout.write_text(original.replace(NOTICE,replacement))
                gate=_rights(root)
                self.assertEqual(gate['status'],'pass')
                self.assertTrue(gate['evidence']['commercial_notice_present'])

    def test_astro_source_inside_other_elements_cannot_invent_a_footer(self):
        root,layout=self.private_repository(); original=layout.read_text()
        start=original.index('    <footer')
        end=original.index('    </footer>')+len('    </footer>')
        empty=original[:start]+original[end:]
        for expression in (
            '{/* </main><footer>'+NOTICE+'</footer><main> */}',
            '{`</main><footer>'+NOTICE+'</footer><main>`}',
            '{"</main><footer>'+NOTICE+'</footer><main>"}',
        ):
            with self.subTest(expression=expression):
                self.assert_notice_blocked(root,layout,empty.replace('<slot />',expression))
        for expression in (
            '{`></main><footer>'+NOTICE+'</footer><main>`}',
            '{`}></main><footer>'+NOTICE+'</footer><main>`}',
            '{"x></main><footer>'+NOTICE+'</footer><main>"}',
            '{1 > 0 ? `</main><footer>'+NOTICE+'</footer><main>` : ""}',
        ):
            with self.subTest(attribute=expression):
                self.assert_notice_blocked(root,layout,empty.replace('<main ', '<main data-note='+expression+' ',1))
        head_comment='{/* </title></head><body><footer>'+NOTICE+'</footer></body><head><title> */}'
        self.assert_notice_blocked(root,layout,empty.replace('{title}',head_comment))

    def test_default_hidden_popover_cannot_supply_notice(self):
        root,layout=self.private_repository(); original=layout.read_text()
        for attrs in ('popover','popover="auto"','popover="manual"'):
            with self.subTest(attrs=attrs):
                self.assert_notice_blocked(root,layout,original.replace(NOTICE,'<span '+attrs+'>'+NOTICE+'</span>'))

    def test_duplicate_document_elements_cannot_prove_public_notice(self):
        root,layout=self.private_repository(); original=layout.read_text()
        for source in (
            original.replace('<body>','<body hidden></body><body>'),
            original.replace('<body>','<body></body><body>'),
            original.replace('<html lang="en">','<html hidden></html><html lang="en">'),
        ):
            with self.subTest(source=source):
                self.assert_notice_blocked(root,layout,source)

    def test_missing_public_notice_blocks_every_target_without_writes(self):
        root,layout=self.private_repository()
        layout.write_text(layout.read_text().replace(NOTICE,'<!-- '+NOTICE+' -->'))
        before={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
        for target in ('pilot','indexed','advertising'):
            with self.subTest(target=target):
                report=evaluate_readiness(root,release_target=target)
                gate=next(g for g in report['gates'] if g['id']=='source_rights')
                self.assertEqual(gate['status'],'blocked')
                self.assertTrue(gate['required']); self.assertTrue(gate['blocking'])
                self.assertFalse(report['release_ready'])
                self.assertFalse(report['network_performed']); self.assertFalse(report['writes_performed'])
        self.assertEqual(before,{p:p.read_bytes() for p in root.rglob('*') if p.is_file()})

if __name__=='__main__': unittest.main()
