import test from 'node:test';
import assert from 'node:assert/strict';
import type { Rule } from '../src/lib/readiness.ts';
import type { EntryNote } from '../scripts/validate-entry-notes.ts';
const mod = await import('../src/lib/corrections.ts').catch(() => ({})) as any;
const projectBase = '/us-national-park-trip-readiness-tracker/';
const canonicalOrigin = 'https://vasuki8.github.io';
const reviewedAt = '2026-09-29T02:03:04.123Z';
const checkedAt = '2026-09-30T04:05:06.123456Z';
const recordId = 'same source: /?#&é';
const rule = (park_code = 'yose', id = recordId): Rule => ({
  id, park_code, areas: ['*'], effective_from: '2026-04-01', effective_to: '2026-10-31',
  start_time: '05:00', end_time: '16:00', requirement: 'timed_entry', reviewed_at: reviewedAt,
  review_status: 'reviewed', summary: 'Synthetic dated entry summary.', exception_note: 'Synthetic exception requires review.',
  evidence: { url: `https://www.nps.gov/${park_code}/planyourvisit/reservations.htm`, excerpt: 'EXCERPT_NOT_FOR_DRAFT',
    content_hash: 'a'.repeat(64), hash_scope: 'excerpt', reviewed_at: reviewedAt,
    source_updated_at: null, method: 'manual_official_page_review' },
});
const note = (park_code = 'yose', id = recordId): EntryNote => ({
  id, park_code, subject_type: 'general_entry', period_status: 'not_published', effective_from: null, effective_to: null,
  reviewed_at: reviewedAt, review_status: 'needs_review', summary: 'Synthetic undated entry observation.',
  limitation: 'No effective dates were published.', evidence: { ...rule(park_code, id).evidence, source_updated_at: null },
  rights_basis: 'Government-authored synthetic fixture.', rights_reviewed_at: reviewedAt,
});
const notice = (url: string | null = 'https://provider.example/synthetic-notice', id = recordId) => ({
  id, title: 'Synthetic retained notice.', description: 'Unclassified and unconfirmed for travel dates.',
  category: 'Park Closure', url, scope_status: 'unclassified', source_updated_at: null,
  observed_first_at: '2026-09-28T01:02:03Z', observed_changed_at: checkedAt,
});
const snapshot = (park_code = 'yose', records = [notice()]) => ({
  park_code, collection_status: 'quarantined', coverage_status: 'last_good_retained', last_checked_at: checkedAt,
  last_successful_fetch_at: '2026-09-29T01:02:03Z', source_updated_at: null, records,
});
const fixture = () => ({
  parks: [{ code: 'yose', name: 'Synthetic Yosemite', slug: 'yosemite' }, { code: 'romo', name: 'Synthetic Rocky Mountain', slug: 'rocky-mountain' }],
  rules: [rule(), rule('romo')], notes: [note()], snapshots: [snapshot(), snapshot('romo', [notice(null)])],
});
function api(name: string) { assert.equal(typeof mod[name], 'function', `${name} must exist`); return mod[name]; }
const catalog = (input = fixture(), base = '/') => api('createCorrectionSources')(input, base);
const facts = (source: any) => Object.fromEntries(source.facts.map((fact: any) => [fact.label, fact.value]));

test('public identity distinguishes record kind and park even when record IDs are identical', () => {
  const key = api('correctionKey'); const anchor = api('correctionAnchor');
  assert.equal(key('rule', 'yose', recordId), `rule:yose:${recordId}`);
  assert.equal(key('note', 'yose', recordId), `note:yose:${recordId}`);
  assert.equal(key('alert', 'romo', recordId), `alert:romo:${recordId}`);
  assert.equal(anchor('rule', 'yose', recordId), `entry-rule-${recordId}`);
  assert.equal(anchor('note', 'yose', recordId), `entry-note-${recordId}`);
  assert.equal(anchor('alert', 'romo', recordId), `alert-romo-${recordId}`);
  assert.equal(new Set(catalog().map((source: any) => source.key)).size, 5);
});

test('correction links stay on-site and encode only the source identity under either hosting base', () => {
  const href = api('correctionHref');
  for (const base of ['/', projectBase]) {
    const actual = href('rule', 'yose', recordId, base);
    assert.equal(actual, `${base}corrections/?source=${encodeURIComponent(`rule:yose:${recordId}`)}`);
    const url = new URL(actual, 'http://127.0.0.1:4321');
    assert.deepEqual([...url.searchParams], [['source', `rule:yose:${recordId}`]]);
  }
});

test('dated guidance retains public wording and exact review/status/source clocks', () => {
  const input = fixture(); input.rules[0].review_status = 'conflict';
  input.rules[0].evidence.source_updated_at = '2026-09-27T22:00:00Z';
  const source = catalog(input, projectBase)[0];
  assert.equal(source.kind, 'rule'); assert.equal(source.label, 'Dated entry guidance');
  assert.equal(source.parkName, input.parks[0].name); assert.equal(source.parkCode, 'yose'); assert.equal(source.recordId, recordId);
  assert.equal(source.wording, `${input.rules[0].summary}\n\n${input.rules[0].exception_note}`);
  assert.equal(source.sourceUrl, input.rules[0].evidence.url); assert.equal(source.sourceLinkLabel, 'Read the official source');
  assert.equal(source.returnHref, `${projectBase}parks/yosemite/#${encodeURIComponent(`entry-rule-${recordId}`)}`);
  assert.equal(facts(source)['Review status'], 'conflict'); assert.equal(facts(source)['Source reviewed at'], reviewedAt);
  assert.equal(facts(source)['Source update time'], input.rules[0].evidence.source_updated_at);
  assert.equal(facts(source)['Effective from'], input.rules[0].effective_from);
  assert.equal(facts(source)['Effective through'], input.rules[0].effective_to);
});

test('undated observations preserve limitations without inventing an effective period', () => {
  const input = fixture(); const source = catalog(input).find((entry: any) => entry.kind === 'note');
  assert.equal(source.label, 'Undated entry observation');
  assert.equal(source.wording, `${input.notes[0].summary}\n\n${input.notes[0].limitation}`);
  assert.equal(source.sourceLinkLabel, 'Read the official source');
  assert.equal(source.returnHref, `/parks/yosemite/#${encodeURIComponent(`entry-note-${recordId}`)}`);
  assert.equal(facts(source)['Review status'], 'needs_review'); assert.equal(facts(source)['Source reviewed at'], reviewedAt);
  assert.equal(facts(source)['Source update time'], 'Not supplied');
  assert.ok(!JSON.stringify(source).includes('2026-04-01'));
  assert.ok(!JSON.stringify(source).includes('2026-10-31'));
});

test('retained alerts keep independent attempt/success/observation clocks and provider attribution', () => {
  const input = fixture(); const source = catalog(input).find((entry: any) => entry.kind === 'alert' && entry.parkCode === 'yose');
  assert.equal(source.label, 'Retained NPS notice');
  assert.equal(source.wording, `${input.snapshots[0].records[0].title}\n\n${input.snapshots[0].records[0].description}`);
  assert.equal(source.sourceLinkLabel, 'Source link supplied by NPS');
  assert.equal(source.sourceUrl, input.snapshots[0].records[0].url);
  assert.equal(source.returnHref, `/parks/yosemite/#${encodeURIComponent(`alert-yose-${recordId}`)}`);
  const metadata = facts(source);
  assert.equal(metadata['Collection status'], 'quarantined'); assert.equal(metadata['Coverage status'], 'last_good_retained');
  assert.equal(metadata['Last attempted check'], checkedAt); assert.equal(metadata['Last successful check'], input.snapshots[0].last_successful_fetch_at);
  assert.equal(metadata['Source update time'], 'Not supplied');
  assert.equal(metadata['First observed in the feed'], input.snapshots[0].records[0].observed_first_at);
  assert.equal(metadata['Last observed change'], checkedAt);
});

test('missing alert destinations and clocks stay missing instead of borrowing an official source or current time', () => {
  const input: any = fixture(); input.snapshots[1].last_checked_at = null; input.snapshots[1].last_successful_fetch_at = null;
  delete input.snapshots[1].records[0].observed_first_at; delete input.snapshots[1].records[0].observed_changed_at;
  const source = catalog(input).find((entry: any) => entry.kind === 'alert' && entry.parkCode === 'romo');
  assert.equal(source.sourceUrl, null); assert.equal(source.sourceLinkLabel, 'Source link supplied by NPS');
  const metadata = facts(source);
  assert.equal(metadata['Last attempted check'], 'Never'); assert.equal(metadata['Last successful check'], 'Never');
  assert.equal(metadata['Source update time'], 'Not supplied');
  assert.equal(metadata['First observed in the feed'], 'Not supplied'); assert.equal(metadata['Last observed change'], 'Not supplied');
  assert.match(new URL(source.draftHref).searchParams.get('body')!, /Source link: Not supplied/);
});

test('GitHub drafts contain only public identity, canonical page/source destinations, original facts and blank prompts', () => {
  const input: any = fixture(); const privateMarker = 'PRIVATE_TRIP_OR_OPERATOR_DATA';
  input.trip = { date: privateMarker, time: privateMarker, area: privateMarker, booking: privateMarker };
  for (const park of input.parks) park.private_capture = privateMarker;
  for (const item of [...input.rules, ...input.notes]) { item.private_packet = privateMarker; item.evidence.private_credential = privateMarker; }
  input.snapshots[0].private_ledger = privateMarker; input.snapshots[0].records[0].private_capture = privateMarker;
  for (const base of ['/', projectBase]) for (const source of catalog(input, base)) {
    const url = new URL(source.draftHref); assert.equal(url.origin, 'https://github.com');
    assert.equal(url.pathname, '/Vasuki8/us-national-park-trip-readiness-tracker/issues/new');
    assert.deepEqual([...url.searchParams.keys()].sort(), ['body', 'title']);
    const body = url.searchParams.get('body')!;
    const slug = input.parks.find((park: any) => park.code === source.parkCode).slug;
    const anchor = source.kind === 'rule' ? `entry-rule-${recordId}` : source.kind === 'note' ? `entry-note-${recordId}` : `alert-${source.parkCode}-${recordId}`;
    assert.ok(body.includes(`${canonicalOrigin}${projectBase}parks/${slug}/#${encodeURIComponent(anchor)}`));
    assert.ok(body.includes(source.key)); assert.ok(body.includes(source.parkName));
    for (const fact of source.facts) assert.ok(body.includes(`${fact.label}: ${fact.value}`));
    assert.match(body, /Correction requested:\n\n/); assert.match(body, /Official evidence supporting the correction:\n\n/);
    assert.ok(url.searchParams.get('title')!.includes(source.parkName));
    assert.ok(!JSON.stringify(source).includes(privateMarker));
    assert.ok(!body.includes('EXCERPT_NOT_FOR_DRAFT')); assert.ok(!body.includes(source.wording));
    assert.ok(!source.draftHref.includes('127.0.0.1')); assert.ok(!body.includes('?source='));
  }
});

test('exact known source selections ignore unrelated visitor query fields without copying them', () => {
  const select = api('selectCorrectionSource'); const sources = catalog();
  for (const source of sources) {
    const search = `?source=${encodeURIComponent(source.key)}&trip=PRIVATE_TRAVEL_DETAILS&api_key=PRIVATE_CREDENTIAL`;
    assert.equal(select(sources, search), source);
    assert.ok(!source.draftHref.includes('PRIVATE_'));
  }
});

test('unknown, removed, empty, malformed and ambiguous source selections cannot select or reflect arbitrary context', () => {
  const select = api('selectCorrectionSource'); const sources = catalog(); const encoded = encodeURIComponent(sources[0].key);
  for (const search of ['', '?source=', '?source=rule:yose:removed', '?source=https://private.example/?key=PRIVATE',
    '?source=%E0%A4%A', '?source=%', '?source=' + encoded + '%ZZ', '?source=' + encoded + '#trip=private',
    `?source=${encoded}&source=${encoded}`, `?source=${encoded}&%73ource=unknown`, `?source=${encoded}&source=`, '?SOURCE=' + encoded]) {
    assert.equal(select(sources, search), undefined, search);
  }
  assert.equal(select([], `?source=${encoded}`), undefined);
  assert.equal(select([...sources, sources[0]], `?source=${encoded}`), undefined);
});

test('malformed source encoding cannot select an allowlisted literal percent or replacement-character identity', () => {
  const select = api('selectCorrectionSource'); const input = fixture();
  input.rules = [rule('yose', 'literal%ZZ'), rule('yose', 'replacement�')];
  const sources = catalog(input);
  assert.equal(select(sources, '?source=rule:yose:literal%ZZ'), undefined);
  assert.equal(select(sources, '?source=rule:yose:replacement%FF'), undefined);
  assert.equal(select(sources, '?source=rule:yose:literal%25ZZ&ignored=%FF'), sources[0]);
});

test('catalog construction and selection do not mutate supplied public data or aliases', () => {
  const input = fixture(); const before = structuredClone(input);
  const deepFreeze = (value: any): any => { if (value && typeof value === 'object') { Object.values(value).forEach(deepFreeze); Object.freeze(value); } return value; };
  deepFreeze(input); const sources = catalog(input);
  assert.deepEqual(input, before); api('selectCorrectionSource')(sources, '?source=' + encodeURIComponent(sources[0].key));
  assert.deepEqual(input, before);
  sources[0].facts[0].value = 'Changed displayed fact'; assert.deepEqual(input, before);
  for (const source of sources) assert.deepEqual(Object.keys(source).sort(),
    ['draftHref', 'facts', 'key', 'kind', 'label', 'parkCode', 'parkName', 'recordId', 'returnHref', 'sourceLinkLabel', 'sourceUrl', 'wording'].sort());
});
