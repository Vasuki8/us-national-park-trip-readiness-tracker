import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { canonicalPreview, PILOT_CODES, validatePreviewBundle } from '../scripts/preview-bundle.ts';
import { validateSnapshot } from '../scripts/validate-data.ts';
import { historyDigest, validateHistory } from '../scripts/validate-history.ts';
import { buildAlertPromotionPatch } from '../scripts/prepare-alert-promotion.ts';
import { syntheticPublicFiles } from './synthetic-preview.ts';

const root = resolve(import.meta.dirname, '..');
const generated = spawnSync('python', [resolve(root, 'tests/notice_url_pipeline_fixture.py')], {
  cwd: root, encoding: 'utf8', timeout: 30_000, maxBuffer: 256 * 1024,
  env: {...process.env, PYTHONPATH: root, PYTHONNOUSERSITE: '1', PYTHONDONTWRITEBYTECODE: '1'},
});
const safeUrls = [
  'https://www.nps.gov/yose/synthetic/',
  'https://www.nps.gov/subjects/synthetic/',
  'https://go.nps.gov/synthetic/',
  'https://inciweb.wildfire.gov/incident/synthetic/',
  'https://example.org/synthetic/directory/?view=summary#details',
  'https://example.org/synthetic/caf%C3%A9/',
  'https://example.org/synthetic/encoded-directory%2F',
];
const editedUrl = 'https://www.nps.gov/yose/synthetic-changed/';
const unsafeUrls = [
  'https://example.org/synthetic/../directory/',
  'https://example.org/synthetic/%2e%2e/directory/',
  'https://example.org/synthetic/./directory/',
  'https://example.org/synthetic//directory/',
  'https://example.org//directory/',
  'https://example.org/synthetic/directory//',
  'https://example.org/synthetic%2f/directory/',
  'https://example.org/%2Fdirectory/',
  'https://example.org/synthetic\\directory/',
  'https://example.org/synthetic%5cdirectory/',
];
const semantic = (record: any) => Object.fromEntries(
  ['category', 'description', 'id', 'title', 'url'].map(key => [key, record[key]]));
function fixture() {
  assert.equal(generated.error, undefined);
  assert.equal(generated.status, 0, generated.stderr);
  assert.equal(generated.stderr, '');
  const value = JSON.parse(generated.stdout);
  assert.equal(value.purpose, 'SYNTHETIC TEST DATA — NOT PARK CONDITIONS');
  assert.deepEqual(value.safe_urls, safeUrls);
  assert.equal(value.edited_url, editedUrl);
  assert.deepEqual(value.unsafe_urls, unsafeUrls);
  return value;
}
function validateBundle(bundle: any) {
  assert.deepEqual(validatePreviewBundle(bundle), bundle);
  for (const view of bundle.views) {
    assert.equal(historyDigest(view.snapshot), view.history.snapshot_hash);
    assert.doesNotThrow(() => validateSnapshot(view.snapshot, view.snapshot.park_code));
    assert.deepEqual(validateHistory(view.history, view.snapshot), view.history);
  }
}
function rehashBundle(bundle: any) {
  const {bundle_id, ...body} = bundle;
  return {...body, bundle_id: historyDigest(body)};
}
function simulatedReviewEnvelope(bundle: any) {
  // Exercise the in-memory preparer with synthetic evidence; no patch is written or applied.
  const value = structuredClone(bundle);
  value.data_kind = 'unreviewed_source';
  return rehashBundle(value);
}

test('provider directory URL bytes and normalized-record hashes survive collection, immutable archive replay and TypeScript bundle validation', () => {
  const value = fixture();
  const {baseline, unchanged, edited, degraded} = value.bundles;
  for (const bundle of [baseline, unchanged, edited, degraded]) validateBundle(bundle);
  assert.deepEqual(baseline.views.map((view: any) => view.snapshot.park_code), [...PILOT_CODES]);
  assert.ok(baseline.views.slice(1).every((view: any) => view.snapshot.collection_status === 'never_checked'));
  const records = baseline.views[0].snapshot.records;
  assert.deepEqual(records.map((record: any) => record.url), safeUrls);
  const evidence = new Map<string, string>(value.evidence.map((item: any) => [item.content_hash, item.canonical]));
  for (const record of [...records, edited.views[0].snapshot.records[0]]) {
    assert.equal(record.park_code, 'yose');
    assert.equal(record.hash_scope, 'normalized_record');
    assert.equal(record.content_hash, historyDigest(semantic(record)));
    assert.equal(evidence.get(record.content_hash), canonicalPreview(semantic(record)));
    const withoutDirectorySlash = record.url.replace(/(?:\/|%2F)(?=[?#]|$)/, '');
    assert.notEqual(record.content_hash, historyDigest({...semantic(record), url: withoutDirectorySlash}));
  }
  assert.equal(value.canonical_bundle, canonicalPreview(degraded));
});

test('unchanged and edited directory URLs retain observation clocks and historical URL evidence through the promotion validator', () => {
  const {baseline, unchanged, edited} = fixture().bundles;
  const first = baseline.views[0].snapshot, same = unchanged.views[0].snapshot;
  const current = edited.views[0].snapshot, history = edited.views[0].history;
  assert.deepEqual(same.records, first.records);
  assert.equal(same.last_successful_fetch_at, '2026-09-28T21:00:00Z');
  assert.deepEqual(unchanged.views[0].history.observations[0].changes, []);
  assert.equal(current.records[0].url, editedUrl);
  assert.equal(current.records[0].observed_first_at, '2026-09-28T20:00:00Z');
  assert.equal(current.records[0].observed_changed_at, '2026-09-28T22:00:00Z');
  assert.equal(history.total_changes, 1);
  assert.equal(history.observations[0].changes[0].kind, 'edited');
  assert.equal(history.observations[0].changes[0].before.url, safeUrls[0]);
  assert.equal(history.observations[0].changes[0].after.url, editedUrl);
  const files = syntheticPublicFiles(baseline.views);
  assert.throws(() => buildAlertPromotionPatch(edited, files), /alert_promotion_refused/);
  const result = buildAlertPromotionPatch(simulatedReviewEnvelope(edited), files);
  assert.equal(result.report.changed_files, 2);
  assert.equal(result.report.publication_performed, false);
  assert.equal(result.report.production_data_written, false);
  assert.equal(result.report.human_review_required, true);
  assert.ok(result.patch.includes(editedUrl));
  assert.ok(result.patch.includes(safeUrls[0]));
});

test('unsafe directory URL attempts and transport failures retain accepted links and the successful-fetch clock throughout the pipeline', () => {
  const value = fixture(), {edited, degraded} = value.bundles;
  const view = degraded.views[0], retained = edited.views[0].snapshot;
  assert.equal(value.attempts.length, unsafeUrls.length + 1);
  assert.equal(value.attempts[0].collection_status, 'failed');
  assert.ok(value.attempts.slice(1).every((attempt: any) => attempt.collection_status === 'quarantined'));
  assert.ok(value.attempts.every((attempt: any) => attempt.operation === 'archived'
    && attempt.publication_performed === false && attempt.site_data_written === false
    && attempt.last_successful_fetch_at === retained.last_successful_fetch_at));
  assert.deepEqual(view.snapshot.records, retained.records);
  assert.equal(view.snapshot.collection_status, 'quarantined');
  assert.equal(view.snapshot.last_successful_fetch_at, '2026-09-28T22:00:00Z');
  assert.equal(view.snapshot.last_checked_at, value.attempts.at(-1).last_checked_at);
  assert.equal(view.history.total_observations, unsafeUrls.length + 4);
  assert.equal(view.history.total_changes, 1);
  const attempts = view.history.observations.filter((observation: any) => observation.sequence > 3);
  assert.ok(attempts.every((observation: any) => observation.comparison === 'not_compared'
    && observation.change_count === 0 && observation.changes.length === 0));
  validateBundle(degraded);
  const result = buildAlertPromotionPatch(simulatedReviewEnvelope(degraded), syntheticPublicFiles(edited.views));
  assert.equal(result.report.quarantined_parks, 1);
  assert.ok(result.patch.includes('"last_successful_fetch_at": "2026-09-28T22:00:00Z"'));
  assert.equal(result.report.publication_performed, false);
});

test('rehashing unsafe path counterparts cannot bypass public snapshot, historical evidence, bundle or promotion validation', () => {
  const {baseline, edited} = fixture().bundles;
  for (const url of unsafeUrls) {
    const bundle = structuredClone(edited), view = bundle.views[0];
    view.snapshot.records[0].url = url;
    view.snapshot.records[0].content_hash = historyDigest(semantic(view.snapshot.records[0]));
    const after = view.history.observations[0].changes[0].after;
    after.url = url; after.content_hash = historyDigest(semantic(after));
    view.history.snapshot_hash = historyDigest(view.snapshot);
    assert.throws(() => validateSnapshot(view.snapshot, 'yose'), url);
    assert.throws(() => validateHistory(view.history, view.snapshot), url);
    assert.throws(() => validatePreviewBundle(rehashBundle(bundle)), url);
    assert.throws(() => buildAlertPromotionPatch(simulatedReviewEnvelope(bundle), syntheticPublicFiles(baseline.views)), url);
    const historical = structuredClone(edited.views[0]);
    historical.history.observations[0].changes[0].before.url = url;
    historical.history.observations[0].changes[0].before.content_hash = historyDigest(
      semantic(historical.history.observations[0].changes[0].before));
    assert.throws(() => validateHistory(historical.history, historical.snapshot), url);
  }
});
