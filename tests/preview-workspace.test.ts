import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, readdirSync, existsSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createWorkspace, workspacePaths, writeReady, readReady } from '../scripts/preview-workspace.mjs';
const manifest = {schema_version:1, purpose:'private_preview_build', bundle_id:'a'.repeat(64), publication_performed:false};
function temp(fn:(root:string)=>void) { const root=mkdtempSync(join(tmpdir(),'preview-work-'));try{fn(root);}finally{rmSync(root,{recursive:true,force:true});} }
test('every preview gets a new ignored workspace and never overwrites production',()=>temp(root=>{
  mkdirSync(join(root,'dist')); writeFileSync(join(root,'dist/index.html'),'production sentinel');
  const a=createWorkspace(root), b=createWorkspace(root); assert.notEqual(a,b);
  assert.equal(readFileSync(join(root,'dist/index.html'),'utf8'),'production sentinel');
  assert.equal(existsSync(join(a,'ready.json')),false); assert.equal(existsSync(join(b,'ready.json')),false);
}));
test('workspace output/cache/input paths remain inside the generated workspace',()=>temp(root=>{
  const work=createWorkspace(root), paths=workspacePaths(root,work);
  assert.equal(paths.output,join(work,'dist')); assert.equal(paths.bundle,join(work,'bundle.json')); assert.equal(paths.cache,join(work,'cache'));
}));
test('production, archive, unknown and traversal destinations are not valid workspaces',()=>temp(root=>{
  for(const path of [root,join(root,'dist'),join(root,'state'),join(root,'.superpowers/preview-builds/not-a-run'),join(root,'.superpowers/preview-builds/run-a/../run-b')])
    assert.throws(()=>workspacePaths(root,path));
}));
test('symlinked output or workspace ancestry is refused',()=>temp(root=>{
  const external=join(root,'external');mkdirSync(external);symlinkSync(external,join(root,'.superpowers'),'dir');assert.throws(()=>createWorkspace(root));
}));
test('unready or malformed markers cannot be read as a completed preview',()=>temp(root=>{
  const work=createWorkspace(root);assert.throws(()=>readReady(root,work));
  writeFileSync(join(work,'ready.json'),'{"publication_performed":true}');assert.throws(()=>readReady(root,work));
}));
test('ready marker requires successful output files and never overwrites another marker',()=>temp(root=>{
  const work=createWorkspace(root);assert.throws(()=>writeReady(root,work,manifest));
  mkdirSync(join(work,'dist'));writeFileSync(join(work,'dist/index.html'),'<meta name="robots" content="noindex, nofollow">');
  writeFileSync(join(work,'dist/preview.json'),JSON.stringify({bundle_id:manifest.bundle_id,purpose:'private_preview',publication_performed:false}));
  writeReady(root,work,manifest);assert.deepEqual(readReady(root,work),manifest);
  assert.throws(()=>writeReady(root,work,manifest));
}));
test('partial temporary files never count as ready',()=>temp(root=>{
  const work=createWorkspace(root);writeFileSync(join(work,'.ready.tmp'),JSON.stringify(manifest));assert.throws(()=>readReady(root,work));
  assert.equal(readdirSync(work).includes('ready.json'),false);
}));
test('completion fails when output identity differs from the candidate',()=>temp(root=>{
  const work=createWorkspace(root);mkdirSync(join(work,'dist'));writeFileSync(join(work,'dist/index.html'),'<meta name="robots" content="noindex, nofollow">');
  writeFileSync(join(work,'dist/preview.json'),JSON.stringify({bundle_id:'b'.repeat(64),purpose:'private_preview',publication_performed:false}));
  assert.throws(()=>writeReady(root,work,manifest));assert.equal(existsSync(join(work,'ready.json')),false);
}));
