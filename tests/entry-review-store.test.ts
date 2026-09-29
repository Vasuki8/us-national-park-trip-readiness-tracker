import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

test('private ledger uses all six repository guidance bindings and leaves production files unchanged', () => {
  const paths = ['data/rules.json', 'data/entry-notes.json', 'data/entry-review.json', 'data/history.json'];
  const before = paths.map((path) => readFileSync(path));
  const script = `
import json,tempfile
from datetime import timedelta
from html import escape
from pathlib import Path
from tracker.entry_sources import PROFILES,instant
from tracker.entry_review_store import EntryReviewStore
from tracker.entry_review_model import safe_summary
records=json.loads(Path('data/rules.json').read_text())+json.loads(Path('data/entry-notes.json').read_text())
latest=max(instant(r['reviewed_at']) for r in records)
checked=(latest+timedelta(hours=1)).isoformat(timespec='milliseconds').replace('+00:00','Z')
captures=[]
for code,profile in PROFILES.items():
    body='<html><body><h1>'+escape(profile['heading'])+'</h1>'
    body+=''.join('<p>'+escape(r['evidence']['excerpt'])+'</p>' for r in records if r['park_code']==code)
    body+='</body></html>'
    captures.append(dict(source_url=profile['url'],final_url=profile['url'],checked_at=checked,status='success',content_type='text/html',html=body))
with tempfile.TemporaryDirectory() as folder:
    store=EntryReviewStore(Path(folder)/'private-ledger')
    first=store.record(dict(records=records,captures=captures,baselines=[],seed_register=json.loads(Path('data/entry-review.json').read_text())),expected_revision=None,now=latest+timedelta(hours=2))
    saved=store.read()
    assert saved['records']==records
    assert len(saved['events'][0]['extraction']['sources'])==5
    proposal=saved['register']['proposals'][0]['id']
    store.disposition(dict(proposal_id=proposal,reviewer='synthetic-reviewer',decision='retain_hold',rationale='Synthetic verification; not an actual source review.'),expected_revision=first['revision'],now=latest+timedelta(hours=3))
    result=store.read()
    assert result['register']==saved['register']
    print(json.dumps(safe_summary(result)))
`;
  const result = spawnSync('python3', ['-c', script], { encoding: 'utf8', timeout: 30_000, maxBuffer: 1024 * 1024 });
  assert.equal(result.status, 0, result.stderr);
  const summary = JSON.parse(result.stdout);
  assert.equal(summary.guidance_records, 6);
  assert.equal(summary.pending_proposals, 6);
  assert.equal(summary.recorded_batches, 1);
  assert.equal(summary.reviewer_dispositions, 1);
  assert.equal(summary.approval_performed, false);
  assert.equal(summary.publication_performed, false);
  paths.forEach((path, index) => assert.deepEqual(readFileSync(path), before[index]));
});

test('bounded review bridge fails without echoing malformed private payloads', () => {
  for (const input of ['not-json-private-key', '{"secret":"never-echo-this"}', Buffer.from([0xff])]) {
    const result = spawnSync(process.execPath, ['--experimental-strip-types', 'scripts/entry-review-bridge.ts'],
      { input, encoding: 'utf8', timeout: 10_000, env: { PATH: process.env.PATH, NODE_NO_WARNINGS: '1' } });
    assert.equal(result.status, 2);
    assert.equal(result.stdout, '');
    assert.equal(result.stderr, 'entry_review_bridge_failed\n');
  }
});
