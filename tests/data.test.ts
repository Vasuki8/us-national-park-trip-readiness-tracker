import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateInventory, validateRule, validateSnapshot } from '../scripts/validate-data.ts';
const parks = JSON.parse(readFileSync('data/parks.json', 'utf8'));
const rules = JSON.parse(readFileSync('data/rules.json', 'utf8'));
const snapshot = JSON.parse(readFileSync('data/alerts/yose.json', 'utf8'));
test('production inventory contains exactly the five pilots', () => { validateInventory(parks); assert.equal(parks.length, 5); });
test('every stored rule has valid official evidence and an excerpt hash', () => { for (const rule of rules) validateRule(rule, parks); });
test('uncollected snapshots cannot claim a successful check', () => {
  assert.throws(() => validateSnapshot({ ...snapshot, last_successful_fetch_at: '2026-09-28T19:00:00Z' }, 'yose'));
});
test('successful snapshots require coherent timestamps', () => {
  assert.throws(() => validateSnapshot({ ...snapshot, collection_status: 'success' }, 'yose'));
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
