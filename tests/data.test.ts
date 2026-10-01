import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateInventory, validateRule, validateSnapshot } from '../scripts/validate-data.ts';
import { validateSourceRights } from '../scripts/validate-source-rights.ts';
import { syntheticEmptyViews } from './synthetic-preview.ts';
const parks = JSON.parse(readFileSync('data/parks.json', 'utf8'));
const rules = JSON.parse(readFileSync('data/rules.json', 'utf8'));
const snapshot = JSON.parse(readFileSync('data/alerts/yose.json', 'utf8'));
const notes = JSON.parse(readFileSync('data/entry-notes.json', 'utf8'));
const sourceRights = JSON.parse(readFileSync('data/source-rights.json', 'utf8'));
const uncollected = syntheticEmptyViews()[0].snapshot;
test('production inventory contains exactly the five pilots', () => { validateInventory(parks); assert.equal(parks.length, 5); });
test('every stored rule has valid official evidence and an excerpt hash', () => { for (const rule of rules) validateRule(rule, parks); });
test('uncollected snapshots cannot claim a successful check', () => {
  assert.throws(() => validateSnapshot({ ...uncollected, last_successful_fetch_at: '2026-09-28T19:00:00Z' }, 'yose'));
});
test('successful snapshots require coherent timestamps', () => {
  assert.throws(() => validateSnapshot({ ...uncollected, collection_status: 'success' }, 'yose'));
});
test('all five public alert snapshots satisfy the production contract', () => {
  for (const park of parks) validateSnapshot(JSON.parse(readFileSync(`data/alerts/${park.code}.json`, 'utf8')), park.code);
});
test('rule evidence cannot point to a lookalike hostname', () => {
  assert.throws(() => validateRule({ ...rules[0], evidence: { ...rules[0].evidence, url: 'https://www.nps.gov.evil.test/yose/' } }, parks));
});
test('evidence tampering fails the build', () => {
  assert.throws(() => validateRule({ ...rules[0], evidence: { ...rules[0].evidence, excerpt: 'Modified without a new hash' } }, parks));
});
test('invalid dates, time windows and areas fail the build', () => {
  for (const change of [{ effective_to: '2026-02-30' }, { areas: ['invented'] }, { start_time: '25:00' }]) assert.throws(() => validateRule({ ...rules[0], ...change }, parks));
});
test('unknown collector states and duplicate park codes are rejected', () => {
  assert.throws(() => validateSnapshot({ ...snapshot, collection_status: 'all_clear' }, 'yose'));
  assert.throws(() => validateInventory([...parks, parks[0]]));
});

test('source-rights manifest exactly covers all public guidance records', () => {
  validateSourceRights(sourceRights, [...rules, ...notes]);
});
test('source-rights coverage cannot omit or duplicate a public guidance record', () => {
  assert.throws(() => validateSourceRights({ ...sourceRights, records: sourceRights.records.slice(1) }, [...rules, ...notes]));
  assert.throws(() => validateSourceRights({ ...sourceRights, records: [...sourceRights.records, sourceRights.records[0]] }, [...rules, ...notes]));
});
test('source-rights evidence cannot claim marks, media or third-party material are reproduced', () => {
  for (const change of [{ nps_marks_reproduced: true }, { media_reproduced: true }, { third_party_material_reproduced: true }]) {
    assert.throws(() => validateSourceRights({ ...sourceRights, records: [{ ...sourceRights.records[0], ...change }, ...sourceRights.records.slice(1)] }, [...rules, ...notes]));
  }
});
