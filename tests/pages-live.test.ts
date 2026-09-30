import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const sha = 'a'.repeat(40);
const base = '/us-national-park-trip-readiness-tracker/';
const origin = 'https://vasuki8.github.io';
const url = origin + base;
const load = () => import('../scripts/verify-pages-live.mjs');

async function fixture(run: (directory: string, files: Record<string, string>) => Promise<void>, path = base) {
  const directory = await mkdtemp(join(tmpdir(), 'trip-live-'));
  const files = {
    'index.html': '<!doctype html><html><head><meta name="robots" content="noindex, nofollow"></head><body>Pilot</body></html>',
    'parks/yose/index.html': '<!doctype html><html><head><meta name="robots" content="noindex, nofollow"></head><body>Yosemite</body></html>',
    '_astro/site.css': 'body { color: black }',
    'robots.txt': 'User-agent: *\nDisallow: /\n',
    'build.json': JSON.stringify({ code_commit: sha, base_path: path, snapshot_id: 'pilot-0123456789ab' }),
    '_headers': '/*\n X-Robots-Tag: noindex\n',
  };
  try {
    for (const [name, text] of Object.entries(files)) {
      await mkdir(join(directory, name, '..'), { recursive: true });
      await writeFile(join(directory, name), text);
    }
    await run(directory, files);
  } finally { await rm(directory, { recursive: true, force: true }); }
}

function transport(files: Record<string, string>, path = base) {
  const requests: string[] = [];
  const fetch = async (address: string, options: RequestInit) => {
    requests.push(address);
    assert.equal(options.redirect, 'manual');
    assert.equal(options.headers?.['Accept-Encoding'], 'identity');
    const relative = new URL(address).pathname.slice(path.length);
    const name = relative === '' || relative.endsWith('/') ? relative + 'index.html' : relative;
    return new Response(files[name] ?? 'Not found', {
      status: files[name] === undefined ? 404 : 200,
      headers: { 'X-Content-Type-Options': 'nosniff' },
    });
  };
  return { fetch, requests };
}

test('verifies directory URLs, pages, assets and the exact public manifest under root and project paths', async () => {
  const { verifyLiveSite } = await load();
  for (const path of ['/', base]) await fixture(async (directory, files) => {
    const remote = transport(files, path);
    const report = await verifyLiveSite({ directory, url: origin + path, commit: sha, mode: 'deploy', fetch: remote.fetch });
    assert.equal(report.passed, true);
    assert.equal(report.code_commit, sha);
    assert.equal(report.snapshot_id, 'pilot-0123456789ab');
    assert.equal(report.pages_checked, 2);
    assert.equal(report.files_checked, 5);
    assert.equal(report.base_path, path);
    assert.equal(report.response_headers['x-content-type-options'], 'nosniff');
    assert.equal(report.response_headers['x-robots-tag'], null);
    assert.ok(remote.requests.includes(origin + path));
    assert.ok(remote.requests.includes(origin + path + 'parks/yose/'));
    assert.ok(remote.requests.includes(origin + path + '_astro/site.css'));
    assert.ok(remote.requests.includes(origin + path + 'build.json'));
    assert.ok(!remote.requests.some(address => address.endsWith('_headers')));
    assert.ok(!JSON.stringify(report).includes(directory));
  }, path);
});

test('refuses stale HTML, wrong assets and wrong live manifests for deploy and rollback', async () => {
  const { verifyLiveSite } = await load();
  for (const mode of ['deploy', 'rollback']) for (const name of ['index.html', '_astro/site.css', 'build.json']) {
    await fixture(async (directory, files) => {
      const remote = transport({ ...files, [name]: 'stale deployment' });
      const report = await verifyLiveSite({ directory, url, commit: sha, mode, fetch: remote.fetch, attempts: 1 });
      assert.equal(report.passed, false);
      assert.equal(report.reason, 'content_mismatch');
      assert.equal(report.mode, mode);
    });
  }
});

test('refuses redirects, missing pages, provider errors and unexpected content encoding', async () => {
  const { verifyLiveSite } = await load();
  for (const response of [new Response('', { status: 302, headers: { Location: 'https://other.example/' } }),
    new Response('missing', { status: 404 }), new Response('error', { status: 503 }),
    new Response('compressed', { headers: { 'Content-Encoding': 'gzip' } })]) {
    await fixture(async directory => {
      const report = await verifyLiveSite({ directory, url, commit: sha, mode: 'deploy', attempts: 1,
        fetch: async () => response.clone() });
      assert.equal(report.passed, false);
    });
  }
});

test('retries propagation failures and reports a later exact match', async () => {
  const { verifyLiveSite } = await load();
  await fixture(async (directory, files) => {
    const remote = transport(files);
    let calls = 0;
    const report = await verifyLiveSite({ directory, url, commit: sha, mode: 'rollback',
      sleep: async () => {}, fetch: async (address, options) => ++calls === 1
        ? new Response('old site') : remote.fetch(address, options) });
    assert.equal(report.passed, true);
    assert.equal(report.attempts, 2);
    assert.equal(report.mode, 'rollback');
  });
});

test('refuses invalid release identity and unsafe URLs before making requests', async () => {
  const { verifyLiveSite } = await load();
  const cases = [{ commit: 'HEAD' }, { mode: 'automatic' }, { url: origin + '/wrong/' },
    { url: 'http://vasuki8.github.io' + base }, { url: url + '?key=private' },
    { url: url + '#fragment' }, { url: 'https://name:password@vasuki8.github.io' + base }];
  for (const change of cases) await fixture(async directory => {
    let calls = 0;
    const report = await verifyLiveSite({ directory, url, commit: sha, mode: 'deploy', ...change,
      fetch: async () => { calls++; throw Error('should not contact provider'); } });
    assert.equal(report.passed, false);
    assert.equal(calls, 0);
    assert.ok(!JSON.stringify(report).includes('password'));
    assert.ok(!JSON.stringify(report).includes('key=private'));
  });
});

test('refuses an artifact for another commit and missing or malformed manifests offline', async () => {
  const { verifyLiveSite } = await load();
  for (const content of ['{broken', '[]', JSON.stringify({ code_commit: 'b'.repeat(40), base_path: base })]) {
    await fixture(async directory => {
      await writeFile(join(directory, 'build.json'), content);
      let calls = 0;
      const report = await verifyLiveSite({ directory, url, commit: sha, mode: 'deploy',
        fetch: async () => { calls++; throw Error('should not contact provider'); } });
      assert.equal(report.passed, false);
      assert.equal(calls, 0);
    });
  }
});

test('refuses symlinks and oversized local artifacts before network', async () => {
  const { verifyLiveSite } = await load();
  for (const kind of ['symlink', 'oversized']) await fixture(async directory => {
    if (kind === 'symlink') await symlink(join(directory, 'index.html'), join(directory, 'leak.html'));
    else await writeFile(join(directory, 'large.bin'), Buffer.alloc(4 * 1024 * 1024 + 1));
    let calls = 0;
    const report = await verifyLiveSite({ directory, url, commit: sha, mode: 'deploy',
      fetch: async () => { calls++; throw Error('should not contact provider'); } });
    assert.equal(report.passed, false);
    assert.equal(calls, 0);
  });
});

test('bounds response sizes and redacts transport failures', async () => {
  const { verifyLiveSite } = await load();
  for (const kind of ['oversized', 'timeout']) await fixture(async directory => {
    const report = await verifyLiveSite({ directory, url, commit: sha, mode: 'deploy', attempts: 1,
      fetch: async () => {
        if (kind === 'timeout') throw Error('private credential and path');
        return new Response(Buffer.alloc(4 * 1024 * 1024 + 1));
      } });
    assert.equal(report.passed, false);
    assert.ok(!JSON.stringify(report).includes('credential'));
  });
});
