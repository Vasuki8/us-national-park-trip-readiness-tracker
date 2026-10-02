import { selectCorrectionSource, type CorrectionSource } from '../lib/corrections';

const context = document.querySelector<HTMLElement>('#correction-context');
if (context) {
  let sources: CorrectionSource[] = [];
  try {
    const parsed = JSON.parse(context.dataset.correctionSources || '[]');
    if (Array.isArray(parsed)) sources = parsed;
  } catch { /* General reporting remains available if the embedded catalog is damaged. */ }
  const render = () => {
    const source = selectCorrectionSource(sources, window.location.search);
    document.querySelector<HTMLElement>('#correction-source')!.hidden = !source;
    document.querySelector<HTMLElement>('#correction-intro')!.hidden = Boolean(source);
    document.querySelector<HTMLElement>('#correction-unavailable')!.hidden = Boolean(source) || !new URLSearchParams(window.location.search).has('source');
    if (!source) return;
    document.querySelector('#correction-source-label')!.textContent = `${source.parkName} · ${source.label}`;
    document.querySelector('#correction-source-id')!.textContent = source.recordId;
    document.querySelector('#correction-wording')!.textContent = source.wording;
    const facts = document.querySelector('#correction-facts')!;
    facts.replaceChildren(...source.facts.flatMap(({ label, value }) => {
      const term = document.createElement('dt'); term.textContent = label;
      const definition = document.createElement('dd'); definition.textContent = value;
      return [term, definition];
    }));
    const official = document.querySelector<HTMLAnchorElement>('#correction-official-source')!;
    official.hidden = source.sourceUrl === null;
    official.href = source.sourceUrl ?? '#';
    official.textContent = source.sourceLinkLabel;
    document.querySelector<HTMLElement>('#correction-missing-link')!.hidden = source.sourceUrl !== null;
    document.querySelector<HTMLAnchorElement>('#correction-return')!.href = source.returnHref;
    document.querySelector<HTMLAnchorElement>('#correction-draft')!.href = source.draftHref;
  };
  render();
  window.addEventListener('pageshow', render);
  window.addEventListener('popstate', render);
}
