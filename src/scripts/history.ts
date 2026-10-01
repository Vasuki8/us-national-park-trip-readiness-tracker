import { describeHistory, type HistoryMetadata } from '../lib/history';
const timelines = [...document.querySelectorAll<HTMLElement>('[data-history]')].map((element) => {
  let metadata: HistoryMetadata = { collection_status: 'unknown', last_checked_at: null, last_successful_fetch_at: null };
  try {
    const value = JSON.parse(element.dataset.historyMetadata || '{}');
    if (value && typeof value.collection_status === 'string') metadata = {
      collection_status: value.collection_status,
      last_checked_at: typeof value.last_checked_at === 'string' ? value.last_checked_at : null,
      last_successful_fetch_at: typeof value.last_successful_fetch_at === 'string' ? value.last_successful_fetch_at : null,
    };
  } catch { /* Keep visibly unverified metadata if the page payload is damaged. */ }
  return { element, metadata };
});
function refreshHistory() {
  const now = new Date();
  for (const { element, metadata } of timelines) {
    const status = describeHistory(metadata, now);
    for (const [selector, text] of [['[data-history-status]', status.title], ['[data-history-detail]', status.detail]]) {
      const target = element.querySelector(selector);
      if (target && target.textContent !== text) target.textContent = text;
    }
  }
}
if (timelines.length) {
  refreshHistory();
  window.setInterval(refreshHistory, 60_000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refreshHistory(); });
  window.addEventListener('pageshow', refreshHistory);
  window.addEventListener('beforeprint', refreshHistory);
}
