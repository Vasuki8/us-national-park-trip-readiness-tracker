/** Build-only loading of the optional reviewed minimal activity catalog. */
import { createHash } from 'node:crypto';
import { activityDigest, MAX_ACTIVITY_RIGHTS_BYTES, validatePublicActivities, validateActivityRights,
  type PublicActivityCatalog } from '../../scripts/validate-park-activities.ts';

export interface LoadedPublicActivityCatalog {
  catalog: PublicActivityCatalog | null;
  snapshotInputs: { activity_catalog_hash?: string; activity_rights_hash?: string };
}

export function loadPublicActivityCatalog(rawActivities: unknown, rawRights: unknown): LoadedPublicActivityCatalog {
  if ((rawActivities === undefined) !== (rawRights === undefined)) throw new Error('incomplete_public_activity_pair');
  if (rawActivities === undefined) return { catalog: null, snapshotInputs: {} };
  const activities = validatePublicActivities(rawActivities);
  const rights = validateActivityRights(rawRights, activities);
  // Legacy complete-text pairs keep their validation/recovery contract, but
  // their prose and rights never reach this minimal catalog's consumers.
  if (activities.schema_version !== 2) return { catalog: null, snapshotInputs: {} };
  return {
    catalog: activities,
    snapshotInputs: {
      activity_catalog_hash: activityDigest(activities),
      activity_rights_hash: activityDigest(rights, MAX_ACTIVITY_RIGHTS_BYTES),
    },
  };
}

export function activityCatalogSnapshotId(previousInputs: Record<string, unknown>, activities: LoadedPublicActivityCatalog): string {
  // Adding no keys preserves the previous JSON shape and hash when this consumer
  // has no version 2 catalog. Empty/wholly withheld catalogs still bind both files.
  return `pilot-${createHash('sha256').update(JSON.stringify({ ...previousInputs, ...activities.snapshotInputs })).digest('hex').slice(0, 12)}`;
}
