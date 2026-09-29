import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { assessEntrySources, guidanceDigest, reconcileEntryReview } from '../scripts/entry-review.ts';

const parks = JSON.parse(readFileSync(new URL('../data/parks.json', import.meta.url), 'utf8'));
const T0='2026-09-28T10:00:00Z', T1='2026-09-28T12:00:00Z', T2='2026-09-28T13:00:00Z';
const YOSE='https://www.nps.gov/yose/planyourvisit/reservations.htm';
const YELL='https://www.nps.gov/yell/planyourvisit/permitsandreservations.htm';
const hash=(s:string)=>createHash('sha256').update(s).digest('hex');

function rule(id='synthetic-yose', excerpt='Synthetic entry guidance for reconciliation testing.') {
  return { id, park_code:'yose', summary:'Synthetic reviewed rule.', exception_note:'Synthetic exception note.',
    areas:['*'], effective_from:'2026-01-01', effective_to:'2026-12-31',
    requirement:'no_timed_entry', start_time:null, end_time:null, reviewed_at:T0, review_status:'reviewed',
    evidence:{url:YOSE, excerpt, content_hash:hash(excerpt), hash_scope:'excerpt', reviewed_at:T0,
      source_updated_at:null, method:'manual_official_page_review'},
    rights_basis:'Synthetic test rights basis.', rights_reviewed_at:T0 };
}
function note() {
  const excerpt='Synthetic undated Yellowstone entry note.';
  return { id:'synthetic-yell', park_code:'yell', subject_type:'general_entry', period_status:'not_published',
    effective_from:null, effective_to:null, reviewed_at:T0, review_status:'reviewed',
    summary:'Synthetic note.', limitation:'Synthetic limitation.',
    evidence:{url:YELL, excerpt, content_hash:hash(excerpt), hash_scope:'excerpt', reviewed_at:T0,
      source_updated_at:null, method:'manual_official_page_review'},
    rights_basis:'Synthetic test rights basis.', rights_reviewed_at:T0 };
}
function observation(record:any, status:'observed'|'failed'='failed') {
  return { guidance_id:record.id, guidance_hash:guidanceDigest(record), source_url:record.evidence.url,
    checked_at:T1, status, excerpt:status==='observed'?record.evidence.excerpt:null };
}
function approve(record:any, excerpt=record.evidence.excerpt) {
  return {...record, reviewed_at:T2, review_status:'reviewed',
    evidence:{...record.evidence, excerpt, content_hash:hash(excerpt), reviewed_at:T2}};
}

test('reconciliation clears only a complete held source and validates replacement guidance', () => {
  const current=[rule(), note()];
  const assessed=assessEntrySources(current,[observation(current[0]),observation(current[1],'observed')],
    {schema_version:1,proposals:[]},new Date(T2));
  const pid=assessed.register.proposals[0].id;
  const next=[approve(current[0]), current[1]];
  const result=reconcileEntryReview(current,assessed.register,[pid],next,new Date(T2),parks);
  assert.deepEqual(result.affected_guidance_ids,['synthetic-yose']);
  assert.deepEqual(result.source_urls,[YOSE]);
  assert.deepEqual(result.register,{schema_version:1,proposals:[]});
});

test('partial approval of a shared source is refused', () => {
  const current=[rule('synthetic-yose-a','Synthetic first source rule.'),rule('synthetic-yose-b','Synthetic second source rule.')];
  const assessed=assessEntrySources(current,current.map((r)=>observation(r)),
    {schema_version:1,proposals:[]},new Date(T2));
  const next=current.map((r)=>approve(r));
  assert.throws(()=>reconcileEntryReview(current,assessed.register,[assessed.register.proposals[0].id],next,new Date(T2),parks));
});

test('unaffected records and rights metadata cannot be changed during reconciliation', () => {
  const current=[rule(), note()];
  const assessed=assessEntrySources(current,[observation(current[0]),observation(current[1],'observed')],
    {schema_version:1,proposals:[]},new Date(T2));
  const pid=assessed.register.proposals[0].id;
  const changedOther=structuredClone(current[1]); changedOther.summary='Not part of this approval.';
  assert.throws(()=>reconcileEntryReview(current,assessed.register,[pid],[approve(current[0]),changedOther],new Date(T2),parks));
  const changedRights=approve(current[0]); changedRights.rights_reviewed_at=T2;
  assert.throws(()=>reconcileEntryReview(current,assessed.register,[pid],[changedRights,current[1]],new Date(T2),parks));
});

test('affected records require explicit reviewed state and the exact reviewer timestamp', () => {
  const current=[rule()];
  const assessed=assessEntrySources(current,[observation(current[0])],{schema_version:1,proposals:[]},new Date(T2));
  const pid=assessed.register.proposals[0].id;
  for (const mutate of [(r:any)=>r.review_status='needs_review',(r:any)=>r.reviewed_at=T1,(r:any)=>r.evidence.reviewed_at=T1]) {
    const next=approve(current[0]); mutate(next);
    assert.throws(()=>reconcileEntryReview(current,assessed.register,[pid],[next],new Date(T2),parks));
  }
});

test('unknown, duplicate and incomplete proposal selections fail closed', () => {
  const current=[rule()];
  const assessed=assessEntrySources(current,[observation(current[0])],{schema_version:1,proposals:[]},new Date(T2));
  const pid=assessed.register.proposals[0].id; const next=[approve(current[0])];
  for (const ids of [[],['0'.repeat(64)],[pid,pid]]) assert.throws(()=>reconcileEntryReview(current,assessed.register,ids,next,new Date(T2),parks));
});
