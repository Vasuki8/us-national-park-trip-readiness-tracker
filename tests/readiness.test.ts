import test from 'node:test';
import assert from 'node:assert/strict';
import { evaluateEntry, freshness, parkLocalDate, isCalendarDate, describeAlerts } from '../src/lib/readiness.ts';
import type { Rule, Trip } from '../src/lib/readiness.ts';
// Synthetic rules for deterministic tests; never imported by the website.
const now = new Date('2026-09-28T20:00:00Z');
const baseline: Rule = {
  id: 'synthetic-entry', park_code: 'test', areas: ['rest'],
  effective_from: '2026-05-22', effective_to: '2026-10-12',
  start_time: '09:00', end_time: '14:00', requirement: 'timed_entry',
  reviewed_at: '2026-09-28T19:00:00Z', review_status: 'reviewed',
  summary: 'Synthetic test rule', exception_note: 'Check the official exceptions.',
  evidence: { url: 'https://www.nps.gov/test/index.htm', excerpt: 'Synthetic evidence.', content_hash: '0'.repeat(64), hash_scope: 'excerpt', reviewed_at: '2026-09-28T19:00:00Z', source_updated_at: null, method: 'manual_official_page_review' },
};
const trip: Trip = { park_code: 'test', date: '2026-09-29', time: '10:00', area: 'rest', special_case: false };
const run = (changes: Partial<Trip> = {}, rules: Rule[] = [baseline]) => evaluateEntry(rules, { ...trip, ...changes }, now);
test('a missing feed check stays missing', () => assert.equal(freshness(null, 4, now), 'missing'));
test('four-hour boundary is fresh; one millisecond later is stale', () => {
  assert.equal(freshness('2026-09-28T16:00:00Z', 4, now), 'fresh');
  assert.equal(freshness('2026-09-28T15:59:59.999Z', 4, now), 'stale');
});
test('future or malformed check times cannot look fresh', () => {
  for (const value of ['2026-09-29T00:00:00Z', 'not-a-date', '2026-09-28']) assert.equal(freshness(value, 4, now), 'invalid');
});
test('invalid clocks and thresholds fail closed', () => {
  assert.equal(freshness(baseline.reviewed_at, 4, new Date('bad')), 'invalid');
  assert.equal(freshness(baseline.reviewed_at, -1, now), 'invalid');
});
test('calendar dates validate real leap days', () => {
  for (const d of ['2024-02-29', '2026-12-31']) assert.equal(isCalendarDate(d), true);
  for (const d of ['2026-02-29', '2026-02-30', '2026-13-01', '09/28/2026', '']) assert.equal(isCalendarDate(d), false);
});
test('local midnight and daylight-saving dates do not use the browser timezone', () => {
  assert.equal(parkLocalDate(new Date('2026-03-08T07:30:00Z'), 'America/Los_Angeles'), '2026-03-07');
  assert.equal(parkLocalDate(new Date('2026-03-08T08:30:00Z'), 'America/Los_Angeles'), '2026-03-08');
  assert.equal(parkLocalDate(new Date('2026-11-01T08:30:00Z'), 'America/Los_Angeles'), '2026-11-01');
  assert.equal(parkLocalDate(new Date('2026-11-01T09:30:00Z'), 'America/Los_Angeles'), '2026-11-01');
});
test('missing/invalid date needs input', () => {
  for (const date of ['', '2026-02-30']) assert.equal(run({ date }).state, 'needs-input');
});
test('unreviewed parks and another year do not inherit a rule', () => {
  assert.equal(run({ park_code: 'other' }).state, 'not-verified');
  assert.equal(run({ date: '2027-06-01' }).state, 'not-verified');
});
test('effective first and last dates are inclusive', () => {
  for (const date of ['2026-05-22', '2026-10-12']) assert.equal(run({ date }).state, 'review-required');
});
test('outside the reviewed season is unresolved, not an exemption', () => {
  for (const date of ['2026-05-21', '2026-10-13']) assert.equal(run({ date }).state, 'not-verified');
});
test('a rule older than seven days cannot make a current determination', () => {
  assert.equal(run({}, [{ ...baseline, reviewed_at: '2026-09-20T00:00:00Z' }]).state, 'stale');
});
test('a source pending review or in conflict cannot grant an exemption', () => {
  assert.equal(run({}, [{ ...baseline, review_status: 'needs_review' }]).state, 'review-required');
  assert.equal(run({}, [{ ...baseline, review_status: 'conflict' }]).state, 'conflict');
});
test('missing area is not silently treated as the rest of the park', () => assert.equal(run({ area: '' }).state, 'needs-input'));
test('unknown area is not covered', () => assert.equal(run({ area: 'unknown' }).state, 'not-verified'));
test('missing or invalid wall-clock time needs input', () => {
  for (const time of ['', '9:00', '24:00', '12:99']) assert.equal(run({ time }).state, 'needs-input');
});
test('the daily start applies and the exact end is conservatively unresolved', () => {
  assert.equal(run({ time: '09:00' }).state, 'review-required');
  assert.equal(run({ time: '14:00' }).state, 'review-required');
  assert.match(run({ time: '14:00' }).detail, /boundary/);
});
test('before and after the daily window applies only to this specific rule', () => {
  for (const time of ['08:59', '14:01']) assert.equal(run({ time }).state, 'not-required-under-rule');
});
test('different areas can have different rules at the same time', () => {
  const bear = { ...baseline, id: 'synthetic-bear', areas: ['bear-lake'], start_time: '05:00', end_time: '18:00' };
  assert.equal(run({ time: '08:00' }, [baseline, bear]).state, 'not-required-under-rule');
  assert.equal(run({ area: 'bear-lake', time: '08:00' }, [baseline, bear]).state, 'review-required');
});
test('special travel or existing permits require direct review, not guessed exceptions', () => assert.equal(run({ special_case: true }).state, 'review-required'));
test('overlapping conflicting rules cannot silently choose the last record', () => {
  assert.equal(run({}, [baseline, { ...baseline, id: 'conflicting', requirement: 'no_timed_entry' }]).state, 'conflict');
});
test('a reviewed park-wide no-timed-entry rule does not require an irrelevant time', () => {
  const rule: Rule = { ...baseline, areas: ['*'], effective_from: '2026-01-01', effective_to: '2026-12-31', start_time: null, end_time: null, requirement: 'no_timed_entry' };
  assert.equal(run({ time: '', area: '' }, [rule]).state, 'not-required-under-rule');
  assert.match(run({}, [rule]).detail, /fees|permits/);
});
const neverChecked = { collection_status: 'never_checked', last_successful_fetch_at: null, records: [] };
test('uncollected alerts are not displayed as zero current alerts', () => assert.match(describeAlerts(neverChecked, now).title, /not been collected/));
test('successful empty alerts response says only what the checked feed returned', () => {
  const result = describeAlerts({ ...neverChecked, collection_status: 'success', last_successful_fetch_at: '2026-09-28T19:00:00Z' }, now);
  assert.equal(result.title, 'No alerts returned by the checked feed');
  assert.match(result.detail, /not an all-clear/);
});
test('failed and quarantined checks remain degraded even when last-good data is recent', () => {
  for (const collection_status of ['failed', 'quarantined']) assert.equal(describeAlerts({ ...neverChecked, collection_status, last_successful_fetch_at: '2026-09-28T19:00:00Z' }, now).state, 'review-required');
});
test('alerts become stale in the browser without a new publication', () => assert.equal(describeAlerts({ ...neverChecked, collection_status: 'success', last_successful_fetch_at: '2026-09-28T10:00:00Z' }, now).state, 'stale'));
test('impossible calendar timestamps cannot normalize into fresh evidence', () => {
  assert.equal(freshness('2026-02-30T12:00:00Z', 72, new Date('2026-03-03T12:00:00Z')), 'invalid');
  assert.equal(freshness('2026-03-01T24:00:00Z', 72, new Date('2026-03-03T12:00:00Z')), 'invalid');
});
