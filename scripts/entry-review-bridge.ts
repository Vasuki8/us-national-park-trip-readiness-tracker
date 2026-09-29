/** Private stdin/stdout adapter to the existing review policy. No file/network writes. */
import { assessEntrySources } from './entry-review.ts';
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
    || Object.keys(value).sort().join(' ') !== 'now observations pending records') throw new Error('invalid_input');
  const result = assessEntrySources(value.records, value.observations, value.pending, new Date(value.now));
  const encoded = JSON.stringify(result);
  if (Buffer.byteLength(encoded) > MAX_BYTES) throw new Error('output_too_large');
  process.stdout.write(encoded);
} catch {
  // Do not echo untrusted text, exceptions, source URLs, paths or runtime options.
  process.stderr.write('entry_review_bridge_failed\n');
  process.exitCode = 2;
}
