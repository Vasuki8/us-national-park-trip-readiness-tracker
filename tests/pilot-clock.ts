import { readFileSync } from 'node:fs';
import { freshness, type Rule } from '../src/lib/readiness.ts';
import type { Snapshot } from '../src/lib/data.ts';
import type { History } from '../src/lib/history.ts';
import type { EntryNote } from '../scripts/validate-entry-notes.ts';

const readPublicJson = <T>(path: string): T => JSON.parse(readFileSync(new URL(`../data/${path}`, import.meta.url), 'utf8'));
export const publicParks = readPublicJson<{ code: string; slug: string; conditions_url: string }[]>('parks.json');
export const publicRules = readPublicJson<Rule[]>('rules.json');
export const publicNotes = readPublicJson<EntryNote[]>('entry-notes.json');
export const publicHistories = readPublicJson<History[]>('history.json');
export const publicParkSnapshots = publicParks.map((park) => readPublicJson<Snapshot>(`alerts/${park.code}.json`));

type ReviewClock = { reviewed_at: string };
type SnapshotClocks = Pick<Snapshot, 'last_checked_at' | 'last_successful_fetch_at'>;

// A reference after the evidence avoids future timestamps. It cannot make
// independently aged reviews or retained successful feeds fresh.
export function evidenceReferenceTime(reviews: readonly ReviewClock[], snapshots: readonly SnapshotClocks[]): string {
  const known = [
    ...reviews.map((record) => record.reviewed_at),
    ...snapshots.flatMap((snapshot) => [snapshot.last_checked_at, snapshot.last_successful_fetch_at]),
  ].filter((clock): clock is string => clock !== null);
  if (!known.length || known.some((clock) => freshness(clock, 1, new Date(clock)) !== 'fresh')) {
    throw new Error('A reference clock requires valid, non-null evidence.');
  }
  return new Date(Math.max(...known.map((clock) => Date.parse(clock))) + 1_000).toISOString();
}

// Deliberate annual-rule scenarios run at their guidance review, independently
// of alert updates. Their visit dates remain explicit scenario inputs.
export function guidanceScenarioTime(reviews: readonly ReviewClock[]): string {
  const clock = evidenceReferenceTime(reviews, []);
  if (reviews.some((review) => freshness(review.reviewed_at, 168, new Date(clock)) !== 'fresh')) {
    throw new Error('The selected guidance has no shared fresh-review scenario.');
  }
  return clock;
}

export const PUBLIC_PILOT_REFERENCE_TIME = evidenceReferenceTime([...publicRules, ...publicNotes], publicParkSnapshots);
export const PUBLIC_PILOT_STALE_TIME = new Date(Date.parse(PUBLIC_PILOT_REFERENCE_TIME) + 8 * 24 * 3_600_000).toISOString();
