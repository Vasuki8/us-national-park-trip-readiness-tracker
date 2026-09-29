/** Private local workspaces only; no production fallback and no automatic cleanup. */
import { lstatSync, mkdirSync, mkdtempSync, readdirSync, openSync, closeSync, writeFileSync, fsyncSync, linkSync, unlinkSync, readFileSync } from 'node:fs';
import { resolve, dirname, basename, join, isAbsolute } from 'node:path';
function requireValue(value){if(!value)throw new Error('unsafe_or_incomplete_preview');}
export function assertSafePath(path){
  requireValue(typeof path==='string' && path.length>0);
  for(let p=resolve(path);;p=dirname(p)){
    try{requireValue(!lstatSync(p).isSymbolicLink());}catch(error){if(error.code!=='ENOENT')throw error;}
    if(dirname(p)===p)break;
  }
}
const parentFor=root=>join(resolve(root),'.superpowers','preview-builds');
export function createWorkspace(root){
  const parent=parentFor(root);assertSafePath(parent);
  mkdirSync(parent,{recursive:true,mode:0o700});
  requireValue(readdirSync(parent).length<64);
  return mkdtempSync(join(parent,'run-'));
}
export function workspacePaths(root,workspace){
  requireValue(typeof workspace==='string' && isAbsolute(workspace) && workspace===resolve(workspace));
  requireValue(dirname(workspace)===parentFor(root) && /^run-[A-Za-z0-9]+$/.test(basename(workspace)));
  assertSafePath(workspace);requireValue(lstatSync(workspace).isDirectory());
  const paths={bundle:join(workspace,'bundle.json'),output:join(workspace,'dist'),cache:join(workspace,'cache'),ready:join(workspace,'ready.json')};
  for(const path of Object.values(paths))assertSafePath(path);
  return paths;
}
function marker(value){
  requireValue(value && typeof value==='object' && !Array.isArray(value));
  requireValue(Object.keys(value).sort().join(' ')==='bundle_id publication_performed purpose schema_version');
  requireValue(value.schema_version===1 && value.purpose==='private_preview_build' && value.publication_performed===false && /^[a-f0-9]{64}$/.test(value.bundle_id));
  return value;
}
function boundedText(path,limit){
  assertSafePath(path);const stat=lstatSync(path);requireValue(stat.isFile() && stat.size<=limit);
  return readFileSync(path,'utf8');
}
function verifyOutput(paths,value){
  const html=boundedText(join(paths.output,'index.html'),16*1024*1024);
  requireValue(/<meta\s+name="robots"\s+content="noindex, nofollow"/.test(html));
  const data=JSON.parse(boundedText(join(paths.output,'preview.json'),65536));
  requireValue(data.bundle_id===value.bundle_id && data.purpose==='private_preview' && data.publication_performed===false);
}
export function writeReady(root,workspace,value){
  const paths=workspacePaths(root,workspace);marker(value);verifyOutput(paths,value);
  const temporary=join(workspace,'.ready.tmp');assertSafePath(temporary);
  const fd=openSync(temporary,'wx',0o600);
  try{writeFileSync(fd,JSON.stringify(value));fsyncSync(fd);}finally{closeSync(fd);}
  try{linkSync(temporary,paths.ready);}finally{unlinkSync(temporary);}
}
export function readReady(root,workspace){
  const paths=workspacePaths(root,workspace);const value=marker(JSON.parse(boundedText(paths.ready,1024)));
  verifyOutput(paths,value);return value;
}
