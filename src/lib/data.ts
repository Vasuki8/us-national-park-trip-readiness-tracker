import parks from '../../data/parks.json';
import rawRules from '../../data/rules.json';
import rawNotes from '../../data/entry-notes.json';
import rawEntryReview from '../../data/entry-review.json';
import rawHistory from '../../data/history.json';
import rawPlanningResources from '../../data/planning-resources.json';
import yose from '../../data/alerts/yose.json';
import romo from '../../data/alerts/romo.json';
import yell from '../../data/alerts/yell.json';
import zion from '../../data/alerts/zion.json';
import grca from '../../data/alerts/grca.json';
import { validateEntryNotes, type EntryNote } from '../../scripts/validate-entry-notes';
import { applyEntryReview } from '../../scripts/entry-review';
import { validateHistory } from '../../scripts/validate-history';
import { validatePlanningResources } from '../../scripts/validate-planning-resources';
import { validatePublicProfiles, validateProfileRights } from '../../scripts/validate-park-profiles';
import type { CatalogActivityInventory } from '../../scripts/validate-park-activities';
import { activityCatalogSnapshotId, loadPublicActivityCatalog } from './public-activity-catalog';
import type { Rule } from './readiness';
import type { CoverageInput, ReviewCoverage } from './source-coverage';
export { parks };
const approvedRules = rawRules as Rule[];
// Validate notes at the server/build boundary; they never enter the date evaluator.
validateEntryNotes(rawNotes, parks.map((park) => park.code));
// Pending proposals bind original records; only overlaid review states reach consumers.
// No candidate replacement text is serialized to the browser or used as approved guidance.
const entryReview = applyEntryReview<Rule | EntryNote>([...approvedRules, ...rawNotes], rawEntryReview, new Date());
export const rules = entryReview.guidance.slice(0, approvedRules.length) as Rule[];
export const notes = entryReview.guidance.slice(approvedRules.length) as EntryNote[];
export const entryReviewHoldsFor = (code: string) => entryReview.holds.filter((hold) => hold.park_code === code);
// Relevant links are not operational reviews and never enter rule/feed coverage.
export const planningResources = validatePlanningResources(rawPlanningResources, parks.map((park) => park.code));
export const planningResourcesFor = (code: string) => planningResources.filter((resource) => resource.park_code === code);
// Eager, build-only imports retain the optional paired-data contract and never request the API.
const profileFiles = import.meta.glob('../../data/{park-profiles,profile-source-rights}.json', { eager: true, import: 'default' });
const rawProfiles = profileFiles['../../data/park-profiles.json'];
const rawProfileRights = profileFiles['../../data/profile-source-rights.json'];
if ((rawProfiles === undefined) !== (rawProfileRights === undefined)) throw new Error('incomplete_public_profile_pair');
const publicProfiles = rawProfiles === undefined ? null : validatePublicProfiles(rawProfiles);
if (publicProfiles) validateProfileRights(rawProfileRights, publicProfiles);
export const profiles = publicProfiles?.profiles ?? [];
export const profileFor = (code: string) => profiles.find(profile => profile.park_code === code) ?? null;
const activityFiles = import.meta.glob('../../data/{park-activities,activity-source-rights}.json', { eager: true, import: 'default' });
const publicActivityCatalog = loadPublicActivityCatalog(activityFiles['../../data/park-activities.json'], activityFiles['../../data/activity-source-rights.json']);
export const activitiesFor = (code: string): CatalogActivityInventory | null => publicActivityCatalog.catalog?.inventories.find(inventory => inventory.park_code === code) ?? null;
export interface Notice { id: string; title: string; description: string; category: string; url: string | null; scope_status: string }
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
  snapshot_id: activityCatalogSnapshotId({ parks, rules, notes, rawEntryReview, snapshots, histories, planningResources, ...(profiles.length ? { profiles } : {}) }, publicActivityCatalog),
  built_at: new Date().toISOString(), published_at: null,
  code_commit: process.env.GITHUB_SHA || null, live_collection_enabled: false,
  base_path: import.meta.env.BASE_URL,
};
