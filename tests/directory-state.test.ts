import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';

class Element extends EventTarget {
  value = '';
  hidden = false;
  dataset: Record<string, string> = {};
  textWrites: string[] = [];
  private text = '';
  get textContent() { return this.text; }
  set textContent(value: string) { this.text = value; this.textWrites.push(value); }
}

interface DirectoryPark { name: string; code: string; states: readonly string[]; searchText?: string | null }

// Execute the actual browser script with synthetic cards and only DOM APIs replaced.
function directoryPage(query = '', state = '', parks: readonly DirectoryPark[] = [
  { name: 'Yosemite', code: 'yose', states: ['California'] },
  { name: 'Yellowstone', code: 'yell', states: ['Wyoming', 'Montana', 'Idaho'] },
  { name: 'Zion', code: 'zion', states: ['Utah'] },
]) {
  const search = new Element(); search.value = query;
  const filter = new Element(); filter.value = state;
  const count = new Element(); count.textContent = `${parks.length} parks in this pilot`; count.textWrites = [];
  const empty = new Element(); empty.hidden = true;
  const cards = parks.map((park) => {
    const card = new Element();
    card.dataset = Object.freeze({ states: JSON.stringify(park.states), ...(park.searchText === null ? {} : {
      search: park.searchText ?? `${park.name} ${park.code} ${park.states.join(' ')}`.toLowerCase(),
    }) });
    return card;
  });
  const originalMetadata = JSON.stringify(cards.map((card) => card.dataset));
  const elements = new Map([['#park-search', search], ['#state-filter', filter], ['#search-count', count], ['#empty-search', empty]]);
  const document = {
    querySelector: (selector: string) => {
      const element = elements.get(selector);
      assert.ok(element, `expected directory element ${selector}`);
      return element;
    },
    querySelectorAll: (selector: string) => {
      assert.equal(selector, '[data-park-card]');
      return cards;
    },
  };
  const queuedTasks: (() => void)[] = [];
  const window = Object.assign(new EventTarget(), {
    setTimeout: (callback: () => void, delay: number) => {
      assert.equal(delay, 0);
      queuedTasks.push(callback);
    },
  });
  const flushTasks = () => queuedTasks.splice(0).forEach((callback) => callback());
  const source = ts.transpileModule(readFileSync(new URL('../src/scripts/directory.ts', import.meta.url), 'utf8'), {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS },
  }).outputText;
  runInNewContext(source, { document, window });
  return {
    search, filter, count, empty, flushTasks, originalMetadata,
    metadata: () => JSON.stringify(cards.map((card) => card.dataset)),
    showPage: () => window.dispatchEvent(new Event('pageshow')),
    shown: () => parks.filter((_, index) => !cards[index].hidden).map((park) => park.name),
    restore: (restoredQuery: string, restoredState: string) => {
      search.value = restoredQuery;
      filter.value = restoredState;
      window.dispatchEvent(new Event('pageshow'));
      flushTasks();
    },
  };
}

test('directory initialization applies a prefilled search without waiting for an input event', () => {
  const page = directoryPage('  YEll  ');
  assert.deepEqual(page.shown(), ['Yellowstone']);
  assert.equal(page.count.textContent, '1 park shown');
  assert.equal(page.empty.hidden, true);
});

test('directory initialization applies a restored state including a multi-state park', () => {
  const page = directoryPage('', 'Montana');
  assert.deepEqual(page.shown(), ['Yellowstone']);
  assert.equal(page.count.textContent, '1 park shown');
});

test('restored search and state are combined and disclose an empty result', () => {
  const page = directoryPage('Yellowstone', 'Utah');
  assert.deepEqual(page.shown(), []);
  assert.equal(page.count.textContent, '0 parks shown');
  assert.equal(page.empty.hidden, false);
});

test('returning to the page resynchronizes changed controls without input or change events', () => {
  const page = directoryPage();
  page.restore('yellow', 'Wyoming');
  assert.deepEqual(page.shown(), ['Yellowstone']);
  assert.equal(page.count.textContent, '1 park shown');
  page.restore('yellow', 'California');
  assert.deepEqual(page.shown(), []);
  assert.equal(page.empty.hidden, false);
  page.restore('', '');
  assert.deepEqual(page.shown(), ['Yosemite', 'Yellowstone', 'Zion']);
  assert.equal(page.count.textContent, '3 parks shown');
  assert.equal(page.empty.hidden, true);
});

test('page return reads controls restored after pageshow when its queued refresh runs', () => {
  const page = directoryPage();
  page.showPage();
  page.search.value = 'yellow';
  page.filter.value = 'Wyoming';
  page.flushTasks();
  assert.deepEqual(page.shown(), ['Yellowstone']);
  assert.equal(page.count.textContent, '1 park shown');
  assert.equal(page.empty.hidden, true);
});

test('unchanged page returns and equivalent searches do not rewrite the live result count', () => {
  const page = directoryPage('yellow');
  assert.equal(page.count.textContent, '1 park shown');
  assert.deepEqual(page.count.textWrites, ['1 park shown']);
  page.restore('yellow', '');
  page.restore('YELLOW', 'Wyoming');
  page.search.dispatchEvent(new Event('input'));
  page.filter.dispatchEvent(new Event('change'));
  assert.deepEqual(page.shown(), ['Yellowstone']);
  assert.deepEqual(page.count.textWrites, ['1 park shown']);
});

test('existing input and change events still filter and clear the directory', () => {
  const page = directoryPage();
  page.search.value = 'yose';
  page.search.dispatchEvent(new Event('input'));
  assert.deepEqual(page.shown(), ['Yosemite']);
  page.filter.value = 'Utah';
  page.filter.dispatchEvent(new Event('change'));
  assert.deepEqual(page.shown(), []);
  assert.equal(page.empty.hidden, false);
  page.search.value = '';
  page.search.dispatchEvent(new Event('input'));
  assert.deepEqual(page.shown(), ['Zion']);
  assert.equal(page.empty.hidden, true);
  page.filter.value = '';
  page.filter.dispatchEvent(new Event('change'));
  assert.deepEqual(page.shown(), ['Yosemite', 'Yellowstone', 'Zion']);
  assert.equal(page.count.textContent, '3 parks shown');
});

const multiwordParks: readonly DirectoryPark[] = [
  { name: 'Rocky Mountain', code: 'romo', states: ['Colorado'] },
  { name: 'Grand Canyon', code: 'grca', states: ['Arizona'] },
  { name: 'Synthetic [.*] Park', code: 'synt', states: ['Testing'] },
];

test('prefilled multiword names match pasted whitespace without rewriting visitor controls', () => {
  for (const query of ['  ROCKY   MOUNTAIN  ', 'rocky\tmountain', '\tRocky\u00a0 Mountain\n']) {
    const page = directoryPage(query, '', multiwordParks);
    assert.deepEqual(page.shown(), ['Rocky Mountain'], query);
    assert.equal(page.count.textContent, '1 park shown');
    assert.equal(page.empty.hidden, true);
    assert.equal(page.search.value, query, 'matching must not rewrite the pasted query');
    assert.equal(page.metadata(), page.originalMetadata);
  }
});

test('equivalent whitespace queries remain quiet through input and queued control restoration', () => {
  const page = directoryPage('rocky mountain', '', multiwordParks);
  assert.deepEqual(page.shown(), ['Rocky Mountain']);
  assert.deepEqual(page.count.textWrites, ['1 park shown']);
  const typed = '  ROCKY \t  MOUNTAIN  ';
  page.search.value = typed;
  page.search.dispatchEvent(new Event('input'));
  assert.deepEqual(page.shown(), ['Rocky Mountain']);
  assert.equal(page.search.value, typed);
  page.showPage();
  const restored = '\nrocky\t Mountain  ';
  page.search.value = restored;
  page.filter.value = 'Colorado';
  page.flushTasks();
  assert.deepEqual(page.shown(), ['Rocky Mountain']);
  assert.equal(page.search.value, restored);
  assert.equal(page.filter.value, 'Colorado');
  assert.deepEqual(page.count.textWrites, ['1 park shown']);
  assert.equal(page.empty.hidden, true);
  assert.equal(page.metadata(), page.originalMetadata);
});

test('card search text normalizes mixed whitespace and case while absent search metadata stays excluded', () => {
  const page = directoryPage('synthetic national park', '', [
    { name: 'Synthetic National Park', code: 'synt', states: ['Testing'], searchText: '  SYNTHETIC\tNATIONAL\nPARK  synt\u00a0Testing  ' },
    { name: 'Missing search metadata', code: 'none', states: ['Testing'], searchText: null },
  ]);
  assert.deepEqual(page.shown(), ['Synthetic National Park']);
  assert.equal(page.count.textContent, '1 park shown');
  assert.equal(page.metadata(), page.originalMetadata);
  page.search.value = ' \t\n ';
  page.search.dispatchEvent(new Event('input'));
  assert.deepEqual(page.shown(), ['Synthetic National Park'], 'empty normalized queries cannot select a card without search metadata');
  assert.equal(page.search.value, ' \t\n ');
  assert.equal(page.metadata(), page.originalMetadata);
});

test('normalized multiword search remains literal and combines with exact state filtering', () => {
  const query = '  SYNTHETIC   [.*]  PARK  ';
  const page = directoryPage(query, 'Testing', multiwordParks);
  assert.deepEqual(page.shown(), ['Synthetic [.*] Park']);
  for (const state of ['testing', 'Test', 'Testing ', 'Utah']) {
    page.filter.value = state;
    page.filter.dispatchEvent(new Event('change'));
    assert.deepEqual(page.shown(), [], state);
    assert.equal(page.count.textContent, '0 parks shown');
    assert.equal(page.empty.hidden, false);
    assert.equal(page.filter.value, state);
  }
  page.filter.value = 'Testing';
  page.search.value = '[.*]';
  page.search.dispatchEvent(new Event('input'));
  assert.deepEqual(page.shown(), ['Synthetic [.*] Park'], 'regular-expression punctuation is a literal substring');
  page.search.value = '<img src=x>';
  page.search.dispatchEvent(new Event('input'));
  assert.deepEqual(page.shown(), []);
  assert.equal(page.search.value, '<img src=x>');
  assert.equal(page.metadata(), page.originalMetadata);
});
