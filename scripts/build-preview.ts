/** Explicit offline preview build. Never use the production root or inherited credentials. */
import { spawnSync, type SpawnSyncOptions } from 'node:child_process';
import { readFileSync, writeFileSync, statSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readPreviewBundle, canonicalPreview } from './preview-bundle.ts';
import { createWorkspace, workspacePaths, writeReady, readReady } from './preview-workspace.mjs';
export const ROOT=fileURLToPath(new URL('../',import.meta.url));
type Runner=(command:string,args:string[],options:SpawnSyncOptions)=>{status:number|null;signal:NodeJS.Signals|null;error?:Error};
export function astroBin():string {
  const folder=join(ROOT,'node_modules','astro');
  const pkg=JSON.parse(readFileSync(join(folder,'package.json'),'utf8'));
  const entry=typeof pkg.bin==='string'?pkg.bin:pkg.bin?.astro;
  if(typeof entry!=='string')throw new Error('local_astro_unavailable');
  const path=resolve(folder,entry);
  if(!path.startsWith(folder+'/') || !statSync(path).isFile())throw new Error('local_astro_unavailable');
  return path;
}
export function previewEnvironment(workspace:string,source:NodeJS.ProcessEnv=process.env):NodeJS.ProcessEnv {
  const env:NodeJS.ProcessEnv={};
  for(const key of ['PATH','HOME','TMPDIR','TMP','TEMP','SystemRoot','USERPROFILE','CI']) if(source[key])env[key]=source[key];
  env.PARK_PREVIEW_WORKSPACE=workspace;env.ASTRO_TELEMETRY_DISABLED='1';return env;
}
export function buildPreview(input:string,run:Runner=spawnSync) {
  const bundle=readPreviewBundle(input); // Validate before any workspace or subprocess.
  const executable=astroBin();
  const workspace=createWorkspace(ROOT), paths=workspacePaths(ROOT,workspace);
  try {
    writeFileSync(paths.bundle,canonicalPreview(bundle),{flag:'wx',mode:0o600});
    const result=run(process.execPath,[executable,'build','--root',join(ROOT,'preview')],{
      cwd:ROOT,env:previewEnvironment(workspace),timeout:120_000,maxBuffer:2*1024*1024,stdio:'pipe',shell:false,
    });
    if(result.status!==0 || result.error || result.signal)throw new Error('preview_build_incomplete');
    if(readPreviewBundle(paths.bundle).bundle_id!==bundle.bundle_id)throw new Error('preview_input_changed');
    const marker={schema_version:1,purpose:'private_preview_build',bundle_id:bundle.bundle_id,publication_performed:false};
    writeReady(ROOT,workspace,marker);readReady(ROOT,workspace);
    return {status:'ready',bundle_id:bundle.bundle_id,workspace,output:paths.output,publication_performed:false,production_data_written:false};
  } catch { throw new Error('private_preview_build_failed'); }
}
export function main(args=process.argv.slice(2)):number {
  if(args.length!==2 || args[0]!=='--bundle'){
    console.error('Usage: node --experimental-strip-types scripts/build-preview.ts --bundle <candidate.json>');return 2;
  }
  try{console.log(JSON.stringify(buildPreview(args[1])));return 0;}
  catch{console.error('Private preview refused or incomplete. Production data was not changed; no ready result is available for this attempt.');return 2;}
}
if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url))process.exitCode=main();
