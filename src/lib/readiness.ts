/** Pure readiness decisions. Local dates/times are visitor inputs, never UTC conversions. */
export interface Evidence {
  url: string; excerpt: string; content_hash: string; hash_scope: 'excerpt';
  reviewed_at: string; source_updated_at: string | null; method: 'manual_official_page_review';
}
export interface Rule {
  id: string; park_code: string; areas: string[]; effective_from: string; effective_to: string;
  start_time: string | null; end_time: string | null;
  requirement: 'timed_entry' | 'no_timed_entry'; reviewed_at: string;
  review_status: 'reviewed' | 'needs_review' | 'conflict';
  summary: string; exception_note: string; evidence: Evidence;
}
export interface Trip { park_code: string; date: string; time: string; area: string; special_case: boolean }
export type State = 'needs-input' | 'not-verified' | 'review-required' | 'not-required-under-rule' | 'stale' | 'conflict';
export interface Decision { state: State; title: string; detail: string; ruleId?: string }
export type Freshness = 'missing' | 'fresh' | 'stale' | 'invalid';
const instant = /^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/;
const wallTime = /^(?:[01]\d|2[0-3]):[0-5]\d$/;

export function freshness(checkedAt: string | null, hours: number, now: Date): Freshness {
  if (!Number.isFinite(now.getTime()) || !Number.isFinite(hours) || hours <= 0) return 'invalid';
  if (checkedAt === null) return 'missing';
  const timestamp = Date.parse(checkedAt);
  if (!instant.test(checkedAt) || !isCalendarDate(checkedAt.slice(0, 10)) || !Number.isFinite(timestamp) || timestamp > now.getTime()) return 'invalid';
  return now.getTime() - timestamp > hours * 3_600_000 ? 'stale' : 'fresh';
}
export function isCalendarDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T12:00:00Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value;
}
export function parkLocalDate(now: Date, timezone: string): string {
  const parts = new Intl.DateTimeFormat('en-US', { timeZone: timezone, year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(now);
  const get = (name: string) => parts.find((part) => part.type === name)!.value;
  return `${get('year')}-${get('month')}-${get('day')}`;
}
const decision = (state: State, title: string, detail: string, ruleId?: string): Decision => ({ state, title, detail, ruleId });

export function evaluateEntry(rules: Rule[], trip: Trip, now: Date): Decision {
  if (!isCalendarDate(trip.date)) return decision('needs-input', 'Choose a valid visit date', 'Use the calendar date at the park. This check covers one day of first-entry, private-vehicle travel.');
  const dated = rules.filter((rule) => rule.park_code === trip.park_code && trip.date >= rule.effective_from && trip.date <= rule.effective_to);
  if (!dated.length) return decision('not-verified', 'Entry requirements not verified for this date', 'There is no reviewed rule covering your selection. Check the official park guidance; a different year or season cannot be assumed.');
  if (!trip.area && dated.some((rule) => !rule.areas.includes('*'))) return decision('needs-input', 'Choose the area you plan to enter', 'Requirements can differ within the same park. Bear Lake Road is not interchangeable with the rest of Rocky Mountain.');
  const matching = dated.filter((rule) => rule.areas.includes('*') || rule.areas.includes(trip.area));
  if (!matching.length) return decision('not-verified', 'This area is not covered by a reviewed rule', 'Use the official park source to check this area.');
  if (matching.length !== 1 || matching.some((rule) => rule.review_status === 'conflict')) return decision('conflict', 'Conflicting guidance needs review', 'Do not rely on an automatic exemption. Check the official source before making plans.');
  const rule = matching[0];
  if (rule.review_status !== 'reviewed') return decision('review-required', 'Source guidance needs re-review', 'The stored rule is suspended until its source is reviewed again.', rule.id);
  if (freshness(rule.reviewed_at, 168, now) !== 'fresh') return decision('stale', 'Entry guidance needs a fresh review', 'This review is older than seven days, or its timestamp cannot be trusted. Follow the official link; no current conclusion is being made.', rule.id);
  if (trip.special_case) return decision('review-required', 'Check the rules for your circumstances', 'Existing campground/service reservations, wilderness permits, re-entry, commercial travel and non-vehicle visits need direct review. We do not infer an exemption.', rule.id);
  const limitation = 'This applies only to the reviewed timed-entry rule. Fees, activity permits, camping, road access and parking must be checked separately.';
  if (rule.requirement === 'no_timed_entry') return decision('not-required-under-rule', 'No timed entry under this reviewed rule', limitation, rule.id);
  if (!wallTime.test(trip.time)) return decision('needs-input', 'Add your arrival time at this area', 'Enter park-local time. For Bear Lake Road, use the time you expect to enter that corridor, not the park entrance.', rule.id);
  if (!rule.start_time || !rule.end_time) return decision('review-required', 'The daily window is incomplete', 'Check the official source; incomplete timing cannot grant an exemption.', rule.id);
  if (trip.time === rule.end_time) return decision('review-required', 'Verify the exact time boundary', 'Your arrival is on the published boundary. The source describes entry after this time; check directly rather than assuming an exemption.', rule.id);
  if (trip.time < rule.start_time || trip.time > rule.end_time) return decision('not-required-under-rule', 'Outside this reviewed timed-entry window', limitation, rule.id);
  return decision('review-required', 'Review your timed-entry reservation', `Your selection falls in the published window. ${rule.exception_note} We do not verify bookings or availability.`, rule.id);
}

export interface AlertState { collection_status: string; last_successful_fetch_at: string | null; records: unknown[] }
export function describeAlerts(snapshot: AlertState, now: Date): Decision {
  if (snapshot.collection_status === 'never_checked') return decision('not-verified', 'Conditions have not been collected', 'The automated alerts feed is not connected in this pilot. Check the official conditions page before travelling.');
  if (snapshot.collection_status !== 'success') return decision('review-required', 'The latest condition check was not successful', 'Last-good notices may be retained below. They are not a complete current view; check the official source.');
  if (freshness(snapshot.last_successful_fetch_at, 4, now) !== 'fresh') return decision('stale', 'The condition snapshot needs a fresh check', 'The last successful check is older than four hours, missing, or has an invalid timestamp. Verify the official source.');
  if (!snapshot.records.length) return decision('review-required', 'No alerts returned by the checked feed', 'This is not an all-clear. The feed may not cover every road, facility or activity.');
  return decision('review-required', 'Official notices need your review', 'These are notices in the checked feed, not a park-wide status. Their applicability to your date or destination may be unknown.');
}
