import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, rmSync, statSync, readdirSync, chmodSync, symlinkSync, writeFileSync, linkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { createWorkspace, workspacePaths, writeReady, readReady } from '../scripts/preview-workspace.mjs';

function fixture(fn:(root:string,parent:string)=>void){
  const base=mkdtempSync(join(tmpdir(),'private-preview-'));
  const root=join(base,'project'),parent=join(base,'private');
  mkdirSync(root,{mode:0o700});mkdirSync(parent,{mode:0o700});
  try{fn(root,parent);}finally{rmSync(base,{recursive:true,force:true});}
}
const marker={schema_version:1,purpose:'private_preview_build',bundle_id:'a'.repeat(64),publication_performed:false};
function readyFiles(work:string){
  mkdirSync(join(work,'dist'),{mode:0o700});
  writeFileSync(join(work,'dist/index.html'),'<meta name="robots" content="noindex, nofollow">',{mode:0o600});
  writeFileSync(join(work,'dist/preview.json'),JSON.stringify({...marker,purpose:'private_preview'}),{mode:0o600});
}

test('preview workspace uses the explicit private parent outside the checkout',()=>fixture((root,parent)=>{
  const work=createWorkspace(root,parent);
  assert.equal(dirname(work),parent);
  assert.deepEqual(readdirSync(root),[]);
  assert.equal(statSync(work).mode&0o077,0);
  assert.equal(workspacePaths(root,work).output,join(work,'dist'));
}));

test('missing, relative, checkout, ancestor, readable and symlink parents refuse without creation',()=>fixture((root,parent)=>{
  const readable=join(dirname(root),'readable');mkdirSync(readable,{mode:0o755});chmodSync(readable,0o755);
  const link=join(dirname(root),'link');symlinkSync(parent,link,'dir');
  for(const candidate of [undefined,'relative',root,dirname(root),join(root,'unlisted'),join(parent,'absent'),readable,link]){
    const before=readdirSync(root);
    assert.throws(()=>createWorkspace(root,candidate),String(candidate));
    assert.deepEqual(readdirSync(root),before);
  }
  assert.deepEqual(readdirSync(parent),[]);
}));

test('ready validation refuses readable and hardlinked output files and private-workspace permission changes',()=>fixture((root,parent)=>{
  const work=createWorkspace(root,parent);readyFiles(work);
  const extra=join(work,'dist/extra.txt');writeFileSync(extra,'private',{mode:0o600});
  chmodSync(extra,0o644);assert.throws(()=>writeReady(root,work,marker));
  chmodSync(extra,0o600);linkSync(extra,join(parent,'second-link'));assert.throws(()=>writeReady(root,work,marker));
  rmSync(join(parent,'second-link'));writeReady(root,work,marker);
  assert.deepEqual(readReady(root,work),marker);
  chmodSync(work,0o755);assert.throws(()=>readReady(root,work));
  chmodSync(work,0o700);chmodSync(parent,0o755);assert.throws(()=>readReady(root,work));
}));
