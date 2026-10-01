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

// Execute the actual browser script with synthetic cards and only DOM APIs replaced.
function directoryPage(query = '', state = '') {
  const search = new Element(); search.value = query;
  const filter = new Element(); filter.value = state;
  const count = new Element(); count.textContent = '3 parks in this pilot'; count.textWrites = [];
  const empty = new Element(); empty.hidden = true;
  const parks = [
    { name: 'Yosemite', code: 'yose', states: ['California'] },
    { name: 'Yellowstone', code: 'yell', states: ['Wyoming', 'Montana', 'Idaho'] },
    { name: 'Zion', code: 'zion', states: ['Utah'] },
  ];
  const cards = parks.map((park) => {
    const card = new Element();
    card.dataset = { search: `${park.name} ${park.code} ${park.states.join(' ')}`.toLowerCase(), states: JSON.stringify(park.states) };
    return card;
  });
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
    search, filter, count, empty, flushTasks,
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
