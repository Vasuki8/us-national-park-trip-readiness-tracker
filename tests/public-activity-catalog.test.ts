import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { activityCatalogSnapshotId, loadPublicActivityCatalog } from '../src/lib/public-activity-catalog.ts';

const codes = ['yose', 'romo', 'yell', 'zion', 'grca'];
const checked = '2026-10-04T10:00:00.123456Z';
const policy = {
  ownership_url: 'https://www.nps.gov/aboutus/disclaimer.htm',
  marks_url: 'https://www.nps.gov/subjects/partnerships/arrowhead-requests.htm?fullweb=1',
  commercial_notice: 'No protection is claimed in original U.S. Government works.',
  third_party_material_allowed: false, nps_marks_allowed: false, raw_private_captures_public: false,
};
// This independent encoder uses the fixtures' ASCII field names, retaining their
// Unicode string values. It never calls the production canonical/hash helpers.
const canonical = (value: any): string => value && typeof value === 'object'
  ? Array.isArray(value) ? '[' + value.map(canonical).join(',') + ']'
    : '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}'
  : JSON.stringify(value);
const digest = (value: any) => createHash('sha256').update(canonical(value), 'utf8').digest('hex');
function rehash(record: any) {
  record.view_hash = digest(Object.fromEntries(Object.entries(record)
    .filter(([key]) => key !== 'view_hash' && key !== 'hash_scope')));
}
function catalog(): any {
  return { schema_version: 2, purpose: 'public_park_activities', inventories: codes.map(code => {
    const record = {
      id: 'selected-a', park_code: code, title: `Synthetic ${code} café 🌲 & "view"`,
      url: `https://www.nps.gov/${code}/synthetic.htm`,
      activity_categories: [{ id: 'category-a', name: 'Synthetic category 🌲' }], category_scope: 'published',
      geographic_relationship: 'unconfirmed', responsible_agency: null, difficulty: null, permit_required: null,
      availability_status: 'not_verified', source_updated_at: null,
      observed_first_at: checked, observed_changed_at: checked,
      source_content_hash: 'a'.repeat(64), view_hash: '', hash_scope: 'catalog_view',
    };
    rehash(record);
    return {
      schema_version: 2, park_code: code, provider: 'NPS',
      source_url: `https://developer.nps.gov/api/v1/thingstodo?parkCode=${code}`,
      collection_status: 'success', coverage_status: 'checked_activity_feed_only',
      last_checked_at: checked, last_successful_fetch_at: checked,
      source_issued_at: null, source_updated_at: null, published_at: null, error_code: null,
      records: [record], source_records: ['selected-a', 'withheld-b'].map((id, index) => ({
        id, content_hash: (index ? 'b' : 'a').repeat(64), hash_scope: 'normalized_record',
        observed_first_at: checked, observed_changed_at: checked,
        publication_status: index ? 'withheld' : 'selected',
      })),
    };
  }) };
}
function rights(data: any): any {
  const v2 = data.schema_version === 2;
  return {
    schema_version: data.schema_version, purpose: 'public_park_activity_text_rights',
    reviewed_at: '2026-10-04T10:00:01Z', review_method: 'official_nps_policy_and_exact_activity_review',
    policy: structuredClone(policy), ...(v2 ? { projection_hash: digest(data) } : {}),
    records: data.inventories.flatMap((inventory: any) => inventory.records.map((record: any) => ({
      park_code: inventory.park_code, activity_id: record.id, source_url: inventory.source_url,
      ...(v2 ? { source_content_hash: record.source_content_hash, view_hash: record.view_hash }
        : { content_hash: record.content_hash }),
      classification: 'nps_government_text',
      use_scope: v2 ? 'activity_catalog_title_url_and_optional_categories' : 'normalized_activity_text_and_metadata',
      third_party_material_reproduced: false, nps_marks_reproduced: false, media_reproduced: false,
    }))),
  };
}
function legacy(): any {
  const data = catalog(); data.schema_version = 1;
  data.inventories.forEach((inventory: any) => {
    inventory.schema_version = 1; delete inventory.source_records;
    const semantic = {
      id: 'selected-a', park_code: inventory.park_code, title: 'Synthetic legacy activity',
      url: `https://www.nps.gov/${inventory.park_code}/synthetic.htm`,
      description: '<b>FULL_PROSE_MUST_STAY_BUILD_ONLY</b>', long_description: 'PRIVATE_LONG_DESCRIPTION',
      location: null, location_description: null, duration: null, duration_description: null,
      season_description: null, accessibility_information: null, activity_description: null,
      fee_description: null, reservation_description: null, pets_description: null, age: null,
      age_description: null, time_of_day_description: null, credit: 'PRIVATE_CREDIT',
      fees_apply: null, reservation_required: null, pets_permitted: null, pets_permitted_with_restrictions: null,
      seasons: null, times_of_day: null, activity_categories: null,
      related_parks: [{ park_code: inventory.park_code, full_name: null, url: null,
        states: null, designation: null, name: null }],
      geographic_relationship: 'unconfirmed', responsible_agency: null, difficulty: null, permit_required: null,
    };
    inventory.records = [{ ...semantic, source_updated_at: null, observed_first_at: checked,
      observed_changed_at: checked, content_hash: digest(semantic), hash_scope: 'normalized_record' }];
  });
  return data;
}
const priorInputs = {
  parks: [{ code: 'yose' }], rules: [], notes: [], rawEntryReview: { records: [] },
  snapshots: [], histories: [], planningResources: [], profiles: [{ park_code: 'yose' }],
};
const snapshotId = (inputs: unknown) => `pilot-${createHash('sha256').update(JSON.stringify(inputs)).digest('hex').slice(0, 12)}`;
function loadedSnapshot(data: any, manifest = rights(data)) {
  return activityCatalogSnapshotId(priorInputs, loadPublicActivityCatalog(data, manifest));
}
function reverseKeys(value: any): any {
  if (!value || typeof value !== 'object') return value;
  if (Array.isArray(value)) return value.map(reverseKeys);
  return Object.fromEntries(Object.entries(value).reverse().map(([key, item]) => [key, reverseKeys(item)]));
}

test('an absent activity pair preserves the earlier build inputs and snapshot identity', () => {
  const loaded = loadPublicActivityCatalog(undefined, undefined);
  assert.deepEqual(loaded, { catalog: null, snapshotInputs: {} });
  assert.deepEqual({ ...priorInputs, ...loaded.snapshotInputs }, priorInputs);
  assert.equal(activityCatalogSnapshotId(priorInputs, loaded), snapshotId(priorInputs));
  const { profiles: _profiles, ...withoutProfiles } = priorInputs;
  assert.deepEqual({ ...withoutProfiles, ...loaded.snapshotInputs }, withoutProfiles);
  assert.equal(activityCatalogSnapshotId(withoutProfiles, loaded), snapshotId(withoutProfiles));
});

test('valid version 1 text is validated but never exposed or added to the build snapshot', () => {
  const data = legacy(), manifest = rights(data);
  const loaded = loadPublicActivityCatalog(data, manifest);
  assert.deepEqual(loaded, { catalog: null, snapshotInputs: {} });
  assert.equal(loadedSnapshot(data, manifest), snapshotId(priorInputs));
  assert.doesNotMatch(JSON.stringify(loaded), /FULL_PROSE|PRIVATE_|normalized_activity_text_and_metadata/);
});

test('partial, null and malformed activity pairs fail rather than becoming absent', () => {
  const data = catalog(), manifest = rights(data);
  for (const [projection, review] of [[data, undefined], [undefined, manifest], [null, null],
    [null, manifest], [data, null], [{}, {}], [[], []]]) {
    assert.throws(() => loadPublicActivityCatalog(projection, review));
  }
});

test('version 1 data and rights remain validated even though the consumer suppresses them', () => {
  const data = legacy(), manifest = rights(data);
  const badData = structuredClone(data); badData.inventories[0].records[0].description += ' tampered';
  assert.throws(() => loadPublicActivityCatalog(badData, manifest));
  const badRights = structuredClone(manifest); badRights.records[0].content_hash = 'f'.repeat(64);
  assert.throws(() => loadPublicActivityCatalog(data, badRights));
  manifest.reviewed_at = '2026-10-04T10:00:00.123455Z';
  assert.throws(() => loadPublicActivityCatalog(data, manifest));
});

test('cross-version pairs and changed catalogs without matching exact rights are refused', () => {
  const data = catalog(), old = legacy();
  assert.throws(() => loadPublicActivityCatalog(data, rights(old)));
  assert.throws(() => loadPublicActivityCatalog(old, rights(data)));
  const manifest = rights(data);
  data.inventories[0].records[0].title += ' altered'; rehash(data.inventories[0].records[0]);
  assert.throws(() => loadPublicActivityCatalog(data, manifest));
  manifest.projection_hash = digest(data);
  assert.throws(() => loadPublicActivityCatalog(data, manifest));
});

test('version 2 returns the detached catalog and only canonical projection and rights hashes', () => {
  const data = catalog(), manifest = rights(data), original = structuredClone({ data, manifest });
  const loaded = loadPublicActivityCatalog(data, manifest);
  assert.deepEqual(loaded.catalog, data);
  assert.deepEqual(loaded.snapshotInputs, { activity_catalog_hash: digest(data), activity_rights_hash: digest(manifest) });
  assert.deepEqual(Object.keys(loaded), ['catalog', 'snapshotInputs']);
  assert.notEqual(loaded.catalog, data);
  assert.notEqual(loaded.catalog!.inventories[0].records[0], data.inventories[0].records[0]);
  loaded.catalog!.inventories[0].records[0].title = 'Changed returned copy';
  loaded.catalog!.inventories[0].source_records[1].content_hash = 'f'.repeat(64);
  assert.deepEqual({ data, manifest }, original);
  const detached = loadPublicActivityCatalog(data, manifest);
  data.inventories[0].records[0].title = 'Changed original'; manifest.reviewed_at = 'changed original';
  assert.equal(detached.catalog!.inventories[0].records[0].title, original.data.inventories[0].records[0].title);
  assert.deepEqual(detached.snapshotInputs, { activity_catalog_hash: digest(original.data), activity_rights_hash: digest(original.manifest) });
});

test('object key insertion order does not change catalog digests or the resulting snapshot', () => {
  const data = catalog(), manifest = rights(data);
  const loaded = loadPublicActivityCatalog(data, manifest);
  const reordered = loadPublicActivityCatalog(reverseKeys(data), reverseKeys(manifest));
  assert.deepEqual(reordered.snapshotInputs, loaded.snapshotInputs);
  assert.equal(loadedSnapshot(reverseKeys(data), reverseKeys(manifest)), loadedSnapshot(data, manifest));
});

for (const [name, mutate] of [
  ['selected title', (data: any) => { data.inventories[0].records[0].title += ' changed'; rehash(data.inventories[0].records[0]); }],
  ['selected categories', (data: any) => { data.inventories[0].records[0].activity_categories = []; rehash(data.inventories[0].records[0]); }],
  ['withheld source hash', (data: any) => { data.inventories[0].source_records[1].content_hash = 'c'.repeat(64); }],
  ['withheld observation clock', (data: any) => { data.inventories[0].source_records[1].observed_first_at = '2026-10-04T10:00:00.123455Z'; }],
  ['original feed clock', (data: any) => { data.inventories.forEach((inventory: any) => {
    inventory.last_checked_at = inventory.last_successful_fetch_at = '2026-10-04T10:00:00.123457Z';
  }); }],
] as const) test(`${name} contributes to the build snapshot even when selected listing counts do not change`, () => {
  const data = catalog(), before = loadedSnapshot(data); mutate(data);
  assert.notEqual(loadedSnapshot(data), before);
});

test('a later exact rights review contributes independently without changing catalog or source clocks', () => {
  const data = catalog(), manifest = rights(data), before = loadPublicActivityCatalog(data, manifest);
  manifest.reviewed_at = '2026-10-04T10:00:02Z';
  const after = loadPublicActivityCatalog(data, manifest);
  assert.equal(after.snapshotInputs.activity_catalog_hash, before.snapshotInputs.activity_catalog_hash);
  assert.notEqual(after.snapshotInputs.activity_rights_hash, before.snapshotInputs.activity_rights_hash);
  assert.notEqual(loadedSnapshot(data, manifest), snapshotId({ ...priorInputs, ...before.snapshotInputs }));
  assert.equal(after.catalog!.inventories[0].last_checked_at, checked);
});

for (const scenario of ['empty', 'wholly withheld'] as const) test(`${scenario} version 2 catalogs still bind both complete files`, () => {
  const data = catalog();
  data.inventories.forEach((inventory: any) => {
    inventory.records = [];
    if (scenario === 'empty') inventory.source_records = [];
    else inventory.source_records.forEach((source: any) => source.publication_status = 'withheld');
  });
  const manifest = rights(data), loaded = loadPublicActivityCatalog(data, manifest);
  assert.deepEqual(loaded.catalog, data);
  assert.deepEqual(loaded.snapshotInputs, { activity_catalog_hash: digest(data), activity_rights_hash: digest(manifest) });
  assert.notEqual(loadedSnapshot(data, manifest), snapshotId(priorInputs));
  manifest.reviewed_at = '2026-10-04T10:00:02Z';
  assert.notEqual(loadedSnapshot(data, manifest), snapshotId({ ...priorInputs, ...loaded.snapshotInputs }));
});
