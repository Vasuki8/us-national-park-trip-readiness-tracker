import test from 'node:test';
import assert from 'node:assert/strict';
import { evidenceReferenceTime, guidanceScenarioTime } from './pilot-clock.ts';
import { describeAlerts, freshness } from '../src/lib/readiness.ts';
import { describeHistory } from '../src/lib/history.ts';
import { summarizeCoverage } from '../src/lib/source-coverage.ts';

const reviewed = '2026-09-01T12:00:00Z';
const refreshed = '2026-09-09T12:00:00Z';
const attempted = '2026-09-10T12:00:00Z';
const review = { park_code: 'yose', review_status: 'reviewed', reviewed_at: reviewed };
const snapshot = { park_code: 'yose', collection_status: 'success', coverage_status: 'checked_feed_only',
  last_checked_at: refreshed, last_successful_fetch_at: refreshed, records: [] };

test('an alert-only refresh after seven days does not refresh the unchanged guidance', () => {
  const input = { parks: [{ code: 'yose' }], rules: [review], notes: [], snapshots: [snapshot] };
  const before = structuredClone(input);
  const now = new Date(evidenceReferenceTime(input.rules, input.snapshots));
  assert.equal(now.toISOString(), '2026-09-09T12:00:01.000Z');
  const coverage = summarizeCoverage(input, now);
  assert.equal(coverage.recentAlertParks, 1);
  assert.equal(coverage.reviewWithinWindowParks, 0);
  assert.equal(coverage.rows[0].entryLabel, 'Source review needs refreshing');
  assert.equal(describeAlerts(snapshot, now).title, 'No alerts returned by the checked feed');
  assert.equal(describeHistory(snapshot, now).title, 'Recent feed check; coverage remains limited');
  assert.deepEqual(input, before);
});

test('a nullable success clock retains its later failed attempt without inventing a success', () => {
  const failed = { ...snapshot, collection_status: 'failed', last_checked_at: attempted, last_successful_fetch_at: null };
  const neverChecked = { last_checked_at: null, last_successful_fetch_at: null };
  const now = new Date(evidenceReferenceTime([review], [failed, neverChecked]));
  assert.equal(now.toISOString(), '2026-09-10T12:00:01.000Z');
  assert.equal(describeAlerts(failed, now).title, 'The latest condition check was not successful');
  assert.equal(describeHistory(failed, now).title, 'The latest check was not successful');
  assert.equal(failed.last_successful_fetch_at, null);
});

test('a later attempted check sets the reference while its retained success stays stale', () => {
  const failed = { ...snapshot, collection_status: 'failed', last_checked_at: attempted };
  const now = new Date(evidenceReferenceTime([review], [failed]));
  assert.equal(now.toISOString(), '2026-09-10T12:00:01.000Z');
  assert.equal(freshness(failed.last_successful_fetch_at, 4, now), 'stale');
  assert.equal(failed.last_successful_fetch_at, refreshed);
});

test('a reference after a partial refresh preserves independently stale successful feeds', () => {
  const older = { ...snapshot, park_code: 'romo', last_checked_at: reviewed, last_successful_fetch_at: reviewed };
  const now = new Date(evidenceReferenceTime([review], [snapshot, older]));
  assert.equal(describeAlerts(older, now).title, 'The condition snapshot needs a fresh check');
  assert.equal(describeHistory(older, now).title, 'History needs a fresh check');
  assert.equal(describeAlerts(snapshot, now).title, 'No alerts returned by the checked feed');
});

test('annual guidance scenarios use their review clocks independently of a later alert refresh', () => {
  const now = new Date(guidanceScenarioTime([review]));
  assert.equal(now.toISOString(), '2026-09-01T12:00:01.000Z');
  assert.equal(freshness(review.reviewed_at, 168, now), 'fresh');
  assert.equal(freshness(review.reviewed_at, 168, new Date(now.getTime() + 8 * 24 * 3_600_000)), 'stale');
});

test('missing or invalid evidence cannot manufacture a reference clock', () => {
  assert.throws(() => evidenceReferenceTime([], [{ last_checked_at: null, last_successful_fetch_at: null }]));
  assert.throws(() => evidenceReferenceTime([{ reviewed_at: '2026-02-30T12:00:00Z' }], []));
  assert.throws(() => evidenceReferenceTime([review], [{ last_checked_at: 'invalid', last_successful_fetch_at: null }]));
});

test('a deliberately fresh guidance scenario refuses reviews with no shared freshness window', () => {
  assert.throws(() => guidanceScenarioTime([review, { reviewed_at: refreshed }]));
});
