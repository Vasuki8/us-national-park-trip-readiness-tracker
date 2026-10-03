import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

test('real profile rendering escapes source text and distinguishes absent, null, empty and retained degraded evidence', () => {
  const result = spawnSync(process.execPath, ['node_modules/astro/bin/astro.mjs', 'build', '--root', 'tests/profile-site'], {
    cwd: new URL('../', import.meta.url), encoding: 'utf8', timeout: 120_000,
    env: { ...process.env, ASTRO_TELEMETRY_DISABLED: '1' },
  });
  assert.equal(result.status, 0, result.error?.message ?? result.stdout + result.stderr);
  const html = (scenario: string) => readFileSync(new URL(`../.superpowers/profile-site/dist/${scenario}/index.html`, import.meta.url), 'utf8');
  const absent = html('absent');
  assert.match(absent, /Park profile not available/);
  assert.doesNotMatch(absent, /data-profile-success|data-profile-source/);
  assert.match(absent, /data-profile-clock="null"/);
  const missing = html('missing');
  assert.match(missing, /An introduction is not available/);
  assert.match(missing, /Seasonal context is not available/);
  assert.match(missing, /Activity categories are not available/);
  const empty = html('empty');
  assert.match(empty, /The stored official profile has no introduction text/);
  assert.match(empty, /The stored official profile has no seasonal text/);
  assert.match(empty, /No activity categories were supplied\. This does not establish that there are no activities/);
  for (const scenario of ['escaped', 'failed', 'quarantined']) {
    const page = html(scenario);
    assert.ok(page.includes('&lt;script&gt;window.syntheticInjection = true&lt;/script&gt;'));
    assert.ok(page.includes('Synthetic seasonal &lt;b&gt;context&lt;/b&gt;, not a forecast.'));
    assert.ok(page.includes('&lt;img src=x onerror='));
    assert.doesNotMatch(page, /<script>window\.syntheticInjection|<img\b|<b>context/);
    assert.match(page, /datetime="2026-09-28T10:00:00Z"[^>]*>2026-09-28T10:00:00Z<\/time>/);
    if (scenario !== 'escaped') {
      assert.ok(page.includes(`data-profile-state="${scenario}"`));
      assert.ok(page.includes('datetime="2026-09-29T10:00:00Z"'));
      assert.match(page, /Retained text is dated by its last successful check/);
    }
  }
  assert.match(html('stale'), /data-profile-state="stale"/);
  assert.match(html('stale'), /datetime="2020-01-01T10:00:00Z"/);
});
