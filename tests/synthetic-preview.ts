/** Offline test inputs. Public promotions must never change these synthetic chains. */
import { copyFileSync, cpSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { PILOT_CODES } from '../scripts/preview-bundle.ts';
import { historyDigest } from '../scripts/validate-history.ts';

const root = resolve(import.meta.dirname, '..');
const empty = JSON.parse(readFileSync(new URL('./fixtures/history-preview.json', import.meta.url), 'utf8')).cases.empty;

export function syntheticEmptyViews() {
  return PILOT_CODES.map(code => {
    const view = structuredClone(empty);
    view.snapshot.park_code = code;
    view.snapshot.source_url = `https://developer.nps.gov/api/v1/alerts?parkCode=${code}`;
    view.history.park_code = code;
    view.history.snapshot_hash = historyDigest(view.snapshot);
    return view;
  });
}

export function syntheticPublicFiles(views = syntheticEmptyViews()) {
  return [
    ...views.map(view => ({path: `data/alerts/${view.snapshot.park_code}.json`, text: JSON.stringify(view.snapshot, null, 2) + '\n'})),
    {path: 'data/history.json', text: JSON.stringify(views.map(view => view.history), null, 2) + '\n'},
  ];
}

export function createSyntheticPromotionProject(dir: string) {
  const project = join(dir, 'project');
  mkdirSync(join(project, 'data/alerts'), {recursive: true});
  for (const folder of ['scripts', 'src/lib', 'tracker']) cpSync(join(root, folder), join(project, folder), {recursive: true});
  copyFileSync(join(root, 'package.json'), join(project, 'package.json'));
  for (const file of syntheticPublicFiles()) writeFileSync(join(project, file.path), file.text);
  return project;
}
