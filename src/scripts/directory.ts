const search = document.querySelector<HTMLInputElement>('#park-search');
const filter = document.querySelector<HTMLSelectElement>('#state-filter');
if (search && filter) {
  const cards = [...document.querySelectorAll<HTMLElement>('[data-park-card]')];
  const update = () => {
    let count = 0;
    const query = search.value.trim().toLowerCase();
    for (const card of cards) {
      const states: string[] = JSON.parse(card.dataset.states || '[]');
      card.hidden = !(card.dataset.search?.includes(query) && (!filter.value || states.includes(filter.value)));
      if (!card.hidden) count += 1;
    }
    const resultCount = document.querySelector('#search-count')!;
    const label = `${count} ${count === 1 ? 'park' : 'parks'} shown`;
    if (resultCount.textContent !== label) resultCount.textContent = label;
    document.querySelector<HTMLElement>('#empty-search')!.hidden = count !== 0;
  };
  search.addEventListener('input', update);
  filter.addEventListener('change', update);
  window.addEventListener('pageshow', () => { window.setTimeout(update, 0); });
  update();
}
