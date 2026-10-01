const noticeRoot = document.querySelector<HTMLElement>('[data-retained-notices]');
if (noticeRoot) {
  const search = noticeRoot.querySelector<HTMLInputElement>('[data-notice-search]')!;
  const category = noticeRoot.querySelector<HTMLSelectElement>('select[data-notice-category]')!;
  const clear = noticeRoot.querySelector<HTMLButtonElement>('[data-notice-clear]')!;
  const controls = noticeRoot.querySelector<HTMLElement>('[data-notice-controls]')!;
  const resultCount = noticeRoot.querySelector<HTMLElement>('[data-notice-count]')!;
  const empty = noticeRoot.querySelector<HTMLElement>('[data-notice-empty]')!;
  const cards = [...noticeRoot.querySelectorAll<HTMLElement>('[data-retained-notice]')];
  const normalize = (text: string) => text.trim().toLowerCase().replace(/\s+/g, ' ');
  const matches = (card: HTMLElement) => normalize(card.dataset.noticeText || '').includes(normalize(search.value))
    && (!category.value || card.dataset.noticeCategory === category.value);
  const update = () => {
    let shown = 0;
    for (const card of cards) {
      card.hidden = !matches(card);
      if (!card.hidden) shown += 1;
    }
    const label = `Showing ${shown} of ${cards.length} retained notices`;
    if (resultCount.textContent !== label) resultCount.textContent = label;
    empty.hidden = shown !== 0;
  };
  const reset = () => { search.value = ''; category.value = ''; update(); };
  const synchronize = () => {
    let target: HTMLElement | undefined;
    try {
      const id = decodeURIComponent(window.location.hash.slice(1));
      target = cards.find((card) => card.id === id);
    } catch { /* Malformed fragments do not identify a stored notice. */ }
    const excluded = Boolean(target && !matches(target));
    const reveal = Boolean(target && (target.hidden || excluded));
    if (excluded) reset();
    else update();
    // Native fragment navigation already handles visible targets. Hidden targets
    // need their position restored after conflicting filters have been cleared.
    if (reveal) target!.scrollIntoView({ block: 'start' });
  };
  search.addEventListener('input', update);
  category.addEventListener('change', update);
  clear.addEventListener('click', reset);
  window.addEventListener('hashchange', synchronize);
  // Browser restoration can apply control values after pageshow has fired.
  window.addEventListener('pageshow', () => { window.setTimeout(synchronize, 0); });
  synchronize();
  controls.hidden = false;
}
