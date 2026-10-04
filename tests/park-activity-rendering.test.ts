import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

test('native activity rendering preserves selected text, uncertainty and withheld privacy across catalog states', () => {
  const result = spawnSync(process.execPath, ['node_modules/astro/bin/astro.mjs', 'build', '--root', 'tests/activity-site'], {
    cwd: new URL('../', import.meta.url), encoding: 'utf8', timeout: 120_000,
    env: { ...process.env, ASTRO_TELEMETRY_DISABLED: '1' },
  });
  assert.equal(result.status, 0, result.error?.message ?? result.stdout + result.stderr);
  const html = (scenario: string) => readFileSync(new URL(`../.superpowers/activity-site/dist/${scenario}/index.html`, import.meta.url), 'utf8');
  const absent = html('absent');
  assert.match(absent, /id="things-to-do"[^>]*tabindex="-1"[^>]*aria-labelledby="things-to-do-title"/);
  assert.match(absent, /Activity catalog not available/);
  assert.match(absent, /data-activity-clock="null"/);
  assert.doesNotMatch(absent, /data-activity-success|data-activity-source|data-activity-record/);
  for (const scenario of ['published', 'category-null', 'category-empty', 'category-withheld', 'failed', 'quarantined', 'stale', 'large']) {
    const page = html(scenario);
    const disclosure = page.match(/<details\b[^>]*data-activity-inventory[^>]*>/)?.[0];
    assert.ok(disclosure, `${scenario}: the stored inventory has a native disclosure`);
    assert.doesNotMatch(disclosure, /\bopen(?:[\s=>]|$)/);
    assert.ok(page.includes('Synthetic café &amp; &quot;quoted&quot; 🌲 listing'));
    assert.match(page, /data-activity-link[^>]*href="https:\/\/www\.nps\.gov\/yose\/synthetic-1\.htm"|href="https:\/\/www\.nps\.gov\/yose\/synthetic-1\.htm"[^>]*data-activity-link/);
    assert.match(page, /availability.*not verified/i);
    assert.match(page, /relationship to this park is unconfirmed/i);
    assert.match(page, /responsible agency.*unknown/i);
    assert.match(page, /difficulty.*unknown/i);
    assert.match(page, /permit requirements.*unknown/i);
    assert.doesNotMatch(page, /PRIVATE_SOURCE_ID|source_content_hash|view_hash|content_hash|withholding_reason/);
    assert.match(page, /Source issue\/update time: Not supplied/);
    assert.match(page, /Freshness labels reflect the build without JavaScript/);
  }
  const published = html('published');
  assert.match(published, /data-activity-counts[^>]*>1 published listings? · 2 source listings · 1 withheld listings?</);
  assert.match(published, /withholding does not mean source removal/i);
  assert.match(published, /Synthetic &amp; &quot;exact&quot; category/);
  assert.match(html('category-null'), /Categories are not available in the stored listing/);
  assert.match(html('category-empty'), /No categories were supplied for this listing/);
  assert.match(html('category-withheld'), /Categories are withheld from this published view/);
  for (const scenario of ['category-null', 'category-empty', 'category-withheld']) assert.doesNotMatch(html(scenario), /data-activity-category/);
  const empty = html('empty');
  assert.match(empty, /No listings were returned by the checked activity feed/);
  assert.match(empty, /does not establish that there are no activities/);
  assert.doesNotMatch(empty, /data-activity-record/);
  const whollyWithheld = html('wholly-withheld');
  assert.match(whollyWithheld, /All stored source listings are withheld from this catalog/);
  assert.doesNotMatch(whollyWithheld, /No listings were returned|PRIVATE_SOURCE_ID|data-activity-record/);
  for (const scenario of ['failed', 'quarantined']) {
    const page = html(scenario);
    assert.ok(page.includes(`data-activity-state="${scenario}"`));
    assert.match(page, /Retained listings are dated by their last successful check/);
    assert.match(page, /datetime="2026-10-04T05:49:46\.709637Z"[^>]*>2026-10-04T05:49:46\.709637Z<\/time>/);
    assert.match(page, /datetime="2026-10-04T05:49:46\.709638Z"/);
    assert.match(page, /Coverage: Incomplete/);
  }
  assert.match(html('stale'), /data-activity-state="stale"/);
  assert.match(html('stale'), /datetime="2020-01-01T10:00:00\.123456Z"/);
  const large = html('large');
  assert.equal([...large.matchAll(/<li\b[^>]*data-activity-record/g)].length, 84);
  assert.equal([...large.matchAll(/<a\b[^>]*data-activity-link/g)].length, 84);
  assert.match(large, /data-activity-counts[^>]*>84 published listings · 85 source listings · 1 withheld listings?</);
  const clock = published.match(/data-activity-clock="([^"]*)"/)?.[1];
  assert.ok(clock);
  const metadata = JSON.parse(clock.replaceAll('&quot;', '"'));
  assert.deepEqual(metadata, { collection_status: 'success', last_checked_at: '2026-10-04T05:49:46.709637Z', last_successful_fetch_at: '2026-10-04T05:49:46.709637Z' });
});
