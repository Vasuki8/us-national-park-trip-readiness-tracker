/** Coverage is evidence availability, never a guarantee of access or safety. */
import { freshness } from './readiness.ts';
export interface ReviewCoverage { park_code: string; review_status: string; reviewed_at: string }
export interface SnapshotCoverage {
  park_code: string; collection_status: string; coverage_status: string;
  last_successful_fetch_at: string | null;
}
export interface CoverageInput {
  parks: { code: string }[]; rules: ReviewCoverage[]; notes: ReviewCoverage[]; snapshots: SnapshotCoverage[];
}
export function summarizeCoverage(input: CoverageInput, now: Date) {
  const rows = [...new Set(input.parks.map((park) => park.code))].map((code) => {
    const rules = input.rules.filter((rule) => rule.park_code === code);
    const reviews = [...rules, ...input.notes.filter((note) => note.park_code === code)];
    const hasStoredReview = reviews.length > 0;
    const reviewWithinWindow = hasStoredReview && reviews.every((review) => review.review_status === 'reviewed' && freshness(review.reviewed_at, 168, now) === 'fresh');
    let entryLabel = 'Entry review pending';
    if (reviews.some((review) => review.review_status === 'conflict')) entryLabel = 'Conflicting source reviews';
    else if (reviews.some((review) => review.review_status !== 'reviewed')) entryLabel = 'Source review pending';
    else if (hasStoredReview && !reviewWithinWindow) entryLabel = 'Source review needs refreshing';
    else if (hasStoredReview) entryLabel = rules.length ? 'Dated rules stored' : 'Undated source review';
    const matches = input.snapshots.filter((snapshot) => snapshot.park_code === code);
    const snapshot = matches.length === 1 ? matches[0] : undefined;
    let alertLabel = matches.length > 1 ? 'Alert state unverified' : 'Alerts not collected';
    let recentAlertCheck = false;
    if (snapshot) {
      if (snapshot.collection_status === 'failed') alertLabel = 'Latest alert check failed';
      else if (snapshot.collection_status === 'quarantined') alertLabel = 'Alert feed needs review';
      else if (snapshot.collection_status === 'success' && snapshot.coverage_status === 'checked_feed_only') {
        recentAlertCheck = freshness(snapshot.last_successful_fetch_at, 4, now) === 'fresh';
        alertLabel = recentAlertCheck ? 'Alert feed checked' : 'Alert check needs refreshing';
      } else if (snapshot.collection_status !== 'never_checked') alertLabel = 'Alert state unverified';
    }
    return { code, hasStoredReview, hasDatedRule: rules.length > 0, reviewWithinWindow, recentAlertCheck, entryLabel, alertLabel };
  });
  return {
    parkCount: rows.length,
    storedReviewParks: rows.filter((row) => row.hasStoredReview).length,
    datedRuleParks: rows.filter((row) => row.hasDatedRule).length,
    reviewWithinWindowParks: rows.filter((row) => row.reviewWithinWindow).length,
    recentAlertParks: rows.filter((row) => row.recentAlertCheck).length,
    rows,
  };
}
