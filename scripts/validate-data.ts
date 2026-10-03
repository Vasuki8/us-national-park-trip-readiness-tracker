/** Build gate for the curated inventory and collector-produced snapshots. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { isIP } from 'node:net';
import { lstatSync, readFileSync, readdirSync } from 'node:fs';
import { posix, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { isCalendarDate } from '../src/lib/readiness.ts';
import { validateSourceRights } from './validate-source-rights.ts';
import { canonicalProfileJson, MAX_PROFILE_BYTES, validatePublicProfiles, validateProfileRights } from './validate-park-profiles.ts';
const hosts = new Set(['www.nps.gov', 'nps.gov', 'home.nps.gov']);
const required = (value: unknown) => assert.ok(typeof value === 'string' && value.trim().length > 0);
const validTime = (value: unknown) => typeof value === 'string' && /^(?:[01]\d|2[0-3]):[0-5]\d$/.test(value);
function source(value: string, code: string): void {
  const url = new URL(value);
  assert.ok(url.protocol === 'https:' && hosts.has(url.hostname) && !url.username && !url.password && !url.port);
  assert.ok(url.pathname.startsWith(`/${code}/`));
  assert.ok(!/api.?key|token|secret/i.test(url.search));
}
function alertSource(value: unknown): void {
  if (value === null) return;
  assert.ok(typeof value === 'string' && value.length > 0);
  const url = new URL(value);
  const host = url.hostname.toLowerCase();
  const path = decodeURIComponent(value.replace(/^https:\/\/[^/]+/, '').split(/[?#]/)[0]);
  assert.ok(url.protocol === 'https:' && host && host !== 'localhost' && isIP(host) === 0
    && !url.username && !url.password && !url.port
    && !(host.includes('nps.gov') && host !== 'nps.gov' && !host.endsWith('.nps.gov')));
  assert.ok((!path || posix.normalize(path) === path) && !path.includes('\\'));
  assert.ok(!/api.?key|token|secret/i.test(decodeURIComponent(url.search + url.hash)));
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
    assert.equal(typeof item.description, 'string'); alertSource(item.url);
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
  const parks = read('parks.json'); const rules = read('rules.json'); const notes = read('entry-notes.json');
  const sourceRights = read('source-rights.json');
  validateInventory(parks); assert.ok(Array.isArray(rules));
  assert.equal(new Set(rules.map((r: any) => r.id)).size, rules.length);
  rules.forEach((r: any) => validateRule(r, parks));
  validateSourceRights(sourceRights, [...rules, ...notes]);
  assert.deepEqual(readdirSync(resolve(root, 'alerts')).filter((p) => p.endsWith('.json')).sort(), parks.map((p: any) => `${p.code}.json`).sort());
  for (const park of parks) validateSnapshot(read(`alerts/${park.code}.json`), park.code);
  const profileFilePresent = (path: string) => {
    try {
      const stat = lstatSync(resolve(root, path));
      assert.ok(stat.isFile() && stat.size <= MAX_PROFILE_BYTES, 'Public profile inputs must be bounded regular files.');
      return true;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') return false;
      throw error;
    }
  };
  const profilesPresent = profileFilePresent('park-profiles.json');
  const rightsPresent = profileFilePresent('profile-source-rights.json');
  assert.equal(profilesPresent, rightsPresent, 'Public park profiles require their paired exact text-rights manifest.');
  if (profilesPresent) {
    assert.ok(lstatSync(resolve(root)).isDirectory(), 'The public profile data directory must be a regular directory.');
    const readProfiles = (path: string) => {
      const bytes = readFileSync(resolve(root, path));
      assert.ok(bytes.length <= MAX_PROFILE_BYTES);
      const text = new TextDecoder('utf-8', {fatal: true, ignoreBOM: true}).decode(bytes);
      const value = JSON.parse(text), canonical = canonicalProfileJson(value);
      assert.ok(text === canonical || text === canonical + '\n', 'Public profile inputs must use canonical JSON.');
      return value;
    };
    const profiles = validatePublicProfiles(readProfiles('park-profiles.json'));
    validateProfileRights(readProfiles('profile-source-rights.json'), profiles);
  }
  console.log(`Validated ${parks.length} parks, ${rules.length} reviewed rules and ${parks.length} alert snapshots.`);
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) validateData();
