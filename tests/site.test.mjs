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
const profiles = JSON.parse(readFileSync(new URL('../data/park-profiles.json', import.meta.url), 'utf8')).profiles;
const activities = JSON.parse(readFileSync(new URL('../data/park-activities.json', import.meta.url), 'utf8')).inventories;
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

test('park overviews retain approved introductions and category-only context in native HTML', () => {
  for (const park of parks) {
    const snapshot = profiles.find(item => item.park_code === park.code);
    const html = readFileSync(`${output}/parks/${park.slug}/index.html`, 'utf8');
    const overview = html.match(/<section\b[^>]*id="overview"[^>]*>[\s\S]*?<\/section>/)?.[0];
    assert.ok(overview, `${park.code}: an overview exists without JavaScript`);
    const text = decodeHtml(overview);
    if (snapshot.profile.description?.trim()) assert.ok(text.includes(snapshot.profile.description));
    else assert.ok(text.includes('The stored official profile has no introduction text.'));
    assert.ok(text.includes(`href="${snapshot.profile.url}"`));
    assert.match(overview, /<details\b[^>]*data-profile-categories/);
    assert.ok(text.includes('Categories do not establish individual activities, seasonal availability or access.'));
    const categories = [...overview.matchAll(/<li\b[^>]*data-profile-category[^>]*>([\s\S]*?)<\/li>/g)].map(match => decodeHtml(match[1]));
    assert.deepEqual(categories, snapshot.profile.activity_categories.map(category => category.name));
  }
});

test('when-to-visit context preserves original profile clocks and seasonal limitations', () => {
  for (const park of parks) {
    const snapshot = profiles.find(item => item.park_code === park.code);
    const html = readFileSync(`${output}/parks/${park.slug}/index.html`, 'utf8');
    const seasonal = html.match(/<section\b[^>]*id="when-to-visit"[^>]*>[\s\S]*?<\/section>/)?.[0];
    assert.ok(seasonal, `${park.code}: seasonal context exists without JavaScript`);
    assert.ok(decodeHtml(seasonal).includes(snapshot.profile.seasonal_weather.text));
    assert.ok(seasonal.includes('Seasonal context, not a forecast for your travel dates.'));
    for (const id of ['overview', 'when-to-visit']) {
      const section = html.match(new RegExp(`<section\\b[^>]*id="${id}"[^>]*>[\\s\\S]*?<\\/section>`))[0];
      assert.deepEqual(embeddedJson(section, 'data-profile-clock'), {
        collection_status: snapshot.collection_status,
        last_checked_at: snapshot.last_checked_at,
        last_successful_fetch_at: snapshot.last_successful_fetch_at,
      });
      assert.ok(section.includes(`datetime="${snapshot.last_successful_fetch_at}"`));
      assert.ok(section.includes('Source issue/update time: Not supplied.'));
      assert.ok(section.includes(snapshot.source_url.replaceAll('&', '&amp;')));
      assert.ok(section.includes('Freshness labels reflect the build without JavaScript.'));
    }
  }
});

test('activity inventories publish only exact approved links and categories with original three-field clocks', () => {
  for (const park of parks) {
    const inventory = activities.find(item => item.park_code === park.code);
    const html = readFileSync(`${output}/parks/${park.slug}/index.html`, 'utf8');
    const section = html.match(/<section\b[^>]*\bid="things-to-do"[^>]*>[\s\S]*?<\/section>/)?.[0];
    assert.ok(section, `${park.code}: native activity section exists`);
    const disclosure = section.match(/<details\b[^>]*\bdata-activity-inventory\b[^>]*>/)?.[0];
    assert.ok(disclosure);
    assert.doesNotMatch(disclosure, /\bopen(?:[\s=>]|$)/, 'large inventories start collapsed');
    const links = [...section.matchAll(/<a\b([^>]*\bdata-activity-link\b[^>]*)>([\s\S]*?)<\/a>/g)];
    assert.equal(links.length, inventory.records.length);
    for (const [index, record] of inventory.records.entries()) {
      assert.equal(decodeHtml(links[index][1].match(/\bhref="([^"]*)"/)[1]), record.url);
      assert.equal(decodeHtml(links[index][2].replace(/<[^>]+>/g, '').trim()), record.title);
    }
    const categories = [...section.matchAll(/<[^>]+\bdata-activity-category\b[^>]*>([^<]*)<\//g)].map(match => decodeHtml(match[1]));
    assert.deepEqual(categories, inventory.records.flatMap(record => record.activity_categories?.map(item => item.name) ?? []));
    assert.deepEqual(embeddedJson(section, 'data-activity-clock'), {
      collection_status: inventory.collection_status, last_checked_at: inventory.last_checked_at,
      last_successful_fetch_at: inventory.last_successful_fetch_at,
    });
    assert.match(section, /Availability is not verified/);
    assert.match(section, /relationship to this park is unconfirmed/);
    assert.ok(section.includes(inventory.last_successful_fetch_at));
    assert.doesNotMatch(section, /source_content_hash|view_hash|source_records|projection_hash/);
  }
});

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
    const expected = ['#overview', '#when-to-visit', '#things-to-do', '#alert-status', ...(snapshot.records.length ? ['#retained-notices'] : []), '#trip-context', '#checklist-title', '#guidance-title', `#history-${park.code}`, '#official-checks'];
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
    const targets = ['overview', 'when-to-visit', 'things-to-do', 'alert-status', ...(snapshot.records.length ? ['retained-notices'] : []), 'trip-context', 'checklist-title', 'guidance-title', `history-${park.code}`, 'official-checks'];
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

test('exact dated and undated guidance destinations accept native focus and retain their source evidence', () => {
  const catalog = embeddedJson(readFileSync(`${output}/corrections/index.html`, 'utf8'), 'data-correction-sources');
  const guidance = [...rules.map(record => ({kind: 'rule', record})), ...notes.map(record => ({kind: 'note', record}))];
  assert.ok(guidance.length > 0, 'the public inventory supplies guidance destinations');
  for (const {kind, record} of guidance) {
    const park = parks.find(item => item.code === record.park_code);
    const html = readFileSync(`${output}/parks/${park.slug}/index.html`, 'utf8');
    const id = `entry-${kind}-${record.id}`;
    const matches = [...html.matchAll(/<article\b([^>]*)>([\s\S]*?)<\/article>/g)]
      .filter(match => decodeHtml(match[1].match(/\bid="([^"]*)"/)?.[1] ?? '') === id);
    assert.equal(matches.length, 1, `${id}: native destination identifies exactly one article`);
    const [, attributes, contents] = matches[0];
    assert.match(attributes, /\btabindex="-1"/, `${id}: focus the source without adding a Tab stop`);
    assert.doesNotMatch(attributes, /\b(?:hidden|inert|aria-hidden)\b/, `${id}: source stays available`);
    const text = decodeHtml(contents);
    assert.ok(text.includes(record.summary), `${id}: original guidance wording`);
    assert.ok(text.includes(record.evidence.excerpt), `${id}: original supporting excerpt`);
    assert.ok(text.includes(record.evidence.content_hash), `${id}: original evidence hash`);
    assert.ok(text.includes(`datetime="${record.reviewed_at}"`), `${id}: original review clock`);
    assert.ok(text.includes(`href="${record.evidence.url}"`), `${id}: original official source`);
    if (kind === 'note') assert.ok(text.includes(record.limitation), `${id}: undated limitation stays explicit`);
    assert.match(text, /<details><summary>View supporting text and evidence<\/summary>/);
    const source = catalog.filter(item => item.key === `${kind}:${park.code}:${record.id}`);
    assert.equal(source.length, 1, `${id}: unique correction identity`);
    assert.equal(source[0].returnHref, `${base}parks/${park.slug}/#${encodeURIComponent(id)}`);
  }
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
test('each overview history returns to its own focusable public readiness page under the hosting base', () => {
  const overview = readFileSync(`${output}/changes/index.html`, 'utf8');
  for (const park of parks) {
    const panel = overview.match(new RegExp(`<section[^>]*id="history-${park.code}"[^>]*>[\\s\\S]*?</section>`))?.[0];
    assert.ok(panel, `${park.code}: overview history panel exists`);
    const links = [...panel.matchAll(/<a\b[^>]*href="([^"]*)"[^>]*>Open this park’s trip readiness<\/a>/g)];
    assert.equal(links.length, 1, `${park.code}: one native readiness return link`);
    assert.equal(decodeHtml(links[0][1]), `${base}parks/${park.slug}/#trip-context`);
    const parkHtml = readFileSync(`${output}/parks/${park.slug}/index.html`, 'utf8');
    assert.match(parkHtml, /<section\b[^>]*id="trip-context"[^>]*tabindex="-1"/);
    assert.doesNotMatch(parkHtml, />Open this park’s trip readiness<\/a>/, 'park histories do not repeat an overview return link');
  }
});

test('each retained notice is a unique native keyboard destination with its original public identity', () => {
  for (const park of parks) {
    const snapshot = snapshots.find((item) => item.park_code === park.code);
    const html = readFileSync(`${output}/parks/${park.slug}/index.html`, 'utf8');
    const targets = [...html.matchAll(/<article\b[^>]*\bdata-retained-notice\b[^>]*>/g)].map((match) => match[0]);
    assert.equal(targets.length, snapshot.records.length);
    for (const record of snapshot.records) {
      const matching = targets.filter((tag) => decodeHtml(tag.match(/\bid="([^"]*)"/)[1]) === `alert-${park.code}-${record.id}`);
      assert.equal(matching.length, 1, `${park.code}: unique exact notice ${record.id}`);
      assert.match(matching[0], /\btabindex="-1"/, 'native notice navigation moves keyboard focus to the evidence');
    }
    assert.deepEqual(embeddedJson(html, 'data-snapshot'), snapshot);
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
