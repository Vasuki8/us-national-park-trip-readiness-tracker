/** Explicit offline preview build. Never use the production root or inherited credentials. */
import { spawnSync, type SpawnSyncOptions } from 'node:child_process';
import { readFileSync, writeFileSync, statSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readPreviewBundle, canonicalPreview } from './preview-bundle.ts';
import { createWorkspace, workspacePaths, writeReady, readReady, assertPrivateInput } from './preview-workspace.mjs';
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
  env.PARK_PREVIEW_WORKSPACE=workspace;env.PARK_PREVIEW_PROJECT_ROOT=ROOT;
  env.ASTRO_TELEMETRY_DISABLED='1';return env;
}
export function buildPreview(input:string,workspaceParent:string,run:Runner=spawnSync) {
  assertPrivateInput(ROOT,input);
  const bundle=readPreviewBundle(input); // Validate before any workspace or subprocess.
  const executable=astroBin();
  const workspace=createWorkspace(ROOT,workspaceParent), paths=workspacePaths(ROOT,workspace);
  try {
    writeFileSync(paths.bundle,canonicalPreview(bundle),{flag:'wx',mode:0o600});
    // The synchronous child inherits private creation permissions; restore the
    // caller's development umask even when spawning or the runner fails.
    const previousMask=process.umask(0o077);
    let result:ReturnType<Runner>;
    try{result=run(process.execPath,[executable,'build','--root',join(ROOT,'preview')],{
        cwd:workspace,env:previewEnvironment(workspace),timeout:120_000,maxBuffer:2*1024*1024,stdio:'pipe',shell:false,
      });
    }finally{process.umask(previousMask);}
    if(result.status!==0 || result.error || result.signal)throw new Error('preview_build_incomplete');
    if(readPreviewBundle(paths.bundle).bundle_id!==bundle.bundle_id)throw new Error('preview_input_changed');
    const marker={schema_version:1,purpose:'private_preview_build',bundle_id:bundle.bundle_id,publication_performed:false};
    writeReady(ROOT,workspace,marker);readReady(ROOT,workspace);
    return {status:'ready',bundle_id:bundle.bundle_id,workspace,output:paths.output,publication_performed:false,production_data_written:false};
  } catch { throw new Error('private_preview_build_failed'); }
}
export function main(args=process.argv.slice(2)):number {
  if(args.length!==4 || args[0]!=='--bundle' || args[2]!=='--workspace-parent'){
    console.error('Usage: node --experimental-strip-types scripts/build-preview.ts --bundle <candidate.json> --workspace-parent <private-directory>');return 2;
  }
  try{console.log(JSON.stringify(buildPreview(args[1],args[3])));return 0;}
  catch{console.error('Private preview refused or incomplete. Production data was not changed; no ready result is available for this attempt.');return 2;}
}
if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url))process.exitCode=main();
