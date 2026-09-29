"""Manual-only GitHub Pages deployment/rollback workflow contracts."""
import re
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
        self.assertRegex(text,r'path:\s*_verified/dist')
        self.assertIn('find _verified/dist -type l',text)

    def test_pages_project_subpath_is_refused_before_upload(self):
        text=self.text()
        self.assertIn('id: pages',text)
        self.assertIn('steps.pages.outputs.base_path',text)
        self.assertIn('Current verified build requires Pages root hosting',text)
        guard=text.index('Current verified build requires Pages root hosting')
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

if __name__=='__main__': unittest.main()
