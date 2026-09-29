/** Strict, server-only candidate loading. No defaults to production or private state. */
import { openSync, readSync, closeSync, fstatSync } from 'node:fs';
import { historyDigest, validateHistory } from './validate-history.ts';
import { assertSafePath } from './preview-workspace.mjs';
import type { History } from '../src/lib/history.ts';
export const PILOT_CODES = ['yose','romo','yell','zion','grca'] as const;
export const MAX_BUNDLE_BYTES = 10 * 1024 * 1024;
export interface PreviewSnapshot {
  park_code: string; collection_status: string; last_checked_at: string | null; last_successful_fetch_at: string | null;
  records: {id:string; title:string; description:string; url:string; category:string}[];
}
export interface PreviewBundle {
  schema_version: 1; purpose: 'private_preview'; data_kind: 'synthetic' | 'unreviewed_source';
  publication_performed: false; bundle_id: string;
  views: {snapshot: PreviewSnapshot; history: History}[];
}
function required(value: unknown): asserts value { if (!value) throw new Error('invalid_preview_bundle'); }
function keys(value: unknown, names: string): asserts value is Record<string, any> {
  required(value && typeof value === 'object' && !Array.isArray(value));
  required(Object.keys(value).sort().join(' ') === names.split(' ').sort().join(' '));
}
export function canonicalPreview(value: unknown, depth=0): string {
  required(depth <= 24);
  if (value === null || typeof value === 'boolean' || typeof value === 'string') return JSON.stringify(value);
  if (typeof value === 'number') { required(Number.isSafeInteger(value)); return JSON.stringify(value); }
  if (Array.isArray(value)) return `[${value.map(item=>canonicalPreview(item,depth+1)).join(',')}]`;
  required(value && typeof value === 'object');
  const object=value as Record<string,unknown>;
  return `{${Object.keys(object).sort().map(key=>`${JSON.stringify(key)}:${canonicalPreview(object[key],depth+1)}`).join(',')}}`;
}
export function validatePreviewBundle(value: unknown): PreviewBundle {
  try {
    keys(value,'schema_version purpose data_kind publication_performed bundle_id views');
    required(value.schema_version === 1 && value.purpose === 'private_preview' && value.publication_performed === false);
    required(['synthetic','unreviewed_source'].includes(value.data_kind));
    required(typeof value.bundle_id === 'string' && /^[a-f0-9]{64}$/.test(value.bundle_id));
    required(Buffer.byteLength(canonicalPreview(value),'utf8') <= MAX_BUNDLE_BYTES);
    const {bundle_id, ...body}=value; required(historyDigest(body) === bundle_id);
    required(Array.isArray(value.views) && value.views.length === PILOT_CODES.length);
    value.views.forEach((view: unknown,index:number)=>{
      keys(view,'snapshot history');
      required(view.snapshot?.park_code === PILOT_CODES[index]);
      validateHistory(view.history,view.snapshot);
    });
    return structuredClone(value) as PreviewBundle;
  } catch { throw new Error('invalid_preview_bundle'); }
}
export function readPreviewBundle(path:string):PreviewBundle {
  let fd: number | undefined;
  try {
    assertSafePath(path); fd=openSync(path,'r');
    const stat=fstatSync(fd); required(stat.isFile() && stat.size <= MAX_BUNDLE_BYTES);
    const bytes=Buffer.alloc(Math.min(stat.size+1,MAX_BUNDLE_BYTES+1)); let offset=0;
    while(offset<bytes.length){const n=readSync(fd,bytes,offset,bytes.length-offset,null);if(!n)break;offset+=n;}
    required(offset===stat.size);
    const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes.subarray(0,offset));
    const value=validatePreviewBundle(JSON.parse(text));
    // The producer emits canonical JSON. Reject duplicate keys, ignored trailing data,
    // invalid encodings and manual formatting changes rather than normalize silently.
    required(text===canonicalPreview(value)); return value;
  } catch { throw new Error('invalid_preview_bundle'); }
  finally { if(fd !== undefined) closeSync(fd); }
}
