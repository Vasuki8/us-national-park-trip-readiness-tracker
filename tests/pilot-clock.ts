import { readFileSync } from 'node:fs';
import type { Rule } from '../src/lib/readiness.ts';
import type { Snapshot } from '../src/lib/data.ts';
import type { History } from '../src/lib/history.ts';
import type { EntryNote } from '../scripts/validate-entry-notes.ts';

const readPublicJson = <T>(path: string): T => JSON.parse(readFileSync(new URL(`../data/${path}`, import.meta.url), 'utf8'));
export const publicParks = readPublicJson<{ code: string; slug: string; conditions_url: string }[]>('parks.json');
export const publicRules = readPublicJson<Rule[]>('rules.json');
export const publicNotes = readPublicJson<EntryNote[]>('entry-notes.json');
export const publicHistories = readPublicJson<History[]>('history.json');
export const publicParkSnapshots = publicParks.map((park) => readPublicJson<Snapshot>(`alerts/${park.code}.json`));

// Production-browser scenarios must run after the stored evidence, even as the
// approved public pilot advances. The historical fixtures retain their own clock.
const evidenceClocks = [
  ...[...publicRules, ...publicNotes].map((record) => record.reviewed_at),
  ...publicParkSnapshots.map((snapshot) => snapshot.last_successful_fetch_at),
];
if (evidenceClocks.some((clock) => clock === null || !Number.isFinite(Date.parse(clock)))) {
  throw new Error('The populated public pilot must have valid review and successful-feed clocks.');
}
export const PUBLIC_PILOT_FRESH_TIME = new Date(Math.max(...evidenceClocks.map((clock) => Date.parse(clock!))) + 1_000).toISOString();
export const PUBLIC_PILOT_STALE_TIME = new Date(Date.parse(PUBLIC_PILOT_FRESH_TIME) + 8 * 24 * 3_600_000).toISOString();
