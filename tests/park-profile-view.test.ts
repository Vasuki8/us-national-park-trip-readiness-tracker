import test from 'node:test';
import assert from 'node:assert/strict';
import { describeProfile, type ProfileClock } from '../src/lib/park-profile.ts';

const checked = '2026-10-01T10:00:00Z';
const successful: ProfileClock = { collection_status: 'success', last_checked_at: checked, last_successful_fetch_at: checked };

for (const [clock, state] of [
  ['2026-10-01T10:00:00.123Z', 'invalid'],
  ['2026-10-01T10:00:00.124Z', 'fresh'],
  ['2026-10-08T10:00:00.123Z', 'fresh'],
  ['2026-10-08T10:00:00.124Z', 'stale'],
] as const) test(`microsecond source clocks remain ${state} at ${clock}`, () => {
  const source = '2026-10-01T10:00:00.123456Z';
  assert.equal(describeProfile({ ...successful, last_checked_at: source, last_successful_fetch_at: source }, new Date(clock)).state, state);
});

for (const [clock, state] of [
  ['2026-10-01T10:00:00Z', 'fresh'],
  ['2026-10-08T09:59:59.999Z', 'fresh'],
  ['2026-10-08T10:00:00Z', 'stale'],
  ['2026-10-08T10:00:00.001Z', 'stale'],
] as const) test(`successful park text is ${state} at ${clock}`, () => {
  assert.equal(describeProfile(successful, new Date(clock)).state, state);
});

for (const status of ['failed', 'quarantined'] as const) test(`${status} attempts never renew retained profile freshness`, () => {
  const input = { ...successful, collection_status: status, last_checked_at: '2026-10-09T10:00:00Z' };
  const before = structuredClone(input);
  const result = describeProfile(input, new Date('2026-10-09T10:00:01Z'));
  assert.equal(result.state, status);
  assert.match(result.detail, /Retained text/);
  assert.deepEqual(input, before);
});

test('a missing profile cannot gain a check time or a current label', () => {
  assert.equal(describeProfile(null, new Date('2026-10-01T10:00:00Z')).state, 'unavailable');
});

for (const [name, input, now] of [
  ['future success', successful, new Date('2026-10-01T09:59:59Z')],
  ['future attempt', { ...successful, collection_status: 'failed', last_checked_at: '2026-10-02T10:00:00Z' }, new Date('2026-10-01T10:00:01Z')],
  ['rewound attempt', { ...successful, last_checked_at: '2026-09-30T10:00:00Z' }, new Date('2026-10-01T10:00:01Z')],
  ['impossible date', { ...successful, last_checked_at: '2026-02-30T10:00:00Z' }, new Date('2026-10-01T10:00:01Z')],
  ['invalid current clock', successful, new Date('invalid')],
] as const) test(`${name} cannot establish current profile text`, () => {
  assert.equal(describeProfile(input as ProfileClock, now).state, 'invalid');
});
