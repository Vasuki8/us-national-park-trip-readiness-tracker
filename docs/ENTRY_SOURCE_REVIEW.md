# General-entry source review — 28 September 2026

The three previously unaudited pilot parks now have stored general-entry source observations in `data/entry-notes.json`. This is not a complete park-readiness or activity-permit audit.

| Park | Official page and reviewed subject | Date treatment |
|---|---|---|
| Yellowstone | https://www.nps.gov/yell/planyourvisit/permitsandreservations.htm — general-entry reservation statement and separate overnight/activity requirements | The general-entry statement does not specify an effective period. Keep dates null. |
| Zion | https://www.nps.gov/zion/planyourvisit/permitsandreservations.htm — general entry and shuttle statement, separately described activity permits | Do not translate general-entry guidance into permission to drive a restricted road or undertake a permitted activity. Dates stay null. |
| Grand Canyon | https://www.nps.gov/grca/planyourvisit/grand-canyon-national-park-public-health-update.htm — Entrance Fees and Passes section | Other sections contain dated operating information; those dates do not date the general-entry statement. Dates stay null. |

Each stored observation includes the exact supporting excerpt, its SHA-256, the actual review time, a limited government-authored-text rights basis, and an original scope warning. The hash covers only the retained excerpt, not an entire source page. General page-footer revisions are not used as field-level source updates. Photographs, marks, maps and third-party media are excluded.

The existing three Yosemite/Rocky Mountain 2026 rules are unchanged. `evaluateEntry` does not consume undated notes: a note cannot grant an exemption for 2026, 2027 or any selected travel date. The visitor sees the source observation and must confirm date-specific applicability with NPS. Rules and notes have separate types and validation. Coverage counts distinguish stored sources, dated rules, review freshness and successfully checked alert feeds.

`src/lib/data.ts` calls `validateEntryNotes` at the server/build boundary before using notes, so the Astro build rejects tampered or invalid evidence. The site snapshot hash includes those notes. The browser receives only minimal public metadata for directory age calculations, not the Node validation module.

Automatic source-change detection, raw response retention, operational-condition normalization and comprehensive permit/fee coverage remain unfinished. These notes do not close those release gates.
