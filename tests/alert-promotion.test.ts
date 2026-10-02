import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdtempSync, rmSync, readdirSync, mkdirSync, copyFileSync, cpSync, chmodSync, statSync, symlinkSync, linkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { canonicalPreview } from '../scripts/preview-bundle.ts';
import { historyDigest } from '../scripts/validate-history.ts';
import { buildAlertPromotionPatch } from '../scripts/prepare-alert-promotion.ts';
import { createSyntheticPromotionProject, syntheticEmptyViews, syntheticPublicFiles } from './synthetic-preview.ts';

const root = resolve(import.meta.dirname, '..');
const json = (path: string) => JSON.parse(readFileSync(join(root, path), 'utf8'));
const mixed = json('tests/fixtures/history-preview.json').cases.mixed;
const fixtures = json('tests/fixtures/history-preview.json').cases;
function candidate(kind = 'unreviewed_source') {
  const views = syntheticEmptyViews();
  views[0] = structuredClone(mixed);
  const body = {schema_version: 1, purpose: 'private_preview', data_kind: kind, publication_performed: false, views};
  return {...body, bundle_id: historyDigest(body)};
}
function temporary(fn: (dir: string) => void) {
  const dir = mkdtempSync(join(tmpdir(), 'alert-promotion-'));
  try { fn(dir); } finally { rmSync(dir, {recursive: true, force: true}); }
}
function run(bundle: string, output: string, project: string, archive?: string) {
  return spawnSync(process.execPath, ['--experimental-strip-types', join(project, 'scripts/prepare-alert-promotion.ts'),
    '--bundle', bundle, '--output', output, ...(archive ? ['--archive-dir', archive] : [])], {cwd: project, encoding: 'utf8', timeout: 65000});
}
const currentFiles = () => syntheticPublicFiles();
function withView(view: any) {
  const value = candidate(); value.views[0] = structuredClone(view);
  const {bundle_id, ...body} = value; return {...body, bundle_id: historyDigest(body)};
}
function publicCheckpoint(view: any) {
  const files = currentFiles(), histories = JSON.parse(files.at(-1)!.text);
  files[0].text = JSON.stringify(view.snapshot, null, 2) + '\n';
  histories[0] = view.history; files.at(-1)!.text = JSON.stringify(histories, null, 2) + '\n';
  return files;
}

function initialFailureCheckpoint(status: 'failed' | 'quarantined', bounded: boolean) {
  const view = structuredClone(fixtures.empty);
  Object.assign(view.snapshot, {collection_status: status, coverage_status: 'incomplete',
    error_code: status === 'failed' ? 'provider_request_failed' : 'response_requires_review',
    last_checked_at: '2026-09-28T09:00:00Z'});
  const observation = {observation_id: 'd'.repeat(64), sequence: bounded ? 2 : 1,
    checked_at: view.snapshot.last_checked_at, collection_status: status, comparison: 'not_compared',
    change_count: 0, omitted_changes: 0, changes: []};
  Object.assign(view.history, {head_observation_id: observation.observation_id,
    snapshot_hash: historyDigest(view.snapshot), total_observations: observation.sequence,
    omitted_observations: bounded ? 1 : 0, observations: [observation]});
  return view;
}

function firstSuccessView(checkpoint: any, comparison: 'baseline' | 'compared', change: 'none' | 'added' | 'edited' = 'none') {
  const view = structuredClone(fixtures.baseline), head = view.history.observations[0];
  head.sequence = checkpoint.history.total_observations + 1; head.comparison = comparison;
  const semanticFields = ['category', 'description', 'id', 'title', 'url'];
  const evidence = (record: any) => Object.fromEntries([...semanticFields, 'content_hash'].map(key => [key, record[key]]));
  if (change === 'added') {
    head.changes = view.snapshot.records.map((record: any) => ({kind: 'added', record_id: record.id, before: null, after: evidence(record)}));
  } else if (change === 'edited') {
    const after = evidence(view.snapshot.records[0]);
    const before: Record<string, unknown> = {...after, title: 'Synthetic unobserved earlier title'};
    before.content_hash = historyDigest(Object.fromEntries(semanticFields.map(key => [key, before[key]])));
    head.changes = [{kind: 'edited', record_id: after.id, before, after}];
  }
  head.change_count = head.changes.length;
  Object.assign(view.history, {total_observations: head.sequence, total_changes: head.change_count,
    omitted_observations: checkpoint.history.omitted_observations,
    observations: [head, ...structuredClone(checkpoint.history.observations)]});
  return view;
}

test('first-success promotion accepts baseline controls after initial failed and quarantined checkpoints', () => {
  for (const bounded of [true, false]) for (const status of ['failed', 'quarantined'] as const) {
    const checkpoint = initialFailureCheckpoint(status, bounded), view = firstSuccessView(checkpoint, 'baseline');
    const bundle = withView(view), files = publicCheckpoint(checkpoint), before = structuredClone({bundle, files});
    const result = buildAlertPromotionPatch(bundle, files);
    assert.equal(result.report.changed_files, 2);
    assert.equal(result.report.publication_performed, false);
    assert.equal(result.report.production_data_written, false);
    assert.ok(result.patch.includes('+  "last_successful_fetch_at": "2026-09-28T10:00:00Z"'));
    assert.deepEqual({bundle, files}, before);
  }
});

test('first-success promotion refuses zero-change comparisons against known-null checkpoints', () => {
  for (const bounded of [true, false]) for (const status of ['failed', 'quarantined'] as const) {
    const checkpoint = initialFailureCheckpoint(status, bounded);
    assert.throws(() => buildAlertPromotionPatch(withView(firstSuccessView(checkpoint, 'compared')), publicCheckpoint(checkpoint)),
      `${status}, bounded=${bounded}`);
  }
});

test('first-success promotion refuses fabricated added and edited comparisons against known-null checkpoints', () => {
  for (const bounded of [true, false]) for (const status of ['failed', 'quarantined'] as const) for (const change of ['added', 'edited'] as const) {
    const checkpoint = initialFailureCheckpoint(status, bounded);
    assert.throws(() => buildAlertPromotionPatch(withView(firstSuccessView(checkpoint, 'compared', change)), publicCheckpoint(checkpoint)),
      `${status}, bounded=${bounded}, ${change}`);
  }
});

for (const changed of [false, true]) test(`first-success promotion accepts subsequent ${changed ? 'changed' : 'unchanged'} comparisons and retained clocks`, () => {
  for (const bounded of [true, false]) for (const status of ['failed', 'quarantined'] as const) {
    const checkpoint = initialFailureCheckpoint(status, bounded);
    const view = structuredClone(changed ? fixtures.failed : fixtures.baseline);
    if (!changed) {
      view.snapshot.collection_status = 'failed'; view.snapshot.coverage_status = 'incomplete';
      view.snapshot.error_code = 'provider_request_failed'; view.snapshot.last_checked_at = '2026-09-28T14:00:00Z';
      view.snapshot.last_successful_fetch_at = '2026-09-28T12:00:00Z';
      const baseline = view.history.observations[0];
      const compared = {...structuredClone(baseline), observation_id: 'b'.repeat(64),
        checked_at: view.snapshot.last_successful_fetch_at, comparison: 'compared'};
      const failed = {...structuredClone(baseline), observation_id: 'a'.repeat(64),
        checked_at: view.snapshot.last_checked_at, collection_status: 'failed', comparison: 'not_compared'};
      view.history.observations = [failed, compared, baseline];
      view.history.head_observation_id = failed.observation_id;
    }
    const between = {...structuredClone(checkpoint.history.observations[0]), observation_id: 'e'.repeat(64),
      checked_at: '2026-09-28T11:00:00Z'};
    view.history.observations.splice(2, 0, between);
    view.history.observations.push(...structuredClone(checkpoint.history.observations));
    view.history.total_observations = checkpoint.history.total_observations + 4;
    view.history.omitted_observations = checkpoint.history.omitted_observations;
    view.history.observations.forEach((observation: any, index: number) => { observation.sequence = view.history.total_observations - index; });
    view.history.snapshot_hash = historyDigest(view.snapshot);
    const bundle = withView(view), files = publicCheckpoint(checkpoint), before = structuredClone({bundle, files});
    const result = buildAlertPromotionPatch(bundle, files);
    assert.equal(result.report.failed_parks, 1);
    assert.ok(result.patch.includes('+  "last_successful_fetch_at": "2026-09-28T12:00:00Z"'));
    assert.ok(result.patch.includes('"observed_first_at": "2026-09-28T10:00:00Z"'));
    assert.ok(result.patch.includes(`"observed_changed_at": "2026-09-28T${changed ? '12' : '10'}:00:00Z"`));
    assert.deepEqual({bundle, files}, before);
  }
});

test('offline CLI creates a private patch that applies matching snapshots and histories together', () => temporary(dir => {
  const project = createSyntheticPromotionProject(dir);
  const bundle = join(dir, 'bundle.json'), output = join(dir, 'candidate.patch');
  writeFileSync(bundle, canonicalPreview(candidate()), {mode: 0o600});
  const paths = currentFiles().map(file => file.path);
  const before = paths.map(path => readFileSync(join(project, path)));
  const production = paths.map(path => readFileSync(join(root, path)));
  const result = run(bundle, output, project);
  assert.equal(result.status, 0, result.stderr);
  const report = JSON.parse(result.stdout);
  assert.equal(report.publication_performed, false);
  assert.equal(report.production_data_written, false);
  assert.equal(report.never_checked_parks, 4);
  assert.doesNotMatch(result.stdout, /Synthetic|description|alert-promotion-/);
  const patch = readFileSync(output, 'utf8');
  assert.match(patch, /diff --git a\/data\/alerts\/yose.json b\/data\/alerts\/yose.json/);
  assert.match(patch, /diff --git a\/data\/history.json b\/data\/history.json/);
  paths.forEach((path, index) => {
    assert.deepEqual(readFileSync(join(project, path)), before[index]);
    assert.deepEqual(readFileSync(join(root, path)), production[index]);
  });
  // Apply only to a disposable copy; verify the actual Git patch and pairing contract.
  const sandbox = join(dir, 'copy');
  mkdirSync(join(sandbox, 'data/alerts'), {recursive: true});
  for (const path of paths) copyFileSync(join(project, path), join(sandbox, path));
  const applied = spawnSync('git', ['apply', output], {cwd: sandbox, encoding: 'utf8'});
  assert.equal(applied.status, 0, applied.stderr);
  assert.deepEqual(JSON.parse(readFileSync(join(sandbox, 'data/alerts/yose.json'), 'utf8')), mixed.snapshot);
  assert.deepEqual(JSON.parse(readFileSync(join(sandbox, 'data/history.json'), 'utf8'))[0], mixed.history);
  assert.equal(JSON.parse(readFileSync(join(sandbox, 'data/alerts/romo.json'), 'utf8')).collection_status, 'never_checked');
}));

test('synthetic bundle is refused without output or source-text diagnostics', () => temporary(dir => {
  const project = createSyntheticPromotionProject(dir);
  const bundle = join(dir, 'bundle.json'), output = join(dir, 'candidate.patch');
  writeFileSync(bundle, canonicalPreview(candidate('synthetic')), {mode: 0o600});
  const result = run(bundle, output, project);
  assert.equal(result.status, 2);
  assert.equal(result.stdout, '');
  assert.doesNotMatch(result.stderr, /Synthetic|alert-promotion-/);
  assert.deepEqual(readdirSync(dir).sort(), ['bundle.json', 'project']);
}));

test('failed and quarantined candidates preserve last-good timestamps and status in the patch', () => {
  for (const name of ['failed', 'quarantined']) {
    const view = structuredClone(fixtures.failed);
    if (name === 'quarantined') {
      view.snapshot.collection_status = 'quarantined'; view.snapshot.error_code = 'response_requires_review';
      view.history.observations[0].collection_status = 'quarantined';
      view.history.snapshot_hash = historyDigest(view.snapshot);
    }
    const value = withView(view);
    const result = buildAlertPromotionPatch(value, currentFiles());
    assert.match(result.patch, new RegExp(`\\+  "collection_status": "${name}"`));
    assert.ok(result.patch.includes(`+  "last_successful_fetch_at": "${view.snapshot.last_successful_fetch_at}"`));
    assert.equal(result.report[name === 'failed' ? 'failed_parks' : 'quarantined_parks'], 1);
  }
});

test('older snapshots, changed heads at equal sequence and mismatched pairs cannot form a patch', () => {
  assert.throws(() => buildAlertPromotionPatch(withView(fixtures.baseline), publicCheckpoint(mixed)));
  const fork = withView(mixed);
  fork.views[0].history.head_observation_id = 'a'.repeat(64);
  fork.views[0].history.observations[0].observation_id = 'a'.repeat(64);
  const {bundle_id, ...body} = fork; fork.bundle_id = historyDigest(body);
  assert.throws(() => buildAlertPromotionPatch(fork, publicCheckpoint(mixed)));
  const mismatched = candidate(); mismatched.views[0].history = fixtures.baseline.history;
  const {bundle_id: ignored, ...badBody} = mismatched; mismatched.bundle_id = historyDigest(badBody);
  assert.throws(() => buildAlertPromotionPatch(mismatched, currentFiles()));
});

test('a descendant must retain the complete published checkpoint rather than just a larger count', () => {
  assert.doesNotThrow(() => buildAlertPromotionPatch(candidate(), publicCheckpoint(fixtures.baseline)));
  const value = candidate();
  const checkpoint = value.views[0].history.observations.find((o: any) => o.sequence === 1);
  checkpoint.observation_id = 'b'.repeat(64);
  const {bundle_id, ...body} = value; value.bundle_id = historyDigest(body);
  assert.throws(() => buildAlertPromotionPatch(value, publicCheckpoint(fixtures.baseline)));
  assert.throws(() => buildAlertPromotionPatch(withView(fixtures.truncated), publicCheckpoint(fixtures.baseline)));
});

test('a newer candidate cannot rewrite any overlapping published observation', () => {
  const value = withView(fixtures.failed);
  value.views[0].history.observations[2].observation_id = 'c'.repeat(64);
  const {bundle_id, ...body} = value; value.bundle_id = historyDigest(body);
  assert.throws(() => buildAlertPromotionPatch(value, publicCheckpoint(mixed)));
});

test('failed candidates cannot relabel the retained records when the successful check has not advanced', () => {
  const value = withView(fixtures.failed);
  value.views[0].snapshot.records[0].observed_first_at = value.views[0].snapshot.last_successful_fetch_at;
  value.views[0].history.snapshot_hash = historyDigest(value.views[0].snapshot);
  const {bundle_id, ...body} = value; value.bundle_id = historyDigest(body);
  assert.throws(() => buildAlertPromotionPatch(value, publicCheckpoint(mixed)));
});

test('a descendant cannot remove published records without the matching removal events', () => {
  const view = structuredClone(mixed);
  view.snapshot.records = [];
  view.history.observations[0].changes = [];
  view.history.observations[0].change_count = 0;
  view.history.total_changes = 0;
  view.history.snapshot_hash = historyDigest(view.snapshot);
  assert.throws(() => buildAlertPromotionPatch(withView(view), publicCheckpoint(fixtures.baseline)));
});

test('a later successful check preserves first-observation clocks on records that survive it', () => {
  const view = structuredClone(mixed);
  view.snapshot.records[0].observed_first_at = view.snapshot.last_checked_at;
  view.history.snapshot_hash = historyDigest(view.snapshot);
  assert.throws(() => buildAlertPromotionPatch(withView(view), publicCheckpoint(fixtures.baseline)));
  assert.doesNotThrow(() => buildAlertPromotionPatch(withView(fixtures.failed), publicCheckpoint(fixtures.baseline)));
});

test('a truncated descendant cannot erase cumulative changes already published', () => {
  const view = structuredClone(fixtures.truncated);
  view.snapshot.last_checked_at = '2026-09-28T16:00:00Z';
  view.history.snapshot_hash = historyDigest(view.snapshot);
  const next = {...structuredClone(view.history.observations[0]), observation_id: 'd'.repeat(64),
    sequence: 4, checked_at: '2026-09-28T16:00:00Z', change_count: 0, omitted_changes: 0, changes: []};
  view.history.observations.unshift(next);
  view.history.head_observation_id = next.observation_id;
  view.history.total_observations = 4;
  view.history.total_changes = 0; view.history.omitted_changes = 0;
  assert.throws(() => buildAlertPromotionPatch(withView(view), publicCheckpoint(fixtures.truncated)));
});

test('an unchanged public dataset produces no empty approval artifact', () => {
  assert.throws(() => buildAlertPromotionPatch(candidate(), publicCheckpoint(mixed)));
});

test('current public inventory cannot be empty, duplicated or mismatched', () => {
  for (const change of [
    (files: any[]) => files.pop(),
    (files: any[]) => { files[1].text = files[0].text; },
    (files: any[]) => { files.at(-1).text = '[]'; },
    (files: any[]) => { const h = JSON.parse(files.at(-1).text); h[1] = h[0]; files.at(-1).text = JSON.stringify(h); },
  ]) {
    const files = currentFiles(); change(files);
    assert.throws(() => buildAlertPromotionPatch(candidate(), files));
  }
});

test('patch uses original bytes for stale-base refusal and handles a missing final newline', () => temporary(dir => {
  const files = currentFiles(); files[0].text = files[0].text.trimEnd();
  const output = join(dir, 'candidate.patch');
  writeFileSync(output, buildAlertPromotionPatch(candidate(), files).patch);
  mkdirSync(join(dir, 'data/alerts'), {recursive: true});
  for (const file of files) writeFileSync(join(dir, file.path), file.text);
  let result = spawnSync('git', ['apply', '--check', output], {cwd: dir, encoding: 'utf8'});
  assert.equal(result.status, 0, result.stderr);
  writeFileSync(join(dir, files[0].path), files[0].text.replace('never_checked', 'failed'));
  result = spawnSync('git', ['apply', '--check', output], {cwd: dir, encoding: 'utf8'});
  assert.notEqual(result.status, 0);
}));

test('exact retries are immutable and conflicting destinations are never overwritten', () => temporary(dir => {
  const project = createSyntheticPromotionProject(dir);
  const bundle = join(dir, 'bundle.json'), output = join(dir, 'candidate.patch');
  writeFileSync(bundle, canonicalPreview(candidate()), {mode: 0o600});
  assert.equal(run(bundle, output, project).status, 0);
  const before = statSync(output).mtimeMs, bytes = readFileSync(output);
  assert.equal(run(bundle, output, project).status, 0);
  assert.equal(statSync(output).mtimeMs, before);
  assert.equal(statSync(output).mode & 0o077, 0);
  writeFileSync(output, 'retained conflicting bytes');
  assert.equal(run(bundle, output, project).status, 2);
  assert.equal(readFileSync(output, 'utf8'), 'retained conflicting bytes');
  assert.equal(readdirSync(dir).length, 3);
  assert.ok(bytes.length > 0);
}));

test('a retry refuses corrupt UTF-8 bytes even when lossy decoding would preserve the apparent text', () => temporary(dir => {
  const project = createSyntheticPromotionProject(dir);
  const value = withView(fixtures.baseline), record = value.views[0].snapshot.records[0];
  record.description += '\uFFFD'; record.evidence_excerpt = record.description;
  record.content_hash = historyDigest({id: record.id, title: record.title, description: record.description, url: record.url, category: record.category});
  value.views[0].history.snapshot_hash = historyDigest(value.views[0].snapshot);
  const {bundle_id, ...body} = value; value.bundle_id = historyDigest(body);
  const bundle = join(dir, 'bundle.json'), output = join(dir, 'candidate.patch');
  writeFileSync(bundle, canonicalPreview(value), {mode: 0o600});
  assert.equal(run(bundle, output, project).status, 0);
  const bytes = readFileSync(output), position = bytes.indexOf(Buffer.from('\uFFFD'));
  assert.ok(position > 0);
  const corrupt = Buffer.concat([bytes.subarray(0, position), Buffer.from([0xff]), bytes.subarray(position + 3)]);
  writeFileSync(output, corrupt);
  assert.equal(run(bundle, output, project).status, 2);
  assert.deepEqual(readFileSync(output), corrupt);
}));

test('checkout destinations, public parents and unsafe input aliases refuse without writes', () => temporary(dir => {
  const project = createSyntheticPromotionProject(dir);
  const bundle = join(dir, 'bundle.json'), output = join(dir, 'candidate.patch');
  writeFileSync(bundle, canonicalPreview(candidate()), {mode: 0o600});
  for (const destination of [join(project, 'dist-pages/private.patch'), join(project, 'state/private.patch'), dirname(project), 'relative.patch']) {
    assert.equal(run(bundle, destination, project).status, 2);
  }
  chmodSync(bundle, 0o644); assert.equal(run(bundle, output, project).status, 2);
  chmodSync(bundle, 0o600);
  chmodSync(dir, 0o755); assert.equal(run(bundle, output, project).status, 2);
  chmodSync(dir, 0o700);
  const alias = join(dir, 'alias.json'); symlinkSync(bundle, alias);
  assert.equal(run(alias, output, project).status, 2);
  rmSync(alias); linkSync(bundle, alias);
  assert.equal(run(bundle, output, project).status, 2);
  assert.deepEqual(readdirSync(dir).sort(), ['alias.json', 'bundle.json', 'project']);
}));

function archivedScenario(dir: string, scenario: string) {
  const generated = spawnSync('python', [join(root, 'tests/promotion_archive_fixture.py'), dir, scenario],
    {cwd: root, encoding: 'utf8', env: {...process.env, PYTHONPATH: root}, timeout: 60000});
  assert.equal(generated.status, 0, generated.stderr);
  assert.equal(statSync(join(dir, 'archive/parks')).mode & 0o077, 0, 'operator fixture archive directories must be owner-only');
  const project = join(dir, 'project'); mkdirSync(join(project, 'data/alerts'), {recursive: true});
  for (const folder of ['scripts', 'src/lib', 'tracker']) cpSync(join(root, folder), join(project, folder), {recursive: true});
  copyFileSync(join(root, 'package.json'), join(project, 'package.json'));
  const publicViews = JSON.parse(readFileSync(join(dir, 'public.json'), 'utf8'));
  for (const view of publicViews) writeFileSync(join(project, `data/alerts/${view.snapshot.park_code}.json`), JSON.stringify(view.snapshot, null, 2) + '\n');
  writeFileSync(join(project, 'data/history.json'), JSON.stringify(publicViews.map((view: any) => view.history), null, 2) + '\n');
  return {project, archive: join(dir, 'archive'), bundle: join(dir, 'bundle.json'), output: join(dir, 'candidate.patch')};
}

test('bounded degraded windows retain the success clock even when every successful observation is omitted', () => temporary(dir => {
  const {project, bundle, output} = archivedScenario(dir, 'hidden-success');
  const original = readFileSync(bundle), value = JSON.parse(original.toString('utf8'));
  assert.equal(value.views[0].history.observations.some((o: any) => o.collection_status === 'success'), false);
  assert.equal(run(bundle, output, project).status, 0);
  const retained = readFileSync(output);
  for (const clock of ['2026-09-28T10:00:00Z', '2026-09-28T12:00:00Z', null]) {
    value.views[0].snapshot.last_successful_fetch_at = clock;
    value.views[0].history.snapshot_hash = historyDigest(value.views[0].snapshot);
    const {bundle_id, ...body} = value; value.bundle_id = historyDigest(body);
    writeFileSync(bundle, canonicalPreview(value));
    const altered = join(dir, 'altered.patch');
    const result = run(bundle, altered, project);
    assert.equal(result.status, 2, `changed success clock ${clock}`);
    assert.equal(result.stdout, '');
    assert.equal(readdirSync(dir).includes('altered.patch'), false);
    assert.deepEqual(readFileSync(output), retained);
  }
}));

test('bounded degraded windows cannot invent a first successful fetch', () => temporary(dir => {
  const {project, bundle, output} = archivedScenario(dir, 'no-success');
  const value = JSON.parse(readFileSync(bundle, 'utf8'));
  assert.equal(value.views[0].snapshot.last_successful_fetch_at, null);
  assert.equal(run(bundle, output, project).status, 0);
  value.views[0].snapshot.last_successful_fetch_at = '2026-09-28T11:00:00Z';
  value.views[0].history.snapshot_hash = historyDigest(value.views[0].snapshot);
  const {bundle_id, ...body} = value; value.bundle_id = historyDigest(body);
  writeFileSync(bundle, canonicalPreview(value));
  assert.equal(run(bundle, join(dir, 'altered.patch'), project).status, 2);
  assert.equal(readdirSync(dir).includes('altered.patch'), false);
}));

test('a verified archive supplies a published checkpoint outside the visible preview window', () => temporary(dir => {
  const {project, archive, bundle, output} = archivedScenario(dir, 'window');
  assert.equal(run(bundle, output, project).status, 2);
  const result = run(bundle, output, project, archive);
  assert.equal(result.status, 0, result.stderr);
  const report = JSON.parse(result.stdout);
  assert.equal(report.archive_continuity_verified, true);
  assert.equal(report.verified_archive_parks, 5);
  assert.equal(report.failed_parks, 1);
  assert.equal(report.publication_performed, false);
  assert.doesNotMatch(result.stdout, /Synthetic|description|alert-promotion-/);
  const applied = spawnSync('git', ['apply', output], {cwd: project, encoding: 'utf8'});
  assert.equal(applied.status, 0, applied.stderr);
  const history = JSON.parse(readFileSync(join(project, 'data/history.json'), 'utf8'))[0];
  assert.equal(history.total_observations, 25);
  assert.equal(history.omitted_observations, 5);
}));

test('a verified archive supplies full changes while the public preview keeps its omission labels', () => temporary(dir => {
  const {project, archive, bundle, output} = archivedScenario(dir, 'changes');
  assert.equal(run(bundle, output, project).status, 2);
  const result = run(bundle, output, project, archive);
  assert.equal(result.status, 0, result.stderr);
  const applied = spawnSync('git', ['apply', output], {cwd: project, encoding: 'utf8'});
  assert.equal(applied.status, 0, applied.stderr);
  const history = JSON.parse(readFileSync(join(project, 'data/history.json'), 'utf8'))[0];
  assert.equal(history.total_changes, 120);
  assert.equal(history.observations[0].changes.length, 100);
  assert.equal(history.omitted_changes, 20);
}));

test('archive verification rejects an otherwise valid public checkpoint from a different chain', () => temporary(dir => {
  const {project, archive, bundle, output} = archivedScenario(dir, 'window');
  const path = join(project, 'data/history.json'), history = JSON.parse(readFileSync(path, 'utf8'));
  history[0].head_observation_id = 'e'.repeat(64); history[0].observations[0].observation_id = 'e'.repeat(64);
  writeFileSync(path, JSON.stringify(history, null, 2) + '\n');
  const before = readFileSync(path);
  const result = run(bundle, output, project, archive);
  assert.equal(result.status, 2); assert.equal(result.stdout, '');
  assert.doesNotMatch(result.stderr, /Synthetic|alert-promotion-|Traceback/);
  assert.deepEqual(readFileSync(path), before);
  assert.equal(readdirSync(dir).includes('candidate.patch'), false);
}));

test('a matching archive never approves changed candidate fields or insecure archive storage', () => temporary(dir => {
  const {project, archive, bundle, output} = archivedScenario(dir, 'window');
  const original = readFileSync(bundle), value = JSON.parse(original.toString('utf8'));
  value.views[0].snapshot.records[0].observed_first_at = value.views[0].snapshot.last_successful_fetch_at.replace('10:00', '09:00');
  value.views[0].history.snapshot_hash = historyDigest(value.views[0].snapshot);
  const {bundle_id, ...body} = value; value.bundle_id = historyDigest(body);
  writeFileSync(bundle, canonicalPreview(value));
  assert.equal(run(bundle, output, project, archive).status, 2);
  writeFileSync(bundle, original);
  chmodSync(join(archive, 'parks/yose/head.json'), 0o644);
  assert.equal(run(bundle, output, project, archive).status, 2);
  chmodSync(join(archive, 'parks/yose/head.json'), 0o600);
  assert.equal(run(bundle, join(archive, 'candidate.patch'), project, archive).status, 2);
  assert.equal(readdirSync(dir).includes('candidate.patch'), false);
}));

test('caller Python settings and provider keys cannot affect the archive verifier environment', () => temporary(dir => {
  const {project, archive, bundle, output} = archivedScenario(dir, 'window');
  const result = spawnSync(process.execPath, ['--experimental-strip-types', join(project, 'scripts/prepare-alert-promotion.ts'),
    '--bundle', bundle, '--output', output, '--archive-dir', archive], {cwd: project, encoding: 'utf8', timeout: 65000,
    env: {...process.env, PYTHONHOME: '/synthetic/missing-python-home', PYTHONPATH: '/synthetic/untrusted-modules', NPS_API_KEY: 'synthetic-provider-key'}});
  assert.equal(result.status, 0, result.stderr);
  assert.equal(JSON.parse(result.stdout).archive_continuity_verified, true);
  assert.doesNotMatch(result.stdout + result.stderr, /synthetic-provider-key|untrusted-modules|missing-python-home/);
}));
