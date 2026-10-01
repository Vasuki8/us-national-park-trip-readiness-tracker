import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, readdirSync, existsSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { createWorkspace, workspacePaths, writeReady, readReady } from '../scripts/preview-workspace.mjs';
const manifest = {schema_version:1, purpose:'private_preview_build', bundle_id:'a'.repeat(64), publication_performed:false};
function temp(fn:(root:string,parent:string)=>void) {
  const base=mkdtempSync(join(tmpdir(),'preview-work-')),root=join(base,'project'),parent=join(base,'private');
  mkdirSync(root,{mode:0o700});mkdirSync(parent,{mode:0o700});
  try{fn(root,parent);}finally{rmSync(base,{recursive:true,force:true});}
}
test('every preview gets a new external workspace and never overwrites production',()=>temp((root,parent)=>{
  mkdirSync(join(root,'dist')); writeFileSync(join(root,'dist/index.html'),'production sentinel');
  const a=createWorkspace(root,parent), b=createWorkspace(root,parent); assert.notEqual(a,b);
  assert.equal(readFileSync(join(root,'dist/index.html'),'utf8'),'production sentinel');
  assert.equal(existsSync(join(a,'ready.json')),false); assert.equal(existsSync(join(b,'ready.json')),false);
}));
test('workspace output/cache/input paths remain inside the generated workspace',()=>temp((root,parent)=>{
  const work=createWorkspace(root,parent), paths=workspacePaths(root,work);
  assert.equal(paths.output,join(work,'dist')); assert.equal(paths.bundle,join(work,'bundle.json')); assert.equal(paths.cache,join(work,'cache'));
}));
test('production, archive, unknown and traversal destinations are not valid workspaces',()=>temp(root=>{
  for(const path of [root,join(root,'dist'),join(root,'state'),join(root,'.superpowers/preview-builds/not-a-run'),join(root,'.superpowers/preview-builds/run-a/../run-b')])
    assert.throws(()=>workspacePaths(root,path));
}));
test('symlinked workspace parent is refused',()=>temp((root,parent)=>{
  const link=join(dirname(root),'link');symlinkSync(parent,link,'dir');assert.throws(()=>createWorkspace(root,link));
}));
test('unready or malformed markers cannot be read as a completed preview',()=>temp((root,parent)=>{
  const work=createWorkspace(root,parent);assert.throws(()=>readReady(root,work));
  writeFileSync(join(work,'ready.json'),'{"publication_performed":true}',{mode:0o600});assert.throws(()=>readReady(root,work));
}));
test('ready marker requires successful output files and never overwrites another marker',()=>temp((root,parent)=>{
  const work=createWorkspace(root,parent);assert.throws(()=>writeReady(root,work,manifest));
  mkdirSync(join(work,'dist'),{mode:0o700});writeFileSync(join(work,'dist/index.html'),'<meta name="robots" content="noindex, nofollow">',{mode:0o600});
  writeFileSync(join(work,'dist/preview.json'),JSON.stringify({bundle_id:manifest.bundle_id,purpose:'private_preview',publication_performed:false}),{mode:0o600});
  writeReady(root,work,manifest);assert.deepEqual(readReady(root,work),manifest);
  assert.throws(()=>writeReady(root,work,manifest));
}));
test('partial temporary files never count as ready',()=>temp((root,parent)=>{
  const work=createWorkspace(root,parent);writeFileSync(join(work,'.ready.tmp'),JSON.stringify(manifest),{mode:0o600});assert.throws(()=>readReady(root,work));
  assert.equal(readdirSync(work).includes('ready.json'),false);
}));
test('completion fails when output identity differs from the candidate',()=>temp((root,parent)=>{
  const work=createWorkspace(root,parent);mkdirSync(join(work,'dist'),{mode:0o700});writeFileSync(join(work,'dist/index.html'),'<meta name="robots" content="noindex, nofollow">',{mode:0o600});
  writeFileSync(join(work,'dist/preview.json'),JSON.stringify({bundle_id:'b'.repeat(64),purpose:'private_preview',publication_performed:false}),{mode:0o600});
  assert.throws(()=>writeReady(root,work,manifest));assert.equal(existsSync(join(work,'ready.json')),false);
}));
