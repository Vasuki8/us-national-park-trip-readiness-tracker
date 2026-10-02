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
  const targetFor = (hash: string): HTMLElement | undefined => {
    if (!hash.startsWith('#') || hash.length === 1) return undefined;
    try {
      const id = decodeURIComponent(hash.slice(1));
      const matching = cards.filter((card) => card.id === id);
      return matching.length === 1 ? matching[0] : undefined;
    } catch { return undefined; }
  };
  const synchronize = () => {
    const target = targetFor(window.location.hash);
    const excluded = Boolean(target && !matches(target));
    const reveal = Boolean(target && (target.hidden || excluded));
    if (excluded) reset();
    else update();
    // Native fragment navigation already handles visible targets. Hidden targets
    // need their position restored after conflicting filters have been cleared.
    if (reveal) {
      target!.focus({ preventScroll: true });
      target!.scrollIntoView({ block: 'start' });
    }
  };
  search.addEventListener('input', update);
  category.addEventListener('change', update);
  clear.addEventListener('click', reset);
  document.addEventListener('click', (event) => {
    if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey
      || !(event.target instanceof Element)) return;
    const anchor = event.target.closest<HTMLAnchorElement>('a[href]');
    if (!anchor || anchor.hasAttribute('download')) return;
    const browsingTarget = anchor.getAttribute('target');
    if (browsingTarget && browsingTarget.toLowerCase() !== '_self') return;
    let destination: URL;
    try { destination = new URL(anchor.getAttribute('href')!, window.location.href); }
    catch { return; }
    if (destination.origin !== window.location.origin || destination.pathname !== window.location.pathname
      || destination.search !== window.location.search) return;
    const target = targetFor(destination.hash);
    if (!target) return;
    // A second activation of the same fragment need not fire hashchange. Reveal
    // before the native link action; the browser retains navigation and focus.
    if (!matches(target)) reset();
    else if (target.hidden) update();
  });
  window.addEventListener('hashchange', synchronize);
  // Browser restoration can apply control values after pageshow has fired.
  window.addEventListener('pageshow', () => { window.setTimeout(synchronize, 0); });
  synchronize();
  controls.hidden = false;
}
