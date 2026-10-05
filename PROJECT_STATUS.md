# Project status and handoff

Updated: **October 4, 2026 (Toronto time), after implementing the pure named-location NWS forecast foundation; the verified live release remains Deployment #8 below**.

## Current development handoff

The [named-location weather foundation](docs/WEATHER_FOUNDATION.md) is implemented
as a separate pure Python adapter with injected requests. It validates location
provenance containers, rounded point/grid identity, forecast geometry, original
generation/update/check/period clocks, nullable units and canonical hashes.
Mapping checks have a 168-hour cache; forecasts have a six-hour source-aware age
policy plus distinct expired/uncovered states. Failed responses retain the
last-good forecast's own mapping and successful clock, including after a newly
discovered grid. Older same-grid source clocks cannot replace newer evidence.

Data/source work is synthetic only: **33 new weather tests**, with **833 tests
passing in the complete local Python suite**. The frozen Node baseline passes
404 tests. Astro checks 41 files with zero errors, warnings or hints; both local
builds contain 14 pages and pass 34 generated-site tests each. Independent
whole-branch review found one envelope-size issue; three regression tests
reproduced it, and the consolidated fix passes all 33 weather tests and the
complete Python suite. Bounded records now reserve room for later failure
metadata, and complete candidates are validated before replacing evidence.
[PR #28](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/28)
records final integration and required CI evidence. Official NWS API
documentation and its OpenAPI schema were consulted;
no real location inventory, park forecast, NWS transport, private checkpoint,
public weather data, weather UI or schedule is introduced. Existing public data,
rights manifests, original clocks and visitor snapshot remain unchanged. Full
required integration checks include both supported CI browser suites; local
Playwright installation has the previously recorded Ubuntu 26.04 limitation.

Next: verify named forecast locations using authoritative NPS geographic
evidence, then implement the separate bounded private NWS transport and immutable
checkpoint/recovery lifecycle. Reviewed public weather export and rendering
follow those prerequisites; NWS alerts remain separate. Ordinary technical
decisions use the owner's engineering delegation, with a documented design,
inline implementation and independent whole-branch review. Native Windows Git
and WSL tests preserve the established managed-worktree operating boundary.

[ParkReadiness](https://vasuki8.github.io/us-national-park-trip-readiness-tracker/)
is live at exact **`b9fa7354d11833208c495d2419b3e505bd0baba8`** /
**`pilot-6658c7c2668e`**, including Overview, When to Visit, Things to Do and the
fresh five-park conditions check. [PR #26](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/26)
is merged. The reviewed head, PR CI checkout and actual merge have the same tree;
independent immutable review found no issues. The owner's standing merge, pull,
push and verified-publication authorization remains recorded in `AGENTS.md` and
the permanent policy; do not ask again for routine actions within that scope.

Data/source work: the successful private NPS collection clock is
**`2026-10-05T00:09:01.984222Z`** (October 4 in Toronto), with **16 notices**
(Yosemite 1, Rocky Mountain 0, Yellowstone 5, Zion 6, Grand Canyon 4). Every full
notice record and original record clock is identical to the approved previous
release. Only snapshot check/success clocks advance, with one successful
sequence-4 zero-change observation per park. All earlier observations and Zion's
two previous changes remain exact. A zero-change comparison does not establish
unchanged conditions; an empty or missing notice is not an all-clear or reopening.
The separate earlier Zion count-seven preflight never entered archive history.

The new committed alert archive has a verified private backup, fresh direct
GitHub recovery and complete five-park chain/byte replay. Exact archive-backed
promotion checks bound the frozen candidate, all six public base files and patch
bytes immediately before native Git application; committed LF targets match.
Prior exact-content approval and current standing publication authorization are
reused within this unchanged text/rights scope; no new human patch or rights
review is claimed. [The promotion contract](docs/ALERT_DATA_PROMOTION.md) now
explains that distinction. Six guidance records, five profiles, 129 published
activity views, rights manifests and their original clocks are unchanged.
Detailed real approvals, checkpoint identities and recovery receipts stay private.

Successful [Verify pilot #254](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37247946974)
(PR) and exact push/main [Verify pilot #255](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37248340998)
each passed **1,406 tests**: 404 Node, 800 Python, 34 per generated-site build,
117 root-browser and 17 project-browser. Astro checks 41 files with zero errors,
warnings or hints; both builds contain 14 pages and retain all three accessibility
screenshots. Local non-browser checks passed 1,272 tests. Local browser launch
was unavailable because pinned Playwright's missing Chromium cannot be installed
on this WSL Ubuntu 26.04 system; both required suites passed on the unchanged
supported Ubuntu 24.04 CI runner. No local automated browser pass is claimed.

[Deployment #8](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37248918183),
job **111572328349**, published the exact Verify #255 artifact **11319838432**:
`sha256:8ea08b6a351dbcf66b53a18df6d24b472c58f4a103820044b86e28fee17f9759`,
expiring **`2026-10-12T00:44:07Z`**. Its digest, 57 regular entries, both manifests,
all 28 noindex pages, exact retained verifier/lockfile and three PNG screenshots
passed independent audit. The manual workflow downloaded the retained build and
did not rebuild, collect or retimestamp sources. A final read-only provider
preflight around 00:47 UTC passed all five parks with counts 1/0/5/6/4; it did not
renew the archived clock.

The workflow report at **`2026-10-05T00:48:29.480Z`** and independent read-only
recheck at **`2026-10-05T00:49:41.888Z`** each matched **24 public files and 14
pages in one attempt**, binding the exact commit, snapshot, URL and project base.
Report artifact **11320226002** has digest
`sha256:b2f679ee65971fd3e127f669ee7b75e2c4af087d2805db304f52a6b3ad9d27f4`,
expires **`2026-10-12T00:48:30Z`**, and passed downloaded digest, safe one-file
layout and exact report checks. All four observed security/robots headers remain
null. Every page retains meta `noindex, nofollow`; indexing, ads, tracking and
recurring operations remain disabled.

Actual live-browser checks confirm all five park pages show the new clock,
exact snapshot, 1/0/5/6/4 retained notices and four-check histories with recent-
feed/limited-coverage labels. Rocky Mountain preserves explicit empty-feed
uncertainty. Zion's earlier before/after evidence and native retained-notice focus
pass. An already-open page initially kept its older document during a fragment
navigation; a full navigation loaded and verified the new release. These checks
do not establish every browser's restoration/print behavior or screen-reader
announcements. Freshness still expires four hours after the actual source check;
manual publication does not provide ongoing live conditions.

The current rollback target is previous production **`2434546` /
`pilot-b45391284d2e`**, Verify #248 artifact **11308073698**, expiring
**`2026-10-11T16:31:53Z`**. Its eligibility, digest, extracted bytes and manifests
were rechecked; the retained verifier matched its 24 hosted files/14 pages before
publication. No new rollback drill was performed. The unchanged readiness CLI
still reports three required pass, zero blocked and two not checked, with
`release_ready: false`, because provider/hosting receipts are reviewed separately.
The current handoff and detailed private operator handoff record the distinction.

Next weather work is the verified geographic evidence and private collection
layer described above. Add NWS alerts separately in the owner's phase order.
Recurring collection, photo rights, indexing and ads retain their deliberate
decisions; current manual freshness and screen-reader review limits remain visible.

## Conditions release preparation — PR #24 (historical)

The following records preparation before publication; the current live results
above take precedence.

[PR #23](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/23)
is merged at **`2434546303d62a5fcacd4fa5542e37d734a89774`**. Independent review
found no issues. The reviewed head, PR CI checkout and actual merge have the
same tree. [Verify pilot #247](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37216326613)
and the exact default-branch push
[Verify pilot #248](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37216789036)
each passed **1,406 tests**: 404 Node, 800 Python, 34 for each generated hosting
build, 117 root-browser and 17 project-browser tests. Astro has zero diagnostics;
both 14-page builds and retention of three accessibility screenshots pass.

Data/source work: the approved five-park alert/history pair contains **16 notices**
(Yosemite 1, Rocky Mountain 0, Yellowstone 5, Zion 6 and Grand Canyon 4), with
the original **`2026-10-04T14:56:52.574947Z`** collection clock. Only Zion changed:
the highway wording identifies the closure from Canyon Junction to the East
Entrance, and the fire notice is absent from the checked feed with its prior
evidence retained. No reopening or ended-restriction conclusion follows. All
15 unchanged records and original clocks remain exact. Guidance, profiles,
activities and rights pairs are unchanged; unknown source/effective/publication
times remain unknown. Private checkpoint upload, fresh recovery, complete
archive replay and exact candidate/application checks are verified and retained
outside the checkout.

Release preparation: artifact **11308073698** from Verify #248 is downloaded and
independently audited. Its ZIP digest is
`19b5175eb38e0d491bacfba7646023611697b34fe4b9da3eb1ede7b99154b705`, and it expires
**`2026-10-11T16:31:53Z`**. Both manifests bind the exact target above and
**`pilot-b45391284d2e`**. Safe layout, all 28 noindex pages, paired source/history
content, all 129 published activity views, three valid screenshots and the exact
retained verifier/lockfile pass. Each output contains 25 files including
`_headers`; hosted verification should check **24 public files and 14 pages**.
Native inspection of the exact project artifact on localhost confirms Zion's
current wording, both comparison disclosures, retained-notice focus and the
19/20/1 Things to Do disclosure. This is local artifact verification.

The current PR #7 release remains the rollback target: **`2fa4d4a` /
`pilot-0609c66f7954`**, Verify #202 artifact **11257849120**. Fresh eligibility,
downloaded digest, safe layout, manifests, screenshots and retained verifier
were independently rechecked; its artifact expires **`2026-10-09T23:58:37Z`**.
A read-only live recheck at **`2026-10-04T16:30:07.464Z`** matched all **22 public
files and 14 pages in one attempt**. All four observed security/robots headers
remain null. No new deployment, rollback drill or live-browser verification of
the proposed build was performed.

Integrated readiness reports **three required pass, zero blocked and two not
checked; `release_ready: false`**. Review, backup and rights pass. Separate
read-only NPS compatibility preflight at 16:32 UTC passed all five parks with
matching counts; the 16:36 UTC injected-clock audit found alerts, guidance,
profiles and activities fresh. The CLI does not ingest these external
freshness/provider and hosting/rollback assessments. Do not invent a CLI pass.
Noindex, ads-disabled and manual-operation safeguards remain intact.

Next: obtain the separate deployment decision for **exact build `2434546` from
Verify #248**, recheck identity and freshness, dispatch the existing verified
artifact, then verify hosted bytes and actual browser behavior. This handoff is
a documentation receipt; it does not change that selected release target.
Alert freshness expires beyond **`2026-10-04T18:56:52.574947Z`** (14:56 Toronto).
Review, backup, CI and preflight do not renew the source clock. Detailed current
approval, recovery, artifact and preparation receipts remain in the private
operator handoff. Publication remains pending.

## Conditions promotion implementation — PR #23

The following records the applied change before its final integration and
release preparation; the current verified results above take precedence.

Things to Do is integrated through [PR #22](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/22)
at `f8222cf`. The reviewed head, PR CI checkout and actual merge share the
verified tree. Verify pilot #245 passed **1,406 tests**, both browser suites,
zero Astro diagnostics and retention of all three accessibility screenshots.
The subsequent default-branch push [Verify pilot #246](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37202077785)
succeeded for exact main `f8222cf`. Those checks describe the preceding build;
this conditions increment needs its own successful default-branch artifact.

Data/source work: the existing private five-park alert collector completed a
successful new observation for every park at **`2026-10-04T14:56:52.574947Z`**,
after a successful keyed read-only preflight. The frozen candidate contains
**16 notices**: Yosemite 1, Rocky Mountain 0, Yellowstone 5, Zion 6 and Grand
Canyon 4. Only Zion changed: one notice was edited and one was no longer present
in the checked feed. Removal does not establish reopening or ended restrictions.
All 15 unchanged notices retain their complete records and original observation
clocks. Source-update, publication and effective-date fields remain unknown.
No guidance, profile or activity source was requested or re-reviewed.

The complete committed alert chains were replayed, selected into a new private
checkpoint, uploaded under standing launch-backup approval, freshly downloaded
directly from the selected private GitHub repository and replayed again. Exact
working/copy/download bytes and all five heads/counts agree; independent
candidate and recovery audits pass. Detailed identities, paths, source context,
patch and receipts remain in the private operator handoff outside the checkout.

The existing offline tools built an isolated candidate preview and prepared a
six-file alert/history patch. After reviewing the concrete promotion scope,
the owner instructed continuation. The private authorization binds that exact
candidate and source-text scope. Its immediate read-only recheck confirmed the
original candidate identity, exact patch bytes, all six public bases and complete archive
continuity for all five parks. Native preview inspection verifies the new Zion
wording, retained before/after evidence, removal warning and limited successful
empty-feed state. The served bytes match the exact private preview on both WSL
and Windows loopback. Native Git applied the checked patch without a bypass;
all six outputs match its exact targets under the existing working-copy line
ending policy. Guidance, profile, activity and rights files are unchanged.

Verification: **404 Node tests, 800 Python tests and 34 tests for each generated
hosting build pass locally**. Astro reports zero errors, warnings or hints across
41 files; both builds emit 14 pages. The initial Node launch lacked the frozen
Python executable; its rerun under `uv run --frozen` passed after Python finished.
No application fix was needed. The supported Ubuntu 24.04 CI runner must verify
both browser suites and retain all three accessibility screenshots before merge;
no local automated browser success is claimed. The earlier 61 focused synthetic
tests also passed. Independent review checks the exact public diff and rendered
Zion evidence, including the absence of any reopening conclusion.

Read-only readiness with the current ledger and exact reviewed profile/activity
bundles, matched against today's fresh downloaded copies, reports **three
required gates passed, zero blocked and two not checked; `release_ready: false`**.
Current public alert freshness/provider evidence and hosting/rollback remain
separate operator assessments. This report predates application; rerun it from
the integrated checkout before proposing release. The separate exact source-use
approval does not turn the conservative report into release readiness.

The public alert pair now contains the approved 16 notices and original October 4
collection clock. The removed Zion fire notice remains in history, and the
highway notice says it is currently closed from Canyon Junction to the East
Entrance. This source-use/public-data action follows
[ALERT_DATA_PROMOTION.md](docs/ALERT_DATA_PROMOTION.md), separately from deployment.
Last verified production remains **`2fa4d4a` /
`pilot-0609c66f7954`**; indexing, ads and schedules remain disabled.

Integration follows the owner's standing merge authorization after required
checks and review. Next: prepare complete release and rollback evidence against
this increment's successful verified-main artifact, then present the separate
deployment decision. Alert freshness expires beyond **`2026-10-04T18:56:52.574947Z`**;
review, backup, CI and provider preflight do not renew the source clock. Retain
honest stale labels if that boundary passes.

## Preceding Things to Do implementation — PR #22

Park pages now expose **Things to Do** after Overview and When to Visit, with a
native section-navigation target and initially collapsed activity inventory.
Exact NPS titles, official listing links and categories are escaped normally.
Published, source and withheld counts stay separate: Yosemite 13/13/0, Rocky
Mountain 11/12/1, Yellowstone 84/88/4, Zion 19/20/1 and Grand Canyon 2/3/1.
Availability remains unverified, physical park relationship unconfirmed, and
agency, difficulty and permit requirements unknown. Missing catalogs, confirmed
empty sources, wholly withheld inventories and category unavailable/empty/
withheld states remain distinct. Withholding never establishes source removal.

The build-only loader validates both optional files before exposing version 2.
Absent pairs and validated version 1 pairs expose no catalog and retain the old
snapshot preimage; partial, malformed or mismatched pairs fail. Complete
canonical catalog and rights digests now bind the build snapshot, including
withheld summaries, clocks and rights review. Original prose, credit, media,
withheld identities/reasons and rights metadata never enter the visitor markup.

Activity freshness uses the original microsecond clock with an inclusive
seven-day expiry. Failed/quarantined attempts retain their last successful
evidence. The browser receives only collection status and original attempt/
success times, recalculating on load, minute, page return, visible-tab return
and before print. Unchanged labels are not rewritten. Native browsing works
without JavaScript; print preserves inventory disclosure state, and expanded
listings print with wrapped official destinations. No provider requests, storage
or trip-control changes are added by the activity interface.

Data/source work: the approved 136-source / 129-view / seven-withheld public pair
is byte-for-byte unchanged. Its source attempt/success clock remains
`2026-10-04T05:49:46.709637Z`; no collection, renewed review, private backup
transfer or source-age renewal was performed. PR #21 integrated the reviewed
pair at `ed2263d`, after Verify pilot #242 passed 1,360 tests, both browser
suites and retained accessibility screenshots. Its remote recovery and approval
receipts remain in the private operator handoff.

Local verification passes **404 Node + 800 Python + 68 generated-site tests =
1,272 tests**, zero Astro diagnostics across 41 files, and both 14-page builds
with snapshot **`pilot-7bb1d6f859a6`**. The static integration regression first
failed on the old build's absent activity section. Focused loader tests pass
15/15 and clock/rendering tests pass 21/21 after their recorded red stages.
Browser discovery registers 117 root and 17 project tests; discovery is not
execution. Independent data/UI and whole-branch static reviews pass. Native
visual verification confirms all 84 Yellowstone titles, links and categories,
initially closed disclosure, keyboard toggles and 320/360px wrapping without
overflow. It does not establish automated print, no-JavaScript or 200% text checks.
The first PR CI run (#244) passed 116 root browser tests but exposed one new
test selector that required an exact Arrival time label while the real label
includes "(optional)"; project tests and screenshot retention were skipped.
The test correction follows the existing form's accessible label contract.
Required CI must pass both browser suites and retain all three accessibility
screenshots before standing-authorized merge;
record exact CI and integration results in [PR #22](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/22) and private
operator handoff. Verify pilot is pinned to Ubuntu 24.04 for its frozen
Playwright installer. Local Chromium remains unavailable on WSL Ubuntu 26.04.

The frozen dependency audit reports one existing high-severity
`http-cache-semantics` advisory with no listed patched version. Installed usage
is Astro's build-time remote-image cache; this static pilot has no remote image
imports or shared authenticated cache. See the scoped evidence and follow-up in
[DEVELOPMENT.md](docs/DEVELOPMENT.md); no dependency fix or exhaustive security
audit is claimed.

Deployment/live verification: no deployment or live probe was performed. Last
verified production remains **`2fa4d4a` / `pilot-0609c66f7954`**.
The last private-evidence release assessment passed review, backup and rights
but left conditions/provider freshness and hosting/rollback not checked.
Indexing and advertising remain disabled.

Next: after required CI and reviewed PR integration, refresh the 17 retained
condition notices and assemble complete release evidence against reviewed main
before requesting any new applicable deployment decision.

## Preceding approved activity promotion — PR #21

The owner explicitly approved the previously presented **129 exact NPS activity
titles, official listing links and source categories**, including public-repository
promotion. The immutable version 2 approval bundle was recorded and verified.
Under standing launch-backup authorization, only that verified bundle was uploaded
to the selected private repository, freshly downloaded directly from GitHub at
the recorded commit and restored into a new private destination. All four copies
have identical canonical bytes and bundle identity. Repository identity, privacy,
write access, disabled Actions and absent Pages were checked before both operations.
Independent read-only recovery and public-pair audits found no discrepancies.

The paired public files now contain **136 source summaries, 129 selected views
and seven withheld listings**. Published counts are Yosemite 13, Rocky Mountain
11, Yellowstone 84, Zion 19 and Grand Canyon 2. Exact titles, safe official links
and complete source categories match the approved bundle; descriptions, credits,
quotations, embedded link metadata, media and marks remain excluded. Withholding
does not mean source removal. Availability remains `not_verified`, geography
`unconfirmed` and unsupported planning fields null. All source hashes and
observations are preserved, with the original attempt/success clock
**`2026-10-04T05:49:46.709637Z`**. Review, backup and promotion renewed no source age.

Promotion used the existing paired patch preparer, exact candidate/base/patch
recheck and native Git applicability check. Both public files retain `-text`.
Two synthetic readiness fixtures now explicitly exclude the real activity pair,
preserving their separate guidance/profile test scope. The Node catalog fixture
also removes the copied pair before testing absent and synthetic inputs. Visitor rendering and
build snapshot inputs are unchanged; Things to Do is not yet implemented.

Read-only readiness with the current replayed ledger, matching downloaded ledger
backup and exact profile/activity review and recovery bundles passes durable
source review, storage backup and source rights: **three required gates pass,
two remain not checked, `release_ready: false`**. Activity evidence confirms
136 source / 129 published / seven withheld, 129 rights-covered views and exact
review/backup matches. Alert freshness/provider compatibility and hosting/rollback
still need release-time evidence. Repository-only readiness cannot infer the
private evidence and remains one pass, one blocked and three not checked for
the pilot target. Disabled indexing and advertising retain their later gates.

Local verification passed **368 Node + 800 Python + 66 generated-site tests =
1,234 tests**, zero Astro diagnostics across 36 files and both 14-page builds.
Both builds retain **`pilot-a2056877d1e7`** because the activity consumer and its
snapshot inputs are subsequent work. The readiness fixture first reproduced
eight failures across 46 tests, then passed all 46 after isolation. The catalog
fixture first reproduced one failure across 44 focused tests, then passed all 44.
Independent exact public-pair and whole-diff reviews found no remaining findings;
all six documents are valid UTF-8, all 40 local links resolve and diff checks pass.

Local Chromium verification could not complete: the pinned browser is absent and
its installer rejects this WSL Ubuntu 26.04 host. No local browser pass or
screenshot-retention result is claimed. Required CI must verify both browser
suites and all three accessibility screenshots before integration. Record exact
CI and merge receipts in the associated PR and private operator handoff.

No new NPS collection, deployment, live probe, schedule, indexing or advertising
was performed. The last verified production build remains **`2fa4d4a` /
`pilot-0609c66f7954`**; its 17 notices require refreshing before a future release.
Private source evidence, approvals, recovery paths and transport receipts remain
outside the public checkout and CI artifacts.

Next: build Things to Do after required CI and reviewed PR integration,
from the validated version 2 catalog with official links, distinct withholding,
unknown planning fields and original-clock freshness. A live release still needs
refreshed conditions, complete release checks and applicable deployment approval.

## Preceding exact activity catalog review — PR #20

All **136 retained activity listings** have now received technical model review
of their complete contexts, with independent park assignments. The coordinating
operator inspected every proposed title, official listing link and category,
and adjudicated the seven retained warning contexts. The private version 2
candidate selects **129 listings**: Yosemite 13, Rocky Mountain 11,
Yellowstone 84, Zion 19 and Grand Canyon 2. Seven are explicitly withheld for
a historically dated closure framed as current, three washout/access conflicts,
an NPS seasonal recommendation against hiking, a rockfall closure and an ended
program. Withholding does not claim source removal, a new closure or reopening.

The exact dispositions, draft narrowed rights manifest, regenerated projection
and passive private HTML packet passed canonical/schema/hash checks and an
independent read-only audit. All source headers, original normalized hashes and
observation clocks match the unchanged checkpoint. The source attempt/success
clock remains **`2026-10-04T05:49:46.709637Z`**. Every selected category list is
an exact source copy; no descriptions, quotations, credits, tracking-bearing
links, embedded HTML, images or protected graphics are proposed for publication.
API provenance and empty credits were not treated as ownership evidence.

The current NPS API guide, disclaimer, DOI copyright notice and NPS marks policy
were checked against the narrower title/link/category scope. This is technical
review, not authenticated human approval or a licence grant. Automatic approval
review rejected recording the real catalog approval because it treats the new
rights/publication scope as an owner legal-risk decision and does not accept
"continue" as explicit authorization. The owner has been asked to approve the
concrete 129-listing scope and public promotion after verified private recovery
and required PR checks. Existing launch-backup authorization remains recorded.

No approved activity bundle, reviewed-bundle backup transfer, public activity
pair or deployment was created. The selected private backup destination's
authenticated identity, privacy, write access, disabled Actions and absent Pages
were rechecked; this proves configuration only. The passive preview delivers
its exact verified bytes, serves unrelated paths as 404 and has no active source
links, scripts, media or external assets. Native disclosure works at the checked
desktop viewport. No new provider requests were made.

Read-only consumer assessment confirms that Things to Do can reuse the current
Astro/profile patterns without dependencies. Load and validate the optional pair
in `src/lib/data.ts`, render version 2 only in a native collapsible inventory,
add `#things-to-do` navigation, and bind catalog plus rights digests into the
build snapshot while preserving the absent-pair hash. Show feed-only coverage,
separate withholding, unknown planning fields and original source clocks.
Follow the existing microsecond-precise seven-day freshness helper and lifecycle
updater; exercise absent/v1, empty/wholly withheld, category null/empty/withheld,
degraded/stale, 84-listing, no-JavaScript and project-base-path cases with synthetic
fixtures. This assessment is a design recommendation, not an implemented renderer.

Documentation-only verification checks all four changed documents as nonempty
UTF-8, resolves all 29 local Markdown links, excludes private source identities,
paths and backup destination metadata, and passes `git diff --check`. The isolated
worktree's unchanged public-data baseline also passes `npm run validate:data`.
No unrelated local application test run is claimed for this documentation change.

Next: obtain the pending explicit source-use/public-promotion decision, record
the reviewed bundle, verify a fresh authenticated remote download and restore,
then prepare and recheck the paired public patch. Things to Do rendering remains
the next implementation step; refreshed conditions and complete release checks
are still required before any separately authorized deployment.

## Preceding minimal activity catalog engineering — PR #18

The separately versioned minimal activity contract is implemented. Version 2
publishes only selected exact titles, safe NPS listing links and optional source
categories. Private dispositions explicitly select or withhold every original
listing; public source summaries retain all original hashes and observations.
Selected views have a narrower hash, and rights bind each view plus the complete
projection. Descriptions, credits, embedded HTML and link metadata remain private.
Geography stays unconfirmed, availability not verified and unsupported fields null.

Private approval additionally binds dispositions and regenerates the complete
catalog from the unchanged checkpoint. Disposition review precedes rights review,
which precedes approval. The optional CLI input is strictly validated; a supplied
JSON null file cannot silently fall back to version 1. Immutable verify/restore,
all input/output/lock overlap guards, byte limits and paired CAS checks remain.
Version 1 approvals retain their complete-text meaning and recovery compatibility.

Promotion compares original source evidence independently of editorial selection
when either side is version 2. Same-clock editorial review renews no source age;
degraded retention, first/changed observations and the source half-drop guard
apply to all source summaries. Readiness separates source, published and withheld
counts, with rights coverage for selected listings only. Existing gates only
become stricter; checkpoint-only recovery cannot cover a reviewed catalog bundle.

Final local verification passed **368 Node + 800 Python + 66 generated-site =
1,234 tests**, strict standalone TypeScript, zero Astro diagnostics across 36
files and both 14-page builds. The builds retain snapshot
**`pilot-a2056877d1e7`**. New synthetic tests cover omission of private markers,
rehash tampering, source/view/rights binding, Unicode and microsecond parity,
version transitions, wholly withheld sources, private recovery, real paired Git
patch application in disposable fixtures and exact readiness evidence.

Independent Python/catalog/lifecycle, TypeScript/documentation and whole-branch
reviews passed with no actionable findings. All 43 local Markdown links resolve
and diff checks pass. Repository-only readiness remains **1 pass, 3 blocked,
3 not checked** overall; required pilot gates are **1 pass, 1 blocked,
3 not checked**, with **`release_ready: false`** and no supplied private evidence.

[PR #18](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/18)
merged reviewed head **`08549288d080be4952224e471bcb00d9db959046`** as
**`aa15df03cec5f18723ae6ffafa9473c5d76423d0`** under standing merge authorization.
Fresh checks and unchanged-main verification passed immediately before merge.
Native Windows Git confirms the actual merge, reviewed head and standard CI
merge share tree **`a2379be8ee0547a911f8d7bb030af810bd19f88e`**; clean primary
`main` was fast-forwarded to the actual merge. This documentation receipt changes
the handoff and plan completion record only, preserving checked application files.

[Verify pilot #236](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37185194589),
job **111385556884**, passed **368 Node + 800 Python + 66 generated-site +
126 Chromium = 1,360 tests**, zero Astro diagnostics across 36 files and both
14-page builds. All **111 root + 15 project-path browser cases** passed and all
three accessibility screenshots survived. CI checked standard PR merge
**`4a0d1fd8fe4908c0c3356cc5343aefcf15dff8d9`**, combining reviewed head with
unchanged main **`af5d99cc9d7619c1480f7bf93a86639350efc174`**. Complete job logs,
checkout parents/tree, required checks, annotations and artifact metadata were
inspected. Artifact **11296128758** uploaded successfully (4,661,210 bytes);
it was not downloaded or deployed. PR verification is not a live release artifact.
The existing high-severity npm advisory, Action Node-runtime and Ubuntu-runner
migration notices remain; dependencies and workflows are unchanged.

No real source collection, rights decision, activity approval, remote backup
transfer, public-data application, visitor activity renderer or deployment
occurred in this engineering increment. The first real private checkpoint still
contains 136 listings at its original October 4 source clock. Public profiles,
guidance and 17 notices are unchanged; alerts remain stale by their four-hour
policy. Indexing and advertising remain disabled, with no new schedule or service.
The last verified live build is still **`2fa4d4a` / `pilot-0609c66f7954`**;
local builds establish no new live result.

Next: inspect the retained real checkpoint under the version 2 catalog contract,
record explicit selected/withheld decisions, withhold unresolved availability
conflicts and establish exact published text-use decisions. Verify approved-bundle
remote recovery before paired public promotion, then build Things to Do with
official links, original freshness and honest uncertainty. Refresh conditions
and complete release checks before any separately authorized live deployment.
See [ACTIVITY_PROMOTION.md](docs/ACTIVITY_PROMOTION.md) and the checked
[design](docs/superpowers/specs/2026-10-04-reviewed-activity-catalog-design.md).

## Preceding first real activity checkpoint and review — PR #16

The existing tools collected the first real private NPS activity checkpoint for
all five pilot parks. All collections succeeded, retaining **136 listings**:
Yosemite 13, Rocky Mountain 12, Yellowstone 88, Zion 20 and Grand Canyon 3.
Coverage is **`checked_activity_feed_only`**, with original attempt/success clock
**`2026-10-04T05:49:46.709637Z`**. The immutable checkpoint and complete unapproved
review export passed offline verification. A receipt-write size argument was
corrected offline after collection; source requests were not repeated.

The selected checkpoint was copied byte for byte to the owner-selected private
GitHub backup. Authenticated identity, expected-owner write access, visibility,
disabled Actions and unconfigured Pages were checked before upload and recovery;
access was unchanged. Exact staging preserved earlier evidence and excluded
credentials, review packets and operator receipts. A **fresh authenticated clone
directly from GitHub** at the recorded remote commit, offline verification and
restore into a **new owner-only WSL destination** passed. All three canonical
copies and identities match (**480,419 bytes**); original working evidence and
source clocks are unchanged. Detailed identities, private paths and receipts
remain outside this public checkout. This is recovery of an **unapproved
checkpoint**, not a reviewed approval bundle or release-readiness proof.

Programmatic inspection covered **5,124 string values**, with selected flagged
context review and no exhaustive human-reading claim. All 136 credits are empty;
287 fields contain HTML. The private report flags **11 records** for attention,
including attributed third-party quotations/production context, partner and
concessioner references, wrapped links carrying contact/tracking metadata,
a closure and a program whose end date preceded collection. Blank credits,
API provenance and a successful recent request do not establish text-use rights
or availability. See [ACTIVITY_SOURCE_REVIEW.md](docs/ACTIVITY_SOURCE_REVIEW.md).

A complete private review packet contains **136 records / 5,032 field values**,
round-trip checked against the retained candidate. All source markup and URLs
remain escaped literal text; no active source media or external links are
present. Loopback delivery, fixed-route refusal, response safeguards, desktop
and mobile width, record expansion and keyboard collapse are verified. The
packet, reports, server and receipts stay on private WSL storage, outside the
checkout, website outputs, backup inventory and public CI artifacts. The private
operator handoff records the exact recovery and review locations.

This increment changes operator documentation and handoff only. No rights
manifest, activity approval bundle, public pair or visitor activity consumer was
created. No dependency/workflow change, public-data application, deployment,
schedule, indexing or ads occurred. Current public profiles, guidance, alerts and
source clocks remain unchanged. Last verified live remains **`2fa4d4a`** /
**`pilot-0609c66f7954`**, with stale alerts and noindex/ad-free safeguards; no new
live-site check occurred. Repository-only readiness is still **1 pass, 3 blocked,
3 not checked**, with **1 pass, 1 blocked, 3 not checked** required and
**`release_ready: false`**. Private checkpoint recovery clears no activity rights
or reviewed-bundle requirement.

Independent read-only re-verification confirms all three checkpoint files and
14 recovery-receipt agreements, with no discrepancies. This independently proves
file integrity and receipt agreement; the operator's authenticated checks and
fresh-clone execution establish remote provenance. Documentation review found
one stale synthetic-only opening, now corrected; no other actionable findings.
All 34 local Markdown links resolve and diff checks pass.

[PR #16](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/16)
merged checked head **`8663d06673c555db3c6d5baa740ad41f60331318`** as
**`242c579452019dad3458b07e4dd40719b06a8c89`** under the owner's standing merge
authorization. Fresh checks and unchanged-main verification passed immediately
before merge. Native Windows Git confirms the actual merge, checked head and
standard CI merge share tree **`5e2426dbd670c301b8cddec50f5b997b7639beb9`**;
local `main` was fast-forwarded to that merge.

[Verify pilot #232](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37182497872),
job **111377715907**, passed **350 Node + 759 Python + 66 generated-site +
126 Chromium = 1,301 tests**, zero Astro diagnostics across 36 files and both
14-page builds. All **111 root + 15 project-path browser cases** passed and all
three accessibility screenshots survived. CI checked standard PR merge
**`442abf2ade8bde12920d58475b9063f923ddec9b`**, combining the reviewed head with
unchanged main **`2accf21f3c96873e26de06bb3a076683471df03d`**. Complete job-log,
checkout-parent/tree, fresh-check and artifact metadata inspection passed.
Artifact **11295502914** uploaded successfully (4,660,941 bytes); it was not
downloaded or deployed. PR-only verification is not a live release artifact.
CI installation reports one high-severity npm advisory with unchanged
dependencies; existing Action Node-runtime and Ubuntu-runner notices remain.

Current branch: **`main`**, after checked PR #16 integration. This documentation-only
receipt records integration without changing the checked application files.
No unrelated local application test run was needed for these documentation
changes; the complete required PR suite passed as recorded above.

Next: implement a separately versioned minimal public activity catalog with
reviewed titles, safe NPS listing URLs and selected category metadata. Bind an
explicit selected/withheld disposition for every retained listing to the exact
public view and its rights/approval; preserve private source records/hashes and
original clocks. Distinguish editorial withholding from source removal and
source null/empty fields; retain v1 verification/recovery compatibility. Withhold
unresolved availability conflicts initially and describe published activity
availability as unverified. The existing complete projection has no omission
mode. Exact rights decisions, activity approval, reviewed-bundle
remote recovery and public-pair preparation must precede Things to Do rendering.
A live release still needs deliberate alert refresh, complete release checks and
applicable deployment authorization.

## Preceding reviewed activity promotion integration — PR #15

The separate activity public contract, exact per-record text-rights manifest,
immutable private approval/recovery and paired public-file patch preparation/
recheck are integrated in **`main`** through PR #15. Build validation and release
readiness accept the optional complete pair and refuse incomplete/invalid pairs;
readiness extends existing review, rights and backup gates only downward. See
[ACTIVITY_PROMOTION.md](docs/ACTIVITY_PROMOTION.md).

Projection preserves every normalized field and original source clock in all
five inventories, including confirmed empty and retained degraded inventories.
Each requires a successful baseline. Rights bind every retained record's park,
ID, fixed API source and content hash; the exact review covers all projected
strings, including long description text and credit. API metadata does not
establish rights. Private approval binds checkpoint, full projection and rights;
fresh restore preserves identity. Explicit limits support large five-park batches
without widening legacy defaults or trimming evidence. Paired promotion checks
exact current base bytes, observation continuity and the severe-drop guard.

Complete local verification passes **759 Python + 350 Node +
66 generated-site = 1,175 tests**, zero Astro diagnostics across 36 files and
both 14-page builds. Final affected Node/build/site runs include the reviewed
TypeScript fixes; strict standalone TypeScript also passes. Both hosting bases
retain **`pilot-a2056877d1e7`**. Independent Python/documentation reviews have no
actionable findings; 44 internal links and diff checks pass. TypeScript review
reproduced Unicode credential-pattern, neutral Unicode-fragment and ancestor-
symlink parity gaps. Four failing regressions established the defects before
fixes; all 55 focused activity/profile/build-gate cases now pass. Independent
TypeScript re-review confirms 14 URL and nine ancestry cases with no remaining
findings. Local Chromium remains unavailable; supported CI completed both browser
suites before integration.

[PR #15](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/15)
merged checked head **`b10daa1d42fff90a25e1ce906a8a4fbc085c536a`** as
**`66d1b65583239d54a1ae56f334d23f0bbdf7693a`** under the owner's standing
merge authorization. Native Windows Git confirms the actual merge, checked head
and CI checkout share tree **`7e5079877cc3b7c62144b48f8c941038070e4282`**;
local `main` was fast-forwarded to that merge.

[Verify pilot #229](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37180240009),
job **111371173112**, passed **350 Node + 759 Python + 66 generated-site +
126 Chromium = 1,301 tests**, zero Astro diagnostics across 36 files and both
14-page builds. All **111 root + 15 project-path browser cases** passed, and all
three accessibility screenshots survived. CI checked standard PR merge
**`ce64ac0595c471a9cf84591c1295c3c440f0606b`**, combining the reviewed head with
unchanged main **`e4659506847494d2b8c1d482a96a5f87eb92d34a`**. Fresh checks,
complete job-log, checkout-parent/tree and artifact metadata inspection passed.
Artifact **11295260413** uploaded successfully (4,661,901 bytes); it was not
downloaded or deployed. PR-only verification is not a live release artifact.
CI installation reports one high-severity npm advisory with unchanged
dependencies; existing Action Node-runtime and Ubuntu-runner notices remain.

Current branch: **`main`**, after checked PR #15 integration. This handoff and
completed implementation-plan receipt record verified integration without changing
the checked runtime files.

This increment uses synthetic sources only. No real activity collection, rights
decision, private backup transfer, public-data application, dependency/workflow
change or deployment occurred. No public activity pair or visitor consumer is
present. Existing public profiles, guidance, alerts and source clocks are
unchanged. The last verified live build remains **`2fa4d4a`** /
**`pilot-0609c66f7954`**, with stale alerts and noindex/ad-free safeguards.
No new live-site check occurred. Synthetic engineering and equal local copies
clear no actual rights, remote-backup, freshness or deployment requirements.
The repository-only readiness report remains **1 pass, 3 blocked, 3 not checked**
overall and **1 pass, 1 blocked, 3 not checked** required for the pilot, with
`release_ready: false` and no supplied private evidence.

Next: collect and review exact real activity listings, verify approved-bundle remote
recovery and prepare the public pair before Things to Do rendering. A live
release still needs deliberate alert refresh, complete release checks and
applicable deployment authorization.

## Preceding private activity collection integration — PR #14

The separate private `/thingstodo` transport, immutable five-park activity
checkpoints and `tracker.activity_stage` commands now support collection,
offline verification, restoration and unapproved review exports. All five
baselines, clocks and degraded-state capacity are checked before reading the
key or invoking transport. Requests use header authentication, refuse redirects,
bound retries/body size and reject strict-JSON, nonfinite-number and configured
key-echo violations. See [ACTIVITY_COLLECTION.md](docs/ACTIVITY_COLLECTION.md).

Each checkpoint binds the exact attempted five-park state and a parent ID
reference. Failed/quarantined attempts retain the last-good records and original
successful/observation clocks. A neutral POSIX installer reuses existing private
path/permission guards, locks a fresh destination and installs without overwrite.
Explicit batch limits accommodate five 8 MiB inventories; existing 8 MiB reader
and 10 MiB canonical-encoding defaults remain unchanged. Restoration preserves
identity and source clocks. Review exports claim no rights or approval.

Fresh local verification passed **324 Node + 689 Python + 66 generated-site
= 1,079 tests**, zero Astro diagnostics across 36 files and both 14-page builds.
The final full Python run includes the reviewed transport fix. Independent
review reproduced an interrupted chunked-response exception bypassing retry
classification. Three real-parser regressions failed with that exception, then
passed after explicit classified handling; all 28 transport cases passed in
independent re-review. All 71 activity integration cases and 10 neutral storage
cases are covered by the final suite. Implementation/documentation reviews have
no remaining findings; 29 relative links and diff checks pass. Both generated
hosting bases retain **`pilot-a2056877d1e7`**. Local Chromium remains unavailable;
supported GitHub CI completed both browser suites before integration.

[PR #14](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/14)
merged checked head **`c5c8e8f62b7815dc3c3d083a4f979d4f2284157a`** as
**`9ae46b90c67a40d7384ec2634cbe6b76f85538c8`** under the owner's standing
merge authorization. Native Windows Git confirms the actual merge, checked head
and CI checkout have identical trees; local `main` was fast-forwarded to the
merge. Independent implementation/re-review and documentation review have no
remaining findings.

[Verify pilot #226](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37158497539),
job **111306784906**, passed **324 Node + 689 Python + 66 generated-site +
126 Chromium = 1,205 tests**, zero Astro diagnostics across 36 files and both
14-page builds. All **111 root + 15 project-path browser cases** passed; all
three root accessibility screenshots survived the project suite. CI checked
standard PR merge **`80f2d441fd44d4279f9a868d27c41cd031ce22c8`**, combining the
checked head with unchanged main **`14e4346dead2e454334eb7afda0456db4ee1b9c1`**.
Fresh checks, complete job-log, checkout-parent/tree and artifact-metadata
inspection passed. Artifact **11286691378** uploaded successfully; it was not
downloaded or deployed. PR-only verification is not a live release artifact.
Existing npm advisory and Action/runner notices are unchanged.

Current branch: **`main`**, after checked PR #14 integration. This handoff receipt
records verified integration facts without changing the checked runtime files.

This increment uses synthetic sources only. No real activity collection, private
backup upload, public-data promotion, dependency/workflow change or deployment
occurred. Public profiles, guidance, alerts and source clocks are unchanged.
The last verified live build remains **`2fa4d4a`** / **`pilot-0609c66f7954`**,
with stale alerts and noindex/ad-free safeguards. No new live-site check occurred.
Synthetic collection/recovery clears no rights, remote-backup or release gates.

Next: implement a separately reviewed activity text-rights and public-projection
contract before real collection, verified remote recovery, public promotion and
Things to Do rendering. A live release still requires deliberate alert refresh,
complete release checks and applicable deployment authorization.

## Preceding individual-activity foundation integration — PR #13

The separate NPS `/thingstodo` adapter now normalizes individual listings for
the five pilots using an injected transport. It preserves source text, nullable
and empty fields, explicit boolean/string flags and documented pet-flag aliases.
Related parks establish attribution; geography, responsible agency, difficulty
and permit needs stay unconfirmed or null. Untrusted HTML/credit remain text,
without rendering or rights inference. Source issue/update/publication clocks
stay null. See [ACTIVITY_FOUNDATION.md](docs/ACTIVITY_FOUNDATION.md).

Complete pagination requires stable totals, exact offsets and unique IDs within
100 pages, 5,000 records, 256 KiB per record and 8 MiB per snapshot. A populated
inventory dropping below half requires review. Failures/refusals discard all
partial candidates and retain the validated defensive baseline, original
successful check and observation clocks. Unchanged semantic hashes preserve
observation clocks; collection attempts must strictly advance. An independent
168-hour freshness policy keeps unknown, failed, quarantined and stale states
distinct, with exact microsecond expiry boundaries.

The initial 26 source-contract tests failed because the module was absent, then
passed after implementation. Further tests exercise aggregate bounds, incoherent
states, odd-count drops and recovery. Exact-size review found an extra counted
comma and an estimated fallback envelope: the boundary regression reproduced
rejection at the valid exact limit, then passed with exact success-envelope and
comma accounting. A second boundary regression confirmed that failed/refused
metadata could exceed a full baseline's size limit. Preflight now requires room
for either degraded envelope before transport; it refuses rather than trimming
evidence. All **31 focused activity tests** now pass. Independent implementation
and documentation reviews have no remaining findings. Fresh **324 Node + 608
Python + 66 generated-site = 998 tests**, zero Astro diagnostics across 36 files
and both 14-page builds passed on the final implementation. Fourteen relative
documentation links and diff checks passed. Local Chromium is unavailable in
this WSL distribution; supported CI completed both browser suites before merge.

[PR #13](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/13)
merged checked head **`3014e08cdd11d1305fe560da7b3e41bc6b374f6c`** as
**`233c411cf2958bfa38cc3826851083c675f3a85e`** under the owner's standing merge
authorization. Native Windows Git confirms the actual merge, checked head and
CI checkout have identical trees; local `main` was fast-forwarded to the merge.
Independent implementation and documentation reviews have no remaining findings.

[Verify pilot #223](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37155596363),
job **111298223185**, passed **324 Node + 608 Python + 66 generated-site +
126 Chromium = 1,124 tests**, zero Astro diagnostics across 36 files and both
14-page builds. All **111 root + 15 project-path browser cases** passed; all
three root accessibility screenshots survived the project suite. CI checked
standard PR merge **`b98198e917dca48a79278e37ec3523561d791529`**, combining the
checked head with unchanged main **`224592162ec99361356f025cbab2b2808e615576`**.
Fresh check, complete job-log, checkout-parent/tree and artifact-metadata
inspection passed. Artifact **11285551765** uploaded successfully; it was not
downloaded or deployed. PR-only verification is not a live release artifact.
Existing npm advisory and Action/runner notices are unchanged.

Current branch: **`main`**, after checked PR #13 integration. Generated public
content remains the preceding profile experience, snapshot **`pilot-a2056877d1e7`**;
this adapter adds no public dataset or source-clock change. This handoff receipt
records integration facts without changing the verified runtime files.

This increment has no default HTTP transport, credentials, activity persistence,
real source collection, private backups, public-data promotion or visitor
rendering. Existing public profiles, guidance, alerts, dependencies and workflows
are unchanged. The last verified live build remains **`2fa4d4a`** /
**`pilot-0609c66f7954`**, with its stale alerts, noindex and ad-free safeguards.
No deployment or new live-site check occurred. Synthetic activity checks clear
no source-rights, durable-backup or live-release gates.

Next: implement the separate bounded header-authenticated activity transport and
immutable private checkpoint/recovery lifecycle, using existing POSIX guards.
Real activity collection, text-rights review, public promotion and Things to Do
rendering remain subsequent steps. A live release still requires deliberate
alert refresh, complete release checks and applicable deployment authorization.

## Preceding Overview and When to Visit integration — PR #12

The five park pages now render Overview and When to Visit from the validated,
approved public profile/rights pair. Native page navigation reaches both sections
with keyboard focus. Exact escaped introductions and seasonal text retain nearby
official sources and original checks. Yellowstone's empty introduction stays
empty with an honest label. Category details list the complete supplied inventory
without asserting individual activity availability. Seasonal context is explicitly
distinct from a travel-date forecast.

Build-only eager imports validate both files before lookup. Incomplete pairs are
refused and an absent pair renders unavailable states. Rendered profile content
and clocks now contribute to the snapshot hash. A small browser script receives
only status and original attempted/successful clocks, recalculating labels every
minute, on return, visibility and printing. The independent 168-hour policy
preserves microsecond expiry boundaries and retained failed/quarantined states.
It never changes evidence clocks. Static content and sources work without
JavaScript, with a build-freshness disclosure. No dependencies, workflows,
public source files, collection, private backups or live deployments changed.

Fresh local verification passed **324 Node + 577 Python + 66 generated-site =
967 tests**, zero Astro diagnostics across 36 files and both 14-page builds.
Seven synthetic pages exercise the real profile component's absent,
missing, empty, escaped, failed, quarantined and stale states. Sixteen pure tests
exercise freshness, invalid clocks and exact microsecond boundaries. Independent
review found no actionable defects. Local browser checks confirmed native section
focus, source clocks, expanded categories, Yellowstone's empty-text label and
360-pixel layout without horizontal overflow. Project-path browser inspection
also confirmed native focus, correct hosting-base navigation and original profile
clocks. Strict TypeScript, all 15 relative documentation links and diff checks
passed. Local Chromium remains unavailable in this WSL distribution; supported
CI completed both suites before integration.

[PR #12](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/12)
merged checked head **`ef475f32b7e8a98062183174951f236db33dd26a`** as
**`561b932f014fabf62f99a5c82b246f992b66d6d8`** under the owner's standing
merge authorization. Native Windows Git confirms their trees are identical;
the local checkout is fast-forwarded to `main`. Independent implementation,
documentation and browser-test correction review has no remaining findings.

[Verify pilot #220](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37117615712),
job **111187358491**, passed **324 Node + 577 Python + 66 generated-site +
126 Chromium = 1,093 tests**, zero Astro diagnostics across 36 files and both
14-page builds. All **111 root + 15 project-path browser cases** passed; all
three root accessibility screenshots survived the project suite. CI checked its
standard PR merge **`7f9df514ed99d9224dffbdb96f694729b83efd77`**, combining the
checked head with unchanged main **`c85f7125a05cb0e03b3ecca8fc525283044d039a`**.
Fresh check, complete job-log and artifact-metadata inspection passed. Artifact
**11271993269** uploaded successfully; it was not downloaded or deployed.
PR-only verification cannot be used as a live release artifact. The existing
dependency advisory and Action/runner notices remain unchanged.

The first PR #12 CI run, Verify pilot #219, passed every Node/Python/build/site
gate and 110 of 111 root browser cases. The new no-JavaScript case selected the
`noscript` wrapper, whose text Playwright deliberately excludes. Existing tests
and the installed matcher confirm the boundary. The test now selects its rendered
paragraph and checks visibility as well as disclosure text. Application output
was unchanged. Both suites subsequently passed on the corrected head before merge.

The optional standalone TypeScript check initially used NodeNext against bundled
Astro modules, producing JSON/import-resolution errors. The project uses bundler
resolution; the same strict check with that resolution and Vite types passed.
No production code or compiler strictness was changed to accommodate the check.

Current branch: **`main`**, after checked PR #12 integration. The generated
snapshot is **`pilot-a2056877d1e7`** under both hosting bases. Its identity includes
the rendered profiles; it does not advance any source clock. The last verified
live build remains **`2fa4d4a`** / **`pilot-0609c66f7954`**, with stale alerts and
its existing noindex/ad-free safeguards. No deployment or new live-site check
occurred. This frontend change establishes no new source accuracy, backup,
hosting or live-release readiness evidence.

Next: build the separate NPS `/thingstodo` activity
contract with provenance, unknown-field and freshness semantics. Named-location
weather and rights-reviewed imagery remain separate subsequent work. A live
release still needs a deliberate alert refresh, full release checks and applicable
deployment authorization.

## Preceding profile collection and promotion — PR #11

The first real NPS `/parks` collection succeeded with checkpoint/check clock
**2026-10-03T03:45:48.554581Z** (October 2 at 23:45 Toronto). This clock was
sampled before the batch requests, not measured at completion. All five scoped
requests succeeded; the immutable private checkpoint, offline verification and
review-candidate export completed. Introductions, seasonal context and category
names were inspected against current official NPS terms and park context.
Yellowstone's API introduction is an empty string and remains empty; its website
introduction was not substituted. Seasonal text remains distinct from forecasts,
categories do not establish activity availability, and source issue/update/
publication timestamps remain null. No photos, marks or raw API responses were
retained for this proposed public scope.

The **19,877-byte checkpoint** was uploaded to the selected private GitHub
repository. Authenticated identity, ownership, private visibility, write access,
disabled Actions and disabled Pages were checked before upload and recovery.
Only that verified checkpoint and reviewed repository setup documentation/
allowlist changes were committed. A fresh authenticated remote clone and fresh
private restore passed the unchanged checkpoint verifier and matched the original
ID and canonical bytes. Earlier ledger/alert checkpoints remain preserved. The
first transfer attempt stopped at the existing ignore allowlist; its inventory
was explicitly extended. The initial fresh clone lacked the transfer-local
credential helper; the same existing helper was configured only for the new
selected-repository clone. Neither issue changed access controls or exposed
credentials. Detailed IDs, commits, paths and receipts remain in owner-only WSL
storage outside the website checkout.

The initial approved-bundle operation was rejected by automatic approval review
pending the owner's text-use decision. The owner then approved the exact scope
displayed on the private review page; the subsequent guarded operation was
accepted. No complete human reading or new deployment authority is inferred.
The **42,692-byte immutable reviewed bundle** binds the complete checkpoint,
public projection, separate rights manifest and decision. Its selected private
upload, fresh authenticated remote download and fresh restore passed independent
bundle verification and exact ID/canonical-byte comparisons. Checkpoint-only
recovery did not substitute for this approved-bundle recovery. Detailed review,
authorization, transfer, recovery and application receipts remain private.

The existing preparer regenerated/rechecked the exact initial two-file patch
immediately before native Windows `git apply --check` and application. The paired
`data/park-profiles.json` and `data/profile-source-rights.json` now match the
approved projection and rights exactly, with one final LF. Windows Git initially
converted that LF to CRLF; validation and independent review caught the mismatch.
The two exact paths now use byte-preserving Git attributes. No source field or
clock changed during the repair. Synthetic profile/readiness fixtures now
establish their own profile-free base instead of inheriting real published
profile evidence; their separate positive and refusal cases remain intact.
Frontend, existing guidance/alerts/history, dependencies and workflows are
unchanged. No deployment or new live-site check occurred.

Fresh local verification passed **307 Node + 577 Python + 62 generated-site =
946 tests**, zero Astro diagnostics across 32 files and both 14-page builds.
The final Python run followed independent review's fixture no-write assertion
repair and passed all 577 tests. Strict TypeScript for the changed test,
12 relative documentation links and `git diff --check` passed. A disposable
native Windows Git checkout with `core.autocrlf=true` preserved both exact profile
file bytes under the new attributes. The existing validator reproduced the CRLF
refusal before repair; Node fixture failures and eight Python readiness failures
were observed before establishing explicit synthetic profile-free bases.
Production validators and release gates were not weakened. Local Chromium suites
remain unavailable in the current WSL distribution; supported CI completed both
browser suites before integration. The development guide's outdated statements
about absent real profiles were corrected; its five relative links and the
narrow independent documentation review passed.

[PR #11](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/11)
merged checked head **`41613b5f7400157ee13922938484b2ada55435b4`** as
**`4a0012c876ad4d8cdd7ebfef3858dc7c093287b6`** under the owner's standing
merge authorization. Native Windows Git confirms the checked-head and actual
merge trees are identical; the local checkout is fast-forwarded to `main`.
Independent review found no remaining actionable issues.

[Verify pilot #216](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37096772806),
job **111128244423**, passed **307 Node + 577 Python + 62 generated-site +
122 Chromium = 1,068 tests**, zero Astro diagnostics across 32 files and both
14-page builds. All **108 root + 14 project-path browser cases** passed, and all
three root accessibility screenshots survived the project suite. CI checked its
standard PR merge **`a4839884e0e2ace17fb5b4891d55e19d60a9fa55`**, combining the
checked head with unchanged main **`34bbd66500ef425cc44d6ca469f1eb55edc6a723`**.
Fresh check, complete job-log and artifact-metadata inspection passed. Artifact
**11264253651** was uploaded successfully; it was not downloaded or deployed.
The existing dependency advisory and Action/runner notices described below
remain unchanged. No new live-site success is claimed.

The private readiness report, with the current reviewed ledger/recovered backup
and separate profile review/recovered bundle, verifies exact public profile and
rights matching plus all five profile rights records. It records **3 required
passes, 0 blocked and 2 not checked**, with `release_ready: false`; external
provider/freshness and hosting assessments are not ingested. The repository-only
report is **1 required pass, 1 blocked and 3 not checked** because no recovered
profile evidence is supplied. The first private report invocation lacked Node 24
on operator PATH and was refused by the existing ledger replay guard; the normal
project runtime rerun passed without ledger mutation. No gate was forced to pass.

The following frontend increment consumes these verified profiles while
preserving the original collection clock. The live alert feed's four-hour
freshness window ended at **2026-10-03T03:10:42.565Z**; a subsequent authorized
live release needs a deliberate alert refresh rather than a build-time clock
change. Profiles retain their independent 168-hour freshness policy.

The owner adopted the complete [permanent project instructions](docs/PROJECT_INSTRUCTIONS.md) on October 2. The product direction is **National Park Explorer & Trip Planner**, with readiness as part of park discovery and trip planning. All 49 instruction sections, the five development phases and priority hierarchy are preserved. `AGENTS.md` requires future sessions to read them in full; they supersede conflicting historical scope exclusions and plans. Codex is responsible for routine engineering, source processing and authorized operations; the owner makes consequential product, business, cost, legal-risk, privacy and strategic decisions.

The current milestone is **Phase 1 — Foundations**. The [foundation assessment](docs/FOUNDATION_ASSESSMENT.md) maps existing ingestion, provenance, cached publication, freshness/failure handling, rights boundaries and page architecture to the broader five-park scope. Keep Astro/GitHub Pages and the existing alert tools while adding separate profile, activity and named-location weather contracts. Cloudflare, scheduled collection, rights-verified imagery, richer planning sections and locally saved trips remain staged directions; hosting migration is not a prerequisite.

Branch at this preceding milestone: **`main`**, after checked PR #11 integration.
The preceding [PR #10](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/10)
merged checked head **`39b3085e647d32ebb409e94a9aa3e0cdafe24d2e`** as
**`d7d8e16a157fb8040fb34a933a82264c386f5f59`** under the owner's standing
integration authorization. Native Git confirms their trees are identical. The new
[profile publication contract](docs/PROFILE_PROMOTION.md) keeps public profiles
and their separate text-rights manifest paired, all-five, exact-field validated
and bound to unchanged source/observation clocks. Both public files were absent
at that integration; the real promotion is recorded above.
An explicit immutable private approval bundle binds the checkpoint and complete
public/rights digests. Offline tools verify/restore that bundle and prepare or
regenerate/check only the paired Git patch, including exact old file bytes or
absence. They never apply or deploy it. Failed/quarantined continuation cannot
replace retained public evidence or renew the successful-fetch clock.

Once the public pair exists, the existing durable review, source rights and
backup gates require matching profile-specific evidence. Existing entry guidance
or alert approvals/backups cannot cover this new text. Absent public profiles
preserve the current seven-gate/schema-2 pilot report. A verified matching bundle
under a separate private parent establishes local recovery only; real off-host
transfer and fresh authenticated download remain deliberate operator evidence.
The existing provider/freshness and hosting limitations are not promoted to
passes. Focused Python/Node regressions reproduced the missing bindings/gate
coverage before implementation; synthetic new-file and replacement patches apply
exactly in a disposable repository. Independent review reproduced a conflicting
earlier observation hidden by a newer fetch; both changed-text and replacement-ID
regressions failed, then passed after requiring the new observation to follow the
public last successful confirmation. The final diff is independently approved.

Fresh local verification passed **307 Node + 577 Python + 62 generated-site =
946 tests**, zero Astro diagnostics across 32 files and both 14-page hosting-base
builds. The new contract/release/readiness coverage adds **17 Node + 19 Python
release + 17 Python readiness tests**. Final Node and Python runs followed the
review repair; 46 readiness methods and 19 release methods also passed separately.
Strict TypeScript for the changed validator/test files, 22 relative documentation
links and `git diff --check` passed. Repository-only readiness retains its exact
existing pilot result: one required pass, four required not checked and
`release_ready: false`. Local browser suites were not rerun; supported CI
completed both suites before integration.

Exact check head [Verify pilot #212](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37092715042),
job **111116255685**, passed **307 Node + 577 Python + 62 generated-site +
122 Chromium = 1,068 tests**, zero Astro diagnostics across 32 files, both
14-page builds and all three accessibility screenshots. All **108 root +
14 project-path browser cases** passed. CI used its standard PR merge checkout
**`37778446a817e2cbf8da100bd1175bf0c346fd41`**, combining the checked head with
unchanged main **`bcd5451160c00bc66b0dc9e5ee197c08e5f36b54`**. Independent log,
head and artifact-metadata review passed. Artifact **11262731917** was uploaded
successfully; no downloaded-artifact audit, deployment or live proof is claimed.

CI and a fresh npm audit report two high entries for the same pre-existing
[http-cache-semantics advisory](https://github.com/advisories/GHSA-ch52-4w7c-c8xp),
including Astro's transitive exposure. PR #9 logs contain the same audit and
esbuild install-script warnings; this increment changes no dependency. The
official advisory lists no patched version. Local source/config inspection finds
static output, no Astro image consumer, no authentication and no shared
authenticated-response cache; the dependency is used by Astro's build-time
remote-image cache. Independent assessment found no current attack path in the
pilot or profile tools. This is a scoped reachability assessment, not a fix or
general security clearance. Do not apply npm's suggested major Astro downgrade.
Reassess this unresolved dependency before adding remote imagery/server caching
and validate a compatible maintainer fix when available. Existing Action runtime
and Ubuntu runner migration notices also remain maintenance follow-ups.

The preceding PR #10 increment performed no real collection, key read, text approval, remote
backup, public promotion, deployment or live-browser check. Frontend, real public
data, dependencies and workflows were unchanged. Its recommended next task was to deliberately collect the
actual five-park profiles, review exact text reuse, back up the approved bundle
to the selected private repository and verify fresh-download recovery, then
prepare/recheck the exact paired public-data change. Source-backed Overview and
When to Visit follow verified public profiles; photos, individual activities and
named-location NWS weather retain separate source/rights contracts.

The preceding [PR #9](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/9) merged checked head **`2f34eb7bbfc8c55443656e3b8c721ffc4bc1ac4c`** as **`866dcbeb766592955aacce78a10898ddd65de76a`** under the owner's standing integration authorization; their trees match. The separate profile transport now uses only the scoped fixed NPS `/parks` endpoint, private header authentication, no redirects, three bounded attempts, a 20-second timeout and a 4,000,000-byte body limit. Strict parser/body refusals and literal or once-percent-decoded key echoes quarantine safely; terminal HTTP/network failures retain last-good profiles as failed attempts. Source bodies, headers and rejected text are never retained.

The [private profile collection tools](docs/PROFILE_COLLECTION.md) now provide all-five immutable checkpoints, offline integrity verification, fresh-destination restore and private review-candidate export. They reuse existing owner-only POSIX guards and validate the entire baseline, source clocks, external destination and output lock before key access or requests. Existing files are never overwritten or repaired. Checkpoints have an explicit parent ID but no mutable latest head or verified history-chain claim; separate outputs may branch from the same baseline. Pre-install interruption loses uncommitted in-memory results; post-install failure may leave a checkpoint that must be verified offline before retry. Review export preserves degraded states and nullable clocks with rights not checked, approval false and no public-data write.

Fresh local verification passed **290 Node + 541 Python + 62 generated-site = 893 tests**, zero Astro diagnostics across 32 files and both 14-page hosting-base builds. The transport, checkpoint and CLI suites add **20 + 27 + 15 tests**; two additional profile regressions verify fetch-level quarantine and defensive baseline retention. Missing implementations, the export-envelope bound ordering and Ctrl-C report failures were observed before their fixes. Independent whole-branch review reproduced and verified the interruption repair, independently passed all 62 new-tool tests, and found no remaining runtime issue. Its final wording finding was corrected to the parser's precise nonfinite JSON-constant contract. Fifteen relative documentation links and `git diff --check` passed. The application commands completed successfully; their log-display wrappers had a shell-variable quoting error after completion, and a separate successful check confirmed all complete suite/diagnostic totals from the retained logs.

Exact PR-head [Verify pilot #209](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37089413134), job **111106351211**, independently passed **290 Node + 541 Python + 62 generated-site + 122 Chromium = 1,015 tests**, zero Astro diagnostics across 32 files and both 14-page builds. All **108 root + 14 project-path browser cases** passed and all three accessibility screenshots were retained before the checked-head merge. No real collection, key read, remote profile backup, data promotion, deployment or live-browser check was performed. Public data, frontend, dependencies, workflows and the hosted artifact are unchanged.

The preceding [PR #8](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/8) merged checked head **`b78f73080a4aa7124de0f8ddb8a23f1c8b94e315`** as **`5bfd61e4c017ff5dc2824c4737ea029dfead0f02`** under the owner's standing integration authorization; their trees match. The legacy `python -m tracker` direct-write entry point is retired: it emits a static migration message and exits 2 without reading keys, parsing destinations, requesting sources or writing files. Operators continue through explicit private staging and reviewed paired promotion. Six regression tests first reproduced the former default-path write and explicit-directory creation using synthetic transport and temporary files, then passed with the refusal. Independent review found no actionable issue.

That preceding increment added the separate, injectable NPS park-profile foundation for introductions, official identity, activity categories and seasonal weather context. It does not interpret categories as individual activities, seasonal text as forecasts or retrieval as source issue/publication time. Missing optional fields stay null, and failed/malformed responses retain last-good evidence. Its independent 168-hour freshness policy never renews success after a failed/quarantined attempt. Complete previous state, source, hash and clocks are validated before transport. Success validates a separate candidate; quarantine retains the copy validated before the request, even if the callback alters the caller's previous data. The current increment supplies its private lifecycle; real profiles, new text-rights review, public promotion and website consumption remain subsequent work.

Preceding PR #8 local verification passed **290 Node + 477 Python + 62 generated-site = 829 tests**, zero Astro diagnostics across 32 files and both 14-page builds. The 39 profile tests and six retired-command tests passed independently in WSL Python 3.12.14. Three added mutation regressions first reproduced valid-rehashed, invalid-hash and coherent future-clock callback changes; they now preserve the original validated baseline. Independent whole-branch review and scoped fix re-review found no remaining actionable issue. Nine relative documentation links and `git diff --check` passed. Initial cross-language test runs lacked the required executables on PATH; the passing reruns explicitly configured Node 24, the project Python 3.12 environment and uv.

Exact PR-head [Verify pilot #206](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37086874124), job **111098899610**, passed **290 Node + 477 Python + 62 generated-site + 122 Chromium = 951 tests**, zero Astro diagnostics across 32 files, both 14-page builds and retention of all three accessibility screenshots. All **108 root + 14 project-path browser cases** passed before the checked-head merge. Public data, frontend code, dependencies and workflows are unchanged. No source collection, data promotion, infrastructure change, deployment or new live-browser check was performed; this integration does not change the hosted artifact.

The preceding documentation-only adoption preserved all **49 sections and five phases**, with exact attachment-to-policy body equality after heading-level normalization. All seven relative Markdown links in its five changed files resolved, and `git diff --check` passed. Independent review found no actionable issue. Application tests were not rerun for that adoption-only commit; current foundation verification is recorded separately above.

Unchanged live-release evidence: [ParkReadiness](https://vasuki8.github.io/us-national-park-trip-readiness-tracker/) serves verified commit **`2fa4d4abd5c78b5ebf4bb77a9360f5d99f073ffc`** / snapshot **`pilot-0609c66f7954`**. [PR #7](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/7) merged checked head **`95099ead434d1591f594cbd4a3bad87330bf152b`** as **`e7018a2d3493914dc983507f5ac104c1e6494495`**; their trees match. The five-park pilot remains light, free, ad-free and unindexed, with the existing search, history, notice filters, correction context, printing, trip/checklist returns, section navigation and native stored-guidance focus.

Exact PR-head [Verify pilot #200](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37079129583), job **111075542826**, and pinned default-branch [Verify pilot #202](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37079690695), job **111077480589**, each passed **290 Node + 432 Python + 62 generated-site + 122 Chromium = 906 tests**, zero Astro diagnostics, both 14-page builds and retention of all three accessibility screenshots. All **108 root + 14 project-path browser cases** passed. Independent applied-diff review found no actionable issue; the owner-authorized merge used the checked head SHA.

The successful **push/main** verification candidate is **`2fa4d4abd5c78b5ebf4bb77a9360f5d99f073ffc`**. Artifact **11257849120**, **3,951,570 bytes**, has digest `sha256:f061fbd24aa7c86d34edadcb45b0438899ac167231454803e640f8b4e793f8c5` and expires **October 9, 2026 at 23:58:37 UTC**. The downloaded ZIP matches that digest and contains 53 safe allowlisted entries, both correct commit/snapshot/base manifests, **14 noindex pages and 23 files per build**, the unchanged retained verifier and three screenshots. Independent immutable-artifact review matched every emitted snapshot/history to the approved JSON, preserved all 17 notice records and original baselines, and confirmed unchanged guidance, excerpts and static assets against the previous live artifact.

The owner explicitly approved this exact deployment. [Deployment #6](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37081311751), job **111082232975**, succeeded and downloaded the matching artifact digest. The manual workflow ran from documentation receipt **`e19528058d3e89d62c6268409b286626b3f5fdc5`**; its validated release target and hosted report remain pinned to **`2fa4d4abd5c78b5ebf4bb77a9360f5d99f073ffc`**. Its separately downloaded, digest-checked one-file report records **22 public files / 14 pages / one attempt**, `passed: true`, matching commit/snapshot/project URL/base at **2026-10-03T00:16:02.844Z**. Report artifact **11258402197** has digest `sha256:082b1df13c9e5cba4970e58006def370d6197cea8214aadf9acf1a9417fc9aa2` and expires **October 10, 2026 at 00:16:04 UTC**. Independent report/log audit passed. All four observed response headers remain null; page meta noindex is the established safeguard. Deployment reused the exact verified artifact and did not rewrite source clocks or nullable publication metadata.

Actual live-browser checks completed at **2026-10-03T00:22:19.949Z**. All 14 pages loaded with noindex/nofollow metadata; the five park pages retained **1/0/5/7/4 notices**, the October 2 feed clock, original baseline time and two-check zero-change histories. Rocky Mountain's empty successful feed explicitly remains uncertain. The directory passed no-match, normalized whitespace/state conjunction, reset and a real back return that reconciled its actual restored controls. Literal retained-notice search and reset passed. Native history-to-trip navigation focused the trip region; a dated decision preserved a checklist mark, focused the exact stored-rule article, continued to its disclosure with Tab and opened the original excerpt with Enter. Guidance review time remained unchanged. No console warnings/errors were captured; the published history screenshot shows the light styling and both recorded checks. These checks do not establish provider availability, every browser's restoration/print behavior or screen-reader announcements.

The published alert refresh comes from the real successful collection at **2026-10-02T23:10:42.565000Z** (October 2 at 19:10 Toronto). Keyed preflight and collection succeeded for all five parks. Counts remain **1/0/5/7/4**, totaling **17 unchanged notices**. Each complete archive chain preserves its original baseline and adds one successful comparison with **zero changes**. Independent verification confirmed full record identity, hashes, first/change observation clocks and nullable publisher timestamps; only feed attempt/success clocks advance. The committed archive checkpoint was uploaded under the owner's standing private-backup authorization, downloaded freshly from the selected private GitHub repository and replayed against all original heads and file bytes. The current reviewed ledger was also freshly downloaded, verified and restored into a new private destination; its revision, six records and working database bytes remain unchanged.

The owner authorized applying the exact prepared refresh before integration. Immediately before application, the existing preparer rechecked all six public base files and exact private patch bytes, and `git apply --check` passed. The isolated noindex preview and independent ready-marker review passed. The applied diff independently matched the candidate: only five alert snapshots and `data/history.json` changed, with entry guidance and source-rights scope unchanged. No mutable public-data test assumes baseline-only histories. Candidate identities, checkpoint inventories, recovery paths, authorization/application records and the completed deployment/browser receipt remain in owner-only WSL storage outside the checkout. The private readiness report records **3 required passes, 0 blocked and 2 not checked**, with `release_ready: false`: the CLI does not ingest external provider/freshness and hosting assessments, including this successful hosted report. No gate was artificially promoted.

Fresh local verification passed data validation, **290 Node + 432 Python + 62 generated-site = 784 tests**, zero diagnostics across 32 Astro files and both 14-page hosting-base builds. Local Chromium remains unavailable on Ubuntu 26.04; supported CI completed both browser suites before integration and repeated them for the published main artifact.

The **previous live PR #6 build is the current rollback candidate**: **`fea984937067fc85fde08d506ced719254e0bc48`** / **`pilot-08efc3ad8281`**, successful push/main [Verify pilot #197](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37072908539), job **111056451305**, artifact **11255867049**, digest `sha256:441ebac553624cbfb4cd07fff0798549a089c823237d128936423950538376c6`, available through **October 9, 2026 at 22:35:29 UTC**. Immediately before this deployment, its GitHub eligibility, downloaded ZIP digest, safe inventory, manifests, both noindex builds, verifier and screenshots were independently rechecked. Previous [Deployment #5](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37073863612) verified 22 files and 14 pages; the original deliberate deployment/rollback/restoration drill remains recorded in `docs/PAGES_RELEASE.md`. No new rollback drill was performed for this refresh.

The current next step is source-backed Overview and When to Visit described at
the top; real-profile collection, approved-bundle recovery and paired data are
now verified. Existing
six-record guidance approvals cannot
approve park descriptions or seasonal text. Do not repeat already verified pilot
work or migrate hosting merely because a preferred platform is listed. The bounded
manual screen-reader review remains an unresolved quality check for the technical
team; actual announcements cannot be inferred from browser status attributes.
The five published feeds were recent at live-check time; their four-hour freshness
window ends **2026-10-03T03:10:42.565Z** (October 2 at 23:10 Toronto), and later stale
warnings remain truthful without another deliberate collection/promotion.
Guidance review time remains **2026-10-01T01:18:28.701Z**; its seven-day window ends
**October 8 at 01:18:28.701 UTC**. Indexing, advertising and recurring operations
remain disabled with their existing gates and applicable owner decisions.

Owner workflow preference, recorded October 2: merge future PRs after required checks and review pass without asking again, include the next concrete step in chat updates and final responses, and keep this handoff current. `AGENTS.md` records the same preferences. A later documentation-only receipt commit does not change the pinned artifact served at the live URL.

### Verified native stored-guidance focus in PR #6

All dated-rule and undated-observation articles accept native fragment focus with `tabindex="-1"`. Exact decision evidence and source-specific correction returns can focus the matched article; Tab continues to its supporting-text disclosure, and Enter opens the original excerpt. Direct article fragments also work without JavaScript. Articles stay outside the normal Tab order. The repair adds two markup attributes and uses the existing focus styling and scroll margin; no script is added. Source IDs, wording, hashes, review/source clocks and link destinations remain unchanged. Same-page decision evidence preserves trip choices, checklist marks and decision wording; native correction returns load the park page with its normal initial state.

The new emitted-page regression first failed on both old hosting-path outputs because guidance articles lacked focus support. Fresh local verification passed **290 Node + 62 generated-site checks = 352 tests**, strict TypeScript for the four changed browser/site test files, zero diagnostics across 32 Astro files and both 14-page builds. Independent review found no actionable issue and independently checked the new emitted assertion under both bases. Existing exact-rule browser cases now require article focus and immediate Tab continuation instead of manually focusing the disclosure. Three new browser cases are registered (**108 root + 14 project-path cases**) for all six public guidance records: keyboard correction returns under both bases and direct no-JavaScript fragments, with exact excerpt/hash/source links, undated limitations, stale original reviews and unchanged metadata. Local Chromium remains unavailable on Ubuntu 26.04; Python behavior is unchanged. Use the PR's current-head receipt to confirm supported browser execution before integration.

Implementation head `18dbcf8ff8f93b1cdb264dc424c8f30471de2979` passed **290 Node + 432 Python + 62 generated-site = 784 non-browser tests**, zero Astro diagnostics and both builds in [Verify pilot #194](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37070434947), job `111048346715`. The root browser suite passed **107 of 108 cases**, including exact-rule article focus/Tab and all six keyboard correction returns. The remaining no-JavaScript case passed native fragment focus, disclosure navigation and source checks for its first record, then failed because the new assertion queried `noscript` itself: Playwright deliberately excludes that element from text matching. It now checks the actual fallback paragraph for visibility and expected wording, following the existing history/print/no-JavaScript tests. Product markup is unchanged by this assertion repair. Project-path execution and screenshot-retention verification were skipped after the first browser failure; artifact upload still ran. Use the PR's final current-head receipt to confirm the repaired all-record no-JavaScript case and both complete suites.

The preceding search/history-validation head `7bef92706a1b98ec0f5af57e5a009091fe6bed3f` passed [Verify pilot #193](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36932662201), job `110605519519`: **290 Node + 432 Python + 60 generated-site + 119 Chromium = 901 tests**, zero Astro diagnostics, both 14-page builds and all three retained accessibility screenshots. All **106 root + 13 project-path browser cases** passed. This records the completed preceding increment's receipt; the PR carries the final current-head receipt for the additional guidance-focus change.

Final guidance-focus head `74168a01599d1e1e1cd92ff6eac51e4fa607128c` passed [Verify pilot #195](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37071184033), job `111050751112`: **290 Node + 432 Python + 62 generated-site + 122 Chromium = 906 tests**, zero Astro diagnostics, both 14-page builds and all three retained accessibility screenshots. All **108 root + 14 project-path browser cases** passed, including the repaired no-JavaScript case for all six records. Required verification and independent reviews passed before the authorized merge; the current handoff above records the resulting main verification and publication.

### Verified directory search and first-success history validation in PR #6

Continue on **`codex/trip-return-state`**, based on integrated `main` commit `c32e6c7762d0677229ddb1102f6abe24e50135bc`. [PR #6](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/6) now repairs pasted directory searches and first-success history validation, alongside the history, navigation and readiness work below. It remains unmerged. The PR records its current review state and final exact-head CI receipt; this increment is ordinary development and does not publish a release.

Pasting `Rocky   Mountain` now finds the same park as `Rocky Mountain`. Directory matching trims, lowercases and collapses whitespace in both the query and card search text while retaining literal substring matching and the exact state filter. Prefilled, typed and queued page-return controls use the same normalization. Raw visitor values and card metadata remain unchanged, missing search metadata stays excluded, and equivalent counts stay quiet. No application storage, URL parameters or requests are added.

Complete public history must mark its earliest successful feed as a baseline, even after initial failed/quarantined attempts. A comparison cannot invent added or edited events before that baseline. Bounded histories can legitimately omit an older baseline; the generic validator preserves those views. When a newer promotion candidate retains a known public checkpoint, the preparer separately checks new successes chronologically against that checkpoint's nullable success clock: the first success after a null clock requires a baseline, followed by comparisons. Existing archive verification and record/clock replay remain intact. Valid subsequent comparisons, intervening degraded attempts and complete histories with no success retain their original meaning.

Four new actual-script directory regressions first failed against the old implementation. Two complete-history and two bounded-promotion refusal tests also failed as expected, while their valid controls passed. All **37 focused tests** now pass. Fresh local verification reported **290 Node + 60 generated-site checks = 350 tests**, strict TypeScript across all eight changed code/test files, zero diagnostics across 32 Astro files and both 14-page builds. Independent review found no remaining product issue; a home-page browser selector ambiguity was corrected by scoping metadata assertions to the directory. Three new browser cases are registered (**106 root + 13 project-path cases**) for pasted/prefilled/restored multiword searches, quiet counts, literal matching, exact-state exclusion, source-metadata conservation and native park routes. Local Chromium remains unavailable on Ubuntu 26.04; Python behavior is unchanged. Use the PR's current-head receipt to confirm supported execution of both browser suites before integration.

The preceding history-navigation head `a9ca0b731f6f5c669e26a856a7d4395b647a6c78` passed [Verify pilot #192](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36929868267), job `110596200342`: **278 Node + 432 Python + 60 generated-site + 116 Chromium = 886 tests**, zero Astro diagnostics, both builds and all three retained accessibility screenshots. That result verifies the earlier work below; it does not verify this new increment.

Next: obtain the owner's integration/publication decision for PR #6 once its current head passes exact-head verification. The PR retains that receipt and review state. Earlier PR #5 authorization does not authorize this release. Public data and source clocks are unchanged. No collection, promotion, private checkpoint, merge or deployment was performed. Indexing, advertising and recurring operations retain their separate operator decisions.

### Verified history-to-retained-evidence navigation in PR #6

Continue on **`codex/trip-return-state`**, based on integrated `main` commit `c32e6c7762d0677229ddb1102f6abe24e50135bc`. [PR #6](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/6) now connects notice history to public park readiness and matching retained notice articles, alongside the native park menu, notice filtering, source corrections, printing and trip-return work below. It remains unmerged. The PR records its current review state and final exact-head CI receipt; this increment is ordinary development and does not publish a release.

Every overview history panel offers a base-aware native link to that park's trip-readiness section, including the current baseline-only histories. Public callers explicitly supply the validated paired snapshot's retained inventory. Comparison entries link only to a unique exact same-park notice ID, using local fragments on park pages and the park route on the overview. Labels distinguish retained wording from the archived comparison and live conditions. Missing or ambiguous matches imply no reopening; removal warnings and before/after evidence stay intact even if an ID later reappears. Shared timelines without this optional public context, including private previews and archive-only fixtures, add no public destinations or matching claims.

Retained articles now accept native fragment focus without entering the normal Tab order. A same-document notice link reveals excluded evidence before default navigation, including repeated activation of an unchanged fragment. Modified, prevented, download, other-target and cross-document activations keep their normal handling. Initialization, hash changes and page returns focus and scroll only a unique target that needed revealing. Already visible targets retain useful filters, and subsequent typing still filters normally. Trip choices, checks, source wording, IDs and clocks remain unchanged; no application storage, URL mutation or requests are added.

Both new emitted-page regressions first failed against the old output. The missing helper failure and six expected actual-script failures preceded **10 helper + 20 runtime tests** passing. Fresh local verification passed **278 Node + 60 generated-site checks = 338 tests**, strict changed-file TypeScript, zero diagnostics across 32 Astro files and both 14-page builds. The real timeline and retained-notice components are also built together from unchanged validated synthetic mixed/failed pairs in the isolated history test site; archive-only routes retain their original context-free rendering. Independent review passed all 30 focused tests and found no actionable issue. Three new root browser cases and one project-path case are registered (**104 root + 12 project-path cases**) for exact matching, archived evidence/removal uncertainty, new and repeated fragment keyboard focus/Tab, no-JavaScript navigation, mobile/doubled text, project-base readiness returns and source-clock preservation. Local Chromium remains unavailable on Ubuntu 26.04; no Python behavior changed. Use the PR's current-head receipt to confirm supported execution of both browser suites before integration.

Implementation head `f5b5b5246341688929518c795c7cae8eee374edd` passed **278 Node + 432 Python + 60 generated-site = 770 non-browser tests**, zero Astro diagnostics and both builds in [Verify pilot #191](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36928463552), job `110591531157`. The root browser suite passed **103 of 104 cases**, including new/repeated fragment focus and the no-JavaScript retained-source paths. The remaining doubled-text case found a real wrapping gap in retained notice descriptions: at 360px and 200% text, Chrome measured a 525px escaped-token paragraph inside a 269px column, with 563px document width. Headings, controls and history evidence fit; the source paragraph was the only overflowing leaf. The retained-notice panel now inherits scoped `overflow-wrap:anywhere`, preserving its exact text and metadata, and the browser regression identifies overflowing source paragraphs before checking the document. Independent review found no issue in this repair. Project-path execution and screenshot-preservation verification were skipped after the first browser failure; artifact upload still ran. Use the PR's final current-head receipt to confirm the repair and both complete browser suites.

Fresh repair verification passed the actual generated-history test and **60 generated-site checks**, strict changed-browser TypeScript, zero Astro diagnostics and both 14-page builds. Independent Chrome measurement at the same 360px/200% setting confirmed the description's scroll width fell from 525px to its 269px client width, the document fit at 345px, and no visible descendant overflowed. The exact description still matched its original embedded fixture record; temporary viewport overrides were reset. Supported current-head CI remains the full-suite release verification recorded on the PR.

Next: obtain the owner's integration/publication decision for PR #6 once its current head passes exact-head verification. The PR retains that receipt and review state. Earlier PR #5 authorization does not authorize this release. No collection, promotion, private checkpoint, merge or deployment was performed. Indexing, advertising and recurring operations retain their separate operator decisions.

### Verified native park-section navigation in PR #6

Native-navigation head `5b50a27b9a5ff4a2cd566177721348ab0f9595fd` passed [Verify pilot #190](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36922511756), job `110571751714`: **262 Node + 432 Python + 56 generated-site + 112 Chromium = 862 tests**, zero Astro diagnostics, both 14-page builds and all three retained accessibility screenshots. This exact-head baseline verifies the following native menu and preceding changes before history-to-retained-evidence navigation was added.

Continue on **`codex/trip-return-state`**, based on integrated `main` commit `c32e6c7762d0677229ddb1102f6abe24e50135bc`. [PR #6](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/6) adds native park-section navigation alongside retained-notice filtering, source-specific correction reporting, printing/saving the current park page, restored-trip reconciliation, exact decision-evidence links and immediate return freshness. It remains unmerged. The PR records its current review state and final exact-head CI receipt; the current increment is ordinary development and does not publish a release.

A wrapping "On this page" menu after each park introduction links to the conditions snapshot, entry check, checklist, stored guidance, notice history and official planning checks. The retained-notices item appears only when its collection exists. All destinations are unique, visible and focusable through native fragments, with negative tabindex so keyboard Tab continues from the chosen section. The collection target preserves active notice filters; exact notice articles retain their separate reveal behavior. Native links need no JavaScript or additional script, storage or requests. The menu is hidden in print and does not change trip choices, checks, source wording or clocks.

Both new generated regressions first failed against the previous output: the menu was absent and existing destinations could not receive native fragment focus. Fresh local verification passed **262 Node + 56 generated-site checks = 318 tests**, strict changed-file TypeScript, zero Astro diagnostics and both 14-page builds. Independent review found no production issue and closed a browser fixture finding: wildcard rules now select an actual covered park-area option and preserve that value. Three new root browser cases and one project-path case are registered (**101 root + 11 project-path cases**) for native focus/Tab, no-JavaScript navigation, mobile/doubled text, print hiding and state/evidence preservation. An existing print assertion now scopes the checklist link because both the menu and checklist legitimately target official planning checks. Local Chromium remains unavailable on Ubuntu 26.04 and no Python behavior changed. Use the PR's current-head CI receipt to confirm supported execution of both browser suites before review/integration.

Next: obtain the owner's integration/publication decision for PR #6 once its current head passes exact-head verification. The PR retains that final receipt and review state. Earlier PR #5 authorization does not authorize this release. No collection, promotion, private checkpoint, merge or deployment was performed for this increment. Indexing, advertising and recurring operations retain their separate operator decisions.

### Verified notice-filter changes in PR #6

Filter handoff head `e806ce96b0a9ec457007b55a2042065a5c889095` passed [Verify pilot #189](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36919549271), job `110561870682`: **262 Node + 432 Python + 52 generated-site + 108 Chromium = 854 tests**, zero Astro diagnostics, both 14-page builds and all three retained accessibility screenshots. This exact-head result verifies the following filter, correction, print and trip changes before the native menu was added.

Populated park notice lists combine literal title/description search with exact provider categories derived from their retained inventory. A shown/total count and honest no-match message describe the view without replacing stale-feed, area-scope or travel-date warnings. Prefilled and restored controls reconcile on initialization and after `pageshow`; unchanged counts remain quiet. Exact source fragments reveal notices excluded by filters, while later typing and unrelated/malformed fragments keep their normal behavior. No application storage, URL parameters or requests are added.

Printing includes every retained notice, even when the screen filters show none. Print controls/counts/empty state are hidden, a static disclosure explains the complete inventory, and screen selections/hidden attributes survive printing. Without JavaScript, the complete native notice inventory and source/correction links remain available with an explicit filtering fallback. The zero-notice park retains its original uncertainty state without an empty filtering toolbar. Public records and all original clocks remain unchanged.

The actual filter script first reproduced 13 expected failures, then passed all **14 focused tests**. Both generated regressions first failed against the old output and now pass under both hosting bases. Fresh local verification passed **262 Node + 52 generated-site checks = 314 tests**, strict changed-file TypeScript, zero Astro diagnostics and both 14-page builds. The Node suite initially lacked the plain `python` executable expected by an existing synthetic pipeline fixture; rerunning with the repository's Python environment passed. Independent review found no product defect and closed two test findings: exact visible identities now retry after queued restoration, and hidden-target assertions require the actual stored article to exist. Five new root browser cases and one project-path case subsequently passed in supported CI (**98 root + 10 project-path cases**). Local Chromium remains unavailable on Ubuntu 26.04 and no Python behavior changed.

Implementation head `ad829e48ce8759a9786db539311a9270e2c6f3e4` passed **262 Node + 432 Python + 52 generated-site = 746 non-browser tests**, zero Astro diagnostics and both builds in [Verify pilot #187](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36918067973), job `110556904034`. The root browser suite passed **97 of 98 cases**, including all four new screen/restoration/fragment/no-JavaScript cases. The remaining print case confirmed that every notice article was visible, then failed because the stylesheet's generated destination URL contributes to a link's accessible name. It now selects the provider anchor structurally and requires one visible link with the exact provider label, destination and printed URL. Independent review confirmed the cause and repair; no product change was needed. Project-path execution and screenshot-preservation verification were skipped after that failure; artifact upload still ran. Use the PR's final exact-head receipt to verify the repaired selectors and both browser suites before integration.

Repaired filter head `5e8095334aa56cbdce808e18432d5c0c227c344b` passed [Verify pilot #188](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36918917922), job `110559758459`: **262 Node + 432 Python + 52 generated-site + 108 Chromium = 854 tests**, zero Astro diagnostics, both 14-page builds and all three retained accessibility screenshots. All five new root cases and the project-path source return case passed, including the repaired print-provider assertion. The following handoff-only commit preserves this implementation; the PR retains the final current-head receipt and review state. Print-media and synthetic lifecycle checks do not establish every platform's native print dialog, pagination or restoration policy.

Next: obtain the owner's integration/publication decision for PR #6, using its current-head receipt before a deliberate release. Earlier PR #5 authorization does not authorize this release. No collection, promotion, private checkpoint, merge or deployment was performed for this increment. Indexing, advertising and recurring operations retain their separate operator decisions.

### Verified correction changes in PR #6

Correction head `746beb1db81817a122ba5adf6f0a65bd096bd2b6` passed [Verify pilot #186](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36912567565), job `110538575699`: **248 Node + 432 Python + 48 generated-site + 102 Chromium = 830 tests**, zero Astro diagnostics, both 14-page builds and all three retained accessibility screenshots. That exact-head result closes the three existing source-link assertion repairs described below and verifies the correction, print and trip changes before filtering was added.

Each dated rule, undated observation and current retained notice has a native correction link. The corrections page selects an exact public record, shows its stored wording and original metadata, links back to that precise park-page article, and offers an editable GitHub issue draft. The draft includes public identity, source links and original clocks, using the canonical hosted park URL even in local previews. It excludes full excerpts, visitor trip choices, extra query values, preview addresses and private records. Source selection rejects unknown, removed, malformed and ambiguous references without reflecting query text; general reporting remains available, including without JavaScript. Provider-supplied notice links retain their attribution, and absent links or update times stay explicit. No issue is submitted automatically.

Correction-route source and GitHub destinations explicitly suppress referrers. The source panel wraps at mobile width and has doubled-text coverage. A review finding also corrected the no-JavaScript keyboard assertion to choose visible focus stops; the native Tab check remains intact. Public source data and all clocks are unchanged.

The correction helper first reproduced ten expected failures, then an additional malformed-encoding regression; all **11 focused tests** pass. Both generated regressions first failed for missing source links/catalog. Fresh local verification passed **248 Node + 48 generated-site tests = 296 tests**, strict changed-file TypeScript, zero Astro diagnostics and both 14-page builds. Independent review closed the referrer/focus findings, and an additional built-output audit matched all 23 public sources and their exact metadata/draft fields under both hosting bases. Five new root browser cases and one project-path case are registered (**93 root + 9 project-path cases**). Local Chromium remains unavailable on Ubuntu 26.04, separate browser inspection timed out and is not counted as verification, and no Python behavior changed.

Implementation head `aaf918be7e4d5ddb946123d85a4ecd92a24def17` passed **248 Node + 432 Python + 48 generated-site = 728 non-browser tests**, zero Astro diagnostics and both builds in [Verify pilot #185](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36910534598), job `110531767541`. All five new correction browser cases passed, including mocked referrer suppression, no-JavaScript fallback and selected-context mobile/doubled-text checks. The root suite passed **90 of 93 cases**: three existing source assertions assumed an article had only one link and became ambiguous when correction links were added. They now select the exact official/provider link by its accessible name; missing provider destinations still require zero provider links. Project-path execution and the post-suite screenshot-preservation check were skipped after the root failure; artifact upload still ran. Supported CI must verify the repaired head before review readiness.

The preceding print implementation head `a4982545afb12fcd531abf4b5476c4e96884c846` passed [Verify pilot #184](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36906078974), job `110516838729`: **237 Node + 432 Python + 44 generated-site + 96 Chromium = 809 tests**, zero Astro diagnostics, both 14-page builds and all three retained accessibility screenshots. That exact-head result verifies the print and trip/evidence changes below, before the correction increment.

### Verified print and trip changes in PR #6

Every park checklist has a **Print / save this page** action using the browser print dialog. Both the action and native `beforeprint` refresh trip guidance, alert/history age and checklist progress. Silently changed trip details clear old checks before the dialog; unchanged choices preserve the visitor's self-reported checks. Printing never submits the first entry check or completes a checklist item. A print-only page-copy timestamp is explicitly separate from source-check/review clocks. Source metadata and original clocks are untouched.

Park print styles include wrapped HTTPS destinations, a single column of all seven official planning checks and preserved review/check timestamps. Long panels can paginate; individual source items, history changes, checklist rows and planning cards avoid splitting where possible. A printed-copy notice explains the limits of stored guidance and self-reported checks, and asks the visitor to recheck official sources before travel. Native browser-menu printing works with static content without JavaScript; the copy discloses that freshness was not recalculated and its page-copy time is unrecorded. Evidence disclosures retain their current open/closed state. No application storage or transmission is added.

Five new actual-script print regressions first produced **five expected failures**, then passed with all **22 focused trip/source-return tests**. Print-era local verification passed **237 Node + 44 generated-site tests = 281 tests**, strict changed-file TypeScript, zero Astro diagnostics and both 14-page builds. Independent review passed 60 focused tests and found no remaining implementation issue. Four root print-media cases and one project-path case subsequently passed in Verify pilot #184. These print-media checks do not establish every platform's print dialog or pagination behavior.

Implementation head `fc3a62c512e95b1a0d8fc92725d85966041a5656` passed all **713 non-browser tests**, zero Astro diagnostics and both builds in [Verify pilot #183](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36904682029), then passed **86 of 88 root browser cases**. The new print checks exposed a real CSS specificity clash: `.button` kept actions visible despite the lower-specificity print `button` rule. Park-scoped print selectors now hide buttons and the checklist action row; the regression also checks the entry-check button. The no-JavaScript text query failed because Playwright's text engine intentionally skips `noscript`; direct paragraph selectors now verify the same visible fallback and freshness copy. Project-path execution and the post-suite screenshot-preservation check were skipped after the root failure; artifact upload still ran. Independent review verified both repairs, and Verify pilot #184 passed them.

Separate Chrome UI inspection of the built preview passed at 1280px and 360px: actions fit/wrapped without overflow, the print-only notice stayed hidden, keyboard focus was visible, and a changed date cleared the self-reported checks. No browser warnings or errors appeared. This screen inspection did not open the native print dialog or verify printed PDF pagination.

The preceding exact head `043ff6688f8525fa6c206a19ca5a948f9b6f9748` passed [Verify pilot #182](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36900811477): **232 Node + 432 Python + 44 generated-site + 91 Chromium = 799 tests**, zero Astro diagnostics, both 14-page builds and retained accessibility screenshots. That result verifies trip-return reconciliation, exact evidence navigation and coverage/history page-return freshness before printing was added. It also closes the earlier rendered-text assertion failure from Verify pilot #181.

Browser-restored date, time, area and special-case controls reconcile after `pageshow`. Changed selections clear the old checklist and refresh an already submitted decision; unchanged persisted returns preserve checks and derive progress, while fresh loads clear browser-restored checks. Minute/visibility refreshes and submission detect silent selection changes. Decisions link to the uniquely matched stored rule even when wording is identical; stale matches remain historical with a fresh-review label, and unmatched/conflicting choices link to general guidance. Coverage and history refresh each source's age immediately on return. Unchanged decision/progress text avoids repeated live-region writes. Synthetic return scenarios establish event ordering, not every browser's restoration policy or screen-reader behavior.

Independent review passed the correction assertion repairs; missing notice destinations require zero links other than the explicit correction link. Verify pilot #186 subsequently confirmed the repaired head. The live release and original public source clocks remain the baseline below. No collection, promotion, private checkpoint, merge or deployment was performed for that correction increment.

### Approved PR #5 release baseline

The owner explicitly approved merging and deploying [PR #5](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/5); it is integrated and live at verified commit **`696f95868568198ef61f428ee53f765731879983`**. The approved PR head `43f75bd1306d3a70c5989a607c829b0759b208f9` and merge have the same tree. Exact default-branch [Verify pilot #178](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36889139145) passed **777 tests**, zero Astro diagnostics, both 14-page builds and all three retained accessibility screenshots. [Deployment #4](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36890126850) published that existing artifact and verified **21 public files and 14 pages in one attempt** at **2026-10-01T16:12:12.182Z**. Detailed artifact and rollback receipts are below.

The published update includes accurate hosted-pilot copy, restored directory filtering/counts, quieter trip/count announcements, private storage-boundary repairs and provider URL normalization fixes. Public data remains snapshot **`pilot-08efc3ad8281`**, with the original guidance and alert clocks. Alerts are stale under the four-hour rule; no source collection or data promotion was performed for this code release. Noindex, ad-free status and manual operations remain in force.

Use the existing private collection/review/backup and paired-promotion runbooks for separately authorized source updates. A development or documentation handoff does not publish a different artifact.

### PR #5 implementation evidence before integration

The final development increment fixed false read-only preflight success for percent-encoded credential-like query/fragment text. The collector now decodes that text once before its existing sensitive-pattern check, matching archive validation. Diagnostic mode reports `source_query_sensitive`; ordinary quarantine retains its generic review error, prior accepted evidence and success clock while advancing only the attempt clock. Safe encoded URL bytes and hashes remain unchanged. Staging already quarantined archive-invalid candidates safely; its fallback is unchanged.

Two new Python test methods first produced **18 expected failing subcases** (12 collector, six preflight). All **87 focused tests** then passed across collector, preflight, staging and history validation. Six disposable external staging probes checked 30 JSON files: rejected URL/body markers were absent and accepted evidence/success clocks were preserved. Independent review found no actionable issues after 16 focused tests and in-memory probes of 3,180 sensitive encodings, safe/nullable URLs, partial-feed retention and sanitized five-park reports.

Fresh local verification passed **217 Node + 432 Python tests = 649 tests** and diff formatting. No TypeScript or website behavior changed in that final increment. Exact PR head `43f75bd1306d3a70c5989a607c829b0759b208f9` then passed [Verify pilot #177](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36887835566) with **777 tests**, both builds, zero Astro diagnostics and screenshot retention. The preceding head `bc6806c21c0ead37e46d782c2f2d8378910f4ab8` passed [Verify pilot #176](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36820431631) with 775 tests; that result precedes the query/fragment repair.

The release review found no regression in public data/clocks, hosting workflows, readiness logic, the light theme or indexing/ad safeguards. Pages still requires a successful default-branch push artifact; PR verification cannot be deployed directly. Existing alert observations remain at `2026-10-01T00:20:43.666438Z`, beyond the four-hour freshness window at review time. A code release must preserve stale labels and must not claim refreshed source evidence or newly cleared freshness/provider gates. Integration and deployment remain deliberate operator actions under `docs/PAGES_RELEASE.md`.

The preceding increment repairs Python collection/archive validation of safe provider directory URLs ending in one slash, matching the existing TypeScript contract. Validation only adjusts the decoded-path comparison; accepted URL bytes and normalized-record hashes are retained. Decoded leading `//`, repeated separators, traversal and backslashes remain refused. `parkCode` remains authoritative, and nullable, shared NPS and safe external links retain their existing contracts.

Six Python regressions cover accepted root/directory/query/fragment URLs, exact hashes and unchanged clocks, archive validation and staged quarantine retention. They first reproduced 22 failing subcases and then passed all 73 focused tests. Four cross-language regressions run actual synthetic collection/staging, immutable evidence and fresh archive replay through snapshot/history/preview and in-memory promotion validation. Unchanged/edited URL history and failed/quarantined attempt clocks are checked; rehashed unsafe counterparts still refuse. The exporter uses disposable external storage, blocks network access and preserves synthetic labels; the preparer refuses those labels before separately testing a simulated envelope. No real approval or publication is established.

Fresh local verification passed **217 Node + 430 Python + 44 generated-site tests = 691 tests**, strict changed-file TypeScript, zero Astro diagnostics and both 14-page builds. Independent review found no actionable issues; its read-only Python/Node probe checked 3,613 decoded-path variants without acceptance mismatches, confirmed external fixture cleanup and retained nullable/external/shared/cross-park/root-link behavior. Exact implementation head `c52fd069eaae16af0338cc388483f6a0ae3f1511` passed [Verify pilot #175](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36820077143): **775 tests**, including **79 root + 5 project-path Chromium tests**, both builds, zero Astro diagnostics and all three retained accessibility screenshots. Artifact `pilot-verification` is `11143755030`, digest `sha256:1bd3a1c56ae6a12d14e72ca6fcf58401c16fa036f567081463c0d8069e1c884a`, retained through **October 8, 2026 at 05:32:38 UTC**. The following handoff-only commit preserves this implementation; check its current-head CI before integration. Local browser execution remains unavailable on Ubuntu 26.04.

The preceding directory increment synchronizes directory cards, result counts and empty-state text with prefilled/restored search and state controls. Initialization and input/change events update immediately; page-return handling queues the update after `pageshow` because persisted form restoration can follow the event. Unchanged result counts do not rewrite live-region text. Seven tests execute the actual script with synthetic controls and queued tasks; two root browser cases and one project-path case cover both directory routes and restoration ordering. The application adds no persistence or transmission of selections.

The shared POSIX editorial file guard now checks canonical containment after its existing raw-path, lexical checkout and symlink checks. Doubled-leading-slash checkout/ancestor aliases refuse before private JSON or ledger access. External aliases retain owner-only JSON, SQLite ledger, backup/restore and preview operations. Error ordering, permissions and single-link requirements remain unchanged; no retained real storage is read, migrated or repaired by this increment.

The preceding local verification passed **213 Node + 424 Python + 44 generated-site tests = 681 tests**, strict changed-file TypeScript, zero Astro diagnostics and both 14-page builds. Directory regressions first produced five expected failures; the later event-order regression failed before the queued correction. Five new editorial path tests produced ten expected failing subcases before canonical checking. Independent review reran all seven directory and five path regressions, external alias backup/restore/preview and refusal-order probes, with no remaining findings. Exact implementation head `3f0c7daa2f476b8501c062a33414a2bc922657af` passed [Verify pilot #173](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36818355841): **765 tests**, including **79 root + 5 project-path Chromium tests**, both builds and all three retained accessibility screenshots. All three new directory browser cases passed. The following handoff-only head `1656bb254e01267bf9fd319081ab37df3296c7c0` passed the same 765 tests in [Verify pilot #174](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36818638591). Those results precede the directory-URL repair. The browser cases emulate event-order restoration and do not establish every browser's restoration policy or screen-reader behavior.

The preceding repair requires absolute private alert archive/staging destinations outside the entire checkout and its ancestors. One shared guard rejects raw traversal and symlink ancestry, then checks canonical containment before storage operations or collection requests. Relative roots, ignored/unlisted checkout folders and Linux doubled-leading-slash checkout aliases are refused. The active runbooks use external absolute paths; old stores are not automatically read, moved, deleted or repaired. Owner-only WSL setup and backup remain separate operator responsibilities.

Trip decisions now replace live-region text only when the displayed result changes. Minute/visibility refreshes still recalculate freshness, including the exact seven-day expiry, and trip edits still reset the checklist. Two tests execute the actual script with synthetic page/clock inputs; a new browser regression observes actual decision-text mutations.

Before the current increment, final PR head `45b3b300072162a130cb9c2993a38c3b6cf4745c` passed [Verify pilot #172](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36816742832): **206 Node + 419 Python + 44 generated-site + 81 Chromium tests = 750 tests**, both 14-page builds, zero Astro diagnostics and all three retained accessibility screenshots. That earlier result does not verify the new directory/editorial changes.

The preceding repairs in this PR corrected informational pages to describe reviewed manual alert/history updates, the four-hour alert freshness window, unscheduled collection and the actual GitHub Pages host. The obsolete claims that no public alerts/history exist or hosting awaits launch are removed.

Generated-site and browser checks follow the current paired history instead of assuming five first baselines forever. Exact metadata, observation clocks/order, visible counts, conditional baseline explanations and omission disclosures remain checked. A real Astro component regression accepts the existing later, bounded, failed and uncollected synthetic histories and rejects corrupted clocks/counts/disclosures. Public release verification still requires the successful public pilot snapshots under the existing release contract; truthful degraded fixture rendering does not clear release eligibility.

Browser scenarios now use a reference after every known review, attempted-check and successful-check timestamp, preserving each park's independent freshness. Annual guidance scenarios use their selected review clocks separately from alert refreshes. Seven synthetic regressions cover alert-only updates after guidance expiry, partial refreshes, later failed attempts, nullable successes and invalid clocks. Before the latest repair, head `0233d696502247808c3a75ce230d9d1cb0e4af5d` passed [Verify pilot #170](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36814213525): **204 Node + 415 Python + 44 generated-site + 80 Chromium tests = 743 tests**, both 14-page builds, zero Astro diagnostics and retention of all three accessibility screenshots. That earlier result does not verify the new destination and trip-result changes.

These development increments preceded the separately approved merge and deployment described above. Public data and its original clocks remain unchanged. Future data updates continue through the private collection/review/backup and paired-promotion runbooks; indexing, advertising and recurring operations retain their separate operator decisions. PR artifacts remain ineligible for default-branch Pages releases.

## PR #5 publication receipt (historical)

**Previous live pilot:** [ParkReadiness](https://vasuki8.github.io/us-national-park-trip-readiness-tracker/) previously served verified commit **`696f95868568198ef61f428ee53f765731879983`**, integrated by [PR #5](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/5). Its public data retained the owner-approved promotion from [PR #4](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/4): six reviewed guidance records and **17 retained notices** (Yosemite 1, Rocky Mountain 0, Yellowstone 5, Zion 7, Grand Canyon 4), with one paired baseline per park. The alert observation time remains **2026-10-01T00:20:43.666438Z**; guidance review time is **2026-10-01T01:18:28.701Z**. Unknown publisher-update and publication timestamps remain null. Deployment reused the verified artifact without rewriting its manifest or source clocks. The current PR #6 publication receipt at the top takes precedence.

Exact main [Verify pilot #178](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36889139145), job `110459996129`, passed **217 Node + 432 Python + 44 generated-site + 84 Chromium tests = 777 tests**, zero Astro diagnostics, both 14-page builds and screenshot retention. Artifact `pilot-verification` is **11175802108**, digest `sha256:9ad38ae23779557f910431e0679d3a9023c3d4de607a0e80c5f4c87f7278a1a6`, retained through **October 8, 2026 at 16:08:34 UTC**. Independent release audit confirmed the approved and merged trees match, release/data safeguards are unchanged, and this artifact's digest matches the one downloaded by the deployment workflow.

[Deployment #4](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36890126850), job `110463348634`, passed all gates and hosted-byte checks. The retained report ZIP was separately read in memory after verifying its digest and one-file layout: `passed: true`, snapshot `pilot-08efc3ad8281`, **21 files / 14 pages / one attempt**, checked at **2026-10-01T16:12:12.182Z**. Report artifact **11175394567** has digest `sha256:7e9d414c09b03ffc3c56cef381f9b3e10759b804f532c6c7e7493f27fb5aa0a8` and expires **October 8, 2026 at 16:12:14 UTC**. Observed X-Robots-Tag, CSP, nosniff and referrer-policy headers remain null; meta noindex remains the established safeguard. This report is retained by public GitHub Actions, with no claim of a new private recovery checkpoint or renewed provider/freshness approval.

Actual live-browser checks completed at **2026-10-01T16:18:13Z**: all 14 pages loaded with light styling and `noindex, nofollow`; exact five-park notice counts, six guidance review clocks, three missing-link notes and stale alert/history warnings remained intact. Both directories passed search, state filtering, empty states and real back-return synchronization with the browser's actual restored controls. Breadcrumb/footer/history-fragment navigation, Rocky Mountain's 2026 guidance and 2027 guard, checklist toggle/reset and trip-edit reset passed. No console warnings/errors were captured. The browser client blocked navigation to `build.json`; exact commit/snapshot identity is established by the separately verified hosted-byte report. External provider availability, forced cross-browser restoration policies and screen-reader behavior were not tested.

The **previous live commit `303475e260c93f2207e03e08945363cc3ac85882` remains an eligible rollback candidate**. It passed [Verify pilot #167](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36807575240): **196 Node + 415 Python + 42 generated-site + 80 Chromium tests = 733 tests**, zero Astro diagnostics, both 14-page builds and screenshot retention. Artifact `pilot-verification` is **11137734399**, digest `sha256:efd5c2ef60e6082ebb3aafaed53ee0d777ec1b4339245b3f6835e9f6128e8910`, retained through **October 8, 2026 at 02:51:50 UTC**. Its availability and exact main/run/SHA binding were freshly checked. No new rollback drill was performed for this code update.

Pages is configured for the manual Actions workflow with HTTPS enforced. [Initial deployment #1](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36807897705), [rollback #2](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36808071466) to older verified main `df1789da5d634c28ad16329e1f828a042b336a59`, and [restoration #3](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36808199666) all passed. Each report matched **21 public files and 14 pages in one attempt**, excluding `_headers`. Actual browser checks after restoration passed all 14 pages, five populated park baselines, exact notice counts/clocks, missing-link notes, search/navigation, the unsupported-year guard and checklist toggle/reset. All pages retain `noindex, nofollow`. Observed `X-Robots-Tag`, CSP, nosniff and referrer-policy response headers were null; `_headers` is not counted as an applied GitHub Pages policy, and project robots does not establish domain-root crawler policy.

At the original launch, public guidance matched the explicitly reviewed private ledger, and the verified separately recovered backup matched its head. A read-only provider preflight at **2026-10-01T02:32:53–55Z** passed all five parks. That launch's provider/freshness and hosting/rollback evidence was separately assessed and retained with the owner-authorized launch receipts in private storage. The conservative readiness CLI still reports those external checks as `not_checked`, because it does not ingest such receipts; no validator or gate was changed to manufacture a pass. Indexing and ads remain disabled.

**Next milestone:** continue on `main` with deliberate private collection/review/backup and paired public-data promotions when updates are needed. There is **no scheduled collection or automatic deployment**. Alert freshness expires after four hours; guidance review expires after seven days. Preserve original evidence clocks and the existing stale/empty-feed limitations. Indexing, ads and recurring operations require their separate operator decisions. Reuse `docs/DURABLE_COLLECTION_SESSION.md` and `docs/PAGES_RELEASE.md`; artifact rollback currently has seven-day retention. The notes below are historical and do not override this handoff.

### Earlier implementation evidence

**Current increment:** the private alert preview now matches the public pages when NPS provides no notice URL: it shows an explicit missing-link note without an anchor or invented destination. Supplied links use the provider-supplied label and the existing no-referrer policy. The preview snapshot type now admits `null`, matching the validated data contract. The real synthetic exporter includes a nullable current URL, and the existing browser scenario covers missing and supplied links. An actual build/browser regression failed before the fix (no missing-link note and one unusable anchor) and passed afterward. All **195 Node tests**, **22 focused Python preview tests**, strict TypeScript and Astro check with zero diagnostics pass. Independent review found no remaining issues. Code head `65f1aac3324021334f4b2fac92883c2bb891f791` then passed [Verify pilot #163](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36804169524): **728 tests**, including both Chromium suites, both 14-page builds and screenshot retention. The following handoff change records that exact code result; it performs no public-data application or release.

The preceding external-workspace code head `b4099d4e2515054283f6a9308c8f3424366aa472` passed [Verify pilot #162](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36802453288): **195 Node + 415 Python + 40 generated-site + 78 Chromium tests = 728 total**, both 14-page builds, zero Astro diagnostics and retained accessibility screenshots. A read-only GitHub check confirmed Pages is not configured. The release workflow audit found no code blocker; follow `docs/PAGES_RELEASE.md` for deliberate configuration, eligible default-branch artifacts, deployment and rollback verification after approved public data is integrated. Public data, hosting settings, indexing and ads are unchanged by this preview correction.

**Latest development handoff:** `scripts/build-preview.ts` now requires `--workspace-parent` pointing to an existing owner-only directory outside the checkout. It validates private input/workspace permissions and links, builds with private creation permissions, and verifies the complete bounded output tree before marking or serving it ready. Astro runs from that private workspace with a pinned source root and bundled prerender dependencies, so cross-filesystem builds keep candidate intermediates outside the checkout. The synthetic browser harness owns and cleans up its external input/build directories. Operator commands and migration details are in `docs/PREVIEW_BUNDLES.md`.

Fresh external-workspace WSL verification passed **195 Node + 415 Python + 40 generated-site tests = 650 local tests**, strict standalone TypeScript, zero Astro diagnostics and both 14-page production builds. An actual synthetic preview build and loopback HTTP check passed. Independent review passed the 19 focused Node tests and additional permission/link/size probes, with no Critical, Important or Minor findings. Astro's in-checkout generated helpers contain source/type metadata and the loopback server lock only, with no candidate data or private paths. CI #162 subsequently confirmed both Chromium suites for that code head as recorded above. Detailed current operator review, backup and candidate receipts remain exclusively in private storage; follow that handoff for the next deliberate promotion action.

Repository: [Vasuki8/us-national-park-trip-readiness-tracker](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker). **`main`** remains the integrated baseline; continue the proposed launch tooling on **`codex/prepare-live-pilot`**. [PR #2](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/2) is merged at `467ecbe6ddd695132d3e779215554f9852028b53`, preserving all reviewed safeguards and the previously merged [PR #3](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/3) manual NPS-preflight repair. PR #1 is already merged. The branch audit found no unique unpublished code in the nine older local development branches: their complete trees match existing main-history snapshots. The remote foundation branch is already an ancestor of main; the separate preflight branch has the exact content already integrated by PR #3.

Fresh independent review found one footer-notice bypass: `<plaintext hidden />` could pass the source check while Astro expanded it to terminal hidden text consuming the following footer in browsers. The recognizer now explicitly refuses plaintext regardless of parser version. The regression failed before the fix and passed afterward. The correction published as `560e87d1f3d0932b0204e01854bf2897f8266551` has the same tree as local commit `06cf50ed7d4288e61b0de92557dfd7bef738d88e`; the merge tree `05f195189751559552569658626bf83cd2b2686f` was checked against the reviewed current-main/PR candidate. No Critical, Important or Minor review findings remain.

Local consolidation checks passed **399 Python tests**, including all **23 source-rights tests on Python 3.12.3 and 3.12.14**. Before the narrow correction, the combined current-main/PR checkout also passed **158 Node tests**, **40 generated-site tests**, Astro check with zero diagnostics, and both 14-page builds. Independent review reran the focused rights/path/workflow checks and all eight live-verifier Node cases. The prior PR head passed [Verify pilot #150](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36736074852) with 674 tests and retained screenshots.

The exact merged main commit `467ecbe6ddd695132d3e779215554f9852028b53` passed [Verify pilot](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36759197048), job `110037100043`: **158 Node + 399 Python + 40 generated-site + 78 Chromium tests = 675 total**, zero Astro diagnostics, both 14-page builds and screenshot retention. Artifact `pilot-verification` is `11118285148`, digest `sha256:89e5db7cd20e2a2e6548b56daaf19d115995eb342444ffd7352234a447b3e6da`, retained through October 7, 2026. That result covers the merged implementation. The reviewed tooling below is committed on **`codex/prepare-live-pilot`**, based on current local/remote main `df1789da5d634c28ad16329e1f828a042b336a59`, in [draft PR #4](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/4). The repaired implementation head passed all 723 supported-Linux CI tests including both browser suites; no independent review findings remain. Continue with deliberate human source review and reconciliation under the private operator runbook. Main integration and deployment have not occurred.

The local setup and clone/ZIP instructions are in `README.md`; `AGENTS.md` supplies concise project instructions for Codex. Open the actual repository root, use Node.js 24 and Python 3.12+ with uv, run `npm ci` and `uv sync --frozen`, then `npm run dev`. Use a POSIX/WSL shell for the full tests and private evidence tools; on Windows keep private evidence in the WSL Linux filesystem. Ordinary tests use `umask 022`; the private operator runbook uses `umask 077` separately.

**Current proposed increment:** `scripts/prepare-alert-promotion.ts` extends the existing private preview flow with an offline, reviewable Git patch for the five public alert snapshots and their matching history. It reuses the strict bundle/history validators, binds the source bundle and all six public base-file hashes, and installs only an owner-only private patch outside the checkout. Default bounded-preview verification refuses synthetic input, rewinds, forks, missing public checkpoints, changed overlapping observations, cumulative-counter rewinds, altered retained records/clocks and unverifiable new changes. Complete new changes are replayed from the public record state. Exact retries compare raw bytes; invalid UTF-8 public input and unsafe paths/permissions are refused. It neither applies the patch nor approves or publishes data. Operator contract: `docs/ALERT_DATA_PROMOTION.md`.

The optional `--archive-dir` check now handles a public checkpoint outside the 20-observation window or new changes omitted from the bounded preview. The read-only `tracker.alert_promotion_archive` bridge replays each complete committed park chain, projects both exact checkpoints and binds the five-park bundle identity. It accepts an exact frozen prefix of a newer archive, while refusing changed/missing checkpoints and damaged later observations. The existing projection logic is shared after one verified chain read per park. Private archive permissions, disjoint destinations, bounded subprocess I/O and a narrow Python environment are enforced. Public omission counts and source clocks remain intact; archive verification establishes consistency, not human approval, source authenticity, backup or release readiness.

The same command now offers `--check --bundle PATH --patch PATH --candidate-id HASH`, with the original optional archive flag. It regenerates the exact candidate, checks the recorded preparation hash and raw patch bytes, and binds all six current public base files, including unchanged parks. The shared loader preserves bundle/pair/continuity checks; a bounded reader also protects existing-patch retries. Check mode creates no files, applies no patch and reports human review still required. Keep the checkout and private inputs unchanged between this point-in-time check and any separately authorized application. Explicitly supplying an empty archive path now refuses rather than silently falling back to bounded continuity.

**Latest repair:** upstream `tracker.preview.prepare_bundle()` now requires an absolute output outside the entire checkout and its ancestors, with an existing owner-only parent, owner-only output directory and single-link owner-only regular files. The old protected-folder list still allowed unlisted checkout destinations and did not reject readable directories or equal candidate files. The repair reuses the existing POSIX guards, validates retained output before creating its writer lock, creates only the final directory, and performs no chmod, relocation, replacement or cleanup of existing files. Relative `state/` and `.superpowers/` bundle output paths are deliberately refused; use the updated examples in `docs/PREVIEW_BUNDLES.md`. The synthetic browser harness now owns an external temporary input directory and removes it after the isolated build has copied the bundle.

Preview-boundary WSL verification passed **188 Node and 415 Python tests: 603 total**, strict standalone TypeScript checking and Astro check with zero diagnostics. Six new Python regression methods initially produced nine failures and one unsupported-platform error; all 22 focused preview tests now pass. The real exporter Node regression failed against the old in-checkout path and now passes with an owner-only external bundle. The actual synthetic Astro preview build and loopback HTTP probe passed: five parks, matching non-publication metadata, noindex, escaped source text, no pending sentinel, unchanged production bytes and removal of the temporary input. The probe server was then stopped. All new evidence uses disposable synthetic storage and establishes no real capture, review or durability.

Independent preview-boundary review passed all 22 focused Python and 6 Node tests plus probes for retained symlinks, subdirectories, FIFOs and unrelated hardlinks refusing before writer creation, checkout roots/ancestors refusing, and abandoned writer locks remaining untouched. No Critical, Important or Minor findings remain. Browser rendering, hostile concurrent mutation, physical durability and real operator approval remain outside this evidence.

The preceding check-mode increment passed all 29 focused promotion tests; independent review found no remaining findings. Four positive-path tests failed before check mode existed. Its unchanged-park regression demonstrates a stale six-file binding that `git apply --check` alone accepts, and the empty archive-option regression failed before the shared-loader fix. The preceding archive review also independently passed 20 Node and 47 Python tests plus probes for one chain read per park, ignored caller Python settings and damaged observations beyond a frozen candidate.

Launch preparation freshly passed **40 generated-site tests** and both 14-page production builds, alongside the latest 188 Node and 415 Python results (**643 local tests**), strict tool TypeScript and zero Astro diagnostics. Both browser suites remain unavailable locally: Playwright 1.58.2 refused Chromium installation on the available WSL Ubuntu 26.04 runtime (`ubuntu26.04-x64` unsupported). The successful synthetic preview startup probe is not browser-suite verification.

Code head `df9b6246e6a6e39a65103c65be038c689a6deb01` passed [Verify pilot #156](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36777128979), job `110097736722`: **188 Node + 415 Python + 40 generated-site + 78 Chromium tests = 721 total**, zero Astro diagnostics, both 14-page builds and retained root accessibility screenshots. Artifact `pilot-verification` is `11126002339`, digest `sha256:af02cb2b7dd95c187e0852d2d57ca73b7edb2f7d53c8d12414236cf647993fe1`, retained through October 7, 2026. This validates that earlier head; PR-only artifacts remain ineligible for the Pages release workflow.

Final combined review reproduced a bounded-continuity gap: after a successful fetch falls outside both 20-observation windows, an otherwise matching failed/quarantined descendant could rewrite that retained success clock. The repair explicitly binds the candidate clock to the newest new successful observation, or preserves the public clock (including null) if none exists. Two real synthetic `HistoryStore` fixture regressions failed before the guard: a rewound hidden success and an invented first success. All **31 focused preparer/check tests**, the **190-test full Node suite** and strict standalone tool TypeScript checking now pass. Independent combined review reproduced the original preparation/check bypass, reviewed the repair and found no remaining Critical, Important or Minor findings.

Repaired implementation head `c77410fc32bae99fa432abf9c5c698f3c3ae757f` passed [Verify pilot #157](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36778491249), job `110102330424`: **190 Node + 415 Python + 40 generated-site + 78 Chromium tests = 723 total**, zero Astro diagnostics, both production builds and screenshot retention. Artifact `pilot-verification` is `11126536959`, digest `sha256:dfa51182e752e0a521d9ff2c6b4272cc8d1d47b57021bce2fde97fd34c677351`, retained through October 7, 2026. This receipt changes only the handoff; inspect PR #4's current-head checks before integration. This PR artifact is not a default-branch release artifact or evidence of a live website.

Local credential and private operator storage setup are complete. The owner confirmed that the existing NPS key is already configured in GitHub secrets and variables; no new registration is needed. The existing workflow consumes the repository Actions secret named exactly `NPS_API_KEY`, and its five-park keyed preflight already passed as recorded in `docs/NPS_PREFLIGHT.md`. The owner then saved that key privately in WSL. A read-only local check confirmed a regular single-link owner-only file, an owner-only parent with no symlink ancestry, and successful loading into `NPS_API_KEY`; it reported only booleans and made no provider requests. Future operator processes must load the saved file privately; an export in another terminal is not inherited automatically. No key value was printed or added to the repository.

The owner selected a dedicated private GitHub repository for the remote backup. The operator procedure in docs/GITHUB_PRIVATE_BACKUP.md reuses the existing backup/verify/restore tools, requires verified selected checkpoints and a fresh authenticated download/recovery rehearsal, and excludes credentials and public CI artifacts. Local working, transfer and recovery paths retain the existing owner-only POSIX requirements. A local clone is a transfer workspace rather than an independent remote copy. The procedure does not claim client-side encryption or indefinite retention.

Detailed operator handoffs and recovery receipts remain in private storage outside the website checkout. Keep real capture inventories, checkpoint IDs, source-context review state, recovery locations and approval records there. Read the current private handoff for the next operator action; do not copy it into public documentation or a PR description.

The subsequent handoff-only head `38fa6159bd0fc5c70b80a80ef6cbbf05a51fe565` also passed [Verify pilot #158](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36779024069), job `110104121310`, including both browser suites and artifact/screenshot retention. The present operator handoff changes documentation only; implementation and public data remain unchanged.

**The website is still unpublished.** Public data remains unchanged, including the five never_checked alert snapshots. Deliberate source-context review, matching public guidance, reviewed alert promotion and live hosting/rollback checks remain prerequisites. Use the existing readiness command with the current private ledger and downloaded verified backup; retain its operator report privately. No reconciliation, public-data application, deployment, indexing or advertising is performed by this documentation change.

The next priorities for local development are:

1. Follow the current private operator handoff and docs/DURABLE_COLLECTION_SESSION.md. Inspect the complete retained source packets, prepare any corrected guidance inventory with the actual review time, and reconcile only explicitly approved sources using docs/GUIDANCE_RECONCILIATION.md. Refresh packets if the ledger changes. Each new ledger head needs its own verified checkpoint and remote recovery check.
2. Follow docs/ALERT_DATA_PROMOTION.md to review the exact private alert candidate and matching preview, then obtain deliberate public-data application authorization. Retain the reviewed candidate ID and rerun its read-only check immediately before application; refresh collection/candidates when evidence ages or inputs change. Public guidance must separately match the approved private inventory. Keep every private evidence file outside the repository and public outputs. Do not reset history or bypass a refused check.
3. After clearing the required data/trust gates, obtain two eligible successful default-branch artifacts, configure Pages for Actions, and follow `docs/PAGES_RELEASE.md` for explicit deployment, live verification and a deliberate rollback/restoration drill. The expected project URL is not yet a verified live website.

## Historical implementation record

The following notes preserve the implementation evidence and operational details from earlier increments. Branch names, draft-PR states and environment limitations below describe their recorded point in time; the current main handoff above supersedes them.

**Private entry capture now offers an offline setup check before the explicit live run. Release readiness binds public guidance to the reviewed private inventory, source-specific approval hashes and per-source reconciliation provenance, with separate pilot/indexed/advertising targets. Private five-park staging, ledger backup/verify/restore and live capture → reviewer-packet paths remain available. No real durable NPS capture, real ledger backup, or real context approval was performed in this development environment. Public guidance and alert data remain unchanged.**

**The private alert staging, archive-import and candidate-bundle destination guards now also protect `dist-pages/` and its descendants, matching the existing protection for `dist/`. This increment repairs the private/public file boundary introduced by the project-path build. It does not perform real source collection, human review, backup or deployment.**

Repository: `Vasuki8/us-national-park-trip-readiness-tracker`.  
Continuation branch: `fix/protect-pages-private-data`, based on `main` at `25495bdf28d2ab31ddb3198acafca1ffd7d40240`. PR #1 was automatically marked merged after the earlier pilot fast-forward update. No Pages release workflow was dispatched.

## Completed: verify the actual hosted Pages release and rollback

The next development priority is making the five-park pilot live. The existing manual Pages workflow previously stopped after GitHub accepted a deployment. It now checks the actual returned URL against the exact selected verified artifact, for both deploy and rollback, and retains a separate success/failure report. Operator contract: `docs/PAGES_RELEASE.md`; implementation: `scripts/verify-pages-live.mjs`.

Every public regular file except the host configuration `_headers` is compared by SHA-256, including HTML at real directory URLs, scripts/styles, images, robots and the public build manifest. The manifest must match the requested commit and hosting base before network requests. Non-200 responses, redirects, stale/mismatched content, transport errors, unsafe URLs, symlinks and oversized artifacts/responses refuse verification. Three attempts allow brief hosting propagation; ten-second requests run within a two-minute network budget. The report includes commit/snapshot/base, mode, counts and observed home-page headers; absent headers remain null. Matching the verified bytes preserves its existing noindex metadata, but no project robots or custom `_headers` policy is inferred as a domain-wide HTTP control.

Verify pilot now retains the dependency-free verifier outside both static outputs. Pages still uploads only the selected static directory, installs no product dependencies, checks out no source and performs no rebuild or collection. Node setup occurs before deployment. A failed live check fails the job and retains `pages-live-verification.json`; it does not automatically reverse a completed deployment. An artifact predating the retained verifier fails layout validation before upload, so prepare at least two eligible post-change default-branch artifacts for an older-version rollback. PR-only runs remain ineligible; retention remains seven days.

Eight new Node test cases exercise root/project URLs, all file classes, deploy/rollback identity mismatches, HTTP errors/redirects/encoding, propagation retry, invalid URL/manifest inputs, symlinks, size bounds and redacted transport failures. Two new workflow contracts cover URL/artifact wiring, failure reporting and the verifier/public-upload boundary. The tests were observed failing before the new verifier/integration existed. All eight focused cases and **398 local Python tests** passed; independent review found no Critical/Important issues and independently passed eight Node cases plus 19 workflow tests. Network cases use synthetic responses and do not establish a real hosted-site check. The local full npm command still hit the known sandbox subprocess/I/O failures in `build-preview`, `entry-review-store`, `entry-source-extraction` and `preview-io`; full CI passed all Node tests below.

Implementation commit `fb600c53b4705ae6e4cf192017e5448e7003922a`, tree `653e4a165d47dfbecda66843e933fb8220b5d82d`, passed [Verify pilot #149](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36735262681), job `109955241867`:

- **158 Node, 398 Python, 40 generated-site and 78 Chromium tests: 674 total.**
- Astro check: 25 files, zero errors/warnings/hints; root/project builds: 14 HTML pages each.
- Root accessibility screenshot retention passed.
- Artifact `pilot-verification`: `11105954073`, digest `sha256:093b4e1d1f218d23110f03cdc05f38b7068d8f18d80121c7ea6bf89b331d776a`, expires October 7, 2026.

This handoff update follows completed implementation, independent review and successful full CI. Work remains proposed in [draft PR #2](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/2). No Pages workflow was dispatched and no real URL, rollback or source approval was verified. Public guidance/alerts remain unchanged; the pilot report remains **1 pass, 1 blocked, 3 not checked**, and indexing/ads remain disabled. A live-verification report alone does not promote any readiness gate.

### Next work toward launch

1. Complete the real owner-controlled capture, human context review and current-head backup/separate-copy session in `docs/DURABLE_COLLECTION_SESSION.md`. Durable destinations and a local NPS key have not been supplied here; the successful Actions API probe is not public-data publication.
2. Finish a deliberate reviewed public-data promotion path using the existing private archive/history projection, with a reviewable candidate and exact paired snapshots/history. The current projection and private preview do not authorize or perform publication. Keep private captures, ledger, packets, archives and backups outside the repository and hosted site. Preserve the existing collection/review/backup tools rather than rebuilding them.
3. Integrate reviewed launch code into the default branch, obtain successful default-branch push builds and retain two eligible artifacts. Configure GitHub Pages to use GitHub Actions and confirm the actual root/project URL. The expected free project URL is `https://vasuki8.github.io/us-national-park-trip-readiness-tracker/`, not a verified live URL.
4. Once the earlier data/trust gates are deliberately cleared, dispatch the existing manual release with the exact eligible commit/run and confirmation. Inspect the retained live report and browser behavior at that URL. Deliberately roll back to the older eligible artifact, verify it, restore the intended release and retain the reports before claiming hosting/rollback evidence. Review external evidence separately; the read-only readiness CLI still does not auto-accept a deployment receipt.

The preceding source-rights handoff commit `2bfcde4c1595c0fcdb369da5fb614d3a724a44e2` passed [Verify pilot #148](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36730398865), job `109938146513`: **664 tests**, zero Astro diagnostics and both 14-page builds. Artifact `11105186391`, digest `sha256:19ebaffee91e738a543eafa3b85760a7f782a062bfb17b5fefdd2d660ef132bc`, retained that prior verified state.

## Completed: validate guidance before source-rights coverage

The source-rights gate previously built a set of guidance ID/source pairs without first validating its input inventory. It could pass empty guidance with an empty manifest, collapse duplicate/conflicting IDs, accept an unofficial or wrong-park URL when the manifest matched it, or approve a reduced inventory missing a pilot source. These false passes were reproduced using disposable repository copies.

The three-line repair reuses the existing `_guidance_inventory` checker and requires nonempty coverage of every fixed pilot source before rights-manifest evaluation. Guidance must have unique valid IDs and exact park/source bindings. Invalid input returns `blocked` with `public_guidance_inventory_invalid`; a matching edited manifest cannot override it. Valid record/manifest reordering, rights metadata and manifest-policy checks, footer checks and report schema remain unchanged. Operator contract: `docs/RELEASE_READINESS.md`.

Six regression methods produced **20 failing cases** before the repair, covering empty inventories, identical/conflicting/cross-file IDs, nonofficial or mismatched bindings, each missing pilot source and all release targets. The order-preservation case remains accepted. All **22 source-rights tests**, the **396-test local Python suite**, data validation and diff checks passed. Independent read-only review found no issues and independently reran all 22 source-rights tests.

Repair commit `fea95b4d875773a144adffcbd159b79819f89007`, tree `c2afd236649dfbfb2ed63de382581f411fa3d359`, passed [Verify pilot #147](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36729360019), job `109934524323`:

- **150 Node, 396 Python, 40 generated-site and 78 Chromium tests: 664 total.**
- Astro check: 25 files, zero errors/warnings/hints.
- Root and GitHub project-path builds: 14 HTML pages each; screenshot retention passed.
- Artifact `pilot-verification`: `11104206230`, digest `sha256:98a341dccec41088b2a1964d3cc73a88cfc5686e2fb5ac128f29015c3ea1d6ac`, expires October 7, 2026.

This handoff was updated after the repair and full CI completed. Work remains proposed in [draft PR #2](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/2). The actual public inventory remains unchanged at six records and still passes its exact source-rights gate. The pilot remains blocked with required counts **1 pass, 1 blocked, 3 not checked**. No provider request, source approval, public-data publication, deployment, indexing or advertising occurred.

The next real trust milestone remains the owner-controlled session in `docs/DURABLE_COLLECTION_SESSION.md`: durable working/separate backup roots, five-source capture and human review, then private alert staging and reviewed publication. This environment still has no supplied durable destinations or local NPS key. The completed inventory and footer checks should be preserved rather than rebuilt; real capture/backup/review and hosting/rollback evidence remain separate gates.

## Completed: require the public footer notice in release checks

The source-rights gate previously accepted its required government-work notice as a substring anywhere in `Layout.astro`. Reproduction showed that an HTML comment, a hidden span or Astro frontmatter alone could keep the gate passing after the real footer notice was removed.

The gate now uses `tracker/source_notice.py` to recognize literal, unconditional text in one direct-body footer. Frontmatter, source-only contexts, inert/hidden content, dynamic/replacement ancestor attributes, conditional/component markup, default-hidden popovers and duplicate document elements cannot establish notice evidence. Complex or truncated Astro source anywhere is refused before HTML-like comments/strings/attribute expressions can invent a footer. The canonical layout, complete property lookups outside the footer, ordinary inline formatting, whitespace and HTML entities remain supported. Report schema/reasons are unchanged; every release target requires this gate. Operator contract: `docs/RELEASE_READINESS.md`.

Eleven new regression methods extend the source-rights suite from 5 to 16 methods. The initial tests produced **46 failures** against the old substring check. Independent review then reproduced JavaScript comment/template/attribute spoofing, hidden popovers and duplicate document markup; **11 additional failing cases** were reproduced before correcting those gaps. Explicit head/title and comparison-expression subcases also cover the same source-spoofing paths. The final local **390-test Python suite**, data validation and diff checks passed.

Independent follow-up review found no remaining Critical/Important findings and independently passed all 16 source-rights methods plus nine additional probes. Its optional browser probe could not run because bundled Chromium was absent and system Chromium hit a sandbox `setsockopt` denial. This is a conservative source recognizer, not an arbitrary Astro evaluator, computed-CSS visibility audit or proof of deployed output; unfamiliar layouts require review. CI supplies the normal build/browser verification below.

Repair commit `2e315071be82135ab3ae452163547bd7ea6f88c0`, tree `36eda55db035b8c1eb4d6aea64daa8b7fa3c31e0`, passed [Verify pilot #145](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36725117066), job `109919897288`:

- **150 Node, 390 Python, 40 generated-site and 78 Chromium tests: 658 total.**
- Astro check: 25 files, zero errors/warnings/hints.
- Root and GitHub project-path builds: 14 HTML pages each; screenshot retention passed.
- Artifact `pilot-verification`: `11102014924`, digest `sha256:31e60d93c76e04d97846219f991c784cd9f7e5ceb0eb2da34d1e02e0f4d60ca0`, expires October 7, 2026.

This handoff update follows the completed repair and successful full CI. Work remains proposed in [draft PR #2](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/2). The actual pilot is still blocked with required counts **1 pass, 1 blocked, 3 not checked**. Public guidance/alerts, provider credentials, source approvals, deployment, indexing and ads were unchanged.

The next real trust milestone is the owner-controlled capture/review/staging/backup session in `docs/DURABLE_COLLECTION_SESSION.md`. No durable working/backup roots or local NPS key have been supplied to this environment. Preserve the existing capture, ledger, reconciliation, backup and staging tools; do not substitute an ephemeral workspace or repository for the private evidence store. Real human review remains a separate action.

The footer repair's final handoff commit `82918b84b902231c2c99213220fa3a36d2b121c8` also passed [Verify pilot #146](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36725960947): **658 tests**, zero Astro diagnostics, both 14-page builds and screenshot retention. Artifact `pilot-verification`: `11104065177`, digest `sha256:33b24e3219d542fe4b4f7dd6ec9a6fe9d7fbc9ccdce708cf06e12a09bf128c64`.

## New: protect the project Pages output from private alert writes

The GitHub Pages build introduced the publishable `dist-pages/` directory, but the existing private staging, history CLI and preview-bundle destination lists still protected only `dist/`. A synthetic reproduction wrote seven private JSON files beneath a temporary project's `dist-pages/` while the reports still claimed no site-data writes. No real provider data or actual public output was used in that reproduction.

All three existing destination guards now include `dist-pages/`, including nested paths. Single-park and five-park live staging refuse before any provider request or file creation; history imports and private candidate exports refuse before archive/output writes. Allowed owner-controlled destinations and the existing ignored `state/` workflow are retained. No public guidance, snapshots, frontend code, package files or workflows changed.

Three new regression methods cover eight unsafe root/nested cases. All eight cases failed against the original code, then passed with the three-list repair. The 76 affected staging/history/preview tests and the complete **379-test Python suite** pass. Data validation and `git diff --check` also pass.

Independent read-only review found no Critical, Important or Minor findings. The reviewer reran 68 focused Python tests and two additional history-report checks, confirming that the shared history guard refuses before store access. No review changes were needed.

Local verification needs a normal `umask 022`: the cloud shell's `077` converted pre-existing tests' intentionally insecure `0755` fixtures into secure `0700` directories, producing five failures and one cascading error before that environment-only adjustment. The existing `npm test` attempt also encountered baseline local limitations in `build-preview.test.ts`, `entry-review-store.test.ts`, `entry-source-extraction.test.ts` and `preview-io.test.ts`; local Astro dependencies are absent and subprocess I/O differs from CI. The normal frontend/build/browser suite must be verified by the unchanged `Verify pilot` workflow on the proposed branch before integration. These local failures are not claimed as passing checks.

The proposed repair at `ab9c630197300761536f9bb6d44d8e441892c855` passed [Verify pilot #143](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36675415344): **150 Node, 379 Python, 40 generated-site and 78 Chromium tests (647 total)**, zero Astro diagnostics, root/project 14-page builds and screenshot retention. Artifact `pilot-verification` is `11079736068`, digest `sha256:81d7ee6a427f9a42856bd088aa8ac13776dbbe44894ab8b4209ef2cecd52a51a`. This resolves the local frontend/build/browser verification limitations for that exact code commit. The branch remains proposed in [draft PR #2](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/2).

The next real trust milestone remains the owner-controlled durable capture/review/staging/backup session described below. This repair clears no release gate and must not be treated as source review or authorization to publish.

## New: checked durable collection runbook

`docs/DURABLE_COLLECTION_SESSION.md` now joins the existing operator contracts into one first-session sequence: choose durable private working/separate backup roots, check offline setup, capture five entry sources, verify a backup and a second copy before human review, reconcile actual reviewed guidance, back up the new head, collect alerts privately, inspect recovery state and read release gates.

A disposable synthetic rehearsal exercised the real CLI setup/status/backup/verify/restore/readiness commands and the existing live operator with mocked transport. It produced five packets and six unresolved holds, verified both backup copies, restored the exact original ledger state, checked all five offline alert summaries without creating staging files and left public data byte-for-byte unchanged. The readiness report remained blocked. No real source requests, review approvals or durable-storage evidence were created. Temporary rehearsal files were discarded.

The current cloud environment has no local `NPS_API_KEY` and no supplied owner-controlled durable working/backup destination. The GitHub Actions secret is not a local credential. The real session still requires those storage choices and the owner's human review; the runbook does not clear a release gate.

The runbook commit `7d20ad06764b79222c55dc6918e3b909a0e508ef` passed [Verify pilot #144](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36720210942): 150 Node, 379 Python, 40 generated-site and 78 Chromium tests (**647 total**), zero Astro diagnostics, both 14-page builds and screenshot retention. Artifact `pilot-verification`: `11098955656`, digest `sha256:de6093dd1c8deb78a69997895f2e11c8647e446cd0bf327f02426d15691a439d`.

The local development commit `679fa089fdddb08c09e976c16afead4c5ecedb2f` was recreated through the connected GitHub app as `3fe0e878`; both commits have the identical tree `b0d120ccd6a353333f7cf244f8dd490c0b8612e4`. The `main` push passed Verify pilot #132, run `36651035959`, job `109684980194`: 148 Node, 328 Python, 18 generated-site, and 74 Chromium tests (**568 total**), Astro check with zero diagnostics, and a 14-page build. Artifact `pilot-verification` is `11070417444`. This integrates code only; it does not satisfy private review, public alert collection, hosting, indexing, or advertising gates.

## Standing product direction

The eventual product remains AdSense-first, light-theme and free of paid-data dependencies. Validate the five-park pilot before expanding to 20 parks. Trustworthy source evidence precedes indexing or advertising. Never infer an all-clear, reopening, permit exemption or annual validity from missing information.

The public build remains 14 HTML pages plus `build.json`, with park/state search, five park pages, date-aware entry guidance, source evidence, checklists, notice history and seven official planning links per park. Yosemite and Rocky Mountain have dated rules; Yellowstone, Zion and Grand Canyon retain undated source observations. Public alert snapshots remain `never_checked`; public histories and the public entry-review register remain empty.

Existing alert collection/archive/staging, candidate previews, visitor history, accessibility repairs, source-change gate, HTML extraction, live entry-page compatibility diagnostic and private review ledger remain in place. Do not rebuild them.

## New: offline private capture setup check

`tracker.entry_review_live --check-only` validates the existing private destination boundaries, replays an existing ledger, checks the expected empty/current head and loads the current guidance inputs. It creates no directories, makes no requests and writes no ledger, packet or public files. The schema-1 metadata report uses `mode: private_entry_capture_preflight` and `setup_validated: true`, with ledger revision/batch/pending-proposal counts, guidance-record count and five required sources. All side-effect flags are false; no source contents or private paths are printed. Exit `0` means setup checked, not guidance approved. Safe refusals exit `2` without a success report.

Live and offline checks share one setup path. Both private parent directories must already exist and be owner-only. The live command previously discovered a missing ledger parent only after requests, and could initialize under an insecure parent. It now refuses both cases before network. `--check-only` and `--live` are mutually exclusive; omitting both still refuses. Existing capture/packet and live exit-code semantics remain intact.

Seven new methods cover empty destinations without creation, real synthetic ledger replay with unchanged SQLite/packet bytes, unsafe destinations, stale/malformed heads, unreadable initial input, mode conflicts and live ledger-parent refusal before requests. The initial RED run produced **14 failing cases**; all **16 focused live-capture tests** now pass. The tests use synthetic captures; no real private storage or source review milestone was cleared.

This is a point-in-time path/head/input-availability check. It does not certify storage durability, backup, source truth, editorial approval, provider compatibility or later writes. Live capture repeats setup validation and the write transaction rechecks the head. The operator contract and example are in `docs/PERSISTENT_ENTRY_CAPTURE.md` and `README.md`.

Independent review found no Critical/Important issues and reran all 16 focused tests successfully. Local verification passed **376 Python, 150 Node and 40 generated-site tests**, zero Astro diagnostics and root/project 14-page builds. Node/site checks used working unrestricted local subprocess I/O. The final GitHub run provides browser checks. The actual pilot remains blocked with required counts **1 pass, 1 blocked, 3 not checked**; indexed/advertising counts remain **1/2/3** and **1/3/3**. This development increment does not perform the owner-controlled real capture, review, backup, alert publication or deployment.

The preceding reviewed-guidance increment on `main`, commit `d378081bc089d9d3d51884219b6c08df5f962ec7`, passed Verify pilot #141, run `36668506696`, job `109738265677`: **369 Python, 150 Node, 40 generated-site and 78 browser tests (637 total)**, zero Astro diagnostics, both 14-page builds and root screenshot retention. Artifact `pilot-verification` is `11077293008`, digest `sha256:b6b3771e35323997834256aa4f699828097aa3192fc1513ea4ad1125ab00dad3`.

## New: bind public guidance to reviewed private records

The durable-review gate previously passed with all five v2 source baselines and zero holds even when public guidance differed from the private reviewed records. It now requires a nonempty, unambiguous inventory; exactly one reviewed baseline per source with exact hashes of that source's private guidance; public/private full-record equality by stable ID; and reconciliation provenance for every current baseline. Summary, dates, exceptions, evidence, review and rights fields are all bound. Record and object-key order do not change identity.

Nine new methods cover changed private guidance, empty/missing/duplicate/extra inventories, absent/wrong/extra approval hashes, duplicate baselines, harmless ordering, safe report output, complete baseline provenance and real synthetic ledger → reconciliation → replay → CLI paths. Initial regressions reproduced **15 failing cases** against the old gate; an additional ordering test could not read the then-absent match evidence. All 29 focused readiness methods pass. The six-record, five-source integration fixture approves only synthetic context, retains approval provenance after a later matching observation, checks both matching and independently edited public JSON, and verifies the report leaves the public files and SQLite ledger unchanged. It is not a real human NPS review.

Independent review also reproduced an inherited provenance gap: four imported v2 baselines could be carried through one source's explicit reconciliation, producing five current v2 baselines and zero holds without reconciling the other four sources. A real synthetic seeded-ledger CLI regression reproduced that pass before the correction. The report now counts only exact current baselines created for sources selected from the preceding event's active register; carry-forward alone cannot satisfy the per-source gate. Full context/hash/timestamp mismatches also block. Seed/import behavior itself is unchanged. Approval provenance is within the replay-verified ledger, not an authentication of the reviewer or an independent check of their assertions.

The report adds only counts and nullable match booleans to the existing schema-2 gate, including `reconciled_v2_sources` separately from the metadata count `approved_v2_sources`. Private records, IDs, paths, context and hashes are not printed. The CLI still replays/verifies the ledger and verifies a supplied backup; direct Python callers must supply already verified evidence. The report never copies private guidance to public data. See `docs/RELEASE_READINESS.md`.

This closes a release-evidence mismatch; it does not clear the real private capture/review, backup, public alert-data or hosting gates. No public data or website activation changed.

Independent follow-up review found no Critical/Important issues and independently reran all 29 focused readiness tests successfully. Local verification passed **369 Python, 150 Node and 40 generated-site tests**, zero Astro diagnostics, and root/project 14-page builds. The Node and generated-site suites used working unrestricted local subprocess I/O; the final GitHub run supplies browser verification. Actual required counts remain pilot **1/1/3**, indexed **1/2/3**, advertising **1/3/3** (pass/blocked/not checked). All targets remain blocked.

The preceding local-link code commit `766f0c008e47c78db8b211106518325c6994ad64` passed Verify pilot #140, run `36665312536`, job `109728613056`: **150 Node, 360 Python, 40 generated-site and 78 browser tests (628 total)**, zero Astro diagnostics, both 14-page builds and retained root screenshots. Artifact `pilot-verification` is `11075238370`, digest `sha256:53d26c763dfab7a1588b5fa7f9253b3a8566a850a00fea04421e014426405e9f`.

## New: complete local static-link coverage

The generated-site gate now scans every emitted HTML page with a dependency-free Python HTML parser instead of the root-relative-only regex. It resolves local `href`/`src` URLs under the domain-root or GitHub project hosting base, including relative destinations, queries and percent-encoded names, and checks local HTML fragment IDs/named anchors. Escaped project paths, missing files and missing fragments fail the existing Node gate. External URLs are skipped without network requests.

Nine regression/characterization methods exercise the real Node gate against temporary outputs under both bases; a tenth exercises the real filesystem checker with older Python parser defaults. The initial six methods reproduced **24 failing subcases** against the old scan, including missed broken destinations/fragments, a newly emitted page and valid external URLs falsely treated as local. The text-element characterization checks that text contents do not supply links or fragment IDs, and an explicit raw/text parser guard preserves this behavior on older supported Python versions. Comments, scripts and inert template contents cannot satisfy a missing fragment; the template element itself retains its normal fragment identity. Both existing 14-page outputs passed the expanded scan with **209 local href/src URLs each**. This closes the earlier Pages review's deferred local-link coverage gap.

Independent review reproduced a trailing-slash normalization gap: regular files requested as directories could pass. Four new root/project cases failed before the fix; trailing-slash local URLs now require directory targets. The older-parser configuration regression also failed before the explicit text-element guard. Review also reproduced Unicode-whitespace URL trimming and suppression of a template element's own ID; six broken-path cases and two valid-template cases failed before those fixes. URL trimming now uses only ASCII C0/space and only template contents are inert.

The helper is a static test utility, not a full browser parser or external-link crawler. It refuses `<base>` elements and covers literal `href`/`src` plus local HTML fragments; `srcset`, CSS URLs, dynamic links and non-HTML fragments remain outside its stated scope. No public data, private source evidence, deployment, indexing or advertising changed. The real private capture/review and hosting gates remain unverified.

Final local verification passed **360 Python tests, 150 Node tests and 40 generated-site tests**, with zero Astro diagnostics and two 14-page builds. The restricted Node run reported subprocess failures in `entry-review-store.test.ts`, `entry-source-extraction.test.ts` and `preview-io.test.ts`; the unrestricted full `npm test` run passed all 150 tests with working subprocess output. Both existing site commands also passed with that access. GitHub CI provides the 78 browser checks and retained screenshot evidence for the published commit.

The preceding readiness handoff at `cf9f62c144fdf0186af0945e5b969b4020bbbdea` passed Verify pilot #139, run `36662854515`, job `109721147012`, including the root screenshot-retention guard. That result covers the **618-test** readiness-target increment.

## New: milestone-specific readiness targets

The report previously required advertising and indexing for a pilot release, contradicting the approved pilot's exclusion of active ads. `tracker.release_readiness` now defaults to `--target pilot` (ad-free and unindexed), with separate `indexed` and `advertising` targets. Durable source review, public alert data, a current verified backup, source rights and hosting/rollback remain required for all three.

All seven gate statuses/evidence remain visible. JSON schema 2 adds `release_target`, per-gate `required`/`required_reason`, and `required_summary`. `blocking` now means required and not passed for the selected target. The full `summary` remains unchanged. Detected ad integration always requires advertising review; removing any pilot indexing control requires indexing review. The report remains read-only.

The actual pilot remains **BLOCKED**, with required counts **1 pass, 1 blocked, 3 not checked**. The one explicit required blocker is uncollected public alerts; missing durable review, backup and live hosting/rollback evidence remain unverified. Disabled indexing and ads are later-target gates. No source/backup/hosting gate was cleared and no website, ads or indexing was activated. See `docs/RELEASE_READINESS.md` for schema migration and the target table.

Eleven additional test methods cover target scoping, a synthetic otherwise-ready ad-free pilot, every failed/unverified core gate, detected ads, partial/complete indexing-control removal, target validation, CLI labels/exit codes and input redaction. The initial regressions failed before implementation. Synthetic READY cases model external core proofs only inside tests; they are not real review approvals.

Independent review found an indexing bypass in the inherited substring checks: commenting out the actual meta tag, limiting robots to a named agent, or narrowing the header path still looked intact. Regressions reproduced that issue and related conditional/component/allow/scoped-header cases. The pilot guard now recognizes active literal head metadata, the canonical wildcard robots group without exceptions, and globally scoped unqualified noindex headers; unfamiliar configurations require review. All 20 focused readiness tests pass. The earlier static link test gap is closed by the increment above.

The final local Python suite passed **350 tests**. The current target reports remain blocked with required counts pilot **1/1/3**, indexed **1/2/3**, and advertising **1/3/3** (pass/blocked/not checked). The Pages code preceding this increment passed exact-head Verify pilot #137, run `36657771103`, at `a14b7430a25bfbb5995d4aecc7a6a902733f3753`, including the screenshot-retention guard; artifact `11073014127` retained both builds and root visual evidence.

The release-target code on `main`, commit `5f3a94a50c2f6f5d37bf02c4a7000f8bf36f7014`, passed Verify pilot #138, run `36662233981`, job `109719292377`: **150 Node, 350 Python, 40 generated-site and 78 Chromium tests, 618 total**, zero Astro diagnostics, and root/project 14-page builds. The screenshot-retention check also passed. Artifact `pilot-verification` is `11074687668`, digest `sha256:3febb905a15504d9fe4d9a5098f1cf0ffc0317d265b3252b2a15dcf758fc30df`. This verifies the report logic and guard regressions, not a real private approval or deployment.

## New: free GitHub project hosting support

The build supports both a domain root and `/us-national-park-trip-readiness-tracker/`. Internal page links, breadcrumbs, directory cards and current-page navigation include the configured Astro base; bundled scripts/styles use the same path. External NPS and fragment links retain their destinations.

CI verifies `dist/` and `dist-pages/` separately and retains both in `pilot-verification`. Each manifest records `base_path`; both outputs use the same public-data snapshot. The manual Pages workflow selects only the output matching the configured Pages path and requested commit, refusing missing or mismatched builds before upload. Older manifests lacking a path remain root-only candidates. Release still deploys an existing verified artifact without rebuilding.

This removes the custom-domain requirement from the code-side hosting path. It does not create a live website, verify rollback, clear private review/collection gates, or enable indexing/ads. See `docs/PAGES_RELEASE.md`.

Code commit `5751fc47218bc5c7f0062a706f38ad8b01be9ae1` passed Verify pilot #136, run `36657308469`, job `109704313944`: **150 Node, 339 Python, 40 generated-site checks (20 per output), and 78 Chromium tests (74 root + 4 project), 607 total**. Astro check returned zero diagnostics; each output built 14 pages. Artifact `pilot-verification` is `11072873775`. Browser behavior is now verified in GitHub CI; local Chromium download remained unavailable.

A follow-up separates the project suite's output into `test-results/pages` so its Playwright cleanup preserves the root suite's screenshots. A local synthetic evidence marker failed preservation before that setting and passed afterward, with the real project HTTP test executed both times. CI now requires all three root mobile/200% text screenshots to remain after the project run and before artifact upload. This is a verification-artifact repair; the generated site and release gates are unchanged.

Independent review found no Critical/Important issues. It separately audited 279 links/assets across all 14 pages per output, including fragment targets, with no missing files, escaped base paths or missing fragments; external destinations matched. The then-deferred query/fragment/relative URL test gap is now covered by the offline local-link gate described above.

## New: five-park private alert staging run

`uv run --frozen python -m tracker.stage collect --live --park all --staging-dir /absolute/private/alert-staging` now checks the existing archive/pending state for all five pilot parks before making a provider request, then collects them sequentially through the unchanged `StagingCollector` receipt and archive path. A pre-existing pending receipt, writer lock or non-advancing clock blocks the batch before network access. A race after precheck can still interrupt the run.

The report contains safe private archive summaries in pilot order. Exit `0` means all five attempts were archived successfully, exit `1` means all five were archived with at least one failed/quarantined check, and exit `2` means a precheck or later execution failed. An interrupted run can have earlier committed parks; the `checks` list reports only those completed commits. Inspect per-park `status` and use offline `recover` for pending receipts before deciding on a new live attempt. The batch is not atomic and does not publish, schedule, review or back up data. See `docs/STAGING_COLLECTION.md`.

Five focused synthetic tests cover successful five-park archival, preflight refusal before network, one provider failure with the remaining parks retained, interrupted partial progress and non-advancing clock refusal. Local verification: **328 Python tests, 148 Node tests, 18 generated-site tests**, Astro check with zero diagnostics, and a 14-page production build. The browser suite could not start its configured history-site web server locally (`astro preview` exited before becoming ready); browser verification requires the GitHub CI environment. No live batch was attempted and the public snapshots remain `never_checked`.

The follow-up `status --park all` reads the five existing per-park summaries without a key, network request, archive write or staging-directory creation. The JSON report preserves pilot order and the existing safe per-park fields; a local read failure returns a generic refusal without a misleading partial report. Four new CLI tests cover empty storage, mixed archived/pending state, error redaction and a later known archive-integrity error. GitHub `main` code commit `00eeb0cb3a8dc2fa5bbe4cb13fb681c40b452b10` passed Verify pilot #134, run `36653736591`, job `109693413426`: **332 Python, 148 Node, 18 generated-site and 74 Chromium tests (572 total)**, Astro check with zero diagnostics, and a 14-page build. The `pilot-verification` artifact is `11071053427`. This is an operator inspection command, not a verified private capture or publication gate.

## New: explicit private reconciliation

The private ledger now supports a fourth write operation, `reconcile`, in addition to `record`, `disposition` and recovery/status operations.

A reconciliation request contains exactly:
- `source_event_revision`: a committed observation event containing the source context the reviewer inspected.
- `proposal_ids`: the active holds being resolved.
- `reviewer` and `rationale`: operator-supplied review metadata.
- `reviewed_at`: the actual editorial review time.
- `records`: the complete resulting private guidance inventory.

Reconciliation is source-level. If a source has multiple active proposals, all of them must be selected; Rocky Mountain's shared source cannot be partially approved. The selected source observation must be the latest retained observation for that source and at least as new as every cleared proposal.

The replacement guidance inventory is validated through the existing rule/note validators. Unaffected records must remain byte-equivalent. Affected records keep the same identity, park and official source, use the exact approved review time, and preserve their existing rights basis and rights-review timestamp. Extra top-level or evidence fields are refused.

The approved excerpt for every affected record must occur exactly once in the retained source context. Missing or duplicated replacement text fails closed. The reconciliation event stores the complete new records plus hashes of the previous and next guidance revisions; prior events remain immutable and reconstructable.

### Reviewed context baseline semantics

Reconciliation derives a persistent **schema-v2 context baseline** from the retained source observation. V2 distinguishes the real editorial sequence: source captured first, then human review/approval. Legacy schema-v1 baselines keep their previous clock semantics.

Subsequent observations automatically consume ledger-held baselines. A caller cannot replace them through a new capture request. When the first explicit reconciliation affects only one source, already-validated legacy baselines for unrelated sources are carried forward rather than silently dropped.

A later matching source observation does not automatically clear a sticky hold. A reviewer may explicitly reconcile from that newer observation if it is the latest retained evidence and the complete source-level hold set is selected.

This is **private editorial approval inside the ledger**, not public publication. The reconcile command does not write `data/`, the website, alert snapshots, public history, deployment state or advertising configuration.

Contract: `docs/GUIDANCE_RECONCILIATION.md` and `docs/ENTRY_REVIEW_LEDGER.md`.

## New: private read-only reviewer packets

`tracker.entry_review_packet` turns one verified ledger snapshot into a deterministic owner-only review packet without network access, ledger mutation, reconciliation, approval or publication.

The operator selects a pilot park and the **latest retained observation event** for that source. Packet generation refuses an unknown/stale event, a source with no retained comparison context, or a source with no active hold.

The packet contains:

- current private approved guidance for the source;
- every active proposal ID that must be reconciled together at source level;
- pending reasons, before excerpts and source-supplied replacement excerpts when present;
- the retained normalized text/H1/link comparison context and context hash;
- exact capture/proposal/review clocks;
- current baseline metadata;
- prior reviewer disposition history; and
- prior reconciliation metadata and old/new guidance hashes.

Dynamic material is escaped. Real `script` elements remain outside the extractor scope; literal script-looking source text is rendered as text. The generated HTML contains no links, images, frames, forms, buttons or scripts and carries a strict Content Security Policy that denies network/connect/object/frame/form activity. Source link targets are shown only as text.

The output directory and packet files are owner-only (`0700` directories, `0600` files) and must live outside the repository under an owner-only parent. Each packet is installed atomically as:

`OUTPUT_DIR/PACKET_ID/index.html`  
`OUTPUT_DIR/PACKET_ID/manifest.json`

The manifest contains metadata/hashes only, including the ledger revision, source event revision, context hash, complete active proposal IDs, guidance hashes and SHA-256 of the HTML. It contains no retained context or private filesystem path. Exact retries are idempotent; a corrupted existing packet is refused rather than overwritten.

A packet is only an inspection snapshot. It deliberately has no `expected_revision` write argument and cannot approve anything. Before a later reconciliation, the operator must re-read the ledger and use its then-current revision.

Operator contract: `docs/REVIEWER_PACKET.md`.

## New: explicit persistent live capture operator path

`tracker.entry_review_live` is the first retained live-entry operator workflow. It reuses the existing fixed NPS transport, source extractor, transactional editorial ledger and read-only reviewer packets; it does not create a second source store.

Before the first network request it requires:

- explicit `--live`;
- an absolute private ledger path accepted by the existing POSIX ledger boundary;
- an absolute packet-output path outside the repository under an owner-only parent; and
- `--expected-revision empty` for a new ledger, or the exact current ledger SHA-256 for a later batch.

A stale expected revision or unsafe packet destination refuses **before network**. The SQLite write still rechecks the expected revision inside its transaction, so a concurrent writer cannot be silently overwritten after capture.

The command then makes one credential-free HTTPS GET to each of the five fixed NPS entry sources using the already-tested transport: no API key, cookies, redirects, retries or arbitrary URL input. Each response remains bounded to 1 MiB and is validated for status, content type/encoding, length and UTF-8 before it can become a successful capture.

All five capture attempts form one complete ledger observation event. Successful raw HTML is retained inside the owner-only SQLite event; failed captures are retained as failed observations rather than discarded or converted into empty success. Existing reconciled baselines are reused automatically. The live append also preserves the latest validated legacy schema-v1 baseline input until explicit reconciliation creates ledger-held baselines, so a later capture cannot manufacture a fresh `context_not_reviewed` hold merely by dropping prior reviewed context. An existing ledger keeps its own current private guidance inventory rather than silently adopting changed repository guidance.

After the ledger commit, the command prepares reviewer packets for every source that has active holds and retained comparison context. A failed source receives no fabricated packet. Packet-generation failures do **not** roll the already committed live evidence back.

Operator command:

```sh
uv run --frozen python -m tracker.entry_review_live \
  --live \
  --store /absolute/private/entry-review \
  --packet-output-dir /absolute/private/review-packets \
  --expected-revision empty
```

For every later run, first use `entry_review_cli status` and replace `empty` with the exact returned revision.

Exit semantics:

- **0** — the complete batch was committed, all five captures succeeded, and every source requiring review has a packet (or no packet is needed).
- **1** — the batch was committed, but at least one capture or required packet is incomplete. This is retained evidence, not a rollback; inspect the safe JSON report and ledger.
- **2** — configuration, validation, stale-write or unexpected failure prevented a normal report. Re-read ledger status before retrying because concurrent/post-commit failures must never be guessed from an exit code alone.

The safe JSON report exposes source URL, HTTP status, capture reason, capture/context hashes, active-hold counts, packet IDs and the committed ledger/source-event revisions. It excludes raw HTML, retained normalized text and private filesystem paths.

This command never calls `reconcile`, never updates public `data/`, never deploys, and never schedules itself. No `NPS_API_KEY` is read or needed.

Contract: `docs/PERSISTENT_ENTRY_CAPTURE.md`.

## New: private ledger backup, verification and restore

`tracker.entry_review_backup` provides an owner-only backup/restore mechanism for the private editorial SQLite ledger. It does not back up public site data and performs no network request, source capture, review decision, reconciliation or publication.

Backup first performs a full ledger replay. It then uses SQLite's backup API to create a transactionally consistent database snapshot in a temporary owner-only directory. The copied database is replayed again and must equal the previously verified logical ledger state before it can be accepted.

A content-addressed manifest binds:

- ledger revision;
- event, guidance-record and pending-proposal counts;
- exact database byte length;
- SHA-256 of the backed-up SQLite database; and
- explicit `network_performed:false`, `approval_performed:false`, and `publication_performed:false`.

The backup ID is SHA-256 over that manifest core. A completed bundle is:

`BACKUP_ROOT/BACKUP_ID/review.sqlite3`  
`BACKUP_ROOT/BACKUP_ID/manifest.json`

Backup roots and files are owner-only and must be outside the repository under an owner-only parent. Exact retries reuse an identical verified bundle. Corrupt/mismatched bundles or unexpected files are refused rather than overwritten.

`verify` checks private permissions, exact bundle contents, manifest identity, database size/SHA-256 and full semantic ledger replay without modifying the backup.

`restore` accepts only a fully verified bundle and only a brand-new destination. It copies into a temporary owner-only ledger directory, replays the restored database, and atomically renames it into place only after the restored head/counts match the backup manifest. Existing destinations are never overwritten. Interrupted backup/restore tests confirm no completed destination is exposed.

Commands and limitations: `docs/ENTRY_REVIEW_BACKUP.md`.

This mechanism makes local backup/restore testable, but it does **not** create an off-host backup service, choose backup media, encrypt the database, authenticate reviewers, certify native Windows/network filesystems, or prove hardware power-loss durability. Those remain operator/storage decisions.

## New: read-only release-readiness report

`tracker.release_readiness` consolidates the pilot launch gates into one deterministic, non-mutating report. It never contacts providers, deploys, changes indexing, enables advertising, writes public/private state, or interprets missing evidence as success.

Default repository-only command:

```sh
uv run --frozen python -m tracker.release_readiness --format text
```

Machine-readable form:

```sh
uv run --frozen python -m tracker.release_readiness --format json
```

When owner-controlled private evidence exists, the report can also replay the private ledger and verify a specific content-addressed backup before evaluating those private gates:

```sh
uv run --frozen python -m tracker.release_readiness \
  --format text \
  --store /absolute/private/entry-review \
  --backup /absolute/private/backups/BACKUP_ID
```

The seven gates are:

1. durable source review;
2. NPS alert API validation;
3. private storage backup;
4. source-rights review;
5. hosting and rollback;
6. search indexing; and
7. advertising readiness.

Status values are only `pass`, `blocked`, or `not_checked`. In schema 2, a non-pass status is release-blocking when its gate is required for the selected target. The default pilot requires the first five gates; unchanged indexing controls and absent ads remain later-target gates.

The current repository-only result is deliberately **BLOCKED**:

- durable source review — `not_checked`: no owner private ledger supplied;
- NPS alert API — `blocked`: all five public snapshots are still `never_checked`;
- storage backup — `not_checked`: no owner private ledger/verified backup supplied;
- source rights — `pass`: the exact six public NPS text uses have record-level metadata and the matching rights manifest; this does not clear broader or future uses;
- hosting/rollback — `not_checked`: a manual verified-artifact deployment path exists, but no live URL or rollback is verified;
- indexing — `blocked` for its later target: repository controls remain intact; not required for the default pilot;
- advertising — `blocked` for its later target: no ad integration is enabled; not required for the default pilot.

The alert gate intentionally never describes `never_checked` snapshots as “no alerts” or an all-clear. If future public snapshots become successful, the static report still returns `not_checked` until freshness/provider compatibility has release evidence rather than self-promoting collection success.

The private source-review gate passes only when the verified private state has schema-v2 reviewed context baselines for all five fixed entry sources and zero pending proposals. The private backup gate passes only when a previously verified backup manifest matches the exact current ledger head and event count.

This report is an evidence summary, not an authorization to launch. Removing `noindex`, adding deployment/ad code, or supplying a private ledger changes individual evidence but does not itself approve release.

Contract: `docs/RELEASE_READINESS.md`.

## New: NPS alert preflight gate hardening

The read-only keyed NPS alert preflight was rerun on the current feature branch after expanding its validation trigger to changes in the workflow, `tracker/preflight.py`, and `tracker/alerts.py`. It remains unscheduled and has read-only repository permissions.

Current run **36607959537**, job **109541744290**, head **16dda2f20c504ada6d9740c1de38f458e47cb7f9**, returned:

```json
{"schema_version":1,"mode":"read_only","status":"not_configured","gate_passed":false,"publication_performed":false,"checks":[]}
```

The runner still received no usable `NPS_API_KEY`, so it made zero provider requests and changed no data. This establishes the current branch configuration state for that execution; it does not expose or directly inspect repository secrets.

The preflight exit contract is now release-gate aligned:

- `verified` / `gate_passed:true` → exit 0;
- `needs_review` → exit 1;
- `not_configured` or `invalid_configuration` → exit 2.

Therefore the current preflight workflow is intentionally **red** while the key is unavailable. A successful Actions job can no longer visually imply that the alert integration is verified when `gate_passed:false`.

The public alert snapshots are untouched and remain `never_checked`; this diagnostic does not publish or stage data. Configure the owner-controlled repository secret named exactly `NPS_API_KEY` before expecting this gate to pass. Do not send the key through chat, issues, or committed files.

Contract and exact run evidence: `docs/NPS_PREFLIGHT.md`.

## New: gated GitHub Pages deployment and rollback path

`.github/workflows/pages-release.yml` adds a production-hosting path without making the site live. The workflow is **manual-only** (`workflow_dispatch`); it has no push, pull-request, or schedule trigger.

Every deployment or rollback requires all four explicit inputs:

- `mode`: `deploy` or `rollback`;
- `target_sha`: an exact lowercase 40-character commit SHA;
- `verify_run_id`: the GitHub Actions run ID containing the verified build artifact; and
- `confirmation`: exactly `DEPLOY_VERIFIED_PILOT` or `ROLLBACK_VERIFIED_PILOT` for the selected mode.

The workflow queries GitHub for that run and refuses unless it is a **successful `Verify pilot` push run on the repository default branch** and its `head_sha` exactly matches `target_sha`. It then downloads that run's existing `pilot-verification` artifact. It does not check out source or run a fresh build during release, so deployment and rollback use the exact static output that already passed verification.

Only `_verified/dist` is repackaged as the Pages artifact. The workflow requires `dist/index.html` and `dist/build.json` and refuses symlinks.

The current verified frontend uses root-absolute links and Astro asset URLs. Default GitHub **project Pages** would serve under `/us-national-park-trip-readiness-tracker/` and would therefore break those URLs. The workflow reads the official `actions/configure-pages@v5` `base_path` output and refuses any nonempty Pages base path **before** artifact upload/deployment. The current build therefore requires root hosting, such as an appropriately configured custom domain, unless the application is later made base-path aware.

The workflow grants only `contents: read`, `actions: read`, `pages: write`, and `id-token: write`. Deployment uses the standard `github-pages` environment and `actions/deploy-pages@v4`.

Rollback is the same artifact path with `mode: rollback` and an older successful default-branch Verify run. It never runs `git revert`, `git reset`, or pushes source changes. The current `pilot-verification` artifact retention is seven days, so this rollback mechanism only covers verified runs whose artifacts have not expired.

No release workflow was dispatched during the implementation or the later `main` integration. PR #1 is now marked merged, and all existing `noindex` controls remain unchanged. `public/_headers` is retained in the build, but GitHub Pages does not by itself establish that those custom response headers are effective; real hosting/header behavior remains part of the post-deployment verification gate.

The release-readiness `hosting_rollback` gate now moves from `blocked` to **`not_checked`**: a deployment/rollback mechanism exists, but no real production URL or rollback has been exercised.

Contract: `docs/PAGES_RELEASE.md`.

## New: exact public NPS text source-rights evidence

`data/source-rights.json` now records the commercial-use evidence for the **exact six public guidance records** and their five NPS source pages. This is deliberately narrower than a claim about all material on NPS websites.

The review is grounded in the current official NPS disclaimer and Arrowhead-use guidance:

- NPS-created material on the NPS website is generally considered public domain unless otherwise indicated;
- NPS asks for source acknowledgement, and commercial republication should include a reference to the original U.S. Government work, such as **“No protection is claimed in original U.S. Government works.”**;
- third-party material must not be assumed public domain; and
- the NPS Arrowhead and other protected marks are not covered by the public-domain rule and require separate authorization.

The manifest therefore allows only:

- the six already-reviewed short NPS text excerpts;
- the project's original planning summaries tied to those records; and
- source attribution/links.

It explicitly records **no third-party material, NPS marks, photographs, graphics, audio/video, or private raw captures** as approved for public reproduction.

`scripts/validate-source-rights.ts` makes exact manifest coverage part of the normal build gate. Omitting or duplicating a guidance record, changing its source URL, claiming marks/media/third-party content, changing the policy URLs, or changing the commercial notice fails validation.

The site footer now includes the commercial U.S. Government-work notice while retaining the existing independent/non-endorsement statement.

The release-readiness source-rights gate now passes only when:

- all six public guidance records retain their record-level rights metadata;
- `source-rights.json` exactly covers all six record/source pairs;
- every covered item remains classified as NPS government text with no third-party/mark/media reproduction;
- the commercial notice is present in the public layout; and
- the public application contains no media asset or reproduced NPS mark/media reference outside this text-only scope.

This **passes the current public-text scope only**. It is not legal advice or blanket clearance for other NPS pages/content. Adding photos, graphics, logos/marks, audio/video, third-party material, or public raw source captures requires a new rights review and evidence update.

Contract: `docs/SOURCE_RIGHTS.md`.

## New: keyed NPS alert API compatibility validated

The owner configured the repository Actions secret `NPS_API_KEY`, and the existing read-only preflight was rerun against live NPS alert responses.

The first keyed request proved authentication was working but exposed collector assumptions that were stricter than the current provider contract. Safe diagnostic mode was added so preflight could report only allowlisted validation reasons—never provider text, credentials, or raw payloads.

Live diagnostics identified:

- Yosemite and Zion alert records with provider-supplied links outside the old hardcoded NPS-host/path rule; and
- a Grand Canyon alert with no direct URL.

The official NPS alert schema documents `url` as a link supplied only **if available**. The collector/history/build contracts were therefore updated so:

- `parkCode` remains the authoritative park-scope field;
- an absent alert URL is normalized to `null`, not invented;
- safe provider-supplied external HTTPS links are retained;
- the UI labels such links as **“More information link supplied by NPS”** rather than implying NPS ownership of the destination; and
- credentials, secret-bearing query/fragment values, malformed/path-traversal URLs, localhost/numeric-IP targets, and NPS-lookalike hosts remain rejected.

The final keyed compatibility run **36628434444**, job **109611267322**, at 2026-09-29T20:44:13–20:44:14Z returned:

- Yosemite — success, 1 record;
- Rocky Mountain — success, 0 records;
- Yellowstone — success, 5 records;
- Zion — success, 8 records;
- Grand Canyon — success, 3 records.

Each park required one page, every diagnostic code was null, `gate_passed:true`, and `publication_performed:false`.

This proves the current keyed NPS API integration/normalization path for the five pilot parks. It does **not** mean the public site is collecting live alerts yet. The public alert snapshots and public history remain untouched/`never_checked`. The next alert milestone is durable private collection/staging and review before any public data publication.

Exact safe evidence: `docs/NPS_PREFLIGHT.md`.

## TDD and self-review record

The reconciliation contract was developed test-first.

- Verify pilot #47 (`36579697560`) failed because `reconcileEntryReview` did not exist.
- Initial implementation exposed a clock-model mismatch between legacy baselines and explicit review-after-capture; schema-v2 baselines were introduced without weakening v1.
- Verify pilot #51 (`36581315199`) reproduced acceptance of extra unreviewed schema fields; exact record/evidence shape is now required.
- Verify pilot #53 (`36581590068`) reproduced rejection of a valid newer matching source observation while an older hold remained; reconciliation now binds to the latest retained source observation.
- Verify pilot #56 (`36582585446`) reproduced loss of an unrelated reviewed legacy baseline when reconciling one source; unaffected latest validated baselines are now preserved.

The final review-focus tests also cover absent and duplicated approved excerpts, partial source-level proposal selections, exact retry, caller baseline override, stale source observations, CLI redaction and unchanged rights metadata.

Review was **author self-review**, not independent approval.

## Earlier implementation verification

Code/test head: **`1ed3731e7590bc9b952276aac757a6c248611569`**.

**Verify pilot #130, run `36637313452`, job `109641517736`, completed successfully.**

| Check | Verified result |
|---|---:|
| Node core/data/review/rights/history tests | 148 passed |
| Python collector/archive/extraction/ledger/reconciliation/packet/live/backup/readiness/Pages/rights/preflight tests | 323 passed |
| Generated-output tests | 18 passed |
| Chromium browser tests | 74 passed |
| **Total automated tests** | **563 passed** |
| Astro check | 24 files; 0 errors, 0 warnings, 0 hints |
| Production static build | 14 HTML pages plus `build.json` |

The keyed-alert compatibility increment was driven by live read-only provider evidence plus synthetic regressions. Initial keyed runs proved authentication worked but quarantined Yosemite/Zion/Grand Canyon. Diagnostic-code tests then failed first before safe allowlisted diagnostics were added. Provider-compatible tests failed before nullable URLs, NPS subdomains, and safe provider-supplied external HTTPS links were accepted across collector, Python/TypeScript history validation, build validation, and rendering.

The earlier regression run #130 passed all 563 automated tests. The later `main` run #132 passed 568, as recorded above. Separately, keyed NPS preflight run **36628434444** passed all five parks with `gate_passed:true`; it used the same collector semantics and performed no public writes.

Verification artifact `pilot-verification`, ID **11064403957**, contains the production site build, screenshots and lockfile—not API credentials, live raw payloads, private archives, or published alert data. CI-reported ZIP SHA-256: `36548eafd4330bec7afb8898a1ef32d2db37ab43585de3f21e53faf701cab1ae`.

Review was author self-review because no independent reviewer/subagent tool is available. No deployment/indexing/advertising/public-alert publication occurred.

## Previously verified real-page compatibility

Diagnostic run `36575873171`, job `109431220513`, captured the five exact configured NPS entry pages on September 29, 2026. All five returned HTTP 200; all body-text/link contexts extracted; all six saved guidance excerpts were uniquely present; temporary ledger replay succeeded.

Every source reason was `context_not_reviewed`, with six temporary holds and **zero approved context baselines**. Those captures were deliberately discarded after the diagnostic. They are compatibility evidence, not a durable reviewed reference archive and not proof that park requirements are unchanged.

Exact safe retrieval metadata and hashes remain in `docs/LIVE_ENTRY_COMPATIBILITY.md`.

## Remaining gates

No real reviewer has used the new reconciliation command on a durable NPS capture. Therefore there are still **zero durable real approved context baselines** created by this workflow.

The private ledger remains owner-only local POSIX storage, not hosted durable storage, encryption, authenticated reviewer identity or multi-host storage. Backup/verify/restore mechanics are now tested, but no off-host target, retention schedule, removable-media policy or cloud backup has been configured. Hardware power-loss, native Windows/network filesystems and hostile same-user mutation remain outside verified guarantees.

The exact six-record public NPS **text-only** rights scope now has explicit evidence and passes its release-readiness gate. This does not clear private raw captures, NPS marks/media, third-party material, or future source uses. Hashes prove internal consistency, not factual truth or source authenticity.

The keyed NPS alerts integration is now **validated**. Read-only run **36628434444**, job **109611267322**, completed with `status: verified` and `gate_passed:true` for all five pilot parks: Yosemite 1 record, Rocky Mountain 0, Yellowstone 5, Zion 8, and Grand Canyon 3. The run wrote no public snapshots or history, so public `data/alerts/*.json` remain `never_checked`. Provider compatibility and public collection/publication remain separate gates.

No scheduler, real deployment, indexing, advertising, tracking, account system, spending or provider agreement was activated. A manual Pages deployment/rollback workflow now exists but was not dispatched. Neither pilot release milestone is declared complete.

## Next coherent task

The code-side private storage gates now include capture, ledger replay, reviewer packets, reconciliation, backup/restore, a five-park alert staging command, and a manual verified-artifact hosting/rollback path. The next trust milestone remains an **owner-controlled real five-source entry-page capture and human review session**, together with a real five-park alert staging run on durable private POSIX/WSL storage. The keyed NPS alert preflight has already succeeded; do not treat it as public collection.

Run `entry_review_live --check-only` on the chosen private paths with the expected empty/current ledger head before the real capture. Both private parents must already exist with owner-only permissions. A successful offline setup report does not perform or approve that capture.

Before reviewing or reconciling real guidance, create a content-addressed ledger backup with `entry_review_backup backup`, run `verify`, and keep a second verified copy on owner-controlled storage separate from the working ledger. Then inspect the generated packets and use `reconcile` only for guidance a human actually approves.

That real session cannot be performed in this development environment because the current tools do not provide the user's durable private POSIX/WSL filesystem or backup destination. Do not substitute GitHub Actions artifacts, repository files or public hosted storage for the editorial ledger/backup.

The keyed NPS alert API compatibility gate is now validated. The batch command makes durable private staging/archive collection easier to operate, but it still needs owner-controlled storage, a real run, backup and review before public snapshot/history publication.

## Verification lineage

Prior communicated totals: 79 foundation; 109 source coverage; 167 private history; 206 staging; 246 visitor history; 293 previews; 309 planning links; 347 accessibility; 380 selected-source gate; 416 extraction; 460 ledger/identity; 488 live entry compatibility; 563 before five-park batch staging; 568 at the initial `main` integration. The offline five-park status increment passed **572 tests** at `00eeb0c`, Verify pilot #134. PR #1 is merged; the site release gates remain blocked or not checked.
