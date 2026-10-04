import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { cpSync, mkdirSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { MAX_ACTIVITY_BYTES, MAX_ACTIVITY_RIGHTS_BYTES, canonicalActivityJson, activityDigest,
  validatePublicActivities, validateActivityRights, validateActivityFiles } from '../scripts/validate-park-activities.ts';
import { validateData } from '../scripts/validate-data.ts';

const root = resolve(import.meta.dirname, '..');
function pythonFixture(large = false): any {
  const python = `
import json
from pathlib import Path
from tracker.park_activities import collect_activities, initial_activities, PILOT_CODES
from tracker.history_model import canonical, digest
clock = '2026-10-04T10:00:00.123456Z'
inventories = []
for code in PILOT_CODES:
    rows = []
    for index in range(${large ? 50 : 2}):
        rows.append({'id':${large ? "str(index).zfill(4)" : "('\\ue000', '\\U00010000')[index]"},
          'title':'Synthetic '+code+' café \\U0001f332', 'url':'https://www.nps.gov/thingstodo/synthetic.htm',
          'shortDescription':${large ? "'x'*50000" : "'Synthetic text '+''.join(chr(n) for n in (8,9,10,13,12,34,92,0x2028))"},
          'longDescription':'<b>Synthetic untrusted HTML</b>', 'location':'', 'locationDescription':None,
          'duration':'Unknown source duration', 'durationDescription':'', 'season':['\\U00010000','\\ue000'],
          'seasonDescription':'Synthetic seasonal text', 'accessibilityInformation':'Synthetic access text',
          'activities':[{'id':'\\U00010000','name':'Synthetic astral category'}, {'id':'\\ue000','name':'Synthetic BMP category'}],
          'activityDescription':'Synthetic activity description', 'doFeesApply':'false', 'feeDescription':'',
          'isReservationRequired':None, 'reservationDescription':None, 'arePetsPermitted':True,
          'arePetsPermittedWithRestrictions':'', 'petsDescription':'Synthetic pet text', 'age':'',
          'ageDescription':'Synthetic age text', 'timeOfDay':[], 'timeOfDayDescription':None, 'credit':'Synthetic credit',
          'relatedParks':[{'parkCode':code,'fullName':'Synthetic '+code,'url':'https://www.nps.gov/'+code+'/',
                           'states':'','designation':None,'name':'Synthetic name'}]})
    snapshot=collect_activities(code,initial_activities(code),clock,
      lambda start,rows=rows: {'total':len(rows),'start':start,'data':rows[start:]})
    assert snapshot['collection_status'] == 'success'
    inventories.append(snapshot)
data={'schema_version':1,'purpose':'public_park_activities','inventories':inventories}
policy=json.loads(Path('data/source-rights.json').read_text())['policy']
rights={'schema_version':1,'purpose':'public_park_activity_text_rights','reviewed_at':'2026-10-04T10:00:01Z',
  'review_method':'official_nps_policy_and_exact_activity_review','policy':policy,'records':[
  {'park_code':s['park_code'],'activity_id':r['id'],'source_url':s['source_url'],'content_hash':r['content_hash'],
   'classification':'nps_government_text','use_scope':'normalized_activity_text_and_metadata',
   'third_party_material_reproduced':False,'nps_marks_reproduced':False,'media_reproduced':False}
   for s in inventories for r in s['records']]}
encoded=canonical(data,max_bytes=42008576)
print(json.dumps({'dataset':data,'rights':rights,'digest':digest(data,max_bytes=42008576),
                  'bytes':len(encoded)},ensure_ascii=False))
`;
  const result = spawnSync('python', ['-s', '-c', python], {cwd: root, encoding: 'utf8', timeout: 60_000,
    env: {...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONIOENCODING: 'utf-8'}, maxBuffer: 30 * 1024 * 1024});
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}
const fixture = pythonFixture();
function dataset(): any { return structuredClone(fixture.dataset); }
function rights(data = dataset()): any {
  const result = structuredClone(fixture.rights);
  result.records = data.inventories.flatMap((s: any) => s.records.map((r: any) => ({
    park_code: s.park_code, activity_id: r.id, source_url: s.source_url, content_hash: r.content_hash,
    classification: 'nps_government_text', use_scope: 'normalized_activity_text_and_metadata',
    third_party_material_reproduced: false, nps_marks_reproduced: false, media_reproduced: false,
  })));
  return result;
}
// Independent ASCII-key encoder lets mutations reach the field and ordering checks.
const canonical = (value: any): string => value && typeof value === 'object'
  ? Array.isArray(value) ? '[' + value.map(canonical).join(',') + ']'
    : '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}'
  : JSON.stringify(value);
function rehash(record: any) {
  const observations = new Set(['source_updated_at', 'observed_first_at', 'observed_changed_at', 'content_hash', 'hash_scope']);
  record.content_hash = createHash('sha256').update(canonical(Object.fromEntries(
    Object.entries(record).filter(([key]) => !observations.has(key))))).digest('hex');
}
function pythonAccepts(data: any): boolean {
  const result = spawnSync('python', ['-s', '-c', `
import json, sys
from tracker.activity_public import ActivityPublicError, validate_public_activities
try:
    validate_public_activities(json.load(sys.stdin))
except ActivityPublicError:
    print('false')
else:
    print('true')
`], {cwd: root, input: JSON.stringify(data), encoding: 'utf8', timeout: 30_000,
    env: {...process.env, PYTHONDONTWRITEBYTECODE: '1'}, maxBuffer: 1024 * 1024});
  assert.equal(result.status, 0, result.stderr); return JSON.parse(result.stdout);
}
function pythonPairAccepts(repositoryRoot: string): boolean {
  const result = spawnSync('python', ['-s', '-c', `
import sys
from pathlib import Path
from tracker.activity_public import ActivityPublicError, read_public_activity_pair
try:
    read_public_activity_pair(Path(sys.argv[1]))
except ActivityPublicError:
    print('false')
else:
    print('true')
`, repositoryRoot], {cwd: root, encoding: 'utf8', timeout: 30_000,
    env: {...process.env, PYTHONDONTWRITEBYTECODE: '1'}, maxBuffer: 1024 * 1024});
  assert.equal(result.status, 0, result.stderr); return JSON.parse(result.stdout);
}
function temporary(fn: (dir: string) => void) {
  const parent = mkdtempSync(join(tmpdir(), 'public-activities-'));
  try {
    const dir = join(parent, 'data');
    cpSync(join(root, 'data'), dir, {recursive: true});
    for (const file of ['park-activities.json', 'activity-source-rights.json']) rmSync(join(dir, file), {force: true});
    fn(dir);
  } finally { rmSync(parent, {recursive: true, force: true}); }
}
function install(dir: string, data = dataset(), manifest = rights(data)) {
  writeFileSync(join(dir, 'park-activities.json'), canonical(data));
  writeFileSync(join(dir, 'activity-source-rights.json'), canonical(manifest));
}

test('Python activity inventories retain every source field, hash and clock', () => {
  const data = dataset();
  assert.deepEqual(validatePublicActivities(data), data);
  assert.equal(activityDigest(data), fixture.digest);
  assert.equal(Buffer.byteLength(canonicalActivityJson(data)), fixture.bytes);
  assert.deepEqual(validateActivityRights(fixture.rights, data), fixture.rights);
  const copy = validatePublicActivities(data);
  copy.inventories[0].records[0].related_parks[0].name = 'changed copy';
  assert.equal(data.inventories[0].records[0].related_parks[0].name, 'Synthetic name');
  const reviewed = validateActivityRights(fixture.rights, data);
  reviewed.records[0].content_hash = '0'.repeat(64);
  assert.notEqual(reviewed.records[0].content_hash, fixture.rights.records[0].content_hash);
});

test('null, false, empty text and empty lists stay distinct activity source states', () => {
  const data = dataset(), r = data.inventories[0].records[0];
  assert.equal(r.fees_apply, false); assert.equal(r.reservation_required, null);
  assert.equal(r.pets_permitted, true); assert.equal(r.pets_permitted_with_restrictions, null);
  assert.equal(r.location, ''); assert.equal(r.location_description, null);
  assert.deepEqual(r.times_of_day, []);
  for (const state of [null, [], ['Synthetic']]) {
    r.seasons = state; r.times_of_day = state; rehash(r);
    assert.deepEqual(validatePublicActivities(data), data);
  }
});

test('confirmed empty inventories need successful fetch evidence and zero rights rows', () => {
  const data = dataset(); data.inventories.forEach((s: any) => s.records = []);
  assert.deepEqual(validatePublicActivities(data), data);
  assert.deepEqual(validateActivityRights(rights(data), data).records, []);
  const manifest = rights(data); manifest.reviewed_at = '2026-10-04T10:00:00.123455Z';
  assert.throws(() => validateActivityRights(manifest, data));
  data.inventories[0].last_successful_fetch_at = null;
  assert.throws(() => validatePublicActivities(data));
});

test('failed and quarantined inventories retain original last-good evidence', () => {
  for (const status of ['failed', 'quarantined']) {
    const data = dataset();
    for (const s of data.inventories) Object.assign(s, {collection_status: status, coverage_status: 'incomplete',
      last_checked_at: '2026-10-04T10:00:00.123457Z',
      error_code: status === 'failed' ? 'provider_request_failed' : 'response_requires_review'});
    assert.deepEqual(validatePublicActivities(data), data);
    validateActivityRights(rights(data), data);
  }
});

test('complete public inventories require five pilots in order and one original attempt clock', () => {
  for (const mutate of [(d: any) => d.inventories.pop(), (d: any) => d.inventories.reverse(),
    (d: any) => d.inventories[1] = d.inventories[0], (d: any) => d.inventories[0].last_successful_fetch_at = null,
    (d: any) => d.inventories[0].collection_status = 'never_checked',
    (d: any) => d.inventories[1].last_checked_at = d.inventories[1].last_successful_fetch_at = '2026-10-04T10:00:01Z']) {
    const data = dataset(); mutate(data); assert.throws(() => validatePublicActivities(data));
  }
});

test('unknown fields are refused throughout activity and rights schemas', () => {
  for (const target of ['dataset', 'inventory', 'record', 'category', 'relation']) {
    const data = dataset(), s = data.inventories[0], r = s.records[0];
    ({dataset: data, inventory: s, record: r, category: r.activity_categories[0], relation: r.related_parks[0]} as any)[target].unknown = true;
    assert.throws(() => validatePublicActivities(data));
  }
  for (const target of ['rights', 'policy', 'record']) {
    const manifest = rights();
    ({rights: manifest, policy: manifest.policy, record: manifest.records[0]} as any)[target].unknown = true;
    assert.throws(() => validateActivityRights(manifest, dataset()));
  }
});

test('each retained semantic field is covered by the exact activity hash', () => {
  for (const key of Object.keys(dataset().inventories[0].records[0]).filter(key =>
    !['source_updated_at', 'observed_first_at', 'observed_changed_at', 'content_hash', 'hash_scope'].includes(key))) {
    const data = dataset(), r = data.inventories[0].records[0];
    if (typeof r[key] === 'string') r[key] += ' changed';
    else if (typeof r[key] === 'boolean') r[key] = !r[key];
    else if (r[key] === null) r[key] = '';
    else r[key] = r[key].length ? [] : ['changed'];
    assert.throws(() => validatePublicActivities(data), key);
  }
});

test('activity interpretation, source clocks and normalized flag types fail closed', () => {
  for (const mutate of [(s: any) => s.records[0].geographic_relationship = 'inside_park',
    ...['responsible_agency','difficulty','permit_required','source_updated_at'].map(key => (s: any) => s.records[0][key] = 'inferred'),
    ...['fees_apply','reservation_required','pets_permitted','pets_permitted_with_restrictions'].map(key => (s: any) => s.records[0][key] = 'false'),
    (s: any) => s.records[0].hash_scope = 'raw_payload',
    ...['source_issued_at','source_updated_at','published_at'].map(key => (s: any) => s[key] = s.last_checked_at)]) {
    const data = dataset(); mutate(data.inventories[0]); rehash(data.inventories[0].records[0]);
    assert.throws(() => validatePublicActivities(data));
  }
});

test('microsecond ordering and real calendar bounds match Python instants', () => {
  for (const clock of ['2026-02-30T10:00:00Z','0000-01-01T00:00:00Z','2026-10-04T24:00:00Z',
    '2026-10-04T10:00:00+00:99','2026-10-04T10:00:00.1234567Z','2026-10-04',
    '0001-01-01T00:00:00+01:00','9999-12-31T23:59:59-01:00']) {
    const data = dataset(); data.inventories.forEach((s: any) => {
      s.last_checked_at = s.last_successful_fetch_at = clock;
      s.records.forEach((r: any) => r.observed_first_at = r.observed_changed_at = clock);
    });
    assert.equal(pythonAccepts(data), false, clock);
    assert.throws(() => validatePublicActivities(data), clock);
  }
  for (const mutate of [(r: any) => r.observed_changed_at = '2026-10-04T10:00:00.123457Z',
    (r: any) => r.observed_first_at = '2026-10-04T10:00:00.123457Z']) {
    const data = dataset(); mutate(data.inventories[0].records[0]); assert.throws(() => validatePublicActivities(data));
  }
  const data = dataset(); data.inventories[0].records[0].observed_first_at = '2026-10-04T11:00:00.123455+01:00';
  validatePublicActivities(data);
});

test('activity URLs accept source-related parks and global NPS listings using original paths', () => {
  for (const url of ['https://www.nps.gov/thingstodo/synthetic.htm','HTTPS://NPS.GOV:443/yose/',
    'https://www.nps.gov/yose','https://www.nps.gov/yose/%E2%98%83.htm',
    'https://www.nps.gov/yose/%ff.htm']) {
    const data = dataset(), r = data.inventories[0].records[0]; r.url = url; rehash(r);
    assert.equal(pythonAccepts(data), true, url); validatePublicActivities(data);
  }
  const data = dataset(), r = data.inventories[0].records[0];
  r.related_parks.push({park_code: 'zion', full_name: null, url: null, states: null, designation: null, name: null});
  r.url = 'https://www.nps.gov/zion/synthetic.htm'; rehash(r); validatePublicActivities(data);
});

test('traversal, unrelated parks, disguised hosts and credential-like URL parts are refused', () => {
  for (const url of ['https://www.nps.gov/grca/', 'https://www.nps.gov/yose/../yose/',
    'https://www.nps.gov/thingstodo/%2e%2e/thingstodo/a', 'https://www.nps.gov//yose/',
    'https://www.nps.gov/yose//','https://www.nps.gov/yose/a/./b','https://www.nps.gov/yose/a//b',
    'https://www.nps.gov/yose/%252e.htm','https://www.nps.gov/yose/%20a','https://www.nps.gov.evil.test/yose/',
    'https://user@www.nps.gov/yose/','https://%77ww.nps.gov/yose/','https://www.nps.gov:444/yose/',
    'https://www.nps.gov/yose/?%74oken=private','https://www.nps.gov/yose/#%73ecret=private']) {
    const data = dataset(), r = data.inventories[0].records[0]; r.url = url; rehash(r);
    assert.equal(pythonAccepts(data), false, url); assert.throws(() => validatePublicActivities(data), url);
  }
  const data = dataset(), r = data.inventories[0].records[0];
  r.related_parks[0].url = 'https://www.nps.gov/thingstodo/synthetic.htm'; rehash(r);
  assert.throws(() => validatePublicActivities(data));
});

test('Unicode credential markers in literal and encoded URL parts match Python case equivalence', () => {
  for (const marker of ['ſecret','toKen','apıkey','apiKey','apİkey','apıKey','APIKEY',
    'api\rkey','api\u2028key','api\u2029key']) {
    for (const representation of [marker,encodeURIComponent(marker)]) {
      for (const separator of ['?','#']) {
        const data = dataset(), r = data.inventories[0].records[0];
        r.url = `https://www.nps.gov/yose/${separator}${representation}=synthetic`; rehash(r);
        assert.equal(pythonAccepts(data), false, r.url);
        assert.throws(() => validatePublicActivities(data), r.url);
      }
    }
  }
  // Ordinary Unicode query text remains source text rather than a credential marker.
  const data = dataset(), r = data.inventories[0].records[0];
  r.url = 'https://www.nps.gov/yose/?ſcenic=traİl&Kiosk=synthetic'; rehash(r);
  assert.equal(pythonAccepts(data), true); validatePublicActivities(data);
});

test('credential-marker separators consume one Unicode scalar exactly as Python does', () => {
  for (const marker of ['api🌲key','api🌲Key','apİ🌲key']) {
    for (const representation of [marker,encodeURIComponent(marker)]) {
      for (const separator of ['?','#']) {
        const data = dataset(), r = data.inventories[0].records[0];
        r.url = `https://www.nps.gov/yose/${separator}${representation}=synthetic`; rehash(r);
        assert.equal(pythonAccepts(data),false,r.url);
        assert.throws(() => validatePublicActivities(data),r.url);
      }
    }
  }
});

test('neutral Unicode fragments including line and paragraph separators remain valid source URLs', () => {
  for (const fragment of ['scenic🌲','scenic\u2028text','scenic\u2029text']) {
    for (const representation of [fragment,encodeURIComponent(fragment)]) {
      const data = dataset(), r = data.inventories[0].records[0];
      r.url = `https://www.nps.gov/yose/#${representation}`; rehash(r);
      assert.equal(pythonAccepts(data),true,r.url); validatePublicActivities(data);
    }
  }
});

test('Python scalar ordering, uniqueness, whitespace and Unicode lengths are preserved', () => {
  const data = dataset(), r = data.inventories[0].records[0];
  assert.deepEqual(data.inventories[0].records.map((item: any) => item.id), ['\ue000','\u{10000}']);
  r.title = '\ufeff'; r.description = '🌲'.repeat(60_000); rehash(r); validatePublicActivities(data);
  for (const mutate of [(s: any) => s.records.reverse(), (s: any) => s.records.push(s.records[0]),
    (s: any) => s.records[0].activity_categories.reverse(), (s: any) => s.records[0].seasons.reverse(),
    (s: any) => s.records[0].times_of_day = ['same','same'],
    (s: any) => s.records[0].related_parks.push(s.records[0].related_parks[0]),
    (s: any) => s.records[0].related_parks = [], (s: any) => s.records[0].related_parks[0].park_code = 'xxxx',
    (s: any) => s.records[0].title = '\u0085', (s: any) => s.records[0].id = 'bad\nid',
    (s: any) => s.records[0].id = '🌲'.repeat(257), (s: any) => s.records[0].description = '🌲'.repeat(65_537),
    (s: any) => s.records[0].credit = '\ud800']) {
    const mutated = dataset(); mutate(mutated.inventories[0]); rehash(mutated.inventories[0].records[0]);
    assert.throws(() => validatePublicActivities(mutated));
  }
  assert.equal(canonicalActivityJson({'\u{10000}': 1, '\ue000': 2}), '{"\ue000":2,"\u{10000}":1}');
  for (const bad of ['\ud800', Infinity, 1.1, undefined]) assert.throws(() => canonicalActivityJson(bad));
});

test('rights bind repeated IDs separately for every park and refuse duplicate or omitted rows', () => {
  const data = dataset(), manifest = rights(data);
  assert.equal(new Set(manifest.records.map((r: any) => r.activity_id)).size, 2);
  assert.equal(validateActivityRights(manifest, data).records.length, 10);
  for (const mutate of [(r: any) => r.records.reverse(), (r: any) => r.records.pop(),
    (r: any) => r.records[1] = r.records[0], (r: any) => r.records[2] = r.records[0],
    (r: any) => r.records[0].activity_id = 'different', (r: any) => r.records[0].content_hash = '0'.repeat(64),
    (r: any) => r.records[0].source_url = data.inventories[1].source_url]) {
    const changed = rights(data); mutate(changed); assert.throws(() => validateActivityRights(changed, data));
  }
});

test('rights require exact policy, complete text scope and review after every attempted check', () => {
  for (const mutate of [(r: any) => r.purpose = 'public_park_profile_text_rights',
    (r: any) => r.reviewed_at = '2026-10-04T10:00:00.123455Z',
    (r: any) => r.policy.ownership_url = 'https://example.test/', (r: any) => r.policy.raw_private_captures_public = true,
    (r: any) => r.review_method = 'api_origin', (r: any) => r.records[0].classification = 'unreviewed',
    (r: any) => r.records[0].use_scope = 'normalized_profile_text_and_category_names',
    ...['third_party_material_reproduced','nps_marks_reproduced','media_reproduced'].map(key => (r: any) => r.records[0][key] = true)]) {
    const manifest = rights(); mutate(manifest); assert.throws(() => validateActivityRights(manifest, dataset()));
  }
  const data = dataset(); data.inventories.forEach((s: any) => Object.assign(s, {collection_status: 'failed',
    coverage_status: 'incomplete', error_code: 'provider_request_failed', last_checked_at: '2026-10-04T10:00:02Z'}));
  assert.throws(() => validateActivityRights(rights(data), data));
});

test('record, inventory and nested-list byte and count limits match the activity source contract', () => {
  for (const mutate of [(r: any) => r.seasons = Array.from({length:1001}, (_, i) => String(i).padStart(4,'0')),
    (r: any) => r.description = r.long_description = r.location = r.location_description = 'x'.repeat(65536)]) {
    const data = dataset(), r = data.inventories[0].records[0]; mutate(r); rehash(r);
    assert.throws(() => validatePublicActivities(data));
  }
  const data = dataset(), s = data.inventories[0];
  s.records = Array.from({length: 90}, (_, i) => {
    const r = structuredClone(s.records[0]); r.id = String(i).padStart(4,'0');
    r.description = r.long_description = 'x'.repeat(60_000); rehash(r); return r;
  });
  assert.throws(() => validatePublicActivities(data));
});

test('exact record and inventory limits match Python while one extra byte is refused', () => {
  const data = dataset(), s = data.inventories[0], r = s.records[0];
  const fields = ['description','long_description','location','location_description'];
  fields.forEach(key => r[key] = ''); rehash(r);
  let padding = 256 * 1024 - Buffer.byteLength(canonical(r));
  for (const key of fields) { const count = Math.min(padding,65_536); r[key] = 'x'.repeat(count); padding -= count; }
  assert.equal(padding, 0); rehash(r); assert.equal(Buffer.byteLength(canonical(r)), 256 * 1024);
  assert.equal(pythonAccepts(data), true); validatePublicActivities(data);
  r.location_description += 'x'; rehash(r);
  assert.equal(pythonAccepts(data), false); assert.throws(() => validatePublicActivities(data));

  const batch = dataset(), inventory = batch.inventories[0], base = inventory.records[0];
  inventory.records = Array.from({length: 32}, (_, index) => {
    const item = structuredClone(base); item.id = String(index).padStart(4,'0');
    fields.forEach(key => item[key] = ''); rehash(item);
    let room = 256 * 1024 - Buffer.byteLength(canonical(item));
    for (const key of fields) { const count = Math.min(room,65_536); item[key] = 'x'.repeat(count); room -= count; }
    rehash(item); return item;
  });
  const over = Buffer.byteLength(canonical(inventory)) - 8 * 1024 * 1024;
  inventory.records[31].location_description = inventory.records[31].location_description.slice(0,-over);
  rehash(inventory.records[31]);
  assert.equal(Buffer.byteLength(canonical(inventory)), 8 * 1024 * 1024);
  assert.equal(pythonAccepts(batch), true); validatePublicActivities(batch);
  inventory.records[31].location_description += 'x'; rehash(inventory.records[31]);
  assert.equal(pythonAccepts(batch), false); assert.throws(() => validatePublicActivities(batch));
});

test('canonical encoding and digest accept exact explicit limits and refuse one extra byte', () => {
  const value = {description:'é'};
  const bytes = Buffer.byteLength(canonical(value));
  assert.equal(canonicalActivityJson(value, bytes), canonical(value));
  assert.equal(activityDigest(value, bytes), createHash('sha256').update(canonical(value)).digest('hex'));
  assert.throws(() => canonicalActivityJson(value, bytes - 1));
  assert.throws(() => activityDigest(value, bytes - 1));
  for (const limit of [0, -1, 1.5, NaN]) assert.throws(() => canonicalActivityJson(value, limit));
  assert.throws(() => canonicalActivityJson('x'.repeat(MAX_ACTIVITY_BYTES)));
  assert.throws(() => validateActivityRights({...rights(), extra:'x'.repeat(MAX_ACTIVITY_RIGHTS_BYTES)}, dataset()));
});

test('Python parity and paired file reading retain valid batches beyond the legacy ten MiB bound', () => temporary(dir => {
  const oracle = pythonFixture(true);
  assert.ok(oracle.bytes > 10 * 1024 * 1024);
  assert.deepEqual(validatePublicActivities(oracle.dataset), oracle.dataset);
  assert.equal(activityDigest(oracle.dataset), oracle.digest);
  assert.equal(Buffer.byteLength(canonicalActivityJson(oracle.dataset)), oracle.bytes);
  install(dir, oracle.dataset, oracle.rights);
  assert.deepEqual(validateActivityFiles(dir), oracle.dataset);
  validateData(dir);
}));

test('the real build gate accepts absent pairs and refuses incomplete or invalid activity additions', () => temporary(dir => {
  assert.equal(validateActivityFiles(dir), null); validateData(dir);
  writeFileSync(join(dir,'park-activities.json'), canonical(dataset()));
  assert.throws(() => validateActivityFiles(dir)); assert.throws(() => validateData(dir));
  install(dir); assert.deepEqual(validateActivityFiles(dir), dataset()); validateData(dir);
  const data = dataset(); data.inventories[0].records[0].description += ' unreviewed';
  writeFileSync(join(dir,'park-activities.json'), canonical(data));
  assert.throws(() => validateData(dir));
  rmSync(join(dir,'park-activities.json')); assert.throws(() => validateActivityFiles(dir));
}));

test('activity pairs require strict UTF-8 and exact canonical bytes with at most one final LF', () => temporary(dir => {
  install(dir);
  const files = ['park-activities.json','activity-source-rights.json'], values = [dataset(),rights()];
  for (let i = 0; i < files.length; i++) {
    const text = canonical(values[i]);
    for (const bad of ['{"purpose":"duplicate",'+text.slice(1), JSON.stringify(values[i],null,2),
      Buffer.concat([Buffer.from([0xff]),Buffer.from(text)]), '\ufeff'+text,text+'\n\n',text+'\r\n',
      text.replace('"schema_version":1', '"schema_version":1.0')]) {
      writeFileSync(join(dir,files[i]),bad); assert.throws(() => validateActivityFiles(dir));
    }
    writeFileSync(join(dir,files[i]),text+'\n'); validateActivityFiles(dir);
  }
}));

test('activity file types and data-directory symlinks cannot bypass the paired gate', () => temporary(dir => {
  const file = join(dir,'park-activities.json');
  symlinkSync(join(dir,'missing'),file,'junction'); assert.throws(() => validateActivityFiles(dir));
  rmSync(file); mkdirSync(file); assert.throws(() => validateActivityFiles(dir));
  rmSync(file,{recursive:true}); install(dir);
  const alias = join(dirname(dir),'linked-data'); symlinkSync(dir,alias,'junction');
  assert.throws(() => validateActivityFiles(alias));
}));

test('symlinked data-directory ancestors are refused for present and absent activity pairs', () => temporary(dir => {
  install(dir);
  const parent = dirname(dir), actualRoot = join(parent,'actual-root'), alias = join(parent,'alias-root');
  mkdirSync(actualRoot); cpSync(dir,join(actualRoot,'data'),{recursive:true});
  assert.equal(pythonPairAccepts(actualRoot), true);
  assert.deepEqual(validateActivityFiles(join(actualRoot,'data')),dataset());
  symlinkSync(actualRoot,alias,'junction');
  assert.equal(pythonPairAccepts(alias), false);
  assert.throws(() => validateActivityFiles(join(alias,'data')));
  // Resolving '..' first must not hide a linked component of the supplied path.
  assert.equal(pythonPairAccepts(`${alias}/../actual-root`),false);
  assert.throws(() => validateActivityFiles(`${alias}/../actual-root/data`));
  for (const file of ['park-activities.json','activity-source-rights.json']) rmSync(join(actualRoot,'data',file));
  assert.equal(validateActivityFiles(join(actualRoot,'data')),null);
  assert.equal(pythonPairAccepts(alias), false);
  assert.throws(() => validateActivityFiles(join(alias,'data')));
  rmSync(join(actualRoot,'data'),{recursive:true});
  assert.equal(pythonPairAccepts(actualRoot),true);
  assert.equal(validateActivityFiles(join(actualRoot,'data')),null);
  assert.equal(pythonPairAccepts(alias),false);
  assert.throws(() => validateActivityFiles(join(alias,'data')));
  const dangling = join(parent,'dangling-root'); symlinkSync(join(parent,'missing-root'),dangling,'junction');
  assert.equal(pythonPairAccepts(dangling),false);
  assert.throws(() => validateActivityFiles(join(dangling,'data')));
}));

test('oversized public files are refused before parsing either member of the pair', () => temporary(dir => {
  install(dir);
  writeFileSync(join(dir,'park-activities.json'),Buffer.alloc(MAX_ACTIVITY_BYTES+2,0x20));
  assert.throws(() => validateActivityFiles(dir));
  install(dir); writeFileSync(join(dir,'activity-source-rights.json'),Buffer.alloc(MAX_ACTIVITY_RIGHTS_BYTES+2,0x20));
  assert.throws(() => validateActivityFiles(dir));
}));
