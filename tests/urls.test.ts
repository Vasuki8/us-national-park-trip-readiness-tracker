import test from 'node:test';
import assert from 'node:assert/strict';
import { siteUrl } from '../src/lib/urls.ts';

test('internal paths stay within root or project hosting', () => {
  for (const base of ['/', '/us-national-park-trip-readiness-tracker/']) {
    assert.equal(siteUrl('/', base), base);
    assert.equal(siteUrl('/parks/yosemite/', base), `${base}parks/yosemite/`);
    assert.equal(siteUrl('/parks/?state=Utah#directory-title', base), `${base}parks/?state=Utah#directory-title`);
  }
});

test('external and page-local destinations retain their URLs', () => {
  for (const url of ['https://www.nps.gov/yose/', '#main', 'mailto:example@example.org', '//www.nps.gov/']) {
    assert.equal(siteUrl(url, '/us-national-park-trip-readiness-tracker/'), url);
  }
});
