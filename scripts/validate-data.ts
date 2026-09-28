/** Build gate for the curated inventory and collector-produced snapshots. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { isCalendarDate } from '../src/lib/readiness.ts';
const hosts = new Set(['www.nps.gov', 'nps.gov', 'home.nps.gov']);
const required = (value: unknown) => assert.ok(typeof value === 'string' && value.trim().length > 0);
const validTime = (value: unknown) => typeof value === 'string' && /^(?:[01]\d|2[0-3]):[0-5]\d$/.test(value);
function source(value: string, code: string): void {
  const url = new URL(value);
  assert.ok(url.protocol === 'https:' && hosts.has(url.hostname) && !url.username && !url.password && !url.port);
  assert.ok(url.pathname.startsWith(`/${code}/`));
  assert.ok(!/api.?key|token|secret/i.test(url.search));
}
function timestamp(value: unknown): number {
  assert.ok(typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.test(value));
  assert.ok(isCalendarDate(value.slice(0, 10)));
  const time = Date.parse(value);
  assert.ok(Number.isFinite(time));
  return time;
}
export function validateInventory(parks: any[]): void {
  assert.ok(Array.isArray(parks) && parks.length === 5);
  assert.equal(new Set(parks.map((p) => p.code)).size, parks.length);
  assert.deepEqual([...parks.map((p) => p.code)].sort(), ['grca', 'romo', 'yell', 'yose', 'zion']);
  assert.equal(new Set(parks.map((p) => p.slug)).size, parks.length);
  for (const park of parks) {
    assert.match(park.slug, /^[a-z]+(?:-[a-z]+)*$/);
    required(park.name); required(park.summary);
    assert.ok(Array.isArray(park.states) && park.states.length > 0);
    park.states.forEach(required);
    new Intl.DateTimeFormat('en', { timeZone: park.timezone }).format();
    for (const key of ['official_url', 'conditions_url', 'entry_url']) source(park[key], park.code);
    assert.ok(Array.isArray(park.areas) && park.areas.length > 0);
    assert.equal(new Set(park.areas.map((a: any) => a.id)).size, park.areas.length);
    for (const area of park.areas) { required(area.id); required(area.label); }
  }
}
export function validateRule(rule: any, parks: any[]): void {
  const park = parks.find((p) => p.code === rule.park_code);
  assert.ok(park); required(rule.id); required(rule.summary); required(rule.exception_note);
  assert.ok(Array.isArray(rule.areas) && rule.areas.length > 0);
  for (const area of rule.areas) assert.ok(area === '*' || park.areas.some((a: any) => a.id === area));
  assert.ok(isCalendarDate(rule.effective_from) && isCalendarDate(rule.effective_to) && rule.effective_from <= rule.effective_to);
  assert.equal(rule.effective_from.slice(0, 4), rule.effective_to.slice(0, 4), 'Annual rules cannot silently span years.');
  assert.ok(['timed_entry', 'no_timed_entry'].includes(rule.requirement));
  assert.ok(['reviewed', 'needs_review', 'conflict'].includes(rule.review_status));
  if (rule.requirement === 'timed_entry') assert.ok(validTime(rule.start_time) && validTime(rule.end_time) && rule.start_time < rule.end_time);
  else assert.ok(rule.start_time === null && rule.end_time === null);
  timestamp(rule.reviewed_at);
  source(rule.evidence.url, rule.park_code);
  required(rule.evidence.excerpt);
  assert.equal(rule.evidence.reviewed_at, rule.reviewed_at);
  assert.equal(rule.evidence.method, 'manual_official_page_review');
  assert.equal(rule.evidence.hash_scope, 'excerpt');
  assert.equal(rule.evidence.content_hash, createHash('sha256').update(rule.evidence.excerpt).digest('hex'));
  assert.equal(rule.evidence.source_updated_at, null, 'These editorial excerpts do not claim a field-specific source update time.');
  required(rule.rights_basis); timestamp(rule.rights_reviewed_at);
}
export function validateSnapshot(snapshot: any, code: string): void {
  assert.equal(snapshot.schema_version, 1); assert.equal(snapshot.park_code, code); assert.equal(snapshot.provider, 'NPS');
  const url = new URL(snapshot.source_url);
  assert.equal(url.origin, 'https://developer.nps.gov'); assert.equal(url.pathname, '/api/v1/alerts');
  assert.equal(url.searchParams.get('parkCode'), code);
  assert.deepEqual([...url.searchParams.keys()], ['parkCode']);
  assert.ok(['never_checked', 'success', 'failed', 'quarantined'].includes(snapshot.collection_status));
  assert.ok(['not_collected', 'checked_feed_only', 'incomplete'].includes(snapshot.coverage_status));
  assert.ok(Array.isArray(snapshot.records));
  if (snapshot.collection_status === 'never_checked') {
    assert.equal(snapshot.last_checked_at, null); assert.equal(snapshot.last_successful_fetch_at, null);
    assert.equal(snapshot.records.length, 0); assert.equal(snapshot.coverage_status, 'not_collected');
  } else {
    timestamp(snapshot.last_checked_at);
    if (snapshot.last_successful_fetch_at !== null) assert.ok(timestamp(snapshot.last_successful_fetch_at) <= timestamp(snapshot.last_checked_at));
    else assert.equal(snapshot.records.length, 0);
    if (snapshot.collection_status === 'success') {
      assert.equal(snapshot.last_successful_fetch_at, snapshot.last_checked_at); assert.equal(snapshot.coverage_status, 'checked_feed_only');
    } else assert.equal(snapshot.coverage_status, 'incomplete');
  }
  assert.equal(new Set(snapshot.records.map((r: any) => r.id)).size, snapshot.records.length);
  for (const item of snapshot.records) {
    for (const key of ['id', 'title', 'category']) required(item[key]);
    assert.equal(typeof item.description, 'string'); source(item.url, code);
    assert.equal(item.park_code, code); assert.equal(item.area_id, null); assert.equal(item.scope_status, 'unclassified');
    assert.equal(item.effective_from, null); assert.equal(item.effective_to, null); assert.equal(item.source_updated_at, null);
    assert.ok(timestamp(item.observed_first_at) <= timestamp(item.observed_changed_at));
    assert.ok(timestamp(item.observed_changed_at) <= timestamp(snapshot.last_successful_fetch_at));
    const canonical = Object.fromEntries(['category', 'description', 'id', 'title', 'url'].map((key) => [key, item[key]]));
    assert.equal(item.content_hash, createHash('sha256').update(JSON.stringify(canonical)).digest('hex'));
  }
}
export function validateData(root = 'data'): void {
  const read = (path: string) => JSON.parse(readFileSync(resolve(root, path), 'utf8'));
  const parks = read('parks.json'); const rules = read('rules.json');
  validateInventory(parks); assert.ok(Array.isArray(rules));
  assert.equal(new Set(rules.map((r: any) => r.id)).size, rules.length);
  rules.forEach((r: any) => validateRule(r, parks));
  assert.deepEqual(readdirSync(resolve(root, 'alerts')).filter((p) => p.endsWith('.json')).sort(), parks.map((p: any) => `${p.code}.json`).sort());
  for (const park of parks) validateSnapshot(read(`alerts/${park.code}.json`), park.code);
  console.log(`Validated ${parks.length} parks, ${rules.length} reviewed rules and ${parks.length} alert snapshots.`);
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) validateData();
