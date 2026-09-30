"""Manual-only GitHub Pages deployment/rollback workflow contracts."""
import re
import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from tracker.release_readiness import evaluate_readiness

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/'.github/workflows/pages-release.yml'

class PagesReleaseWorkflowTests(unittest.TestCase):
    def text(self):
        return WORKFLOW.read_text(encoding='utf-8')

    def test_workflow_is_manual_only_and_never_runs_on_push_or_pull_request(self):
        text=self.text()
        on_block=text.split('permissions:',1)[0]
        self.assertIn('workflow_dispatch:',on_block)
        self.assertNotRegex(on_block,r'(?m)^\s*push\s*:')
        self.assertNotRegex(on_block,r'(?m)^\s*pull_request\s*:')
        self.assertNotRegex(on_block,r'(?m)^\s*schedule\s*:')

    def test_release_requires_explicit_mode_commit_verify_run_and_confirmation(self):
        text=self.text()
        for value in ('mode:','target_sha:','verify_run_id:','confirmation:'):
            self.assertIn(value,text)
        self.assertIn('DEPLOY_VERIFIED_PILOT',text)
        self.assertIn('ROLLBACK_VERIFIED_PILOT',text)
        self.assertIn("mode === 'deploy'",text)
        self.assertIn("mode === 'rollback'",text)

    def test_permissions_are_narrow_and_pages_specific(self):
        text=self.text()
        self.assertRegex(text,r'(?m)^\s*contents:\s*read\s*$')
        self.assertRegex(text,r'(?m)^\s*pages:\s*write\s*$')
        self.assertRegex(text,r'(?m)^\s*id-token:\s*write\s*$')
        for forbidden in ('contents: write','actions: write','pull-requests: write','issues: write'):
            self.assertNotIn(forbidden,text)

    def test_deploys_the_existing_verified_artifact_not_a_rebuild(self):
        text=self.text()
        self.assertIn('actions/download-artifact@v4',text)
        self.assertIn('name: pilot-verification',text)
        self.assertIn('run-id:',text)
        self.assertIn('github-token:',text)
        self.assertIn('actions/upload-pages-artifact@v3',text)
        self.assertIn('actions/deploy-pages@v4',text)
        for forbidden in ('npm run build','npm ci','astro build','actions/checkout@'):
            self.assertNotIn(forbidden,text)

    def test_verify_run_must_be_successful_verify_pilot_for_exact_commit(self):
        text=self.text()
        self.assertIn('actions/github-script@v7',text)
        self.assertIn('Verify pilot',text)
        self.assertIn("run.conclusion !== 'success'",text)
        self.assertIn('run.head_sha',text)
        self.assertIn('target_sha',text)
        self.assertIn('verify_run_id',text)

    def test_artifact_is_sanity_checked_and_only_dist_is_uploaded(self):
        text=self.text()
        self.assertIn('dist/build.json',text)
        self.assertIn('dist/index.html',text)
        self.assertIn('steps.artifact.outputs.site_path',text)
        self.assertIn('find _verified -type l',text)

    def test_pages_path_is_matched_to_verified_artifact_before_upload(self):
        text=self.text()
        self.assertIn('id: pages',text)
        self.assertIn('steps.pages.outputs.base_path',text)
        self.assertIn('Select the verified build matching the Pages path',text)
        guard=text.index('Select the verified build matching the Pages path')
        upload=text.index('actions/upload-pages-artifact@v3')
        deploy=text.index('actions/deploy-pages@v4')
        self.assertLess(guard,upload)
        self.assertLess(guard,deploy)

    def test_rollback_is_the_same_verified_artifact_path_not_a_special_mutating_script(self):
        text=self.text()
        self.assertEqual(text.count('actions/deploy-pages@v4'),1)
        self.assertNotIn('git revert',text)
        self.assertNotIn('git reset',text)
        self.assertNotIn('git push',text)
        self.assertNotIn('gh api --method DELETE',text)

    def test_release_readiness_moves_hosting_from_blocked_to_not_checked_only(self):
        gate=next(g for g in evaluate_readiness(ROOT)['gates'] if g['id']=='hosting_rollback')
        self.assertEqual(gate['status'],'not_checked')
        self.assertFalse(gate['evidence']['rollback_verified'])
        self.assertTrue(gate['evidence']['deployment_markers'])

    def test_noindex_and_public_safety_controls_remain_unchanged(self):
        layout=(ROOT/'src/layouts/Layout.astro').read_text(encoding='utf-8').lower()
        robots=(ROOT/'public/robots.txt').read_text(encoding='utf-8').lower()
        headers=(ROOT/'public/_headers').read_text(encoding='utf-8').lower()
        self.assertIn('noindex',layout)
        self.assertRegex(robots,r'(?m)^disallow:\s*/\s*$')
        self.assertIn('x-robots-tag: noindex',headers)

    def test_live_verification_uses_the_deployment_url_and_exact_selected_artifact(self):
        text=self.text()
        deploy=text.index('id: deployment')
        probe=text.index('name: Verify the actual hosted release')
        self.assertLess(deploy,probe)
        step=text[probe:]
        for value in ('steps.deployment.outputs.page_url','steps.artifact.outputs.site_path',
                      'github.event.inputs.target_sha','github.event.inputs.mode',
                      'node _verified/scripts/verify-pages-live.mjs',
                      '--directory "$SITE_DIRECTORY"','--url "$PAGE_URL"',
                      '--commit "$TARGET_SHA"','--mode "$RELEASE_MODE"'):
            self.assertIn(value,step)
        self.assertIn('node-version:',text)
        self.assertIn('"24"',text)
        self.assertNotIn('continue-on-error:',step)

    def test_receipt_is_retained_on_failed_checks_without_uploading_tools_to_pages(self):
        text=self.text()
        self.assertIn('test -f _verified/scripts/verify-pages-live.mjs',text)
        self.assertIn('> pages-live-verification.json',text)
        self.assertIn("if: always() && steps.deployment.outcome == 'success'",text)
        self.assertIn('name: pages-live-verification',text)
        self.assertIn('path: pages-live-verification.json',text)
        self.assertIn('if-no-files-found: error',text)
        ci=(ROOT/'.github/workflows/ci.yml').read_text(encoding='utf-8')
        self.assertIn('scripts/verify-pages-live.mjs',ci.split('actions/upload-artifact@v4',1)[1])
        pages_upload=text.split('actions/upload-pages-artifact@v3',1)[1].split('- name:',1)[0]
        self.assertNotIn('scripts/',pages_upload)

class PagesArtifactSelectionTests(unittest.TestCase):
    SHA = 'a' * 40
    BASE = '/us-national-park-trip-readiness-tracker/'

    def select(self, path, manifests, raw_manifests=()):
        text = WORKFLOW.read_text(encoding='utf-8')
        step = text.split('name: Select the verified build matching the Pages path', 1)[1]
        script = textwrap.dedent(step.split('script: |\n', 1)[1].split('\n      - name:', 1)[0])
        wrapper = '''const outputs = {}; let error = null;
const core = { setOutput: (key, value) => outputs[key] = value,
  setFailed: message => { error = message; process.exitCode = 1; } };
async function selectArtifact() {
''' + script + '''\n}
selectArtifact().then(() => console.log(JSON.stringify({ outputs, error })));
'''
        with tempfile.TemporaryDirectory() as folder:
            for directory, manifest in manifests.items():
                root = Path(folder) / '_verified' / directory
                root.mkdir(parents=True)
                (root / 'index.html').write_text('<h1>Synthetic test</h1>', encoding='utf-8')
                content = manifest if directory in raw_manifests else json.dumps(manifest)
                (root / 'build.json').write_text(content, encoding='utf-8')
            result = subprocess.run(['node', '-e', wrapper], cwd=folder,
                env={**os.environ, 'PAGES_BASE_PATH': path, 'TARGET_SHA': self.SHA},
                capture_output=True, text=True, timeout=10)
        self.assertTrue(result.stdout, result.stderr)
        return result.returncode, json.loads(result.stdout)

    def manifest(self, base):
        return {'base_path': base, 'code_commit': self.SHA}

    def test_root_and_project_select_only_matching_outputs(self):
        manifests = {'dist': self.manifest('/'), 'dist-pages': self.manifest(self.BASE)}
        for path, expected in [('', '_verified/dist'), ('/', '_verified/dist'),
                (self.BASE, '_verified/dist-pages'), (self.BASE.rstrip('/'), '_verified/dist-pages')]:
            with self.subTest(path=path):
                code, result = self.select(path, manifests)
                self.assertEqual(code, 0)
                self.assertIsNone(result['error'])
                self.assertEqual(result['outputs']['site_path'], expected)

    def test_legacy_manifest_is_root_only(self):
        legacy = {'code_commit': self.SHA}
        self.assertEqual(self.select('', {'dist': legacy})[0], 0)
        code, result = self.select(self.BASE, {'dist': legacy, 'dist-pages': legacy})
        self.assertEqual(code, 1)
        self.assertEqual(result['outputs'], {})

    def test_missing_project_artifact_fails_without_output(self):
        code, result = self.select(self.BASE, {'dist': self.manifest('/')})
        self.assertEqual(code, 1)
        self.assertEqual(result['outputs'], {})

    def test_mismatched_and_invalid_manifest_paths_fail_without_output(self):
        for base in ['/', '/different-project/', None, 42]:
            with self.subTest(base=base):
                code, result = self.select(self.BASE, {'dist-pages': self.manifest(base)})
                self.assertEqual(code, 1)
                self.assertEqual(result['outputs'], {})

    def test_manifest_commit_must_match_requested_verified_commit(self):
        manifest = {**self.manifest(self.BASE), 'code_commit': 'b' * 40}
        code, result = self.select(self.BASE, {'dist-pages': manifest})
        self.assertEqual(code, 1)
        self.assertEqual(result['outputs'], {})

    def test_non_object_manifest_fails_without_output(self):
        for manifest in [None, [], 'invalid']:
            with self.subTest(manifest=manifest):
                code, result = self.select(self.BASE, {'dist-pages': manifest})
                self.assertEqual(code, 1)
                self.assertEqual(result['outputs'], {})

    def test_malformed_json_manifest_fails_without_output(self):
        code, result = self.select(self.BASE, {'dist-pages': '{broken'}, raw_manifests=('dist-pages',))
        self.assertEqual(code, 1)
        self.assertEqual(result['outputs'], {})

if __name__=='__main__': unittest.main()
