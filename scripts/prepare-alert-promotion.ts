/** Offline operator review artifact. This command never applies a patch or approves data. */
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { closeSync, fstatSync, fsyncSync, lstatSync, mkdtempSync, openSync, readFileSync, readSync, rmSync, writeFileSync, linkSync } from 'node:fs';
import { dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { canonicalPreview, MAX_BUNDLE_BYTES, PILOT_CODES, readPreviewBundle, validatePreviewBundle } from './preview-bundle.ts';
import { assertSafePath } from './preview-workspace.mjs';
import { historyDigest, validateHistory } from './validate-history.ts';

const ROOT = resolve(import.meta.dirname, '..');
const MAX_PATCH_BYTES = 32 * 1024 * 1024;
const FILES = [...PILOT_CODES.map(code => `data/alerts/${code}.json`), 'data/history.json'];
function requireValue(value: unknown): asserts value {
  if (!value) throw new Error('alert_promotion_refused');
}
const sha256 = (text: string) => createHash('sha256').update(text, 'utf8').digest('hex');
export interface PublicFile { path: string; text: string }
interface RecordState { content_hash: string; observed_first_at: string; observed_changed_at: string }
function recordState(value: unknown): RecordState {
  const record = value as RecordState; // Both snapshots have already passed validateHistory.
  return {content_hash: record.content_hash, observed_first_at: record.observed_first_at, observed_changed_at: record.observed_changed_at};
}

function hunk(path: string, before: string, after: string): string {
  const lines = (text: string, prefix: string) => {
    const result = text.split('\n');
    if (result.at(-1) === '') result.pop();
    return {count: result.length, text: result.map(line => prefix + line + '\n').join('')
      + (text.endsWith('\n') ? '' : '\\ No newline at end of file\n')};
  };
  const old = lines(before, '-'), next = lines(after, '+');
  return `diff --git a/${path} b/${path}\n--- a/${path}\n+++ b/${path}\n@@ -1,${old.count} +1,${next.count} @@\n${old.text}${next.text}`;
}

export function buildAlertPromotionPatch(input: unknown, current: PublicFile[]) {
  return buildPatch(input, current);
}

function buildPatch(input: unknown, current: PublicFile[], archive?: string) {
  const bundle = validatePreviewBundle(input);
  requireValue(bundle.data_kind === 'unreviewed_source');
  requireValue(current.length === FILES.length && current.every((file, i) => file.path === FILES[i]
    && Buffer.byteLength(file.text, 'utf8') <= MAX_BUNDLE_BYTES));
  const snapshots = current.slice(0, -1).map(file => JSON.parse(file.text));
  const histories = JSON.parse(current.at(-1)!.text);
  requireValue(Array.isArray(histories) && histories.length === PILOT_CODES.length
    && new Set(histories.map(h => h.park_code)).size === PILOT_CODES.length);
  const oldHistories = bundle.views.map((view, i) => {
    requireValue(snapshots[i].park_code === PILOT_CODES[i]);
    return validateHistory(histories.find(h => h.park_code === PILOT_CODES[i]), snapshots[i]);
  });
  let archiveVerified = false;
  if (archive) {
    const request = {schema_version: 1, purpose: 'alert_archive_request', bundle_id: bundle.bundle_id,
      parks: bundle.views.map((view, i) => ({park_code: PILOT_CODES[i],
        public_snapshot_hash: historyDigest(snapshots[i]), public_history_hash: historyDigest(oldHistories[i]),
        public_total_observations: oldHistories[i].total_observations, public_visible_observations: oldHistories[i].observations.length,
        candidate_snapshot_hash: historyDigest(view.snapshot), candidate_history_hash: historyDigest(view.history),
        candidate_total_observations: view.history.total_observations, candidate_visible_observations: view.history.observations.length}))};
    const result = spawnSync('python', ['-s', '-m', 'tracker.alert_promotion_archive', '--archive-dir', archive],
      {cwd: ROOT, input: canonicalPreview(request), encoding: 'utf8', timeout: 60000, maxBuffer: 16384, shell: false,
        env: {PATH: process.env.PATH, PYTHONNOUSERSITE: '1', PYTHONDONTWRITEBYTECODE: '1'}});
    requireValue(!result.error && result.status === 0 && result.stderr === '');
    const proof = JSON.parse(result.stdout);
    requireValue(canonicalPreview(proof) === canonicalPreview({schema_version: 1, purpose: 'alert_archive_continuity',
      request_hash: historyDigest(request), bundle_id: bundle.bundle_id, verified_parks: PILOT_CODES.length, publication_performed: false}));
    archiveVerified = true;
  }
  bundle.views.forEach((view, i) => {
    const old = oldHistories[i];
    const next = view.history;
    requireValue(next.total_observations >= old.total_observations);
    if (next.total_observations === old.total_observations) {
      requireValue(next.head_observation_id === old.head_observation_id
        && next.snapshot_hash === old.snapshot_hash && historyDigest(next) === historyDigest(old));
    } else if (old.total_observations > 0 && !archiveVerified) {
      // A bounded projection must still contain the published checkpoint. Refuse a
      // gap rather than infer ancestry from a newer clock or a larger count alone.
      const checkpoint = next.observations.find(o => o.sequence === old.total_observations);
      requireValue(checkpoint && canonicalPreview(checkpoint) === canonicalPreview(old.observations[0]));
      const oldestVisible = next.observations.at(-1)!.sequence;
      for (const observation of old.observations.filter(o => o.sequence >= oldestVisible)) {
        requireValue(canonicalPreview(next.observations.find(o => o.sequence === observation.sequence))
          === canonicalPreview(observation));
      }
      const newer = next.observations.filter(o => o.sequence > old.total_observations);
      requireValue(next.total_changes === old.total_changes + newer.reduce((sum, o) => sum + o.change_count, 0));
      if (snapshots[i].last_successful_fetch_at !== null) {
        const state = new Map<string, RecordState>(snapshots[i].records.map((r: any) => [r.id, recordState(r)]));
        for (const observation of newer.toReversed()) {
          requireValue(observation.omitted_changes === 0 && observation.comparison !== 'baseline');
          for (const change of observation.changes) {
            const before = state.get(change.record_id);
            requireValue(change.before === null ? !before : before?.content_hash === change.before.content_hash);
            if (change.after === null) state.delete(change.record_id);
            else state.set(change.record_id, {content_hash: change.after.content_hash,
              observed_first_at: before?.observed_first_at ?? observation.checked_at,
              observed_changed_at: observation.checked_at});
          }
        }
        requireValue(view.snapshot.records.length === state.size && view.snapshot.records.every(record =>
          canonicalPreview(state.get(record.id)) === canonicalPreview(recordState(record))));
      }
    }
    if (view.snapshot.last_successful_fetch_at === snapshots[i].last_successful_fetch_at) {
      requireValue(historyDigest(view.snapshot.records) === historyDigest(snapshots[i].records));
    }
  });
  const values = [...bundle.views.map(view => view.snapshot), bundle.views.map(view => view.history)];
  const changes = current.flatMap((file, i) => {
    if (historyDigest(JSON.parse(file.text)) === historyDigest(values[i])) return [];
    return [hunk(file.path, file.text, JSON.stringify(values[i], null, 2) + '\n')];
  });
  requireValue(changes.length > 0);
  const header = ['ParkReadiness alert-data candidate: HUMAN REVIEW REQUIRED',
    'Preparation performs no approval, public-data write or publication.',
    `Source preview bundle: ${bundle.bundle_id}`,
    `Continuity verification: ${archiveVerified ? 'verified private archive' : 'bounded preview'}`,
    ...current.map(file => `Base SHA-256 ${file.path}: ${sha256(file.text)}`), '', ''].join('\n');
  const patch = header + changes.join('');
  requireValue(Buffer.byteLength(patch, 'utf8') <= MAX_PATCH_BYTES);
  return {patch, report: {candidate_id: sha256(patch), bundle_id: bundle.bundle_id,
    archive_continuity_verified: archiveVerified, verified_archive_parks: archiveVerified ? PILOT_CODES.length : 0,
    changed_files: changes.length, never_checked_parks: bundle.views.filter(v => v.snapshot.collection_status === 'never_checked').length,
    failed_parks: bundle.views.filter(v => v.snapshot.collection_status === 'failed').length,
    quarantined_parks: bundle.views.filter(v => v.snapshot.collection_status === 'quarantined').length,
    human_review_required: true, publication_performed: false, production_data_written: false}};
}

function outsideRepository(path: string) {
  requireValue(isAbsolute(path) && path === resolve(path));
  const child = relative(ROOT, path), ancestor = relative(path, ROOT);
  requireValue(child.startsWith('..' + '/') && ancestor.startsWith('..' + '/'));
  assertSafePath(path);
}
function privateStat(path: string, directory = false) {
  const stat = lstatSync(path);
  requireValue((directory ? stat.isDirectory() : stat.isFile()) && stat.uid === process.getuid!()
    && (stat.mode & 0o077) === 0 && (directory || stat.nlink === 1));
  return stat;
}

function loadPromotion(bundlePath: string, output: string, archive?: string) {
  requireValue(process.platform !== 'win32' && typeof process.getuid === 'function');
  outsideRepository(bundlePath); outsideRepository(output);
  requireValue(bundlePath !== output);
  privateStat(dirname(bundlePath), true); privateStat(bundlePath);
  privateStat(dirname(output), true);
  if (archive !== undefined) {
    outsideRepository(archive); privateStat(archive, true);
    for (const path of [bundlePath, output]) {
      requireValue(relative(archive, path).startsWith('../') && relative(path, archive).startsWith('../'));
    }
  }
  const bundle = readPreviewBundle(bundlePath);
  const current = FILES.map(path => {
    const absolute = join(ROOT, path); assertSafePath(absolute);
    const stat = lstatSync(absolute);
    requireValue(stat.isFile() && stat.size <= MAX_BUNDLE_BYTES);
    const raw = readFileSync(absolute);
    requireValue(raw.length <= MAX_BUNDLE_BYTES);
    return {path, text: new TextDecoder('utf-8', {fatal: true, ignoreBOM: true}).decode(raw)};
  });
  return buildPatch(bundle, current, archive);
}

function readPrivatePatch(path: string): Buffer {
  const before = privateStat(path);
  requireValue(before.size <= MAX_PATCH_BYTES);
  const fd = openSync(path, 'r');
  try {
    const stat = fstatSync(fd);
    requireValue(stat.isFile() && stat.dev === before.dev && stat.ino === before.ino
      && stat.uid === process.getuid!() && (stat.mode & 0o077) === 0 && stat.nlink === 1 && stat.size <= MAX_PATCH_BYTES);
    const bytes = Buffer.alloc(stat.size + 1);
    let offset = 0;
    while (offset < bytes.length) {
      const count = readSync(fd, bytes, offset, bytes.length - offset, null);
      if (!count) break;
      offset += count;
    }
    requireValue(offset === stat.size);
    return bytes.subarray(0, offset);
  } finally { closeSync(fd); }
}

export function checkAlertPromotion(bundlePath: string, patchPath: string, candidateId: string, archive?: string) {
  requireValue(typeof candidateId === 'string' && /^[a-f0-9]{64}$/.test(candidateId));
  // Share the exact path, bundle, public-base and continuity checks with preparation.
  const result = loadPromotion(bundlePath, patchPath, archive);
  const bytes = readPrivatePatch(patchPath);
  requireValue(createHash('sha256').update(bytes).digest('hex') === candidateId
    && result.report.candidate_id === candidateId && bytes.equals(Buffer.from(result.patch, 'utf8')));
  return {...result.report, mode: 'alert_promotion_check', public_base_files_checked: FILES.length, patch_bytes_matched: true};
}

export function prepareAlertPromotion(bundlePath: string, output: string, archive?: string) {
  const result = loadPromotion(bundlePath, output, archive);
  try {
    requireValue(readPrivatePatch(output).equals(Buffer.from(result.patch, 'utf8')));
    return result.report; // Exact retries preserve the existing bytes and timestamp.
  } catch (error) { if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error; }
  const temporary = mkdtempSync(join(dirname(output), '.alert-candidate-'));
  try {
    const file = join(temporary, 'candidate.patch'), fd = openSync(file, 'wx', 0o600);
    try { writeFileSync(fd, result.patch, 'utf8'); fsyncSync(fd); } finally { closeSync(fd); }
    linkSync(file, output); // Atomic installation that refuses any existing destination.
  } finally { rmSync(temporary, {recursive: true, force: true}); }
  const fd = openSync(dirname(output), 'r');
  try { fsyncSync(fd); } finally { closeSync(fd); }
  return result.report;
}

export function main(args: string[]): number {
  try {
    if (args[0] === '--check') {
      requireValue((args.length === 7 || (args.length === 9 && args[7] === '--archive-dir'))
        && args[1] === '--bundle' && args[3] === '--patch' && args[5] === '--candidate-id');
      console.log(JSON.stringify(checkAlertPromotion(args[2], args[4], args[6], args[8])));
    } else {
      requireValue((args.length === 4 || (args.length === 6 && args[4] === '--archive-dir'))
        && args[0] === '--bundle' && args[2] === '--output');
      console.log(JSON.stringify(prepareAlertPromotion(args[1], args[3], args[5])));
    }
    return 0;
  } catch {
    console.error('Alert-data candidate preparation/check refused; inspect the private bundle, public pairs and patch destination. No production data was written.');
    return 2;
  }
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) process.exitCode = main(process.argv.slice(2));
