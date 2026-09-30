import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdtempSync, rmSync, existsSync, mkdirSync, cpSync, copyFileSync, statSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join, resolve, dirname } from 'node:path';
import { historyDigest } from '../scripts/validate-history.ts';
import { canonicalPreview, readPreviewBundle } from '../scripts/preview-bundle.ts';
import { buildPreview, previewEnvironment } from '../scripts/build-preview.ts';
const json=(path:string)=>JSON.parse(readFileSync(new URL(path,import.meta.url),'utf8'));
function input(dir:string){
  const views=json('../data/history.json').map((history:any)=>({history,snapshot:json(`../data/alerts/${history.park_code}.json`)}));
  const body={schema_version:1,purpose:'private_preview',data_kind:'synthetic',publication_performed:false,views};
  const bundle={...body,bundle_id:historyDigest(body)},path=join(dir,'bundle.json');writeFileSync(path,canonicalPreview(bundle));return {path,bundle};
}
function temp(fn:(dir:string)=>void){const dir=mkdtempSync(join(tmpdir(),'build-preview-'));try{fn(dir);}finally{rmSync(dir,{recursive:true,force:true});}}
test('invalid bundle fails before invoking Astro',()=>temp(dir=>{
  const path=join(dir,'bad.json');writeFileSync(path,'{}');let called=false;
  assert.throws(()=>buildPreview(path,()=>{called=true;return {status:0,signal:null};}));assert.equal(called,false);
}));
test('build environment excludes API keys and arbitrary runtime options',()=>{
  const env=previewEnvironment('/private/work',{PATH:'/bin',HOME:'/home/test',NPS_API_KEY:'synthetic',NODE_OPTIONS:'synthetic',PARK_PREVIEW_WORKSPACE:'/wrong'});
  assert.equal(env.NPS_API_KEY,undefined);assert.equal(env.NODE_OPTIONS,undefined);
  assert.equal(env.PARK_PREVIEW_WORKSPACE,'/private/work');assert.equal(env.ASTRO_TELEMETRY_DISABLED,'1');
});
test('failed build has no ready marker and never returns prior output as success',()=>temp(dir=>{
  const {path}=input(dir);let workspace='';
  try{
    assert.throws(()=>buildPreview(path,(_cmd,_args,opts)=>{workspace=opts.env!.PARK_PREVIEW_WORKSPACE!;return {status:1,signal:null};}));
    assert.ok(workspace);assert.equal(existsSync(join(workspace,'ready.json')),false);
  }finally{if(workspace)rmSync(workspace,{recursive:true,force:true});}
}));
test('successful build validates output identity and freezes the original bundle',()=>temp(dir=>{
  const {path,bundle}=input(dir);let workspace='';
  try{
    const result=buildPreview(path,(command,args,opts)=>{
      assert.equal(command,process.execPath);assert.ok(args.includes('build'));assert.ok(args.includes('--root'));
      workspace=opts.env!.PARK_PREVIEW_WORKSPACE!;
      const frozen=readFileSync(join(workspace,'bundle.json'),'utf8');writeFileSync(path,'{}');
      assert.equal(JSON.parse(frozen).bundle_id,bundle.bundle_id);
      mkdirSync(join(workspace,'dist'));writeFileSync(join(workspace,'dist/index.html'),'<meta name="robots" content="noindex, nofollow">');
      writeFileSync(join(workspace,'dist/preview.json'),JSON.stringify({bundle_id:bundle.bundle_id,purpose:'private_preview',publication_performed:false}));
      return {status:0,signal:null};
    });
    assert.equal(result.bundle_id,bundle.bundle_id);assert.equal(result.publication_performed,false);
    assert.equal(existsSync(join(workspace,'ready.json')),true);
  }finally{if(workspace)rmSync(workspace,{recursive:true,force:true});}
}));
test('a zero exit code cannot bless missing or mismatched output',()=>temp(dir=>{
  const {path}=input(dir);let workspace='';
  try{
    assert.throws(()=>buildPreview(path,(_c,_a,opts)=>{workspace=opts.env!.PARK_PREVIEW_WORKSPACE!;return {status:0,signal:null};}));
    assert.equal(existsSync(join(workspace,'ready.json')),false);
  }finally{if(workspace)rmSync(workspace,{recursive:true,force:true});}
}));

test('real synthetic exporter keeps its input outside the checkout with private permissions',()=>temp(dir=>{
  const source=resolve(import.meta.dirname,'..'),project=join(dir,'project');
  mkdirSync(join(project,'tests'),{recursive:true});
  cpSync(join(source,'tracker'),join(project,'tracker'),{recursive:true});
  for(const file of ['build_preview_fixture.py','history_fixtures.py'])copyFileSync(join(source,'tests',file),join(project,'tests',file));
  const result=spawnSync('python',['tests/build_preview_fixture.py',dir],{cwd:project,encoding:'utf8',timeout:30000});
  assert.equal(result.status,0,result.stderr);
  const path=JSON.parse(result.stdout).bundle_file;
  assert.equal(dirname(path),join(dir,'bundles'));
  assert.equal(statSync(dirname(path)).mode&0o077,0);
  assert.equal(statSync(path).mode&0o077,0);
  assert.equal(statSync(path).nlink,1);
  const bundle=readPreviewBundle(path);
  assert.equal(bundle.data_kind,'synthetic');
  assert.equal(bundle.views.length,5);
  assert.equal(bundle.views[0].snapshot.records[0].title,'Preview-only synthetic notice');
  assert.equal(bundle.publication_performed,false);
}));
