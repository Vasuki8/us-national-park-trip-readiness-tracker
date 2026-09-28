import { summarizeCoverage, type CoverageInput } from '../lib/source-coverage';
const roots = [...document.querySelectorAll<HTMLElement>('[data-coverage]')];
const refresh = () => {
  for (const root of roots) {
    try {
      const input: CoverageInput = JSON.parse(root.dataset.coverage || '{}');
      const result = summarizeCoverage(input, new Date());
      root.querySelectorAll<HTMLElement>('[data-coverage-metric]').forEach((element) => {
        const key = element.dataset.coverageMetric as keyof typeof result;
        const value = result[key];
        element.textContent = typeof value === 'number' ? String(value).padStart(2, '0') : 'Unknown';
      });
      root.querySelectorAll<HTMLElement>('[data-entry-label]').forEach((element) => {
        element.textContent = result.rows.find((row) => row.code === element.dataset.entryLabel)?.entryLabel ?? 'Source review unavailable';
      });
      root.querySelectorAll<HTMLElement>('[data-alert-label]').forEach((element) => {
        element.textContent = result.rows.find((row) => row.code === element.dataset.alertLabel)?.alertLabel ?? 'Alert state unverified';
      });
    } catch {
      // Invalid embedded metadata cannot leave a reassuring old freshness label.
      root.querySelectorAll<HTMLElement>('[data-coverage-metric]').forEach((element) => { element.textContent = 'Unknown'; });
      root.querySelectorAll<HTMLElement>('[data-entry-label], [data-alert-label]').forEach((element) => { element.textContent = 'Source data unavailable'; });
    }
  }
};
if (roots.length) {
  refresh();
  window.setInterval(refresh, 60_000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
}
