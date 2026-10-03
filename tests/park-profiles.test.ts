import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { cpSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { validatePublicProfiles, validateProfileRights } from '../scripts/validate-park-profiles.ts';
import { validateData } from '../scripts/validate-data.ts';

const root = resolve(import.meta.dirname, '..');
const python = `
import json
from tracker.park_profiles import collect_profile, initial_profile, PILOT_CODES
from tracker.profile_checkpoints import validate_checkpoint
from tracker.history_model import digest
clock = '2026-10-02T10:00:00.123456Z'
profiles=[]
for code in PILOT_CODES:
    raw={'id':code+'-synthetic', 'parkCode':code, 'fullName':'Synthetic '+code,
         'url':'https://www.nps.gov/'+code+'/',
         'description':'Synthetic café \\U0001f332'+''.join(chr(n) for n in (8,9,10,13,12,34,92,0x2028)),
         'weatherInfo':'Synthetic seasonal context, not a forecast.',
         'activities':[{'id':'\\U00010000','name':'Synthetic astral category'},
                       {'id':'\\ue000','name':'Synthetic BMP category'}]}
    profiles.append(collect_profile(code, initial_profile(code), clock,
        lambda start, raw=raw: {'total':'1','start':'0','data':[raw]}))
body={'schema_version':1,'purpose':'private_park_profile_checkpoint',
      'parent_checkpoint_id':None,'checked_at':clock,'profiles':profiles}
checkpoint=validate_checkpoint({**body,'checkpoint_id':digest(body)})
print(json.dumps({'schema_version':1,'purpose':'public_park_profiles',
                  'profiles':checkpoint['profiles']},ensure_ascii=False))
`;
const result = spawnSync('python', ['-s', '-c', python], {cwd: root, encoding: 'utf8', timeout: 30_000,
  env: {...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONIOENCODING: 'utf-8'}, maxBuffer: 1024 * 1024});
assert.equal(result.status, 0, result.stderr);
const fixture = JSON.parse(result.stdout);
const policy = JSON.parse(readFileSync(join(root, 'data/source-rights.json'), 'utf8')).policy;
function dataset() { return structuredClone(fixture); }
function rights(data = dataset()): any {
  return {schema_version: 1, purpose: 'public_park_profile_text_rights', reviewed_at: '2026-10-02T10:00:01Z',
    review_method: 'official_nps_policy_and_exact_profile_review', policy: structuredClone(policy),
    records: data.profiles.map((s: any) => ({park_code: s.park_code, profile_id: s.profile.id,
      source_url: s.source_url, content_hash: s.profile.content_hash, classification: 'nps_government_text',
      use_scope: 'normalized_profile_text_and_category_names', third_party_material_reproduced: false,
      nps_marks_reproduced: false, media_reproduced: false}))};
}
// Independent fixture rehashing permits malformed values to reach structural checks.
const canonical = (value: any): string => value && typeof value === 'object'
    ? Array.isArray(value) ? '[' + value.map(canonical).join(',') + ']'
      : '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}'
    : JSON.stringify(value);
function rehash(profile: any) {
  const fields = ['activity_categories','activity_scope','description','full_name','id','park_code','seasonal_weather','url'];
  const semantic = Object.fromEntries(fields.map(key => [key, profile[key]]));
  profile.content_hash = createHash('sha256').update(canonical(semantic)).digest('hex');
}
function temporary(fn: (dir: string) => void) {
  const dir = mkdtempSync(join(tmpdir(), 'public-profiles-'));
  try {
    const data = join(dir, 'data');
    cpSync(join(root, 'data'), data, {recursive: true});
    // Each case installs its own profile evidence; real promoted data is unrelated.
    for (const file of ['park-profiles.json', 'profile-source-rights.json']) rmSync(join(data, file), {force: true});
    fn(data);
  }
  finally { rmSync(dir, {recursive: true, force: true}); }
}

test('Python checkpoint projections validate without changing hashes, Unicode ordering or clocks', () => {
  const data = dataset(), manifest = rights(data);
  assert.deepEqual(validatePublicProfiles(data), data);
  assert.deepEqual(validateProfileRights(manifest, data), manifest);
  assert.equal(data.profiles[0].profile.activity_categories[0].id, '\ue000');
  assert.equal(data.profiles[0].last_successful_fetch_at, '2026-10-02T10:00:00.123456Z');
  const copy = validatePublicProfiles(data);
  copy.profiles[0].profile.description = 'Edited returned copy';
  assert.equal(data.profiles[0].profile.description, 'Synthetic café 🌲\b\t\n\r\f"\\\u2028');
  const reviewed = validateProfileRights(manifest, data);
  reviewed.records[0].content_hash = '0'.repeat(64);
  assert.notEqual(manifest.records[0].content_hash, reviewed.records[0].content_hash);
});

test('optional null and empty profile values remain distinct valid source states', () => {
  for (const empty of [false, true]) {
    const data = dataset(), p = data.profiles[0].profile;
    p.description = empty ? '' : null; p.seasonal_weather = empty ? {kind: 'seasonal_context', text: ''} : null;
    p.activity_categories = empty ? [] : null; rehash(p);
    assert.deepEqual(validatePublicProfiles(data), data);
    validateProfileRights(rights(data), data);
  }
});

test('degraded snapshots preserve the retained profile and successful-fetch clock', () => {
  for (const status of ['failed', 'quarantined']) {
    const data = dataset();
    for (const s of data.profiles) Object.assign(s, {collection_status: status, coverage_status: 'incomplete',
      last_checked_at: '2026-10-02T10:00:01Z', error_code: status === 'failed' ? 'provider_request_failed' : 'response_requires_review'});
    assert.deepEqual(validatePublicProfiles(data), data);
    validateProfileRights(rights(data), data);
  }
});

test('public inventory refuses absent evidence, duplicate parks and changed pilot order', () => {
  const mutations = [(d: any) => d.profiles.pop(), (d: any) => d.profiles.reverse(),
    (d: any) => d.profiles[1] = d.profiles[0], (d: any) => d.profiles[0].profile = null,
    (d: any) => d.profiles[0].last_successful_fetch_at = null,
    (d: any) => d.profiles[0].collection_status = 'never_checked'];
  for (const mutate of mutations) { const data = dataset(); mutate(data); assert.throws(() => validatePublicProfiles(data)); }
});

test('public profiles preserve the common five-park checkpoint attempt clock', () => {
  const data = dataset(), s = data.profiles[1];
  s.last_checked_at = s.last_successful_fetch_at = '2026-10-02T10:00:01Z';
  assert.throws(() => validatePublicProfiles(data));
});

test('unknown fields are refused at every public schema level', () => {
  for (const target of ['dataset', 'snapshot', 'profile', 'weather', 'category']) {
    const data = dataset(), s = data.profiles[0];
    ({dataset: data, snapshot: s, profile: s.profile, weather: s.profile.seasonal_weather,
      category: s.profile.activity_categories[0]} as any)[target].unreviewed = 'must not cross';
    assert.throws(() => validatePublicProfiles(data));
  }
});

test('profile interpretation, hashes and all publisher clocks fail closed', () => {
  const mutations = [(s: any) => s.profile.description += ' changed', (s: any) => s.profile.hash_scope = 'raw_payload',
    (s: any) => s.profile.activity_scope = 'individual_activities',
    (s: any) => s.profile.seasonal_weather.kind = 'forecast', (s: any) => s.profile.source_updated_at = s.last_checked_at,
    ...['source_issued_at','source_updated_at','published_at'].map(key => (s: any) => s[key] = s.last_checked_at)];
  for (const mutate of mutations) { const data = dataset(); mutate(data.profiles[0]); assert.throws(() => validatePublicProfiles(data)); }
});

test('malformed dates and submillisecond observation ordering are refused', () => {
  for (const value of ['2026-02-30T10:00:00Z', '0000-01-01T00:00:00Z', '2026-10-02T24:00:00Z',
    '2026-10-02T10:00:00+00:99', '2026-10-02T10:00:00.1234567Z', '2026-10-02',
    '0001-01-01T00:00:00+01:00', '9999-12-31T23:59:59-01:00']) {
    const data = dataset(); data.profiles[0].last_checked_at = value; assert.throws(() => validatePublicProfiles(data));
  }
  const data = dataset(); data.profiles[0].profile.observed_changed_at = '2026-10-02T10:00:00.123457Z';
  assert.throws(() => validatePublicProfiles(data));
  for (const value of ['0001-01-01T00:00:00+01:00', '9999-12-31T23:59:59-01:00']) {
    const data = dataset(), s = data.profiles[0];
    s.last_checked_at = s.last_successful_fetch_at = s.profile.observed_first_at = s.profile.observed_changed_at = value;
    assert.throws(() => validatePublicProfiles(data), value);
  }
});

test('URL normalization cannot hide traversal, wrong parks or credentials', () => {
  for (const url of ['https://www.nps.gov/grca/', 'https://www.nps.gov/yose/../yose/',
    'https://www.nps.gov/yose/%2e%2e/yose/', 'https://www.nps.gov//yose/', 'https://www.nps.gov/yose//',
    'https://www.nps.gov.evil.test/yose/', 'https://user@www.nps.gov/yose/', 'https://%77ww.nps.gov/yose/',
    'https://www.nps.gov/yose/?%74oken=private', 'https://www.nps.gov/yose/#%73ecret=private']) {
    const data = dataset(); data.profiles[0].profile.url = url; rehash(data.profiles[0].profile);
    assert.throws(() => validatePublicProfiles(data), url);
  }
});

test('Python scalar category order, category uniqueness and valid Unicode are enforced', () => {
  for (const mutate of [(p: any) => p.activity_categories.reverse(),
    (p: any) => p.activity_categories.push(p.activity_categories[0]), (p: any) => p.description = '\ud800',
    (p: any) => p.id = 'bad\nid', (p: any) => p.full_name = '']) {
    const data = dataset(); mutate(data.profiles[0].profile); rehash(data.profiles[0].profile);
    assert.throws(() => validatePublicProfiles(data));
  }
});

test('rights evidence binds exact profile identity, content and source once per pilot', () => {
  for (const mutate of [(r: any) => r.records.reverse(), (r: any) => r.records.pop(),
    (r: any) => r.records[1] = r.records[0], (r: any) => r.records[0].content_hash = '0'.repeat(64),
    (r: any) => r.records[0].profile_id = 'other', (r: any) => r.records[0].source_url = fixture.profiles[1].source_url,
    (r: any) => r.purpose = 'public_guidance_text_only', (r: any) => r.records[0].unreviewed = true]) {
    const manifest = rights(); mutate(manifest); assert.throws(() => validateProfileRights(manifest, dataset()));
  }
});

test('profile rights require exact policy, permitted text scope and a nonrewound review clock', () => {
  for (const mutate of [(r: any) => r.reviewed_at = '2026-02-30T10:00:00Z',
    (r: any) => r.reviewed_at = '2026-10-02T10:00:00.123455Z', (r: any) => r.policy.ownership_url = 'https://example.test/',
    (r: any) => r.policy.raw_private_captures_public = true, (r: any) => r.review_method = 'api_origin',
    (r: any) => r.records[0].use_scope = 'short_text_excerpt_and_original_summary',
    ...['third_party_material_reproduced','nps_marks_reproduced','media_reproduced'].map(key => (r: any) => r.records[0][key] = true)]) {
    const manifest = rights(); mutate(manifest); assert.throws(() => validateProfileRights(manifest, dataset()));
  }
  const data = dataset();
  for (const s of data.profiles) Object.assign(s, {collection_status: 'failed', coverage_status: 'incomplete',
    error_code: 'provider_request_failed', last_checked_at: '2026-10-02T10:00:02Z'});
  assert.throws(() => validateProfileRights(rights(data), data));
});

test('public profile validators reject oversized input before returning it', () => {
  const data = dataset();
  const categories = Array.from({length: 500}, (_, index) => ({id: 'category-' + String(index).padStart(4, '0'), name: 'x'.repeat(4096)}));
  data.profiles[0].profile.activity_categories = categories; rehash(data.profiles[0].profile);
  validatePublicProfiles(data); // A two-megabyte valid control remains accepted.
  for (const s of data.profiles.slice(1)) { s.profile.activity_categories = categories; rehash(s.profile); }
  assert.throws(() => validatePublicProfiles(data));
  const manifest = rights(); manifest.oversized = 'x'.repeat(8 * 1024 * 1024);
  assert.throws(() => validateProfileRights(manifest, dataset()));
});

test('normal build accepts no profile pair and rejects partial or invalid profile additions', () => temporary(dir => {
  validateData(dir);
  const data = dataset(), manifest = rights(data);
  writeFileSync(join(dir, 'park-profiles.json'), canonical(data));
  assert.throws(() => validateData(dir));
  writeFileSync(join(dir, 'profile-source-rights.json'), canonical(manifest));
  validateData(dir);
  data.profiles[0].profile.description += ' unreviewed change';
  writeFileSync(join(dir, 'park-profiles.json'), canonical(data));
  assert.throws(() => validateData(dir));
  rmSync(join(dir, 'park-profiles.json'));
  assert.throws(() => validateData(dir));
}));

test('public profile files require canonical JSON and reject duplicates or invalid UTF-8', () => temporary(dir => {
  const files = ['park-profiles.json', 'profile-source-rights.json'];
  const values = [dataset(), rights()];
  const texts = values.map(canonical);
  files.forEach((file, i) => writeFileSync(join(dir, file), texts[i]));
  validateData(dir);
  for (let i = 0; i < files.length; i++) {
    for (const bad of ['{"purpose":"discarded duplicate",' + texts[i].slice(1),
      JSON.stringify(values[i], null, 2), Buffer.concat([Buffer.from([0xff]), Buffer.from(texts[i])]),
      '\ufeff' + texts[i], texts[i] + '\n\n']) {
      writeFileSync(join(dir, files[i]), bad);
      assert.throws(() => validateData(dir));
    }
    writeFileSync(join(dir, files[i]), texts[i] + '\n');
    validateData(dir); // Exactly one final newline is a valid producer representation.
  }
}));

test('dangling profile file links cannot make the new dataset silently absent', () => temporary(dir => {
  symlinkSync(join(dir, 'missing-profile-target'), join(dir, 'park-profiles.json'), 'junction');
  assert.throws(() => validateData(dir));
}));

test('a linked public data directory cannot bypass profile file provenance checks', () => temporary(dir => {
  writeFileSync(join(dir, 'park-profiles.json'), canonical(dataset()));
  writeFileSync(join(dir, 'profile-source-rights.json'), canonical(rights()));
  validateData(dir);
  const alias = join(dirname(dir), 'linked-data');
  symlinkSync(dir, alias, 'junction');
  assert.throws(() => validateData(alias));
}));
