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

test('park section navigation contains native destinations only for sections present in each park', () => {
  for (const park of parks) {
    const snapshot = snapshots.find((item) => item.park_code === park.code);
    const html = readFileSync(`${output}/parks/${park.slug}/index.html`, 'utf8');
    const menus = [...html.matchAll(/<nav\b[^>]*\bdata-park-page-nav\b[^>]*>[\s\S]*?<\/nav>/g)];
    assert.equal(menus.length, 1, `${park.code}: a native local navigation menu exists`);
    const menu = menus[0][0];
    assert.match(menu, /aria-label="On this page"/);
    assert.match(menu, /<ul\b/);
    const links = [...menu.matchAll(/<a\b([^>]*)>([\s\S]*?)<\/a>/g)];
    const expected = ['#alert-status', ...(snapshot.records.length ? ['#retained-notices'] : []), '#trip-context', '#checklist-title', '#guidance-title', `#history-${park.code}`, '#official-checks'];
    assert.deepEqual(links.map((link) => decodeHtml(link[1].match(/\bhref="([^"]*)"/)[1])), expected);
    for (const link of links) {
      assert.ok(link[2].replace(/<[^>]+>/g, '').trim().length > 0, 'native links have visible names');
      assert.doesNotMatch(link[1], /\b(?:hidden|disabled|aria-current|onclick)\b/);
    }
    assert.deepEqual(embeddedJson(html, 'data-snapshot'), snapshot);
  }
});

test('park section destinations are unique and focusable without hiding their evidence', () => {
  for (const park of parks) {
    const snapshot = snapshots.find((item) => item.park_code === park.code);
    const html = readFileSync(`${output}/parks/${park.slug}/index.html`, 'utf8');
    const targets = ['alert-status', ...(snapshot.records.length ? ['retained-notices'] : []), 'trip-context', 'checklist-title', 'guidance-title', `history-${park.code}`, 'official-checks'];
    const tags = [...html.matchAll(/<(?:section|h2)\b[^>]*>/g)].map(([tag]) => tag);
    for (const id of targets) {
      const matches = tags.filter((tag) => tag.match(/\bid="([^"]*)"/)?.[1] === id);
      assert.equal(matches.length, 1, `${park.code}: exact destination ${id}`);
      assert.match(matches[0], /tabindex="-1"/, `${id}: native fragment can receive keyboard focus`);
      assert.doesNotMatch(matches[0], /\bhidden(?:[\s=>]|$)/);
      const label = matches[0].match(/\baria-labelledby="([^"]*)"/)?.[1];
      if (label) assert.equal(tags.filter((tag) => tag.match(/\bid="([^"]*)"/)?.[1] === label).length, 1, `${id}: associated section heading exists`);
    }
    if (snapshot.records.length) {
      assert.match(tags.find((tag) => tag.includes('id="retained-notices"')), /aria-labelledby="retained-notices-title"/);
    } else assert.doesNotMatch(html, /\bid="retained-notices"/);
  }
});

test('retained-notice filters use the complete public inventory and exact provider categories', () => {
  const normalize = (text) => text.toLowerCase().replace(/\s+/g, ' ').trim();
  for (const park of parks) {
    const snapshot = snapshots.find((item) => item.park_code === park.code);
    const html = readFileSync(`${output}/parks/${park.slug}/index.html`, 'utf8');
    const retained = html.match(/<section\b[^>]*\bdata-retained-notices\b[^>]*>[\s\S]*?<\/section>/)?.[0];
    if (!snapshot.records.length) {
      assert.equal(retained, undefined, `${park.code}: no filters for an empty retained feed`);
      assert.doesNotMatch(html, /data-notice-search/);
      continue;
    }
    assert.ok(retained, `${park.code}: retained notice section is filterable`);
    const articles = [...retained.matchAll(/<article\b([^>]*)>[\s\S]*?<\/article>/g)];
    assert.equal(articles.length, snapshot.records.length);
    for (const [index, record] of snapshot.records.entries()) {
      const attributes = articles[index][1];
      assert.match(attributes, /\bdata-retained-notice\b/);
      assert.equal(decodeHtml(attributes.match(/\bid="([^"]*)"/)[1]), `alert-${park.code}-${record.id}`);
      assert.equal(decodeHtml(attributes.match(/\bdata-notice-text="([^"]*)"/)[1]), normalize(`${record.title} ${record.description}`));
      assert.equal(decodeHtml(attributes.match(/\bdata-notice-category="([^"]*)"/)[1]), record.category);
      assert.doesNotMatch(attributes, /\bhidden(?:[\s=>]|$)/, 'all notices remain readable in static HTML');
    }
    const categorySelect = retained.match(/<select\b[^>]*\bdata-notice-category\b[^>]*>([\s\S]*?)<\/select>/);
    assert.ok(categorySelect, 'category control exists');
    const options = [...categorySelect[1].matchAll(/<option\b[^>]*\bvalue="([^"]*)"/g)].map((match) => decodeHtml(match[1]));
    assert.deepEqual(options, ['', ...new Set(snapshot.records.map((record) => record.category))].sort());
    assert.deepEqual(embeddedJson(html, 'data-snapshot'), snapshot);
  }
});

test('retained-notice filtering has a static fallback, honest empty state and complete-print disclosure', () => {
  for (const park of parks) {
    const snapshot = snapshots.find((item) => item.park_code === park.code);
    if (!snapshot.records.length) continue;
    const html = readFileSync(`${output}/parks/${park.slug}/index.html`, 'utf8');
    const retained = html.match(/<section\b[^>]*\bdata-retained-notices\b[^>]*>[\s\S]*?<\/section>/)?.[0];
    assert.ok(retained, `${park.code}: retained notices keep fallback and disclosure`);
    const controls = retained.match(/<div\b[^>]*\bdata-notice-controls\b[^>]*>/)?.[0];
    assert.ok(controls);
    assert.match(controls, /\bhidden(?:[\s=>]|$)/, 'inactive controls are hidden without JavaScript');
    assert.match(retained, /<label\b[^>]*for="notice-search"[^>]*>Search retained notices<\/label>/);
    assert.match(retained, /<label\b[^>]*for="notice-category"[^>]*>Notice category<\/label>/);
    assert.match(retained, /<button\b[^>]*type="button"[^>]*\bdata-notice-clear\b[^>]*>Clear notice filters<\/button>/);
    const count = retained.match(/<p\b[^>]*\bdata-notice-count\b[^>]*>[\s\S]*?<\/p>/)?.[0];
    assert.ok(count);
    assert.match(count, /role="status"/);
    assert.match(count, /aria-live="polite"/);
    assert.ok(count.includes(`Showing ${snapshot.records.length} of ${snapshot.records.length} retained notices`));
    assert.match(retained, /No retained notices match these filters\./);
    assert.match(retained, /This does not establish that conditions are clear\./);
    assert.match(retained, /<noscript>[\s\S]*Search and category filters require JavaScript\./);
    assert.ok(retained.includes(`All ${snapshot.records.length} retained notices are included in this page copy.`));
    assert.match(retained, /Search and category selections do not limit it\./);
    assert.match(retained, /Area scope is not classified/);
    assert.match(retained, /applicability remains unconfirmed/);
  }
});

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
