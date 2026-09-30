import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { chmodSync, copyFileSync, cpSync, linkSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, statSync, symlinkSync, truncateSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { canonicalPreview, PILOT_CODES } from '../scripts/preview-bundle.ts';
import { historyDigest } from '../scripts/validate-history.ts';

const root = resolve(import.meta.dirname, '..');
const hash = (bytes: Buffer) => createHash('sha256').update(bytes).digest('hex');
const publicPaths = [...PILOT_CODES.map(code => `data/alerts/${code}.json`), 'data/history.json'];
function temporary(fn: (dir: string) => void) {
  const dir = mkdtempSync(join(tmpdir(), 'alert-check-'));
  try { fn(dir); } finally { rmSync(dir, {recursive: true, force: true}); }
}
function fixture(dir: string, archived = false) {
  const project = join(dir, 'project'), bundle = join(dir, 'bundle.json'), patch = join(dir, 'candidate.patch');
  mkdirSync(join(project, 'data/alerts'), {recursive: true});
  for (const folder of ['scripts', 'src/lib', 'tracker']) cpSync(join(root, folder), join(project, folder), {recursive: true});
  copyFileSync(join(root, 'package.json'), join(project, 'package.json'));
  let archive: string | undefined;
  if (archived) {
    const result = spawnSync('python', [join(root, 'tests/promotion_archive_fixture.py'), dir, 'window'],
      {cwd: root, encoding: 'utf8', env: {...process.env, PYTHONPATH: root}, timeout: 60000});
    assert.equal(result.status, 0, result.stderr);
    archive = join(dir, 'archive');
    const views = JSON.parse(readFileSync(join(dir, 'public.json'), 'utf8'));
    for (const view of views) writeFileSync(join(project, `data/alerts/${view.snapshot.park_code}.json`), JSON.stringify(view.snapshot, null, 2) + '\n');
    writeFileSync(join(project, 'data/history.json'), JSON.stringify(views.map((view: any) => view.history), null, 2) + '\n');
  } else {
    for (const path of publicPaths) copyFileSync(join(root, path), join(project, path));
    const views = JSON.parse(readFileSync(join(project, 'data/history.json'), 'utf8')).map((history: any) =>
      ({history, snapshot: JSON.parse(readFileSync(join(project, `data/alerts/${history.park_code}.json`), 'utf8'))}));
    views[0] = JSON.parse(readFileSync(join(root, 'tests/fixtures/history-preview.json'), 'utf8')).cases.mixed;
    const body = {schema_version: 1, purpose: 'private_preview', data_kind: 'unreviewed_source', publication_performed: false, views};
    writeFileSync(bundle, canonicalPreview({...body, bundle_id: historyDigest(body)}), {mode: 0o600});
  }
  const invoke = (args: string[], timeout = 65000) => spawnSync(process.execPath,
    ['--experimental-strip-types', join(project, 'scripts/prepare-alert-promotion.ts'), ...args], {cwd: project, encoding: 'utf8', timeout});
  const archiveArgs = archive ? ['--archive-dir', archive] : [];
  const prepared = invoke(['--bundle', bundle, '--output', patch, ...archiveArgs]);
  assert.equal(prepared.status, 0, prepared.stderr);
  const id = JSON.parse(prepared.stdout).candidate_id;
  const check = (candidateId = id, patchPath = patch, extra = archiveArgs) =>
    invoke(['--check', '--bundle', bundle, '--patch', patchPath, '--candidate-id', candidateId, ...extra]);
  return {project, bundle, patch, archive, id, check, invoke};
}

test('read-only check binds the recorded candidate and all six public bases without changing files', () => temporary(dir => {
  const {project, bundle, patch, id, check} = fixture(dir);
  const paths = [bundle, patch, ...publicPaths.map(path => join(project, path))];
  const before = paths.map(path => ({bytes: readFileSync(path), mtime: statSync(path).mtimeMs}));
  const result = check();
  assert.equal(result.status, 0, result.stderr);
  const report = JSON.parse(result.stdout);
  assert.equal(report.mode, 'alert_promotion_check');
  assert.equal(report.candidate_id, id);
  assert.equal(report.public_base_files_checked, 6);
  assert.equal(report.patch_bytes_matched, true);
  assert.equal(report.human_review_required, true);
  assert.equal(report.production_data_written, false);
  assert.equal(report.publication_performed, false);
  assert.doesNotMatch(result.stdout + result.stderr, /Synthetic|description|alert-check-/);
  paths.forEach((path, i) => {
    assert.deepEqual(readFileSync(path), before[i].bytes);
    assert.equal(statSync(path).mtimeMs, before[i].mtime);
  });
  assert.deepEqual(readdirSync(dir).sort(), ['bundle.json', 'candidate.patch', 'project']);
}));

test('even a harmless edit to an unchanged park invalidates the six-file base binding', () => temporary(dir => {
  const {project, patch, check} = fixture(dir);
  for (const path of publicPaths) {
    const absolute = join(project, path), original = readFileSync(absolute);
    writeFileSync(absolute, Buffer.concat([original, Buffer.from('\n')]));
    if (path === 'data/alerts/romo.json') {
      const git = spawnSync('git', ['apply', '--check', patch], {cwd: project, encoding: 'utf8'});
      assert.equal(git.status, 0, git.stderr); // Git alone does not check unchanged base files.
    }
    const result = check();
    assert.equal(result.status, 2, path);
    assert.equal(result.stdout, '');
    writeFileSync(absolute, original);
  }
  assert.equal(check().status, 0);
}));

test('changed patch bytes refuse even when the caller supplies their new hash', () => temporary(dir => {
  const {patch, id, check} = fixture(dir), original = readFileSync(patch);
  for (const bytes of [Buffer.concat([original, Buffer.from('\n')]),
    Buffer.concat([original, Buffer.from('diff --git a/data/rules.json b/data/rules.json\n')]),
    Buffer.concat([original, Buffer.from([0xff])])]) {
    writeFileSync(patch, bytes);
    assert.equal(check(id).status, 2);
    const result = check(hash(bytes));
    assert.equal(result.status, 2);
    assert.equal(result.stdout, '');
    assert.deepEqual(readFileSync(patch), bytes);
  }
}));

test('a changed valid bundle or wrong recorded candidate ID cannot bless the frozen patch', () => temporary(dir => {
  const {bundle, patch, check} = fixture(dir), before = readFileSync(patch);
  for (const id of ['0'.repeat(64), 'ABC', '../private', 'A'.repeat(64)]) {
    const result = check(id);
    assert.equal(result.status, 2);
    assert.equal(result.stdout, '');
  }
  const value = JSON.parse(readFileSync(bundle, 'utf8'));
  value.views[0] = JSON.parse(readFileSync(join(root, 'tests/fixtures/history-preview.json'), 'utf8')).cases.failed;
  const {bundle_id, ...body} = value;
  writeFileSync(bundle, canonicalPreview({...body, bundle_id: historyDigest(body)}));
  assert.equal(check().status, 2);
  assert.deepEqual(readFileSync(patch), before);
}));

test('missing, insecure, linked and oversized patch inputs refuse without creation or repair', () => temporary(dir => {
  const {patch, check} = fixture(dir), original = readFileSync(patch);
  assert.equal(check(undefined, join(dir, 'missing.patch')).status, 2);
  assert.ok(!readdirSync(dir).includes('missing.patch'));
  chmodSync(patch, 0o644); assert.equal(check().status, 2);
  assert.equal(statSync(patch).mode & 0o777, 0o644);
  chmodSync(patch, 0o600);
  const alias = join(dir, 'alias.patch'); symlinkSync(patch, alias);
  assert.equal(check(undefined, alias).status, 2);
  rmSync(alias); linkSync(patch, alias);
  assert.equal(check().status, 2);
  rmSync(alias);
  truncateSync(patch, 32 * 1024 * 1024 + 1);
  assert.equal(check().status, 2);
  assert.equal(statSync(patch).size, 32 * 1024 * 1024 + 1);
  writeFileSync(patch, original);
  assert.equal(check().status, 0);
}));

test('check syntax cannot fall through to creating a patch and a named pipe is refused promptly', () => temporary(dir => {
  const {bundle, patch, id, check, invoke} = fixture(dir);
  for (const args of [
    ['--check', '--bundle', bundle, '--patch', join(dir, 'missing.patch')],
    ['--check', '--bundle', bundle, '--output', join(dir, 'missing.patch'), '--candidate-id', id],
    ['--check', '--bundle', bundle, '--patch', patch, '--candidate-id', id, '--apply'],
  ]) assert.equal(invoke(args).status, 2);
  assert.ok(!readdirSync(dir).includes('missing.patch'));
  const fifo = join(dir, 'pipe.patch');
  assert.equal(spawnSync('mkfifo', [fifo]).status, 0);
  chmodSync(fifo, 0o600);
  const result = check(undefined, fifo);
  assert.equal(result.status, 2);
  assert.equal(result.stdout, '');
}));

test('archive-backed candidates require the same verified continuity mode during read-only checks', () => temporary(dir => {
  const {patch, check} = fixture(dir, true), before = readFileSync(patch);
  assert.equal(check(undefined, patch, []).status, 2);
  const result = check();
  assert.equal(result.status, 0, result.stderr);
  assert.equal(JSON.parse(result.stdout).archive_continuity_verified, true);
  assert.deepEqual(readFileSync(patch), before);
}));

test('an explicitly empty archive path refuses in both modes rather than ignoring the option', () => temporary(dir => {
  const {bundle, patch, check, invoke} = fixture(dir), before = readFileSync(patch);
  assert.equal(check(undefined, patch, ['--archive-dir', '']).status, 2);
  assert.equal(invoke(['--bundle', bundle, '--output', patch, '--archive-dir', '']).status, 2);
  assert.deepEqual(readFileSync(patch), before);
}));
