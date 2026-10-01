import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { assertHistoryCounts, assertHistoryPanel } from './history-rendering.mjs';
import { assertLivePilotCopy } from './live-pilot-copy.mjs';
const routes = ['', 'parks', 'parks/yosemite', 'parks/rocky-mountain', 'parks/yellowstone', 'parks/zion', 'parks/grand-canyon', 'how-it-works', 'sources', 'changes', 'about', 'privacy', 'terms', 'corrections'];
const output = process.env.SITE_TEST_OUTPUT || 'dist';
const base = process.env.SITE_TEST_BASE || '/';
const parks = JSON.parse(readFileSync(new URL('../data/parks.json', import.meta.url), 'utf8'));
const rules = JSON.parse(readFileSync(new URL('../data/rules.json', import.meta.url), 'utf8'));
const notes = JSON.parse(readFileSync(new URL('../data/entry-notes.json', import.meta.url), 'utf8'));
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

test('informational pages describe the hosted manual pilot honestly', () => assertLivePilotCopy(output));

test('public source articles offer exact base-aware correction links without JavaScript', () => {
  for (const park of parks) {
    const snapshot = snapshots.find((item) => item.park_code === park.code);
    const sources = [
      ...rules.filter((rule) => rule.park_code === park.code).map((rule) => ({ kind: 'rule', id: rule.id, anchor: `entry-rule-${rule.id}` })),
      ...notes.filter((note) => note.park_code === park.code).map((note) => ({ kind: 'note', id: note.id, anchor: `entry-note-${note.id}` })),
      ...snapshot.records.map((alert) => ({ kind: 'alert', id: alert.id, anchor: `alert-${park.code}-${alert.id}` })),
    ];
    const html = readFileSync(`${output}/parks/${park.slug}/index.html`, 'utf8');
    const articles = [...html.matchAll(/<article\b[^>]*>[\s\S]*?<\/article>/g)].map(([article]) => article);
    const correctionLinks = [...html.matchAll(/<a\b[^>]*\bdata-correction-link\b[^>]*>[\s\S]*?<\/a>/g)];
    assert.equal(correctionLinks.length, sources.length, `${park.code}: one link per current public source`);
    for (const source of sources) {
      const matches = articles.filter((article) => decodeHtml(article.match(/^<article\b[^>]*>/)[0]).includes(`id="${source.anchor}"`));
      assert.equal(matches.length, 1, `${park.code}: exact stable article for ${source.kind}:${source.id}`);
      const links = [...matches[0].matchAll(/<a\b[^>]*\bdata-correction-link\b[^>]*>[\s\S]*?<\/a>/g)].map(([link]) => link);
      assert.equal(links.length, 1, `${park.code}: correction link beside ${source.kind}:${source.id}`);
      const href = links[0].match(/\bhref="([^"]*)"/);
      assert.ok(href, 'Correction link has a native destination');
      assert.equal(decodeHtml(href[1]), `${base}corrections/?source=${encodeURIComponent(`${source.kind}:${park.code}:${source.id}`)}`);
      assert.match(links[0], />Report a correction about this source<\/a>/);
    }
  }
});

test('corrections context catalog retains exactly current public source identities and return destinations', () => {
  const html = readFileSync(`${output}/corrections/index.html`, 'utf8');
  const catalog = embeddedJson(html, 'data-correction-sources');
  const expected = parks.flatMap((park) => {
    const snapshot = snapshots.find((item) => item.park_code === park.code);
    return [
      ...rules.filter((rule) => rule.park_code === park.code).map((rule) => ({ kind: 'rule', recordId: rule.id, sourceUrl: rule.evidence.url, anchor: `entry-rule-${rule.id}` })),
      ...notes.filter((note) => note.park_code === park.code).map((note) => ({ kind: 'note', recordId: note.id, sourceUrl: note.evidence.url, anchor: `entry-note-${note.id}` })),
      ...snapshot.records.map((alert) => ({ kind: 'alert', recordId: alert.id, sourceUrl: alert.url, anchor: `alert-${park.code}-${alert.id}` })),
    ].map(({ anchor, ...source }) => ({
      ...source,
      key: `${source.kind}:${park.code}:${source.recordId}`,
      parkCode: park.code,
      returnHref: `${base}parks/${park.slug}/#${encodeURIComponent(anchor)}`,
    }));
  });
  const identity = ({ key, parkCode, kind, recordId, sourceUrl, returnHref }) => ({ key, parkCode, kind, recordId, sourceUrl, returnHref });
  const byKey = (a, b) => a.key.localeCompare(b.key);
  assert.deepEqual(catalog.map(identity).sort(byKey), expected.sort(byKey));
});

test('all park pages and changes overview retain exact paired history and observation clocks', () => {
  const overview = readFileSync(`${output}/changes/index.html`, 'utf8');
  assertHistoryCounts(overview, histories);
  for (const park of parks) {
    const snapshot = snapshots.find((item) => item.park_code === park.code);
    const history = histories.find((item) => item.park_code === park.code);
    for (const html of [readFileSync(`${output}/parks/${park.slug}/index.html`, 'utf8'), overview]) {
      assertHistoryPanel(html, snapshot, history);
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
