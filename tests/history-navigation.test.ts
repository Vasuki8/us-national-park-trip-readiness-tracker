import test from 'node:test';
import assert from 'node:assert/strict';
import { retainedNoticeHref, type HistoryNoticeContext } from '../src/lib/history-navigation.ts';

const context = (records: readonly { id: string }[] = [{ id: 'retained' }], noticeHrefPrefix = ''): HistoryNoticeContext => ({
  parkCode: 'yose', records, noticeHrefPrefix,
});

test('history without a paired retained inventory does not invent a notice destination', () => {
  assert.equal(retainedNoticeHref(undefined, 'yose', 'retained'), null);
});

test('an empty retained inventory does not turn historical evidence into a current notice', () => {
  assert.equal(retainedNoticeHref(context([]), 'yose', 'retained'), null);
});

test('a matching record ID in another park cannot establish a retained notice link', () => {
  assert.equal(retainedNoticeHref(context(), 'zion', 'retained'), null);
  assert.equal(retainedNoticeHref({ ...context(), parkCode: 'zion' }, 'yose', 'retained'), null);
});

test('retained membership requires the exact case-sensitive record ID', () => {
  const inventory = context([{ id: 'notice-A' }, { id: 'notice-A-extra' }]);
  assert.equal(retainedNoticeHref(inventory, 'yose', 'notice-A'), '#alert-yose-notice-A');
  for (const absent of ['notice', 'notice-a', 'Notice-A', 'notice-A ', 'removed']) {
    assert.equal(retainedNoticeHref(inventory, 'yose', absent), null, absent);
  }
});

test('duplicate matches refuse an ambiguous retained notice destination', () => {
  assert.equal(retainedNoticeHref(context([{ id: 'retained' }, { id: 'retained' }]), 'yose', 'retained'), null);
});

test('an empty prefix produces the existing park-local alert fragment', () => {
  assert.equal(retainedNoticeHref(context(), 'yose', 'retained'), '#alert-yose-retained');
});

test('overview destinations preserve the supplied domain-root or project park route', () => {
  for (const prefix of ['/parks/yosemite/', '/us-national-park-trip-readiness-tracker/parks/yosemite/']) {
    assert.equal(retainedNoticeHref(context(undefined, prefix), 'yose', 'retained'), `${prefix}#alert-yose-retained`);
  }
  assert.equal(retainedNoticeHref({ ...context(undefined, '/parks/yosemite/'), parkHref: '/parks/' }, 'yose', 'retained'),
    '/parks/yosemite/#alert-yose-retained');
});

test('record ID punctuation and literal percent encoding stay within one encoded alert fragment', () => {
  const ids = ['same source: /?#&é+%2F', 'literal%ZZ', '#entry-rule-other'];
  const inventory = context(ids.map(id => ({ id })), '/parks/yosemite/');
  const expected = [
    '/parks/yosemite/#alert-yose-same%20source%3A%20%2F%3F%23%26%C3%A9%2B%252F',
    '/parks/yosemite/#alert-yose-literal%25ZZ',
    '/parks/yosemite/#alert-yose-%23entry-rule-other',
  ];
  ids.forEach((id, index) => assert.equal(retainedNoticeHref(inventory, 'yose', id), expected[index]));
});

test('a past removal can link after reappearance while a disappeared past addition cannot', () => {
  const retained = [{ id: 'reappeared', title: 'Later retained wording', content_hash: 'b'.repeat(64) }];
  const inventory = context(retained);
  const comparisons = [
    { kind: 'removed', record_id: 'reappeared', title: 'Earlier wording', after_hash: null },
    { kind: 'added', record_id: 'disappeared', title: 'Earlier wording', after_hash: 'a'.repeat(64) },
    { kind: 'edited', record_id: 'reappeared', title: 'Another earlier wording', after_hash: 'c'.repeat(64) },
  ];
  assert.deepEqual(comparisons.map(change => retainedNoticeHref(inventory, 'yose', change.record_id)),
    ['#alert-yose-reappeared', null, '#alert-yose-reappeared']);
});

test('retained-link lookup preserves inventory order, evidence and original collection clocks', () => {
  const records = Object.freeze([
    Object.freeze({ id: 'z', title: 'Synthetic retained notice', url: null, content_hash: 'a'.repeat(64),
      observed_first_at: '2026-09-28T10:00:00Z', observed_changed_at: '2026-09-28T12:00:00Z' }),
    Object.freeze({ id: 'a', title: 'Another synthetic notice', url: 'https://example.org/notice/', content_hash: 'b'.repeat(64),
      observed_first_at: '2026-09-28T10:00:00Z', observed_changed_at: '2026-09-28T10:00:00Z' }),
  ]);
  const inventory = Object.freeze({
    parkCode: 'yose', records, noticeHrefPrefix: '/parks/yosemite/', parkHref: '/parks/yosemite/',
    metadata: Object.freeze({ collection_status: 'failed', coverage_status: 'incomplete',
      last_checked_at: '2026-09-28T14:00:00Z', last_successful_fetch_at: '2026-09-28T12:00:00Z',
      source_updated_at: null, published_at: null }),
  });
  const before = structuredClone(inventory);
  assert.equal(retainedNoticeHref(inventory, 'yose', 'a'), '/parks/yosemite/#alert-yose-a');
  assert.equal(retainedNoticeHref(inventory, 'yose', 'missing'), null);
  assert.equal(retainedNoticeHref(inventory, 'zion', 'a'), null);
  assert.deepEqual(inventory, before);
});
