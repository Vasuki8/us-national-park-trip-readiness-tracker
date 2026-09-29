/** Test harness uses the real export/build commands; never a hand-built HTML fixture. */
import { spawnSync, spawn } from 'node:child_process';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import assert from 'node:assert/strict';
import { buildPreview, astroBin, ROOT, previewEnvironment } from '../scripts/build-preview.ts';
function contents(folder:string):Record<string,string> {
  return Object.fromEntries(readdirSync(folder).flatMap(name=>{
    const path=join(folder,name);return statSync(path).isDirectory()?Object.entries(contents(path)):[[path,readFileSync(path).toString('base64')]];
  }));
}
const production={...contents('data'),...contents('dist')};
const generated=spawnSync('uv',['run','--frozen','python','tests/build_preview_fixture.py'],{encoding:'utf8',timeout:30_000});
assert.equal(generated.status,0,'Synthetic preview preparation failed');
const result=buildPreview(JSON.parse(generated.stdout).bundle_file);
assert.deepEqual({...contents('data'),...contents('dist')},production,'Preview modified production files');
const server=spawn(process.execPath,[astroBin(),'preview','--root',join(ROOT,'preview'),'--host','127.0.0.1','--port','4323'],{env:previewEnvironment(result.workspace),stdio:'inherit'});
for(const signal of ['SIGTERM','SIGINT'] as const)process.on(signal,()=>server.kill(signal));
server.on('exit',code=>{process.exitCode=code??1;});
