import test from 'node:test';
import assert from 'node:assert/strict';
import type { ActivityClock } from '../src/lib/park-activities.ts';

const feature = await import('../src/lib/park-activities.ts').catch(error => {
  if (error.code === 'ERR_MODULE_NOT_FOUND') return null;
  throw error;
});
const describe = (clock: ActivityClock | null, now: Date) => {
  assert.ok(feature, 'Activity freshness must describe the stored source clock.');
  return feature.describeActivities(clock, now);
};
const checked = '2026-10-04T05:49:46.709637Z';
const successful: ActivityClock = { collection_status: 'success', last_checked_at: checked, last_successful_fetch_at: checked };

for (const [time, state] of [
  ['2026-10-04T05:49:46.709Z', 'invalid'],
  ['2026-10-04T05:49:46.710Z', 'fresh'],
  ['2026-10-11T05:49:46.709Z', 'fresh'],
  ['2026-10-11T05:49:46.710Z', 'stale'],
] as const) test(`original microsecond activity check is ${state} at ${time}`, () => {
  assert.equal(describe(successful, new Date(time)).state, state);
});

for (const [time, state] of [
  ['2026-10-04T10:00:00Z', 'fresh'],
  ['2026-10-11T09:59:59.999Z', 'fresh'],
  ['2026-10-11T10:00:00Z', 'stale'],
  ['2026-10-11T10:00:00.001Z', 'stale'],
] as const) test(`seven-day activity age is ${state} at ${time}`, () => {
  const clock = '2026-10-04T10:00:00Z';
  assert.equal(describe({ ...successful, last_checked_at: clock, last_successful_fetch_at: clock }, new Date(time)).state, state);
});

test('a recent activity feed check does not establish current availability or access', () => {
  const result = describe(successful, new Date('2026-10-04T05:49:47Z'));
  assert.equal(result.state, 'fresh');
  assert.match(result.detail, /feed only/i);
  assert.match(result.detail, /does not confirm.*availability/i);
});

for (const status of ['failed', 'quarantined'] as const) test(`${status} activity refresh retains its last-good age and input`, () => {
  const clock = { ...successful, collection_status: status, last_checked_at: '2026-10-12T10:00:00Z' };
  const before = structuredClone(clock);
  const result = describe(clock, new Date('2026-10-12T10:00:01Z'));
  assert.equal(result.state, status);
  assert.match(result.detail, /Retained listings/);
  assert.match(result.detail, /last successful check/);
  assert.deepEqual(clock, before);
});

test('an absent activity catalog cannot acquire a fresh check label', () => {
  const result = describe(null, new Date('2026-10-04T10:00:00Z'));
  assert.equal(result.state, 'unavailable');
  assert.doesNotMatch(result.title, /Within/);
});

for (const [name, clock, now] of [
  ['future attempt', { ...successful, collection_status: 'failed', last_checked_at: '2026-10-05T10:00:00Z' }, new Date('2026-10-04T10:00:00Z')],
  ['reversed attempt', { ...successful, last_checked_at: '2026-10-03T10:00:00Z' }, new Date('2026-10-04T10:00:00Z')],
  ['impossible date', { ...successful, last_checked_at: '2026-02-30T10:00:00Z' }, new Date('2026-10-04T10:00:00Z')],
  ['absent successful clock', { ...successful, last_successful_fetch_at: null }, new Date('2026-10-04T10:00:00Z')],
  ['unknown collection state', { ...successful, collection_status: 'never_checked' }, new Date('2026-10-04T10:00:00Z')],
  ['invalid current clock', successful, new Date('invalid')],
  ['too many fractional digits', { ...successful, last_checked_at: '2026-10-04T05:49:46.7096371Z' }, new Date('2026-10-04T10:00:00Z')],
] as const) test(`${name} cannot establish current activity evidence`, () => {
  assert.equal(describe(clock as ActivityClock, now).state, 'invalid');
});

test('equivalent offset clocks retain microsecond comparisons', () => {
  const offset = '2026-10-04T01:49:46.709637-04:00';
  const clock = { ...successful, last_checked_at: offset, last_successful_fetch_at: offset };
  assert.equal(describe(clock, new Date('2026-10-11T05:49:46.709Z')).state, 'fresh');
  assert.equal(describe(clock, new Date('2026-10-11T05:49:46.710Z')).state, 'stale');
});
