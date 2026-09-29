import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

test('a named pipe is refused without waiting for a writer', {skip:process.platform!=='linux'},()=>{
  const dir=mkdtempSync(join(tmpdir(),'preview-fifo-'));
  try{
    const path=join(dir,'candidate.json');
    assert.equal(spawnSync('mkfifo',[path],{timeout:3000}).status,0);
    const module=new URL('../scripts/preview-bundle.ts',import.meta.url).href;
    const code=`import {readPreviewBundle} from ${JSON.stringify(module)}; try {readPreviewBundle(process.argv[1]); process.exitCode=1;} catch {process.exitCode=0;}`;
    const child=spawnSync(process.execPath,['--experimental-strip-types','--input-type=module','-e',code,path],{timeout:3000,killSignal:'SIGKILL',encoding:'utf8'});
    assert.equal(child.error,undefined,'Candidate reader blocked on a non-regular file');
    assert.equal(child.status,0,'Non-regular inputs must be rejected');
  }finally{rmSync(dir,{recursive:true,force:true});}
});
