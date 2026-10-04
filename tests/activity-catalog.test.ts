import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { cpSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { activityDigest, canonicalActivityJson, validateActivityFiles, validateActivityRights,
  validatePublicActivities } from '../scripts/validate-park-activities.ts';
import { validateData } from '../scripts/validate-data.ts';

const root = resolve(import.meta.dirname, '..');
const codes = ['yose', 'romo', 'yell', 'zion', 'grca'];
const clock = '2026-10-04T10:00:00.123456Z';
const policy = JSON.parse(readFileSync(join(root, 'data/source-rights.json'), 'utf8')).policy;
// Independent encoder for ASCII field names; data uses literal Unicode scalars.
const canonical = (value: any): string => value && typeof value === 'object'
  ? Array.isArray(value) ? '[' + value.map(canonical).join(',') + ']'
    : '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}'
  : JSON.stringify(value);
const digest = (value: any) => createHash('sha256').update(canonical(value), 'utf8').digest('hex');
function rehash(record: any) {
  record.view_hash = digest(Object.fromEntries(Object.entries(record)
    .filter(([key]) => key !== 'view_hash' && key !== 'hash_scope')));
}
function dataset(): any {
  return {schema_version: 2, purpose: 'public_park_activities', inventories: codes.map(code => {
    const summaries = ['\ue000', '\u{10000}'].map((id, index) => ({id,
      content_hash: (index ? 'b' : 'a').repeat(64), hash_scope: 'normalized_record',
      observed_first_at: clock, observed_changed_at: clock,
      publication_status: index ? 'withheld' : 'selected'}));
    const record = {id: '\ue000', park_code: code, title: `Synthetic ${code} café 🌲`,
      url: `https://www.nps.gov/${code}/synthetic.htm`, activity_categories: [{id:'\ue000', name:'Synthetic category'}],
      category_scope: 'published', geographic_relationship: 'unconfirmed', responsible_agency: null,
      difficulty: null, permit_required: null, availability_status: 'not_verified', source_updated_at: null,
      observed_first_at: clock, observed_changed_at: clock, source_content_hash: 'a'.repeat(64),
      view_hash: '', hash_scope: 'catalog_view'};
    rehash(record);
    return {schema_version: 2, park_code: code, provider: 'NPS',
      source_url: `https://developer.nps.gov/api/v1/thingstodo?parkCode=${code}`,
      collection_status: 'success', coverage_status: 'checked_activity_feed_only', last_checked_at: clock,
      last_successful_fetch_at: clock, source_issued_at: null, source_updated_at: null, published_at: null,
      records: [record], source_records: summaries, error_code: null};
  })};
}
function rights(data = dataset()): any {
  return {schema_version: 2, purpose:'public_park_activity_text_rights', reviewed_at:'2026-10-04T10:00:01Z',
    review_method:'official_nps_policy_and_exact_activity_review', policy: structuredClone(policy),
    projection_hash: digest(data), records: data.inventories.flatMap((s: any) => s.records.map((r: any) => ({
      park_code:s.park_code, activity_id:r.id, source_url:s.source_url, source_content_hash:r.source_content_hash,
      view_hash:r.view_hash, classification:'nps_government_text', use_scope:'activity_catalog_title_url_and_optional_categories',
      third_party_material_reproduced:false, nps_marks_reproduced:false, media_reproduced:false}))) };
}
function temporary(action: (directory: string) => void) {
  const directory = mkdtempSync(join(tmpdir(), 'catalog-public-test-'));
  try { cpSync(join(root,'data'), directory, {recursive:true}); action(directory); }
  finally { rmSync(directory,{recursive:true,force:true}); }
}
function install(directory: string, data = dataset(), manifest = rights(data)) {
  writeFileSync(join(directory,'park-activities.json'),canonical(data)+'\n');
  writeFileSync(join(directory,'activity-source-rights.json'),canonical(manifest)+'\n');
}
function accepted(data = dataset()) {
  assert.deepEqual(validatePublicActivities(data),data);
  assert.deepEqual(validateActivityRights(rights(data),data),rights(data));
}

test('catalog accepts exact selected source binding, retains withheld summaries and returns detached values', () => {
  const data = dataset(), manifest = rights(data);
  const validated = validatePublicActivities(data), reviewed = validateActivityRights(manifest,data);
  assert.deepEqual(validated,data); assert.deepEqual(reviewed,manifest);
  assert.notEqual(validated,data); assert.notEqual(validated.inventories[0],data.inventories[0]);
  validated.inventories[0].records.length = 0;
  assert.equal(data.inventories[0].records.length,1);
  assert.equal(activityDigest(data),digest(data));
});

test('catalog never accepts omitted source prose, related labels, media, flags or withholding reasons', () => {
  accepted();
  for (const field of ['description','credit','related_parks','media','reservation_required']) {
    const data = dataset(), record = data.inventories[0].records[0];
    record[field] = 'PRIVATE_QUOTE_CONTACT_TRACKING'; rehash(record);
    assert.throws(() => validatePublicActivities(data));
  }
  for (const field of ['title','url','credit','withholding_reason']) {
    const data = dataset(); data.inventories[0].source_records[1][field] = 'PRIVATE_QUOTE_CONTACT_TRACKING';
    assert.throws(() => validatePublicActivities(data));
  }
  assert.ok(!canonicalActivityJson(dataset()).includes('PRIVATE_QUOTE_CONTACT_TRACKING'));
});

test('catalog preserves published null, published empty and intentionally withheld categories distinctly', () => {
  for (const [scope,categories] of [['published',null],['published',[]],['withheld',null]]) {
    const data = dataset(), record = data.inventories[0].records[0];
    record.category_scope = scope; record.activity_categories = categories; rehash(record); accepted(data);
  }
  for (const [scope,categories] of [['withheld',[]],['unknown',null]]) {
    const data = dataset(), record = data.inventories[0].records[0];
    record.category_scope = scope; record.activity_categories = categories; rehash(record);
    assert.throws(() => validatePublicActivities(data));
  }
});

test('catalog plain text rejects HTML, controls, blank text and excess scalar counts after rehash', () => {
  accepted();
  for (const text of ['<b>Trail</b>','Trail>','\u0000','Trail\n','Trail\u007f','Trail\u0085','Trail\u009f','\u3000','🌲'.repeat(1025)]) {
    for (const target of ['title','category']) {
      const data = dataset(), record = data.inventories[0].records[0];
      if (target === 'title') record.title = text;
      else record.activity_categories[0].name = text;
      rehash(record); assert.throws(() => validatePublicActivities(data),`${target}: ${JSON.stringify(text.slice(0,30))}`);
    }
  }
  const data = dataset(), record = data.inventories[0].records[0];
  record.title = '🌲'.repeat(1024); record.activity_categories[0].name = 'é'.repeat(1024); rehash(record); accepted(data);
});

test('catalog only admits exact official park or global activity URLs without query or fragment', () => {
  accepted();
  for (const url of ['https://www.nps.gov/yose/path.htm?','https://www.nps.gov/yose/path.htm#',
    'https://www.nps.gov/yose/path.htm?neutral=1','https://www.nps.gov/yose/path.htm#neutral',
    'https://www.nps.gov/romo/path.htm','https://www.nps.gov/yose/../romo/path.htm',
    'https://www.nps.gov/yose/%2e%2e/romo/path.htm','https://www.nps.gov//yose/path.htm',
    'https://www.nps.gov/yose/%2fpath.htm','https://www.nps.gov/yose/%252fpath.htm',
    'https://www.nps.gov:444/yose/path.htm','https://nps.gov.attacker.test/yose/path.htm',
    'https://user@www.nps.gov/yose/path.htm','http://www.nps.gov/yose/path.htm',
    'https://www.nps.gov/yose/path\\x.htm']) {
    const data = dataset(), record = data.inventories[0].records[0]; record.url = url; rehash(record);
    assert.throws(() => validatePublicActivities(data),url);
  }
  for (const url of ['https://www.nps.gov/thingstodo/synthetic.htm','https://nps.gov/yose/directory/','https://www.nps.gov:443/yose/path.htm']) {
    const data = dataset(), record = data.inventories[0].records[0]; record.url = url; rehash(record); accepted(data);
  }
});

test('catalog binds selected records one-to-one to ordered source summaries and matching hashes/clocks', () => {
  accepted();
  for (const mutate of [(s: any) => s.source_records.reverse(), (s: any) => s.source_records.push(s.source_records[1]),
    (s: any) => s.source_records[0].publication_status = 'withheld', (s: any) => s.source_records[1].publication_status = 'selected',
    (s: any) => s.source_records[0].content_hash = 'c'.repeat(64), (s: any) => s.source_records[0].content_hash = 'A'.repeat(64),
    (s: any) => s.source_records[0].content_hash = 'z'.repeat(64), (s: any) => s.source_records[0].hash_scope = 'catalog_view',
    (s: any) => s.source_records[0].observed_changed_at = '2026-10-04T10:00:00.123455Z',
    (s: any) => s.records = [], (s: any) => s.records.push(s.records[0]),
    (s: any) => s.records[0].source_content_hash = 'c'.repeat(64), (s: any) => s.records[0].park_code = 'romo']) {
    const data = dataset(), inventory = data.inventories[0]; mutate(inventory); inventory.records.forEach(rehash);
    assert.throws(() => validatePublicActivities(data));
  }
});

test('catalog view hash refuses altered text and rights refuse a newly rehashed view or source summary', () => {
  accepted();
  const data = dataset(), manifest = rights(data), record = data.inventories[0].records[0];
  record.title += ' altered'; assert.throws(() => validatePublicActivities(data));
  rehash(record); validatePublicActivities(data); assert.throws(() => validateActivityRights(manifest,data));
  const changed = dataset(), priorRights = rights(changed);
  changed.inventories[0].source_records[1].content_hash = 'c'.repeat(64);
  validatePublicActivities(changed); assert.throws(() => validateActivityRights(priorRights,changed));
  // Refreshing the projection hash alone cannot cover a changed published view.
  manifest.projection_hash = digest(data); assert.throws(() => validateActivityRights(manifest,data));
});

test('catalog refuses unsupported geography, agency, permit, difficulty and availability claims even after rehash', () => {
  accepted();
  for (const [field,value] of [['geographic_relationship','inside_park'],['responsible_agency','NPS'],
    ['difficulty','easy'],['permit_required',false],['availability_status','open'],['source_updated_at',clock],['hash_scope','normalized_record']] as const) {
    const data = dataset(), record = data.inventories[0].records[0]; record[field] = value; rehash(record);
    assert.throws(() => validatePublicActivities(data));
  }
});

test('catalog scalar ordering, surrogate and identifier limits preserve Python semantics', () => {
  const data = dataset(), record = data.inventories[0].records[0];
  record.activity_categories.push({id:'\u{10000}',name:'Astral category'}); rehash(record); accepted(data);
  for (const mutate of [(r: any) => r.activity_categories.reverse(), (r: any) => r.activity_categories.push(r.activity_categories[0]),
    (r: any) => r.title = '\ud800', (r: any) => r.activity_categories[0].id = 'x'.repeat(257),
    (r: any) => r.activity_categories[0].id = 'bad\u0000', (r: any) => r.activity_categories = Array.from({length:1001},(_,i) => ({id:String(i).padStart(4,'0'),name:'Synthetic'}))]) {
    const changed = structuredClone(data), r = changed.inventories[0].records[0]; mutate(r);
    if (!r.title.includes('\ud800')) rehash(r);
    assert.throws(() => validatePublicActivities(changed));
  }
});

test('catalog microsecond observation clocks use exact instant comparisons without refreshing failed evidence', () => {
  accepted();
  const data = dataset();
  data.inventories.forEach((s: any) => Object.assign(s,{collection_status:'failed',coverage_status:'incomplete',
    error_code:'provider_request_failed',last_checked_at:'2026-10-04T10:00:00.123457Z'}));
  accepted(data);
  for (const mutate of [(s: any) => s.source_records[1].observed_changed_at = '2026-10-04T10:00:00.123457Z',
    (s: any) => s.source_records[1].observed_first_at = '2026-10-04T10:00:00.123457Z',
    (s: any) => s.last_successful_fetch_at = null, (s: any) => s.last_successful_fetch_at = '2026-10-04T10:00:00.123458Z',
    (s: any) => s.last_checked_at = '2026-02-30T10:00:00Z', (s: any) => s.last_checked_at = '0000-01-01T00:00:00Z',
    (s: any) => s.last_checked_at = '2026-10-04T10:00:00.1234567Z']) {
    const changed = structuredClone(data); mutate(changed.inventories[0]); assert.throws(() => validatePublicActivities(changed));
  }
  // Equivalent-offset observation times are allowed and must not be rounded to milliseconds.
  const offset = dataset(), s = offset.inventories[0], r = s.records[0];
  s.source_records[0].observed_first_at = r.observed_first_at = '2026-10-04T06:00:00.123455-04:00';
  rehash(r); accepted(offset);
});

test('catalog rights cover only published listings and require exact policy, scope, order and review clocks', () => {
  accepted();
  for (const mutate of [(r: any) => r.schema_version = 1, (r: any) => r.projection_hash = 'a'.repeat(64),
    (r: any) => r.policy.third_party_material_allowed = true, (r: any) => r.review_method = 'guessed',
    (r: any) => r.records.reverse(), (r: any) => r.records.pop(), (r: any) => r.records.push(r.records[0]),
    (r: any) => r.records[0].use_scope = 'normalized_activity_text_and_metadata',
    (r: any) => r.records[0].source_content_hash = 'c'.repeat(64), (r: any) => r.records[0].source_url += '&tracking=1',
    (r: any) => r.records[0].third_party_material_reproduced = true, (r: any) => r.records[0].nps_marks_reproduced = true,
    (r: any) => r.records[0].media_reproduced = true, (r: any) => r.records[0].content_hash = 'a'.repeat(64),
    (r: any) => r.reviewed_at = '2026-10-04T10:00:00.123455Z']) {
    const manifest = rights(); mutate(manifest); assert.throws(() => validateActivityRights(manifest,dataset()));
  }
  const data = dataset(); data.inventories.forEach((s: any) => {s.records = []; s.source_records.forEach((r: any) => r.publication_status = 'withheld');});
  accepted(data); const manifest = rights(data); manifest.reviewed_at = '2026-10-04T10:00:00.123455Z';
  assert.throws(() => validateActivityRights(manifest,data));
});

test('catalog confirmed-empty and wholly-withheld inventories remain distinct successful evidence', () => {
  const data = dataset(); data.inventories[0].records = []; data.inventories[0].source_records = [];
  data.inventories[1].records = []; data.inventories[1].source_records.forEach((r: any) => r.publication_status = 'withheld');
  accepted(data);
});

test('catalog bounded source summaries and public listings refuse excess records and inventory bytes', () => {
  accepted();
  const data = dataset(), s = data.inventories[0];
  s.records = []; s.source_records = Array.from({length:5001},(_,i) => ({...s.source_records[1],id:String(i).padStart(4,'0')}));
  assert.throws(() => validatePublicActivities(data));
  const big = dataset(), r = big.inventories[0].records[0];
  r.activity_categories = Array.from({length:1000},(_,i) => ({id:String(i).padStart(4,'0'),name:'🌲'.repeat(1024)}));
  rehash(r); assert.throws(() => validatePublicActivities(big));
});

test('existing build gates accept valid v2 pairs and refuse incomplete or mismatched public files', () => temporary(directory => {
  assert.equal(validateActivityFiles(directory),null); validateData(directory);
  install(directory); assert.deepEqual(validateActivityFiles(directory),dataset()); validateData(directory);
  rmSync(join(directory,'activity-source-rights.json')); assert.throws(() => validateData(directory));
  install(directory); rmSync(join(directory,'park-activities.json')); assert.throws(() => validateData(directory));
  install(directory); const manifest = rights(); manifest.projection_hash = 'f'.repeat(64);
  writeFileSync(join(directory,'activity-source-rights.json'),canonical(manifest)); assert.throws(() => validateData(directory));
}));

test('catalog pairs retain canonical UTF-8 and duplicate-key refusal at the actual file gate', () => temporary(directory => {
  install(directory); validateActivityFiles(directory);
  for (const [file,value] of [['park-activities.json',dataset()],['activity-source-rights.json',rights()]] as const) {
    const text = canonical(value);
    for (const bad of ['{"schema_version":1,'+text.slice(1),JSON.stringify(value,null,2),text+'\r\n',text+'\n\n',
      '\ufeff'+text,Buffer.concat([Buffer.from([0xff]),Buffer.from(text)])]) {
      writeFileSync(join(directory,file),bad); assert.throws(() => validateActivityFiles(directory));
    }
    writeFileSync(join(directory,file),text+'\n'); validateActivityFiles(directory);
  }
}));

function pythonJson(script: string, input?: unknown): any {
  const result = spawnSync('python', ['-s','-c',script], {cwd:root, encoding:'utf8',
    input: input === undefined ? undefined : JSON.stringify(input), timeout:60_000,
    env:{...process.env,PYTHONDONTWRITEBYTECODE:'1',PYTHONIOENCODING:'utf-8'}, maxBuffer:4 * 1024 * 1024});
  assert.equal(result.status,0,result.stderr); return JSON.parse(result.stdout);
}
function pythonCatalog(): any {
  return pythonJson(`
import copy, json, sys
sys.path.insert(0, 'tests')
from test_activity_checkpoints import checkpoint_fixture, bind, encoded
from test_activity_catalog import dispositions_fixture, catalog_rights_fixture
from test_park_activities import rehash
from tracker.activity_catalog import project_catalog, validate_catalog_rights
from tracker.activity_public import activity_digest
checkpoint = checkpoint_fixture('${clock}')
for index, snapshot in enumerate(checkpoint['inventories']):
    original = snapshot['records'][0]
    original.update(id='\\ue000', title='Synthetic café \\U0001f332',
                    description='PRIVATE_QUOTE_CONTACT_TRACKING', credit='PRIVATE_CREDIT')
    original['activity_categories'] = (None if index == 0 else [] if index == 1 else [
        {'id':'\\ue000','name':'Synthetic BMP'}, {'id':'\\U00010000','name':'Synthetic astral'}])
    rehash(original)
    withheld = copy.deepcopy(original)
    withheld.update(id='\\U00010000', title='<b>PRIVATE_WITHHELD_TITLE</b>',
                    url='https://www.nps.gov/thingstodo/withheld.htm?PRIVATE_CONTACT_TRACKING=1')
    rehash(withheld)
    snapshot['records'] = [original, withheld]
bind(checkpoint)
plan = dispositions_fixture(checkpoint, '2026-10-04T10:00:01Z')
for index, row in enumerate(plan['records']):
    if index % 2:
        row.update(decision='withheld', categories='withheld')
    elif row['park_code'] == 'zion':
        row['categories'] = 'withheld'
dataset = project_catalog(checkpoint, plan)
rights = catalog_rights_fixture(dataset, '2026-10-04T10:00:01Z')
validate_catalog_rights(rights, dataset)
print(json.dumps({'dataset':dataset, 'rights':rights, 'digest':activity_digest(dataset),
                  'canonical':encoded(dataset).decode('utf-8')},ensure_ascii=False))
`);
}

test('Python exact projection excludes private quotation/contact/tracking markers and validates through the TS build gate', () => temporary(directory => {
  const oracle = pythonCatalog();
  assert.deepEqual(validatePublicActivities(oracle.dataset),oracle.dataset);
  assert.deepEqual(validateActivityRights(oracle.rights,oracle.dataset),oracle.rights);
  assert.equal(canonicalActivityJson(oracle.dataset),oracle.canonical);
  assert.equal(activityDigest(oracle.dataset),oracle.digest);
  assert.equal(oracle.dataset.inventories.flatMap((s: any) => s.records).length,5);
  assert.equal(oracle.dataset.inventories.flatMap((s: any) => s.source_records).length,10);
  assert.deepEqual(oracle.dataset.inventories[0].source_records.map((r: any) => r.id),['\ue000','\u{10000}']);
  assert.equal(oracle.dataset.inventories[0].records[0].activity_categories,null);
  assert.deepEqual(oracle.dataset.inventories[1].records[0].activity_categories,[]);
  assert.equal(oracle.dataset.inventories[3].records[0].category_scope,'withheld');
  assert.equal(oracle.dataset.inventories[3].records[0].activity_categories,null);
  for (const marker of ['PRIVATE_QUOTE','CONTACT','TRACKING','PRIVATE_CREDIT','PRIVATE_WITHHELD','description','related_parks']) {
    assert.ok(!oracle.canonical.includes(marker),marker);
    assert.ok(!canonical(oracle.rights).includes(marker),marker);
  }
  install(directory,oracle.dataset,oracle.rights); validateData(directory);
}));

test('Python and TS agree on synthetic URL, Unicode, observation, source/view and rights refusal cases', () => {
  const cases: {data:any; manifest:any; want:boolean; label:string}[] = [];
  const add = (label: string, want: boolean, mutate?: (data: any) => void, review?: (manifest: any) => void) => {
    const data = dataset(); mutate?.(data); const manifest = rights(data); review?.(manifest);
    cases.push({data,manifest,want,label});
  };
  add('valid',true);
  for (const title of ['🌲'.repeat(1024),'\ufeff','Trail\u2028']) add('valid scalar text',true,data => {
    const r = data.inventories[0].records[0]; r.title = title; rehash(r);
  });
  for (const title of ['\u0001','\u0085','\u009f','<Trail>','🌲'.repeat(1025),'\u3000','\ud800']) {
    add('invalid scalar text',false,data => {const r = data.inventories[0].records[0]; r.title = title; rehash(r);});
  }
  for (const url of ['https://www.nps.gov:443/yose/directory/','https://www.nps.gov/yose/%EF%BB%BF.htm',
    'https://www.nps.gov/thingstodo/synthetic.htm','https://www.nps.gov/yose/%3f.htm']) {
    add(url,true,data => {const r = data.inventories[0].records[0]; r.url = url; rehash(r);});
  }
  for (const url of ['https://www.nps.gov/yose/route?', 'https://www.nps.gov/yose/route#',
    'https://www.nps.gov/romo/route','https://www.nps.gov/yose/%2e%2e/zion/route',
    'https://www.nps.gov/yose/%25.htm','https://www.nps.gov/yose/%2froute',
    'https://www.nps.gov/yose/route?toKen=x']) {
    add(url,false,data => {const r = data.inventories[0].records[0]; r.url = url; rehash(r);});
  }
  add('withheld C1 identifier follows original identifier policy',true,data => {data.inventories[0].source_records[1].id = '𐀀\u0085';});
  add('source changed after success by one microsecond',false,data => {data.inventories[0].source_records[1].observed_changed_at = '2026-10-04T10:00:00.123457Z';});
  add('source scalar ID order',false,data => {data.inventories[0].source_records.reverse();});
  add('source hashes lower hex only',false,data => {data.inventories[0].source_records[1].content_hash = 'A'.repeat(64);});
  add('record view stale',false,data => {data.inventories[0].records[0].title += ' changed';});
  add('selection incomplete',false,data => {data.inventories[0].source_records[1].publication_status = 'selected';});
  add('rights view mismatch after projection rehash',false,undefined,manifest => {manifest.records[0].view_hash = 'a'.repeat(64);});
  add('rights flags are exact booleans',false,undefined,manifest => {manifest.records[0].media_reproduced = 0;});
  add('rights stale by one microsecond',false,undefined,manifest => {manifest.reviewed_at = '2026-10-04T10:00:00.123455Z';});
  const results = pythonJson(`
import json,sys
from tracker.activity_public import ActivityPublicError
from tracker.activity_catalog import validate_catalog, validate_catalog_rights
results=[]
for case in json.load(sys.stdin):
    try:
        validate_catalog(case['data'])
        validate_catalog_rights(case['manifest'],case['data'])
    except ActivityPublicError:
        results.append(False)
    else:
        results.append(True)
print(json.dumps(results))
`,cases);
  for (const [index,entry] of cases.entries()) {
    assert.equal(results[index],entry.want,'Python: '+entry.label);
    let accepted = true;
    try {validatePublicActivities(entry.data); validateActivityRights(entry.manifest,entry.data);} catch {accepted = false;}
    assert.equal(accepted,entry.want,'TS: '+entry.label);
  }
});


test('catalog inventory bytes enforce the existing eight MiB bound independently of each listing limit', () => {
  const batch = (count: number) => {
    const data = dataset(), inventory = data.inventories[0], base = inventory.records[0];
    base.activity_categories = Array.from({length:200},(_,index) => ({id:String(index).padStart(4,'0'),name:'x'.repeat(1000)}));
    inventory.records = Array.from({length:count},(_,index) => {
      const record = structuredClone(base); record.id = String(index).padStart(4,'0'); rehash(record); return record;
    });
    inventory.source_records = inventory.records.map((r: any) => ({id:r.id,content_hash:r.source_content_hash,
      hash_scope:'normalized_record',observed_first_at:r.observed_first_at,observed_changed_at:r.observed_changed_at,
      publication_status:'selected'}));
    return data;
  };
  const small = batch(40), large = batch(42);
  assert.ok(Buffer.byteLength(canonical(small.inventories[0])) < 8 * 1024 * 1024);
  assert.ok(Buffer.byteLength(canonical(large.inventories[0])) > 8 * 1024 * 1024);
  large.inventories[0].records.forEach((r: any) => assert.ok(Buffer.byteLength(canonical(r)) < 256 * 1024));
  accepted(small); assert.throws(() => validatePublicActivities(large));
});
