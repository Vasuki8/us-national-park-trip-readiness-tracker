import assert from 'node:assert/strict';

const decodeHtml = (value) => value.replace(/&(?:quot|amp|lt|gt|#39);/g, (entity) => ({ '&quot;': '"', '&amp;': '&', '&lt;': '<', '&gt;': '>', '&#39;': "'" })[entity]);

export function assertHistoryCounts(html, histories) {
  const observations = histories.flatMap((history) => history.observations);
  assert.equal((html.match(/data-history-metadata=/g) || []).length, histories.length);
  assert.equal((html.match(/data-history-observation/g) || []).length, observations.length);
  assert.equal((html.match(/Baseline recorded/g) || []).length, observations.filter((item) => item.comparison === 'baseline').length);
}

export function assertHistoryPanel(html, snapshot, history) {
  const panel = html.match(new RegExp(`<section[^>]*id="history-${history.park_code}"[^>]*>[\\s\\S]*?</section>`))?.[0];
  assert.ok(panel, `Missing history for ${history.park_code}`);
  const metadata = panel.match(/data-history-metadata="([^"]*)"/)?.[1];
  assert.ok(metadata, 'Missing history metadata');
  assert.deepEqual(JSON.parse(decodeHtml(metadata)), {
    collection_status: snapshot.collection_status, last_checked_at: snapshot.last_checked_at,
    last_successful_fetch_at: snapshot.last_successful_fetch_at,
  });
  const times = [...panel.matchAll(/<time datetime="([^"]*)"[^>]*>([^<]*)<\/time>/g)];
  assert.deepEqual(times.map((match) => match[1]), [
    ...(snapshot.last_successful_fetch_at ? [snapshot.last_successful_fetch_at] : []),
    ...history.observations.map((item) => item.checked_at),
  ]);
  for (const match of times) assert.equal(decodeHtml(match[2]), match[1], 'Visible clock must match its datetime');
  assert.equal((panel.match(/data-history-observation/g) || []).length, history.observations.length);
  const baselines = history.observations.filter((item) => item.comparison === 'baseline').length;
  assert.equal((panel.match(/Baseline recorded/g) || []).length, baselines);
  assert.equal((panel.match(/not evidence that its restrictions began at this time/g) || []).length, baselines);
  if (history.omitted_observations) assert.ok(panel.includes(`${history.omitted_observations} older recorded checks not shown.`));
  if (history.omitted_changes) assert.ok(panel.includes(`${history.omitted_changes} recorded notice changes not shown in this view.`));
  for (const observation of history.observations) {
    if (observation.omitted_changes) assert.ok(panel.includes(`${observation.omitted_changes} additional notice changes from this recorded check are not shown in this bounded view.`));
  }
}
