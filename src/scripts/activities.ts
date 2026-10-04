import { describeActivities, type ActivityClock } from '../lib/park-activities';

const checks = [...document.querySelectorAll<HTMLElement>('[data-activity-clock]')].map(element => ({
  element, clock: JSON.parse(element.dataset.activityClock ?? 'null') as ActivityClock | null,
}));
if (checks.length) {
  const update = () => {
    const now = new Date();
    for (const { element, clock } of checks) {
      const result = describeActivities(clock, now);
      const title = element.querySelector<HTMLElement>('[data-activity-state]')!;
      const detail = element.querySelector<HTMLElement>('[data-activity-detail]')!;
      if (title.dataset.activityState !== result.state) title.dataset.activityState = result.state;
      if (title.textContent !== result.title) title.textContent = result.title;
      if (detail.textContent !== result.detail) detail.textContent = result.detail;
    }
  };
  update();
  window.setInterval(update, 60_000);
  window.addEventListener('pageshow', update);
  window.addEventListener('beforeprint', update);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) update(); });
}
