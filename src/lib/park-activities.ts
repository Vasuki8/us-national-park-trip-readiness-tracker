import type { CatalogActivityInventory } from '../../scripts/validate-park-activities';
import { isCalendarDate } from './readiness.ts';

export type ActivityClock = Pick<CatalogActivityInventory, 'collection_status' | 'last_checked_at' | 'last_successful_fetch_at'>;
export type ActivityState = 'fresh' | 'stale' | 'failed' | 'quarantined' | 'unavailable' | 'invalid';

function sourceMicroseconds(value: unknown): bigint | null {
  if (typeof value !== 'string') return null;
  const match = /^(\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d)(?:\.(\d{1,6}))?(Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.exec(value);
  if (!match || value.startsWith('0000-') || !isCalendarDate(value.slice(0, 10))) return null;
  const base = Date.parse(match[1] + match[3]);
  if (!Number.isFinite(base) || new Date(base).getUTCFullYear() < 1 || new Date(base).getUTCFullYear() > 9999) return null;
  // Parse the whole-second instant separately; Date.parse otherwise discards microseconds.
  return BigInt(base) * 1000n + BigInt((match[2] ?? '').padEnd(6, '0'));
}

export function describeActivities(clock: ActivityClock | null, now: Date): { state: ActivityState; title: string; detail: string } {
  if (clock === null) return { state: 'unavailable', title: 'Activity catalog not available', detail: 'Use the official park information to explore activities.' };
  const invalid = { state: 'invalid' as const, title: 'Activity check time cannot be confirmed', detail: 'Use official park information; these check times do not establish current listings or availability.' };
  if (!clock || !['success', 'failed', 'quarantined'].includes(clock.collection_status) || !Number.isFinite(now.getTime())) return invalid;
  const attempted = sourceMicroseconds(clock.last_checked_at), successful = sourceMicroseconds(clock.last_successful_fetch_at);
  const current = BigInt(now.getTime()) * 1000n;
  if (attempted === null || successful === null || successful > attempted || attempted > current) return invalid;
  if (clock.collection_status === 'failed') return { state: 'failed', title: 'Activity catalog refresh failed', detail: 'Retained listings are dated by their last successful check. Confirm current availability and requirements with NPS.' };
  if (clock.collection_status === 'quarantined') return { state: 'quarantined', title: 'Activity catalog refresh needs review', detail: 'Retained listings are dated by their last successful check. Confirm current availability and requirements with NPS.' };
  if (current - successful >= 168n * 3_600_000_000n) return { state: 'stale', title: 'Activity catalog needs a fresh check', detail: 'Stored activity listings may have changed. Check NPS for current availability and requirements.' };
  return { state: 'fresh', title: 'Within the seven-day activity window', detail: 'This check covers the activity feed only; it does not confirm availability, access or permit requirements.' };
}
