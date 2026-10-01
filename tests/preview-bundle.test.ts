import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdtempSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { historyDigest } from '../scripts/validate-history.ts';
import { validatePreviewBundle, readPreviewBundle, canonicalPreview } from '../scripts/preview-bundle.ts';
import { syntheticEmptyViews } from './synthetic-preview.ts';
const json = (path: string) => JSON.parse(readFileSync(new URL(path, import.meta.url), 'utf8'));
const fixtures = json('./fixtures/history-preview.json').cases;
function bundle(scenario = 'empty') {
  const views = syntheticEmptyViews();
  views[0] = structuredClone(fixtures[scenario]);
  const body = {schema_version: 1, purpose: 'private_preview', data_kind: 'synthetic', publication_performed: false, views};
  return {...body, bundle_id: historyDigest(body)};
}
function resign(value: any) { const {bundle_id, ...body} = value; value.bundle_id = historyDigest(body); return value; }
function temp(fn: (dir: string) => void) { const dir = mkdtempSync(join(tmpdir(),'preview-')); try {fn(dir);} finally {rmSync(dir,{recursive:true,force:true});} }
test('valid empty, mixed, baseline, failed and truncated pairs remain intact', () => {
  for (const scenario of Object.keys(fixtures)) assert.deepEqual(validatePreviewBundle(bundle(scenario)), bundle(scenario));
});
test('bundle identity binds every park and metadata', () => {
  const b = bundle(); b.data_kind = 'unreviewed_source'; assert.throws(() => validatePreviewBundle(b));
});
test('unknown fields, approval and publication flags fail even with a new hash', () => {
  for (const change of [(b:any)=>b.private_path='/state', (b:any)=>b.purpose='release', (b:any)=>b.publication_performed=true, (b:any)=>b.data_kind='approved_live', (b:any)=>b.views[0].pending={}]) {
    const b = bundle(); change(b); assert.throws(() => validatePreviewBundle(resign(b)));
  }
});
test('exact five-park inventory, order and uniqueness are required', () => {
  for (const change of [(b:any)=>b.views.pop(), (b:any)=>b.views.reverse(), (b:any)=>b.views[1]=b.views[0]]) {
    const b = bundle(); change(b); assert.throws(() => validatePreviewBundle(resign(b)));
  }
});
test('a different current snapshot cannot be paired with an older history', () => {
  const b = bundle('mixed'); b.views[0].history = fixtures.baseline.history;
  assert.throws(() => validatePreviewBundle(resign(b)));
});
test('wrong park or altered source evidence refuses before a build', () => {
  const b = bundle('mixed'); b.views[0].snapshot.records[0].url = 'https://evil.invalid/';
  assert.throws(() => validatePreviewBundle(resign(b)));
});
test('canonical UTF-8 files round-trip with no field loss', () => temp((dir) => {
  const b = bundle('mixed'), path = join(dir,'bundle.json'); writeFileSync(path,canonicalPreview(b));
  assert.deepEqual(readPreviewBundle(path), b);
}));
test('duplicate JSON fields and noncanonical edits are rejected', () => temp((dir) => {
  const b = bundle(), text = canonicalPreview(b), path = join(dir,'bundle.json');
  for (const data of ['{'+text.slice(1).replace('"data_kind":','"schema_version":1,"data_kind":'), JSON.stringify(b,null,2)]) {
    writeFileSync(path,data); assert.throws(() => readPreviewBundle(path));
  }
}));
test('oversized, malformed and invalid UTF-8 input is rejected', () => temp((dir) => {
  const path = join(dir,'bundle.json');
  for (const data of [Buffer.alloc(10*1024*1024+1,32), Buffer.from('{bad'), Buffer.from([0xff,0xfe])]) {
    writeFileSync(path,data); assert.throws(() => readPreviewBundle(path));
  }
}));
test('symlinks are not accepted as candidate input', () => temp((dir) => {
  const path = join(dir,'bundle.json'), link = join(dir,'alias.json'); writeFileSync(path,canonicalPreview(bundle())); symlinkSync(path,link);
  assert.throws(() => readPreviewBundle(link));
}));
test('validator returns a defensive copy rather than modifying the supplied bundle', () => {
  const b = bundle('mixed'), before = structuredClone(b), result = validatePreviewBundle(b); result.views[0].snapshot.records.length=0;
  assert.deepEqual(b,before);
});
test('private values never appear in validation diagnostics', () => {
  const b = bundle(); (b as any).secret='synthetic-private-value';
  assert.throws(()=>validatePreviewBundle(b),(e:any)=>!String(e).includes('synthetic-private-value'));
});
