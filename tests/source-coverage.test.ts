import test from 'node:test';
import assert from 'node:assert/strict';
const mod = await import('../src/lib/source-coverage.ts').catch(() => ({})) as any;
const now = new Date('2026-09-28T21:00:00Z');
const review = (code: string, overrides = {}) => ({ park_code: code, review_status: 'reviewed', reviewed_at: now.toISOString(), ...overrides });
const snapshot = (code: string, overrides = {}) => ({ park_code: code, collection_status: 'success', coverage_status: 'checked_feed_only', last_successful_fetch_at: now.toISOString(), ...overrides });
function summarize(input: any, clock = now) {
  assert.equal(typeof mod.summarizeCoverage, 'function', 'coverage reducer is implemented');
  return mod.summarizeCoverage(input, clock);
}
const input = (changes = {}) => ({ parks: [{ code: 'yose' }, { code: 'yell' }], rules: [], notes: [], snapshots: [], ...changes });
test('missing data yields explicit missing labels and zero checks', () => {
  const result = summarize(input());
  assert.equal(result.parkCount, 2); assert.equal(result.storedReviewParks, 0); assert.equal(result.recentAlertParks, 0);
  assert.equal(result.rows[0].entryLabel, 'Entry review pending'); assert.equal(result.rows[0].alertLabel, 'Alerts not collected');
});
test('undated notes increase reviewed-source coverage, never dated-rule coverage', () => {
  const result = summarize(input({ rules: [review('yose')], notes: [review('yell')] }));
  assert.equal(result.storedReviewParks, 2); assert.equal(result.datedRuleParks, 1); assert.equal(result.reviewWithinWindowParks, 2);
  assert.equal(result.rows[1].entryLabel, 'Undated source review');
});
test('stale and future source reviews never count as current reviews', () => {
  const result = summarize(input({ rules: [review('yose', { reviewed_at: '2026-09-21T20:59:59Z' })], notes: [review('yell', { reviewed_at: '2026-09-29T00:00:00Z' })] }));
  assert.equal(result.reviewWithinWindowParks, 0); assert.equal(result.storedReviewParks, 2);
  assert.equal(result.rows[0].entryLabel, 'Source review needs refreshing');
});
test('pending or conflicting review defeats otherwise fresh source evidence', () => {
  const result = summarize(input({ rules: [review('yose')], notes: [review('yose', { review_status: 'conflict' }), review('yell', { review_status: 'needs_review' })] }));
  assert.equal(result.reviewWithinWindowParks, 0); assert.equal(result.rows[0].entryLabel, 'Conflicting source reviews');
  assert.equal(result.rows[1].entryLabel, 'Source review pending');
});
test('a recent failed or incomplete check never counts as a fresh successful feed', () => {
  const result = summarize(input({ snapshots: [snapshot('yose', { collection_status: 'failed' }), snapshot('yell', { coverage_status: 'incomplete' })] }));
  assert.equal(result.recentAlertParks, 0); assert.equal(result.rows[0].alertLabel, 'Latest alert check failed');
});
test('quarantine and unrecognized statuses remain visibly unverified', () => {
  const result = summarize(input({ snapshots: [snapshot('yose', { collection_status: 'quarantined' }), snapshot('yell', { collection_status: 'invented' })] }));
  assert.equal(result.recentAlertParks, 0); assert.equal(result.rows[0].alertLabel, 'Alert feed needs review');
  assert.equal(result.rows[1].alertLabel, 'Alert state unverified');
});
test('freshness expires on the browser clock without modifying source metadata', () => {
  const value = input({ rules: [review('yose')], snapshots: [snapshot('yose')] });
  const before = JSON.stringify(value);
  assert.equal(summarize(value).recentAlertParks, 1);
  assert.equal(summarize(value, new Date('2026-09-29T01:00:00Z')).recentAlertParks, 1);
  assert.equal(summarize(value, new Date('2026-09-29T01:00:00.001Z')).recentAlertParks, 0);
  assert.equal(summarize(value, new Date('2026-10-05T21:00:00.001Z')).reviewWithinWindowParks, 0);
  assert.equal(JSON.stringify(value), before);
});
test('duplicate snapshots are unverified and orphan records cannot inflate counts', () => {
  const result = summarize(input({ rules: [review('yose'), review('else')], snapshots: [snapshot('yose'), snapshot('yose'), snapshot('else')] }));
  assert.equal(result.storedReviewParks, 1); assert.equal(result.recentAlertParks, 0);
  assert.equal(result.rows[0].alertLabel, 'Alert state unverified');
});
test('invalid clocks and check times cannot become fresh', () => {
  const value = input({ rules: [review('yose')], snapshots: [snapshot('yose', { last_successful_fetch_at: null })] });
  assert.equal(summarize(value, new Date('invalid')).reviewWithinWindowParks, 0);
  assert.equal(summarize(value).recentAlertParks, 0);
});
