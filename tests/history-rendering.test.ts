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
    assert.doesNotMatch(html, /data-history-notice-link|data-history-park-link|A unique retained notice/, 'shared timelines without public navigation context do not invent production targets');
  }
  for (const scenario of ['mixed', 'failed']) {
    const html = readFileSync(new URL(`../.superpowers/history-site/dist/retained/${scenario}/index.html`, import.meta.url), 'utf8');
    const view = cases[scenario];
    assertHistoryCounts(html, [view.history]);
    assertHistoryPanel(html, view.snapshot, view.history);
    const changes = [...html.matchAll(/<article\b[^>]*class="history-change"[^>]*>[\s\S]*?<\/article>/g)].map(([article]) => article);
    const expected = view.history.observations.flatMap((observation: { changes: { record_id: string }[] }) => observation.changes);
    assert.equal(changes.length, expected.length);
    for (const [index, change] of expected.entries()) {
      const retained = view.snapshot.records.filter((record: { id: string }) => record.id === change.record_id);
      const links = [...changes[index].matchAll(/<a\b[^>]*href="([^"]*)"[^>]*data-history-notice-link[^>]*>/g)];
      assert.equal(links.length, retained.length === 1 ? 1 : 0, 'only exact unique retained IDs have a destination');
      if (retained.length === 1) {
        const anchor = `alert-${view.snapshot.park_code}-${change.record_id}`;
        assert.equal(links[0][1], `#${encodeURIComponent(anchor)}`);
        assert.ok(html.includes(`id="${anchor}" tabindex="-1"`), 'the emitted destination is a focusable retained article');
        assert.match(changes[index], /Retained wording may differ from this comparison\. This is stored evidence, not live conditions\./);
      } else {
        assert.match(changes[index], /A unique retained notice could not be identified for this comparison\. This does not establish reopening\./);
      }
    }
    assert.match(html, /A notice disappearing is not a confirmed reopening\./);
    assert.doesNotMatch(html, /data-history-park-link/, 'same-page evidence navigation adds no redundant overview return link');
  }
  const mixed = readFileSync(new URL('../.superpowers/history-site/dist/mixed/index.html', import.meta.url), 'utf8');
  assert.throws(() => assertHistoryPanel(mixed.replace('2026-09-28T12:00:00Z</time>', '2026-09-29T12:00:00Z</time>'), cases.mixed.snapshot, cases.mixed.history));
  assert.throws(() => assertHistoryPanel(mixed.replace('data-history-observation', 'data-missing-observation'), cases.mixed.snapshot, cases.mixed.history));
  const bounded = readFileSync(new URL('../.superpowers/history-site/dist/truncated/index.html', import.meta.url), 'utf8');
  assert.throws(() => assertHistoryPanel(bounded.replace('2 older recorded checks not shown.', ''), cases.truncated.snapshot, cases.truncated.history));
});
