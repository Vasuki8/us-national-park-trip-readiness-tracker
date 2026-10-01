import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { assertHistoryCounts, assertHistoryPanel } from './history-rendering.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const cases = JSON.parse(readFileSync(new URL('./fixtures/history-preview.json', import.meta.url), 'utf8')).cases;

test('generated history checks accept later observations, bounded windows and uncollected clocks', () => {
  const build = spawnSync(process.execPath, ['node_modules/astro/bin/astro.mjs', 'build', '--root', 'tests/history-site'], {
    cwd: root, encoding: 'utf8', timeout: 120_000, env: { ...process.env, ASTRO_TELEMETRY_DISABLED: '1' },
  });
  assert.equal(build.status, 0, build.error?.message || build.stdout + build.stderr);
  for (const scenario of ['mixed', 'truncated', 'empty', 'baseline', 'failed']) {
    const html = readFileSync(new URL(`../.superpowers/history-site/dist/${scenario}/index.html`, import.meta.url), 'utf8');
    const view = cases[scenario];
    assertHistoryCounts(html, [view.history]);
    assertHistoryPanel(html, view.snapshot, view.history);
  }
  const mixed = readFileSync(new URL('../.superpowers/history-site/dist/mixed/index.html', import.meta.url), 'utf8');
  assert.throws(() => assertHistoryPanel(mixed.replace('2026-09-28T12:00:00Z</time>', '2026-09-29T12:00:00Z</time>'), cases.mixed.snapshot, cases.mixed.history));
  assert.throws(() => assertHistoryPanel(mixed.replace('data-history-observation', 'data-missing-observation'), cases.mixed.snapshot, cases.mixed.history));
  const bounded = readFileSync(new URL('../.superpowers/history-site/dist/truncated/index.html', import.meta.url), 'utf8');
  assert.throws(() => assertHistoryPanel(bounded.replace('2 older recorded checks not shown.', ''), cases.truncated.snapshot, cases.truncated.history));
});
