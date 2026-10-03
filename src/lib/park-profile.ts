import type { ProfileSnapshot } from '../../scripts/validate-park-profiles';
import { freshness } from './readiness.ts';

export type ProfileClock = Pick<ProfileSnapshot, 'collection_status' | 'last_checked_at' | 'last_successful_fetch_at'>;
export type ProfileState = 'fresh' | 'stale' | 'failed' | 'quarantined' | 'unavailable' | 'invalid';

export function describeProfile(clock: ProfileClock | null, now: Date): { state: ProfileState; title: string; detail: string } {
  if (clock === null) return { state: 'unavailable', title: 'Park profile not available', detail: 'Use the official park information.' };
  const invalid = { state: 'invalid' as const, title: 'Profile check time cannot be confirmed', detail: 'Use the official park information; these check times do not establish current text.' };
  if (!clock || typeof clock.last_checked_at !== 'string' || typeof clock.last_successful_fetch_at !== 'string'
    || !['success', 'failed', 'quarantined'].includes(clock.collection_status)
    || !Number.isFinite(now.getTime())
    || [clock.last_checked_at, clock.last_successful_fetch_at].some(value => freshness(value, 168, now) === 'invalid')) return invalid;
  // Preserve the source's microsecond boundary while browser clocks use milliseconds.
  const microseconds = (value: string) => BigInt(Date.parse(value)) * 1000n
    + BigInt((value.match(/\.(\d+)(?:Z|[+-])/)?.[1] ?? '').padEnd(6, '0').slice(3, 6));
  const attempted = microseconds(clock.last_checked_at), successful = microseconds(clock.last_successful_fetch_at);
  const current = BigInt(now.getTime()) * 1000n;
  if (successful > attempted || attempted > current) return invalid;
  if (clock.collection_status === 'failed') return { state: 'failed', title: 'Park profile refresh failed', detail: 'Retained text is dated by its last successful check. Confirm it with NPS.' };
  if (clock.collection_status === 'quarantined') return { state: 'quarantined', title: 'Park profile refresh needs review', detail: 'Retained text is dated by its last successful check. Confirm it with NPS.' };
  if (current - successful >= 168n * 3_600_000_000n) return { state: 'stale', title: 'Park profile needs a fresh check', detail: 'Stored park information may have changed. Check the official sources before planning.' };
  return { state: 'fresh', title: 'Within the seven-day profile window', detail: 'This check covers park text only; it does not confirm weather, access or activity availability.' };
}
