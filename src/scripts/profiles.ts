import { describeProfile, type ProfileClock } from '../lib/park-profile';

const checks = [...document.querySelectorAll<HTMLElement>('[data-profile-clock]')].map(element => ({
  element, clock: JSON.parse(element.dataset.profileClock ?? 'null') as ProfileClock | null,
}));
if (checks.length) {
  const update = () => {
    const now = new Date();
    for (const { element, clock } of checks) {
      const result = describeProfile(clock, now);
      const title = element.querySelector<HTMLElement>('[data-profile-state]')!;
      const detail = element.querySelector<HTMLElement>('[data-profile-detail]')!;
      if (title.dataset.profileState !== result.state) title.dataset.profileState = result.state;
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
