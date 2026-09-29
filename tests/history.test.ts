import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateHistory, historyDigest } from '../scripts/validate-history.ts';
import { describeHistory } from '../src/lib/history.ts';
const fixture = JSON.parse(readFileSync(new URL('./fixtures/history-preview.json', import.meta.url), 'utf8'));
const copy = (name = 'mixed') => structuredClone(fixture.cases[name]);
const now = new Date('2026-09-28T13:00:00Z');
test('Python archive projection hashes and all fixture states validate in TypeScript', () => {
  for (const view of Object.values(fixture.cases) as any[]) {
    assert.equal(historyDigest(view.snapshot), view.history.snapshot_hash);
    assert.deepEqual(validateHistory(view.history, view.snapshot), view.history);
  }
});
test('all five committed histories match never-collected public snapshots', () => {
  const histories = JSON.parse(readFileSync(new URL('../data/history.json', import.meta.url), 'utf8'));
  assert.equal(histories.length, 5); assert.equal(new Set(histories.map((h: any) => h.park_code)).size, 5);
  for (const h of histories) {
    const snapshot = JSON.parse(readFileSync(new URL(`../data/alerts/${h.park_code}.json`, import.meta.url), 'utf8'));
    validateHistory(h, snapshot); assert.equal(h.total_observations, 0);
  }
});
test('mismatched snapshot contents, status, clock and park fail closed', () => {
  for (const mutate of [(v: any) => v.snapshot.records[0].title = 'Altered', (v: any) => v.snapshot.park_code = 'zion',
    (v: any) => v.snapshot.collection_status = 'failed', (v: any) => v.snapshot.last_checked_at = '2026-09-28T15:00:00Z']) {
    const v = copy(); mutate(v); assert.throws(() => validateHistory(v.history, v.snapshot));
  }
});
test('a rehashed snapshot with a different observation clock cannot be substituted', () => {
  const v = copy(); v.snapshot.last_checked_at = '2026-09-28T15:00:00Z';
  v.history.snapshot_hash = historyDigest(v.snapshot); assert.throws(() => validateHistory(v.history, v.snapshot));
});
test('alert evidence permits a missing link and official NPS shared/subdomain links', () => {
  for (const url of [null, 'https://go.nps.gov/short-link', 'https://www.nps.gov/subjects/developer/index.htm', 'https://inciweb.wildfire.gov/incident/example']) {
    const v = copy(); v.history.observations[0].changes[0].after.url = url;
    v.history.observations[0].changes[0].after.content_hash = historyDigest(Object.fromEntries(
      ['category','description','id','title','url'].map((key) => [key, v.history.observations[0].changes[0].after[key]])
    ));
    v.snapshot.records[0].url = url;
    v.snapshot.records[0].content_hash = v.history.observations[0].changes[0].after.content_hash;
    v.history.snapshot_hash = historyDigest(v.snapshot);
    validateHistory(v.history, v.snapshot);
  }
});
test('before and after evidence reject tampering, wrong park and unsafe URLs', () => {
  for (const mutate of [(e: any) => e.description = 'Changed', (e: any) => e.url = 'javascript:alert(1)',
    (e: any) => e.url = 'https://www.nps.gov.evil.test/yose/test.htm',
    (e: any) => e.url = 'https://www.nps.gov/yose/../zion/test.htm', (e: any) => e.url = 'https://www.nps.gov/yose/test.htm#token=private',
    (e: any) => e.id = 'another-id']) {
    const v = copy(); mutate(v.history.observations[0].changes[0].after);
    assert.throws(() => validateHistory(v.history, v.snapshot));
  }
});
test('unknown private fields are rejected at every exposed level', () => {
  for (const mutate of [(v: any) => v.history.pending = {}, (v: any) => v.history.observations[0].private_path = '/state',
    (v: any) => v.history.observations[0].changes[0].raw_response = 'secret',
    (v: any) => v.history.observations[0].changes[0].after.headers = {}]) {
    const v = copy(); mutate(v); assert.throws(() => validateHistory(v.history, v.snapshot));
  }
});
test('missing, duplicate, malformed and out-of-order observations cannot be accepted', () => {
  for (const mutate of [(h: any) => h.observations.pop(), (h: any) => h.observations[1] = h.observations[0],
    (h: any) => h.observations[0].checked_at = '2026-02-30T12:00:00Z', (h: any) => h.observations[0].sequence = 1,
    (h: any) => h.head_observation_id = 'bad', (h: any) => h.schema_version = true]) {
    const v = copy(); mutate(v.history); assert.throws(() => validateHistory(v.history, v.snapshot));
  }
});
test('event kinds and before-after relationships are validated', () => {
  for (const mutate of [(c: any) => c.kind = 'reopened', (c: any) => c.before = null,
    (c: any) => c.after = null, (c: any) => c.before = c.after]) {
    const v = copy(); mutate(v.history.observations[0].changes[0]); assert.throws(() => validateHistory(v.history, v.snapshot));
  }
});
test('baselines and failed observations cannot acquire fabricated changes', () => {
  for (const name of ['baseline', 'failed']) {
    const v = copy(name); v.history.observations[0].changes = copy().history.observations[0].changes;
    assert.throws(() => validateHistory(v.history, v.snapshot));
  }
});
test('omitted counts must reconcile and cannot silently hide visible changes', () => {
  for (const mutate of [(h: any) => h.total_changes = 0, (h: any) => h.omitted_changes = 0,
    (h: any) => h.omitted_observations = -1, (h: any) => h.observations[0].omitted_changes = 1]) {
    const v = copy('truncated'); mutate(v.history); assert.throws(() => validateHistory(v.history, v.snapshot));
  }
});
test('empty history cannot be paired with a collected snapshot', () => {
  const v = copy('empty'); const s = copy().snapshot; v.history.snapshot_hash = historyDigest(s);
  assert.throws(() => validateHistory(v.history, s));
});
test('rendered freshness expires without altering observation timestamps', () => {
  const v = copy(); const original = structuredClone(v);
  assert.match(describeHistory(v.snapshot, now).title, /Recent/);
  assert.match(describeHistory(v.snapshot, new Date('2026-09-28T16:00:00.001Z')).title, /fresh check/);
  assert.deepEqual(v, original);
});
test('failed and quarantined histories remain degraded even with fresh retained data', () => {
  const v = copy('failed');
  assert.match(describeHistory(v.snapshot, new Date('2026-09-28T14:01:00Z')).title, /not successful/);
  v.snapshot.collection_status = 'quarantined';
  assert.match(describeHistory(v.snapshot, now).title, /not successful/);
});
test('empty, invalid-clock and future checks do not become current history', () => {
  assert.match(describeHistory(copy('empty').snapshot, now).title, /not collected/);
  assert.match(describeHistory(copy().snapshot, new Date('invalid')).title, /fresh check/);
  assert.match(describeHistory(copy().snapshot, new Date('2026-09-27')).title, /fresh check/);
});
test('a failed head cannot relabel the time of the visible last successful observation', () => {
  const v = copy('failed'); v.snapshot.last_successful_fetch_at = '2026-09-28T13:00:00Z';
  v.history.snapshot_hash = historyDigest(v.snapshot);
  assert.throws(() => validateHistory(v.history, v.snapshot));
});
test('an all-failed visible window cannot invent a success inside that window', () => {
  const v = copy('truncated'); v.snapshot.last_successful_fetch_at = v.snapshot.last_checked_at;
  v.history.snapshot_hash = historyDigest(v.snapshot);
  assert.throws(() => validateHistory(v.history, v.snapshot));
});
test('year zero is not a valid archive timestamp', () => {
  const v = JSON.parse(JSON.stringify(copy()).replaceAll('2026-', '0000-'));
  v.history.snapshot_hash = historyDigest(v.snapshot);
  assert.throws(() => validateHistory(v.history, v.snapshot));
});
