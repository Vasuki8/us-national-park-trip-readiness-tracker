import { describeAlerts, evaluateEntry, freshness, type Rule, type Trip } from '../lib/readiness';
const context = document.querySelector<HTMLElement>('#trip-context');
if (context) {
  const rules: Rule[] = JSON.parse(context.dataset.rules || '[]');
  const form = document.querySelector<HTMLFormElement>('#trip-form')!;
  const date = document.querySelector<HTMLInputElement>('#trip-date')!;
  const time = document.querySelector<HTMLInputElement>('#trip-time')!;
  const area = document.querySelector<HTMLSelectElement>('#trip-area')!;
  const special = document.querySelector<HTMLInputElement>('#special-case')!;
  const checks = [...document.querySelectorAll<HTMLInputElement>('[data-check]')];
  let evaluated = false;
  const selection = (): Trip => ({ park_code: context.dataset.park!, date: date.value, time: time.value, area: area.value, special_case: special.checked });
  let previousSelection = JSON.stringify(selection());
  const showDecision = () => {
    const result = evaluateEntry(rules, selection(), new Date());
    const title = document.querySelector('#decision-title')!;
    const detail = document.querySelector('#decision-detail')!;
    if (title.textContent !== result.title) title.textContent = result.title;
    if (detail.textContent !== result.detail) detail.textContent = result.detail;
    document.querySelector<HTMLElement>('#entry-decision')!.dataset.state = result.state;
  };
  const progress = () => {
    const completed = checks.filter((check) => check.checked).length;
    const label = completed === checks.length
      ? 'Your checklist is complete. This does not verify a booking or guarantee conditions.'
      : `${completed} of ${checks.length} items reviewed by you`;
    const target = document.querySelector('#checklist-progress')!;
    if (target.textContent !== label) target.textContent = label;
  };
  const reset = () => { checks.forEach((check) => { check.checked = false; }); previousSelection = JSON.stringify(selection()); progress(); };
  const syncTrip = () => { if (JSON.stringify(selection()) !== previousSelection) reset(); };
  document.querySelector<HTMLButtonElement>('#check-entry')!.disabled = false;
  form.addEventListener('submit', (event) => { event.preventDefault(); syncTrip(); evaluated = true; showDecision(); });
  form.addEventListener('input', () => { reset(); if (evaluated) showDecision(); });
  form.addEventListener('change', () => { reset(); if (evaluated) showDecision(); });
  checks.forEach((check) => { check.disabled = false; check.addEventListener('change', progress); });
  document.querySelector<HTMLButtonElement>('#reset-checklist')!.disabled = false;
  document.querySelector('#reset-checklist')!.addEventListener('click', reset);
  const updateFreshness = () => {
    syncTrip();
    document.querySelectorAll<HTMLElement>('[data-reviewed]').forEach((element) => {
      const state = freshness(element.dataset.reviewed || null, 168, new Date());
      element.textContent = state === 'fresh' ? 'Within the seven-day review window. Source changes are not automatically monitored.' : 'Needs a fresh review. Use the official source; stored guidance may have changed.';
    });
    const alert = document.querySelector<HTMLElement>('#alert-status');
    if (alert) {
      const result = describeAlerts(JSON.parse(alert.dataset.snapshot || '{}'), new Date());
      document.querySelector('#notice-title')!.textContent = result.title;
      document.querySelector('#notice-detail')!.textContent = result.detail;
    }
    if (evaluated) showDecision();
  };
  reset(); updateFreshness();
  window.setInterval(updateFreshness, 60_000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) updateFreshness(); });
  window.addEventListener('pageshow', (event) => {
    // Persisted form values can be restored after pageshow has fired.
    window.setTimeout(() => {
      if (!event.persisted) reset();
      updateFreshness(); progress();
    }, 0);
  });
}
