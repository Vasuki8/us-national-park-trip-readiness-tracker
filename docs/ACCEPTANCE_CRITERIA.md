# Release acceptance criteria

These scenarios define the intended release, not a blanket statement that every check has passed. Consult `PROJECT_STATUS.md` and the exact CI run. Synthetic fixtures stay outside production data; deferred features must not look active.

## A. Collection integrity

1. Valid empty alerts means no alerts returned by the checked feed, not everything open.
2. Authentication failures, throttling, timeouts, invalid JSON and provider errors retain last-good values with original success timestamps and degraded status.
3. Exhaust pagination and reconcile counts before complete success.
4. Quarantine malformed schemas, dates, units, source URLs and major record dropouts.
5. Keys remain private and absent from HTML, JavaScript, metadata, errors and commits.
6. Retries, requests and page counts are bounded.

## B. Geographic and temporal meaning

7. A facility closure cannot close the whole park in the UI.
8. A removed alert is no longer in the feed, not a confirmed reopening.
9. Source, effective, attempt, success, review, build and publication clocks remain distinct.
10. Unknown alert applicability to future dates stays unresolved.
11. Previous-year rules do not carry into another year.
12. Areas within a park can have different rules at the same time.
13. Test local midnight, first/last dates, exact daily boundaries, leap dates and DST.
14. Missing arrival time or area yields an unresolved-input explanation.
15. Ambiguous exceptions require official review, not a guessed exemption.

## C. Freshness and history

16. Injected clocks make alert evidence stale even without another deployment.
17. Failed checks do not advance last-success or source-update time.
18. Boilerplate-only changes do not become operational events.
19. Semantic history retains old/new evidence; source-ID changes cannot erase it.
20. Conflicts remain visible rather than silently picking a source.
21. Invalid snapshots cannot replace last-good data; operators can diagnose failure.
22. Rollback does not rewrite old collection timestamps as recent checks.

## D. Weather and fees — deferred in foundation

23. Forecasts identify a named point and issuance/validity time.
24. State warnings are not automatically park warnings.
25. Dates outside the forecast horizon get no invented weather.
26. Fetch failure cannot imply clear weather.
27. Fees preserve currency, units, date, eligibility and pass caveats; incomplete components are not totals.

## E. Interface and content

28. Directory and park pages contain meaningful HTML before JavaScript.
29. Native labels, focus and keyboard interactions work; empty/error states and zoom remain usable.
30. Critical controls, notices and evidence links fit a 360px viewport.
31. Text conveys status without requiring color; no numerical safety score.
32. Checklist completion is self-reported, not a verified booking.
33. Any future saved preferences can be cleared; no automatic advertising use of trip details.
34. Operational claims carry official evidence; missing coverage is visible.
35. Development/fixture pages are noindex and ad-free.

## F. Publication and monetization — later gates

36. Actual production URL and snapshot must be fetched before claiming deployment.
37. Operators can independently inspect source, collection and publication clocks.
38. Build budgets include previews, retries and code pushes, without duplicate deploy triggers.
39. Advertising stays off until account/site, publisher, privacy/consent and placement reviews pass.
40. No ad obscures notices, imitates booking links, or appears on empty/failed-result pages. No unreviewed media or official marks.

## Foundation verification mapping

`tests/readiness.test.ts` and `tests/data.test.ts` cover deterministic rules, evidence and timestamps. `tests/test_alerts.py` covers synthetic collection and transport behavior. `tests/site.test.mjs` checks generated static output and route links. `tests/browser.spec.ts` covers search, forms, checklist resets, 360px overflow and no-JavaScript behavior. This is not a claim that raw evidence retention, semantic history, 200% zoom, live API, weather, fee calculations, production deployment or advertising gates have passed.
