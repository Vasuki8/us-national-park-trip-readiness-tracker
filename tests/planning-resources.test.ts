import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validatePlanningResources } from '../scripts/validate-planning-resources.ts';
const codes = ['yose', 'romo', 'yell', 'zion', 'grca'];
const categories = ['roads', 'facilities', 'camping', 'accessibility', 'fees', 'permits', 'weather'];
const now = new Date('2026-09-30T00:00:00Z');
const fixture = () => ({ schema_version: 1, review_scope: 'link_target_only', resources: codes.flatMap(park_code => categories.map(category => ({
  park_code, category, url: `https://www.nps.gov/${park_code}/planyourvisit/${category}.htm`, source_title: 'Synthetic link target',
  check_prompt: 'Review the official information for your planned visit.', link_reviewed_at: '2026-09-29T02:00:00Z',
}))) });
test('all seven topics for every pilot are accepted as links only', () => {
  const input = fixture(); assert.deepEqual(validatePlanningResources(input, codes, now), input.resources);
});
test('the committed register covers exactly 35 park-topic pairs', () => {
  const input = JSON.parse(readFileSync(new URL('../data/planning-resources.json', import.meta.url), 'utf8'));
  assert.equal(validatePlanningResources(input, codes).length, 35);
});
test('missing, duplicate and unknown park-topic pairs fail closed', () => {
  for (const mutate of [(v: any) => v.resources.pop(), (v: any) => v.resources.push(v.resources[0]),
    (v: any) => v.resources[1] = v.resources[0], (v: any) => v.resources[0].park_code = 'arch',
    (v: any) => v.resources[0].category = 'all_clear']) {
    const v = fixture(); mutate(v); assert.throws(() => validatePlanningResources(v, codes, now));
  }
});
test('cross-park, lookalike, encoded and credential-bearing URLs are refused', () => {
  for (const url of ['http://www.nps.gov/yose/planyourvisit/fees.htm', 'https://www.nps.gov/zion/planyourvisit/fees.htm',
    'https://www.nps.gov.evil.test/yose/planyourvisit/fees.htm', 'https://name:secret@www.nps.gov/yose/planyourvisit/fees.htm',
    'https://www.nps.gov:444/yose/planyourvisit/fees.htm', 'https://www.nps.gov/yose/planyourvisit/../fees.htm',
    'https://www.nps.gov/yose/planyourvisit/%2e%2e/fees.htm', 'https://www.nps.gov/yose/planyourvisit/fees.htm?api_key=x',
    'https://www.nps.gov/yose/planyourvisit/fees.htm#token=x', 'javascript:alert(1)',
    'https://www.nps.gov/yose/planyourvisit/fees.htm\n', 'https://www.nps.gov/yose/planyourvisit\\fees.htm']) {
    const v = fixture(); v.resources[0].url = url; assert.throws(() => validatePlanningResources(v, codes, now));
  }
});
test('link reviews cannot acquire operational status, fee or publication fields', () => {
  for (const field of ['open', 'price', 'forecast', 'effective_from', 'review_status', 'last_successful_fetch_at', 'published_at']) {
    const v: any = fixture(); v.resources[0][field] = true; assert.throws(() => validatePlanningResources(v, codes, now));
  }
});
test('envelope cannot claim an operational review or allow unknown fields', () => {
  for (const mutate of [(v: any) => v.schema_version = true, (v: any) => v.review_scope = 'current_conditions',
    (v: any) => v.approved = true, (v: any) => v.resources = {}]) {
    const v = fixture(); mutate(v); assert.throws(() => validatePlanningResources(v, codes, now));
  }
});
test('invalid, future, year-zero and impossible link review clocks fail', () => {
  for (const stamp of ['2026-02-30T02:00:00Z', '0000-01-01T02:00:00Z', '2026-09-30T00:00:01Z',
    '2026-09-29', '2026-09-29T25:00:00Z', 'not a date', '2026-09-29T02:00:00']) {
    const v = fixture(); v.resources[0].link_reviewed_at = stamp; assert.throws(() => validatePlanningResources(v, codes, now));
  }
  assert.throws(() => validatePlanningResources(fixture(), codes, new Date('invalid')));
});
test('empty, excessively long and malformed text is refused', () => {
  for (const field of ['source_title', 'check_prompt']) for (const text of ['', '   ', 'x'.repeat(601), 'bad\u0000text', '\ud800']) {
    const v: any = fixture(); v.resources[0][field] = text; assert.throws(() => validatePlanningResources(v, codes, now));
  }
});
test('inventory itself must be nonempty, unique, bounded and valid', () => {
  for (const inventory of [[], ['yose', 'yose'], ['../x'], Array(21).fill('yose')]) {
    assert.throws(() => validatePlanningResources(fixture(), inventory, now));
  }
});
test('valid Unicode and a real leap day survive unchanged', () => {
  const v = fixture(); v.resources[0].source_title = 'Café — planning'; v.resources[0].link_reviewed_at = '2024-02-29T00:00:00Z';
  assert.deepEqual(validatePlanningResources(v, codes, now)[0], v.resources[0]);
});
test('validation is order-independent and returns a defensive copy', () => {
  const v = fixture(); v.resources.reverse(); const result = validatePlanningResources(v, codes, now);
  assert.deepEqual(result, v.resources); result[0].source_title = 'different'; assert.notEqual(result[0].source_title, v.resources[0].source_title);
});
test('diagnostics do not echo private input', () => {
  const v = fixture(); v.resources[0].url = 'https://private.example/?secret=TEST_PRIVATE';
  assert.throws(() => validatePlanningResources(v, codes, now), { message: 'invalid_planning_resources' });
});
