import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

// Run at the generated-site gate, after each hosting-base build.
export function assertLivePilotCopy(output) {
  const failures = [];
  const pages = [
    ['how-it-works', [
      [/manual/i, 'explains manual alert updates'],
      [/four hours/i, 'explains the alert freshness window'],
    ], /no live public alert history has been collected yet/i],
    ['sources', [
      [/manual/i, 'explains reviewed manual publication'],
      [/no collection schedule|collection is not scheduled/i, 'discloses unscheduled collection'],
    ], /public collection not enabled|remain labeled not collected/i],
    ['changes', [
      [/manual|deliberate/i, 'explains how recorded history is published'],
    ], /live public history has not been collected/i],
    ['parks', [
      [/manual/i, 'explains manual alert updates'],
    ], /live alerts are not connected/i],
    ['privacy', [
      [/GitHub Pages/, 'identifies the actual hosting provider'],
      [/ordinary (?:web )?requests/i, 'acknowledges requests received by the host'],
    ], /eventual hosting provider|before launch/i],
    ['terms', [
      [/manual/i, 'explains manual alert updates'],
      [/not continuously monitored|no continuous monitoring/i, 'preserves the monitoring limitation'],
    ], /before public launch/i],
  ];
  for (const [route, required, obsolete] of pages) {
    const html = readFileSync(`${output}/${route}/index.html`, 'utf8');
    for (const [pattern, description] of required) {
      if (!pattern.test(html)) failures.push(`${route}: ${description}`);
    }
    if (obsolete.test(html)) failures.push(`${route}: retains an obsolete pre-launch or uncollected claim`);
  }
  assert.deepEqual(failures, [], 'Public copy must describe the manually updated, hosted pilot honestly');
}
