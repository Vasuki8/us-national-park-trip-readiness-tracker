import { correctionAnchor } from './corrections.ts';

export interface HistoryNoticeContext {
  parkCode: string;
  records: readonly { id: string }[];
  noticeHrefPrefix: string;
  parkHref?: string;
}

/** Link only to a unique record retained in the paired park snapshot. */
export function retainedNoticeHref(context: HistoryNoticeContext | undefined, historyParkCode: string, recordId: string): string | null {
  if (!context || context.parkCode !== historyParkCode
    || context.records.filter(record => record.id === recordId).length !== 1) return null;
  return `${context.noticeHrefPrefix}#${encodeURIComponent(correctionAnchor('alert', historyParkCode, recordId))}`;
}
