/** Public observation history types and browser-safe copy. No archive I/O here. */
import { freshness } from './readiness.ts';
export interface HistoryEvidence {
  id: string; title: string; description: string; category: string; url: string; content_hash: string;
}
export interface HistoryChange {
  kind: 'added' | 'edited' | 'removed'; record_id: string;
  before: HistoryEvidence | null; after: HistoryEvidence | null;
}
export interface HistoryObservation {
  observation_id: string; sequence: number; checked_at: string;
  collection_status: 'success' | 'failed' | 'quarantined';
  comparison: 'baseline' | 'compared' | 'not_compared';
  change_count: number; omitted_changes: number; changes: HistoryChange[];
}
export interface History {
  schema_version: 1; park_code: string; head_observation_id: string | null; snapshot_hash: string;
  total_observations: number; omitted_observations: number;
  total_changes: number; omitted_changes: number; observations: HistoryObservation[];
}
export interface HistoryMetadata {
  collection_status: string; last_checked_at: string | null; last_successful_fetch_at: string | null;
}
export const changeLabels = {
  added: 'Notice added to the checked feed', edited: 'Notice changed in the checked feed',
  removed: 'Notice no longer present in the checked feed',
};
export function describeHistory(snapshot: HistoryMetadata, now: Date): { title: string; detail: string } {
  if (snapshot.collection_status === 'never_checked') return {
    title: 'History not collected', detail: 'There are no collected observations to show. An empty timeline does not mean that nothing has changed at the park.',
  };
  if (snapshot.collection_status !== 'success') return {
    title: 'The latest check was not successful', detail: 'Earlier accepted evidence is retained. This failed or quarantined check was not compared as a change to park notices.',
  };
  if (freshness(snapshot.last_successful_fetch_at, 4, now) !== 'fresh') return {
    title: 'History needs a fresh check', detail: 'The last successful check is older than four hours, missing, or has an invalid timestamp. This timeline is historical, not current conditions.',
  };
  return { title: 'Recent feed check; coverage remains limited', detail: 'This records what changed in the checked feed, not when conditions changed on the ground or whether your trip is affected.' };
}
