import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
const routes = ['', 'parks', 'parks/yosemite', 'parks/rocky-mountain', 'parks/yellowstone', 'parks/zion', 'parks/grand-canyon', 'how-it-works', 'sources', 'changes', 'about', 'privacy', 'terms', 'corrections'];
const output = process.env.SITE_TEST_OUTPUT || 'dist';
const base = process.env.SITE_TEST_BASE || '/';
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
test('all park pages show uncollected alerts and official sources', () => {
  for (const slug of ['yosemite', 'rocky-mountain', 'yellowstone', 'zion', 'grand-canyon']) {
    const html = readFileSync(`${output}/parks/${slug}/index.html`, 'utf8');
    assert.ok(html.includes('Conditions have not been collected'));
    assert.ok(html.includes('https://www.nps.gov/'));
    assert.ok(html.includes('not verify bookings'));
  }
});
test('internal page links and bundled assets stay under the base and resolve', () => {
  for (const route of routes) {
    const html = readFileSync(`${output}/${route ? route + '/' : ''}index.html`, 'utf8');
    for (const [, url] of html.matchAll(/(?:href|src)="(\/[^"#?]*)"/g)) {
      assert.ok(url.startsWith(base), `${route} escapes ${base}: ${url}`);
      const local = url.slice(base.length);
      assert.ok(existsSync(join(output, local, url.endsWith('/') ? 'index.html' : '')), `${route} -> ${url}`);
    }
  }
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
