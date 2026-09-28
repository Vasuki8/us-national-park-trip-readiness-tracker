# Official sources and commercial-use review

**Review date:** 28 September 2026. **Scope:** public documentation and selected official pages reviewed during kickoff. This is a product/engineering source review, not legal advice or a guarantee of commercialization rights in every jurisdiction.

A narrow MVP using reviewed NPS-created government facts/text and supported NWS data appears feasible without a paid data-commercialization licence. That does not make every agency-hosted text, photograph, map or mark unrestricted. Original explanations and source-linked facts are the initial scope; unreviewed third-party media and NPS marks are excluded.

The API registration/documentation review is not live integration verification. No authenticated payload or complete park audit follows from these references alone. Current implementation and checks are in `PROJECT_STATUS.md`. The source content and terms must be rechecked before adding new uses or deploying commercially.

## Source register

- **S01 — NPS developer resources:** https://www.nps.gov/subjects/developer/index.htm — Coverage overview; actual endpoint completeness requires integration tests.
- **S02 — NPS registration:** https://www.nps.gov/subjects/developer/get-started.htm — Free owner-controlled API key; no key is exposed in code or chat.
- **S03 — NPS guide:** https://www.nps.gov/subjects/developer/guides.htm — Authentication, request limits and disclaimer pointer.
- **S04 — NPS ownership/disclaimer:** https://www.nps.gov/aboutus/disclaimer.htm — Government-created content, third-party rights and protected marks need distinct treatment.
- **S05 — NWS API:** https://www.weather.gov/documentation/services-web-api — Open-data use, rate limits, point forecast geography and temporal coverage; weather not integrated yet.
- **S06 — Yosemite entrance reservations:** https://www.nps.gov/yose/planyourvisit/reservations.htm — Reviewed 2026 entrance rule; does not settle camping/activity permits. Stored excerpt evidence is in `data/rules.json`.
- **S07 — Rocky Mountain timed entry:** https://www.nps.gov/romo/planyourvisit/timed-entry-permit-system.htm — Area, season, daily time and exceptions matter. Stored excerpt evidence is in `data/rules.json`.
- **S08 — NPS entrance fees:** https://www.nps.gov/aboutus/entrance-fee-prices.htm — Preserve units, nonresident eligibility and pass caveats; no total-cost calculator implemented.
- **S09 — NPS visitor-use statistics:** https://www.nps.gov/subjects/socialscience/visitor-use-statistics-dashboard.htm — A verified national-park top-20 export remains pending; pilots are not a ranking.
- **S10 — Google replicated content:** https://support.google.com/publisherpolicies/answer/11190248?hl=en — Source permission alone is not added value or AdSense approval.
- **S11 — Google Search spam policies:** https://developers.google.com/search/docs/essentials/spam-policies — Do not create scaled low-value pages for rankings.
- **S12 — Google publisher consent:** https://support.google.com/adsense/answer/13554116?hl=en — Regional consent/CMP obligations require review before advertising activation.
- **S13 — GitHub additional-product terms:** https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features — Do not assume GitHub Pages is the production host for an advertising business.
- **S14 — Cloudflare Pages limits:** https://developers.cloudflare.com/pages/platform/limits/ — Budget all builds, not only scheduled refreshes.
- **S15 — Cloudflare terms:** https://www.cloudflare.com/terms/ — Owner-controlled hosting review; no account creation or provider agreement acceptance in this increment.
- **S16 — Astro Cloudflare deployment:** https://docs.astro.build/en/guides/deploy/cloudflare/ — Static deployment candidate; not a verified deployment.
- **S17 — GitHub schedules:** https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule — Jobs may be delayed; display actual check/publication clocks.
- **S18 — Workers Static Assets:** https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/ — Optional future architecture, not needed in the pilot.

## Initial exclusions

No third-party booking inventory, Recreation.gov/RIDB ingestion, photographs, paid map services, NPS arrowhead, or active advertising. Review source-specific rights before expanding beyond government-authored factual text. Keep a clear independent/non-endorsed disclosure. No claim is made to original U.S. Government works.
