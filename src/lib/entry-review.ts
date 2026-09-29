/** Public hold metadata only. Candidate text and hashing stay on the server. */
export type EntryReviewReason = 'text_changed' | 'excerpt_missing' | 'check_failed';
export interface EntryHold {
  guidance_id: string;
  park_code: string;
  source_url: string;
  first_detected_at: string;
  latest_held_check_at: string;
  reasons: EntryReviewReason[];
  proposal_count: number;
}
export const entryReviewLabels: Record<EntryReviewReason, string> = {
  text_changed: 'Selected source text differs from the approved evidence',
  excerpt_missing: 'The selected source excerpt could not be located',
  check_failed: 'The selected source check failed',
};
