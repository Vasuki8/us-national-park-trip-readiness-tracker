import { createHash } from 'node:crypto';
import parks from '../../data/parks.json';
import rawRules from '../../data/rules.json';
import rawNotes from '../../data/entry-notes.json';
import rawHistory from '../../data/history.json';
import yose from '../../data/alerts/yose.json';
import romo from '../../data/alerts/romo.json';
import yell from '../../data/alerts/yell.json';
import zion from '../../data/alerts/zion.json';
import grca from '../../data/alerts/grca.json';
import { validateEntryNotes, type EntryNote } from '../../scripts/validate-entry-notes';
import { validateHistory } from '../../scripts/validate-history';
import type { Rule } from './readiness';
import type { CoverageInput, ReviewCoverage } from './source-coverage';
export { parks };
export const rules = rawRules as Rule[];
// Validate notes at the server/build boundary; they never enter the date evaluator.
validateEntryNotes(rawNotes, parks.map((park) => park.code));
export const notes: EntryNote[] = rawNotes;
export interface Notice { id: string; title: string; description: string; category: string; url: string; scope_status: string }
export interface Snapshot {
  park_code: string; collection_status: string; coverage_status: string; last_checked_at: string | null;
  last_successful_fetch_at: string | null; source_updated_at: string | null; records: Notice[];
}
const snapshots = [yose, romo, yell, zion, grca] as Snapshot[];
export const snapshotFor = (code: string): Snapshot => snapshots.find((snapshot) => snapshot.park_code === code)!;
// History and current notices must belong to the same reviewed data snapshot.
if (rawHistory.length !== parks.length || new Set(rawHistory.map((item) => item.park_code)).size !== parks.length
  || rawHistory.some((item) => !parks.some((park) => park.code === item.park_code))) throw new Error('history_inventory_mismatch');
export const histories = rawHistory.map((item) => validateHistory(item, snapshotFor(item.park_code)));
export const historyFor = (code: string) => histories.find((history) => history.park_code === code)!;
export const rulesFor = (code: string) => rules.filter((rule) => rule.park_code === code);
export const notesFor = (code: string) => notes.filter((note) => note.park_code === code);
const reviewMetadata = ({ park_code, review_status, reviewed_at }: ReviewCoverage): ReviewCoverage => ({ park_code, review_status, reviewed_at });
// Only public, minimal metadata is serialized for browser freshness calculations.
export const coverageInput: CoverageInput = {
  parks: parks.map(({ code }) => ({ code })), rules: rules.map(reviewMetadata), notes: notes.map(reviewMetadata),
  snapshots: snapshots.map(({ park_code, collection_status, coverage_status, last_successful_fetch_at }) => ({ park_code, collection_status, coverage_status, last_successful_fetch_at })),
};
export const buildInfo = {
  snapshot_id: `pilot-${createHash('sha256').update(JSON.stringify({ parks, rules, notes, snapshots, histories })).digest('hex').slice(0, 12)}`,
  built_at: new Date().toISOString(), published_at: null,
  code_commit: process.env.GITHUB_SHA || null, live_collection_enabled: false,
};
