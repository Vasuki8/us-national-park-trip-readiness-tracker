import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
const routes = ['', 'parks', 'parks/yosemite', 'parks/rocky-mountain', 'parks/yellowstone', 'parks/zion', 'parks/grand-canyon', 'how-it-works', 'sources', 'changes', 'about', 'privacy', 'terms', 'corrections'];
const output = process.env.SITE_TEST_OUTPUT || 'dist';
const base = process.env.SITE_TEST_BASE || '/';
const parks = JSON.parse(readFileSync(new URL('../data/parks.json', import.meta.url), 'utf8'));
const histories = JSON.parse(readFileSync(new URL('../data/history.json', import.meta.url), 'utf8'));
const snapshots = parks.map((park) => JSON.parse(readFileSync(new URL(`../data/alerts/${park.code}.json`, import.meta.url), 'utf8')));
const decodeHtml = (value) => value.replace(/&(?:quot|amp|lt|gt|#39);/g, (entity) => ({ '&quot;': '"', '&amp;': '&', '&lt;': '<', '&gt;': '>', '&#39;': "'" })[entity]);
const embeddedJson = (html, attribute) => {
  const match = html.match(new RegExp(`${attribute}="([^"]*)"`));
  assert.ok(match, `Missing ${attribute}`);
  return JSON.parse(decodeHtml(match[1]));
};
for (const route of routes) test(`static HTML and noindex: /${route}`, () => {
  const html = readFileSync(`${output}/${route ? route + '/' : ''}index.html`, 'utf8');
  assert.match(html, /<h1[\s>]/);
  assert.match(html, /name="robots" content="noindex, nofollow"/);
  assert.match(html, /<html lang="en"/);
  assert.doesNotMatch(html, /adsbygoogle|googletagmanager|googlesyndication/);
});
test('all five parks are in static HTML even before JavaScript', () => {
  const html = readFileSync(`${output}/parks/index.html`, 'utf8');
  for (const name of ['Yosemite', 'Rocky Mountain', 'Yellowstone', 'Zion', 'Grand Canyon']) assert.ok(html.includes(name));
});
test('all park pages retain the exact public checked-feed snapshot and official sources', () => {
  for (const park of parks) {
    const snapshot = snapshots.find((item) => item.park_code === park.code);
    const html = readFileSync(`${output}/parks/${park.slug}/index.html`, 'utf8');
    assert.deepEqual(embeddedJson(html, 'data-snapshot'), snapshot);
    assert.equal(snapshot.collection_status, 'success');
    assert.ok(html.includes(snapshot.last_successful_fetch_at));
    assert.ok(html.includes('Published restrictions · Coverage incomplete'));
    assert.ok(html.includes(`href="${park.conditions_url}"`));
    assert.ok(html.includes('Source update time: Not supplied'));
    if (snapshot.records.length) {
      assert.ok(html.includes('Notices retained from the checked feed'));
      const retained = html.split('Notices retained from the checked feed</h2>')[1].split('</section>')[0];
      assert.equal((retained.match(/<article /g) || []).length, snapshot.records.length);
      const text = decodeHtml(retained);
      for (const record of snapshot.records) {
        assert.ok(text.includes(record.title));
        assert.ok(text.includes(record.description));
        if (record.url) assert.ok(text.includes(`href="${record.url}"`));
        else assert.ok(text.includes('NPS did not supply a direct link for this alert.'));
      }
    } else {
      assert.ok(!html.includes('Notices retained from the checked feed'));
      assert.match(html, /No alerts returned by the checked feed|The condition snapshot needs a fresh check/);
    }
    assert.ok(html.includes('not verify bookings'));
  }
});

test('all park pages and changes overview retain exact baseline observation clocks', () => {
  const overview = readFileSync(`${output}/changes/index.html`, 'utf8');
  assert.equal((overview.match(/data-history-observation/g) || []).length, 5);
  assert.equal((overview.match(/Baseline recorded/g) || []).length, 5);
  for (const park of parks) {
    const snapshot = snapshots.find((item) => item.park_code === park.code);
    const history = histories.find((item) => item.park_code === park.code);
    for (const html of [readFileSync(`${output}/parks/${park.slug}/index.html`, 'utf8'), overview]) {
      const panel = html.match(new RegExp(`<section[^>]*id="history-${park.code}"[^>]*>[\\s\\S]*?</section>`))?.[0];
      assert.ok(panel, `Missing history for ${park.code}`);
      assert.deepEqual(embeddedJson(panel, 'data-history-metadata'), {
        collection_status: snapshot.collection_status, last_checked_at: snapshot.last_checked_at,
        last_successful_fetch_at: snapshot.last_successful_fetch_at,
      });
      const clocks = [...panel.matchAll(/<time datetime="([^"]*)"/g)].map((match) => match[1]);
      assert.deepEqual(clocks, [snapshot.last_successful_fetch_at, ...history.observations.map((item) => item.checked_at)]);
      assert.equal((panel.match(/data-history-observation/g) || []).length, history.observations.length);
      assert.ok(panel.includes('not evidence that its restrictions began at this time'));
    }
  }
});
test('internal page links and bundled assets stay under the base and resolve', () => {
  const result = spawnSync('python3', ['tests/site_links.py', '--output', output, '--base', base], { encoding: 'utf8', timeout: 30_000 });
  assert.equal(result.status, 0, result.error?.message || result.stdout + result.stderr);
  console.log(result.stdout.trim());
});
test('active navigation identifies the current path under the hosting base', () => {
  for (const route of ['parks', 'how-it-works', 'sources', 'about', 'privacy', 'terms', 'corrections', 'changes']) {
    const html = readFileSync(`${output}/${route}/index.html`, 'utf8');
    assert.ok(html.includes(`href="${base}${route}/" aria-current="page"`), route);
  }
});
test('build manifest records the independently expected hosting path', () => {
  const info = JSON.parse(readFileSync(`${output}/build.json`, 'utf8'));
  assert.equal(info.base_path, base);
  if (output === 'dist-pages') {
    const root = JSON.parse(readFileSync('dist/build.json', 'utf8'));
    assert.equal(info.snapshot_id, root.snapshot_id);
    assert.equal(info.code_commit, root.code_commit);
  }
});
test('build manifest distinguishes build and publication', () => {
  const info = JSON.parse(readFileSync(`${output}/build.json`, 'utf8'));
  assert.equal(info.published_at, null);
  assert.ok(info.built_at);
  assert.match(info.snapshot_id, /^pilot-[a-f0-9]{12}$/);
  assert.equal(info.live_collection_enabled, false);
});
