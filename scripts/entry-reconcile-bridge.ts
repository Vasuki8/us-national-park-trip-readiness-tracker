/** Private stdin/stdout adapter for explicit guidance reconciliation. No file/network writes. */
import { readFileSync } from 'node:fs';
import { reconcileEntryReview } from './entry-review.ts';
const MAX_BYTES = 4 * 1024 * 1024;
try {
  const chunks: Buffer[] = []; let length = 0;
  for await (const chunk of process.stdin) {
    const bytes = Buffer.from(chunk); length += bytes.length;
    if (length > MAX_BYTES) throw new Error('input_too_large');
    chunks.push(bytes);
  }
  const value = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks)));
  if (!value || typeof value !== 'object' || Array.isArray(value)
    || Object.keys(value).sort().join(' ') !== 'current next pending proposal_ids reviewed_at') throw new Error('invalid_input');
  const parks = JSON.parse(readFileSync(new URL('../data/parks.json', import.meta.url), 'utf8'));
  const result = reconcileEntryReview(value.current, value.pending, value.proposal_ids, value.next,
    new Date(value.reviewed_at), parks);
  const encoded = JSON.stringify(result);
  if (Buffer.byteLength(encoded) > MAX_BYTES) throw new Error('output_too_large');
  process.stdout.write(encoded);
} catch {
  process.stderr.write('entry_reconcile_bridge_failed\n');
  process.exitCode = 2;
}
