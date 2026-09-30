/** Read-only comparison of a hosted Pages site with its verified public artifact.
 * No dependencies, credentials, source collection or publication. Node 24.
 */
import { lstat, readdir, readFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { parseArgs } from 'node:util';

const MAX_FILE = 4 * 1024 * 1024;
const MAX_TOTAL = 64 * 1024 * 1024;
const MAX_FILES = 128;
const DEADLINE_MS = 120_000;
const RESPONSE_HEADERS = ['x-robots-tag', 'content-security-policy', 'x-content-type-options', 'referrer-policy'];
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
class Refusal extends Error {}
const refuse = reason => { throw new Refusal(reason); };

async function inventory(directory) {
  if (!(await lstat(directory)).isDirectory()) refuse('artifact_invalid');
  const files = [];
  let bytes = 0;
  let entries = 0;
  async function visit(relative = '', depth = 0) {
    if (depth > 16) refuse('artifact_limit');
    for (const name of (await readdir(join(directory, relative))).sort()) {
      if (++entries > 256) refuse('artifact_limit');
      const path = relative ? relative + '/' + name : name;
      const info = await lstat(join(directory, path));
      if (info.isSymbolicLink()) refuse('artifact_symlink');
      if (info.isDirectory()) { await visit(path, depth + 1); continue; }
      if (!info.isFile()) refuse('artifact_invalid');
      if (info.size > MAX_FILE || (bytes += info.size) > MAX_TOTAL) refuse('artifact_limit');
      // Host configuration is not HTTP-header evidence. Never request it as a page.
      if (path === '_headers') continue;
      if (files.length >= MAX_FILES) refuse('artifact_limit');
      const body = await readFile(join(directory, path));
      if (body.length !== info.size) refuse('artifact_changed');
      files.push({ path, digest: hash(body) });
    }
  }
  await visit();
  if (!files.some(file => file.path === 'index.html') || !files.some(file => file.path === 'build.json')) {
    refuse('artifact_incomplete');
  }
  // Probe the real home navigation URL before the remaining pages and assets.
  files.sort((a, b) => a.path === 'index.html' ? -1 : b.path === 'index.html' ? 1 : a.path.localeCompare(b.path));
  return files;
}

async function responseDigest(response) {
  if (response.status !== 200) refuse('http_status');
  const encoding = response.headers.get('content-encoding');
  if (encoding && encoding.toLowerCase() !== 'identity') refuse('unexpected_content_encoding');
  const length = response.headers.get('content-length');
  if (length !== null && (!/^\d+$/.test(length) || Number(length) > MAX_FILE)) refuse('response_limit');
  if (!response.body) refuse('response_missing');
  const reader = response.body.getReader();
  const digest = createHash('sha256');
  let size = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      if ((size += value.byteLength) > MAX_FILE) refuse('response_limit');
      digest.update(value);
    }
  } finally { await reader.cancel().catch(() => {}); }
  return digest.digest('hex');
}

export async function verifyLiveSite({ directory, url, commit, mode, fetch = globalThis.fetch,
  sleep = ms => new Promise(resolve => setTimeout(resolve, ms)), attempts = 3 }) {
  const report = { schema_version: 1, passed: false, reason: 'invalid_arguments',
    checked_at: new Date().toISOString(), attempts: 0, files_checked: 0, pages_checked: 0 };
  const deadline = Date.now() + DEADLINE_MS;
  try {
    if (!/^[0-9a-f]{40}$/.test(commit || '') || !['deploy', 'rollback'].includes(mode)
      || !Number.isInteger(attempts) || attempts < 1 || attempts > 3) refuse('invalid_arguments');
    const address = new URL(url);
    if (address.protocol !== 'https:' || address.username || address.password || address.port
      || address.search || address.hash || !address.pathname.endsWith('/')
      || address.href !== url || address.pathname.includes('%')) refuse('invalid_url');
    const files = await inventory(directory);
    const manifest = JSON.parse(await readFile(join(directory, 'build.json'), 'utf8'));
    const base = manifest?.base_path ?? '/';
    if (!manifest || typeof manifest !== 'object' || Array.isArray(manifest)
      || manifest.code_commit !== commit || base !== address.pathname
      || !/^pilot-[0-9a-f]{12}$/.test(manifest.snapshot_id || '')) refuse('artifact_identity_mismatch');
    Object.assign(report, { url: address.href, code_commit: commit, snapshot_id: manifest.snapshot_id,
      base_path: base, mode, scope: 'public_artifact_except_host_configuration' });
    for (let attempt = 1; attempt <= attempts; attempt++) {
      report.attempts = attempt;
      report.files_checked = 0;
      report.pages_checked = 0;
      try {
        for (const file of files) {
          const remaining = deadline - Date.now();
          if (remaining <= 0) refuse('verification_timeout');
          let path = file.path === 'index.html' ? '' : file.path.replace(/\/index\.html$/, '/');
          path = path.split('/').map(encodeURIComponent).join('/');
          const response = await fetch(address.href + path, { redirect: 'manual',
            signal: AbortSignal.timeout(Math.min(10_000, remaining)),
            headers: { 'Accept-Encoding': 'identity', 'Cache-Control': 'no-cache',
              'User-Agent': 'ParkTripReadiness/0.1 PagesVerification' } });
          if (file.path === 'index.html') {
            report.response_headers = Object.fromEntries(RESPONSE_HEADERS.map(name =>
              [name, response.headers.get(name)?.slice(0, 4096) ?? null]));
          }
          if (await responseDigest(response) !== file.digest) refuse('content_mismatch');
          report.files_checked++;
          if (file.path.endsWith('.html')) report.pages_checked++;
        }
        report.passed = true;
        report.reason = 'verified_artifact_matches_live_site';
        return report;
      } catch (error) {
        report.reason = error instanceof Refusal ? error.message : 'request_failed';
        if (attempt === attempts || deadline - Date.now() <= 5000) break;
        await sleep(5000);
      }
    }
  } catch (error) {
    report.reason = error instanceof Refusal ? error.message : 'artifact_or_arguments_invalid';
  }
  return report;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  let report;
  try {
    const { values } = parseArgs({ options: {
      directory: { type: 'string' }, url: { type: 'string' }, commit: { type: 'string' }, mode: { type: 'string' },
    } });
    report = await verifyLiveSite(values);
  } catch { report = { schema_version: 1, passed: false, reason: 'invalid_arguments' }; }
  process.stdout.write(JSON.stringify(report) + '\n');
  process.exitCode = report.passed ? 0 : 1;
}
